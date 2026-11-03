# Variables y funciones comunes de la validación de modelos locales (US14.1), en el clúster Ing. Sistemas.
# Se carga con «source» desde cada .sbatch. Reutiliza el entorno conda y los modelos de la tarea 4L sin
# modificarlos (solo lectura) y escribe únicamente bajo tg4L/validacion/ (salvo la copia del GGUF en el /tmp
# local del nodo, la misma que usa la 4L). Los nodos no conocen la cuenta y $HOME no existe en ellos: se fija aquí.
TG4L=/zine/HPC02S1/freyes/tg4L
VALID=$TG4L/validacion
export HOME=$VALID/home XDG_CACHE_HOME=$VALID/home/.cache PIP_CACHE_DIR=$VALID/home/.cache/pip
export PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
unset LD_LIBRARY_PATH  # el .bashrc lo apunta al miniconda compartido; mezclaría bibliotecas con el entorno
ENV=$TG4L/envs/tg4L            # entorno de la 4L: Python 3.12 y llama.cpp de conda-forge (solo lectura)
MODELOS=$TG4L/modelos          # GGUF de la 4L con su .sha256ok (solo lectura)
TRABAJOS=$VALID/trabajos       # estos scripts, copiados con enviar.ps1
VENV=$VALID/venv               # entorno virtual de la validación (m0-entorno.sbatch), con jsonschema
QWEN=Qwen3.6-35B-A3B-Q8_0.gguf
CONTEXTO_QWEN=163840
mkdir -p "$HOME" "$PIP_CACHE_DIR" "$VALID/logs"

activar() { export PATH=$ENV/bin:/usr/bin:/bin; }
activar_venv() { export PATH=$VENV/bin:$ENV/bin:/usr/bin:/bin; }

# Directorio de salida de la medición: lo vacía de resúmenes anteriores, pero no de modelos ni wheelhouse.
preparar_salida() {  # $1 = m1, m2, …
    SALIDA=$VALID/$1
    mkdir -p "$SALIDA"
    : > "$SALIDA/resumen.txt"
}

# SHA-256 publicado y comprobado al descargar (archivo .sha256ok junto al GGUF).
sha_modelo() {  # $1 = ruta del GGUF en el NFS
    if [ -f "$1.sha256ok" ]; then cut -d' ' -f1 "$1.sha256ok"; else echo "sin .sha256ok para $(basename "$1")"; fi
}

# Primeras líneas del resumen, en el formato que pide reporte.md.
cabecera() {  # $1 = comando, $2 = línea de modelo («SHA-256 del modelo: …» o «No aplica: …»), $3 = archivo
    local destino=${3:-$SALIDA/resumen.txt}
    {
        echo "Comando: $1"
        echo "Trabajo SLURM: ${SLURM_JOB_ID:-sin trabajo}"
        echo "Nodo: $(hostname -s)"
        echo "$2"
    } >> "$destino"
}

# Copia el GGUF al disco local del nodo (el NFS se satura si varios nodos cargan a la vez) y escribe su ruta.
copiar_local() {  # $1 = ruta del GGUF en el NFS, $2 = carpeta local
    local destino
    destino=$2/$(basename "$1")
    mkdir -p "$2"
    if [ "$(stat -c %s "$destino" 2>/dev/null)" != "$(stat -c %s "$1")" ]; then
        echo "$(date '+%F %T') copiando $(basename "$1") al disco local" >&2
        cp "$1" "$destino.part" && mv "$destino.part" "$destino"
    fi
    echo "$destino"
}

# Espera a que llama-server responda en /health (hasta 30 minutos para cargar el modelo).
esperar_servidor() {  # $1 = puerto, $2 = PID del servidor, $3 = log del servidor
    for _ in $(seq 360); do
        if curl -sf "http://127.0.0.1:$1/health" > /dev/null; then return 0; fi
        kill -0 "$2" 2>/dev/null || { echo "llama-server terminó: ver $3"; return 1; }
        sleep 5
    done
    echo "llama-server no respondió en 30 minutos"; return 1
}
