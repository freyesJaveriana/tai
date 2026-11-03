#!/bin/bash
# Validación US14.1, M6 (AC14.1.6), primera parte: descarga en hpchead02 un GGUF de una familia distinta de Qwen para
# el verificador del perfil de evaluación y comprueba su SHA-256 contra el que publica Hugging Face (lfs.oid). Guarda
# también la licencia que declara el repositorio, para decidir si es compatible con el TG (DT10). Escribe en
# validacion/modelos/ y validacion/m6/; reanuda una descarga cortada y no vuelve a bajar un archivo ya comprobado.
# Predeterminado: gpt-oss-20b (OpenAI, Apache 2.0, MoE de ~3,6B parámetros activos) en Q8_0. Otro modelo:
#   sbatch --export=ALL,REPO=<usuario/repo-GGUF>,ARCHIVO=<archivo.gguf> trabajos/m6-descargar.sbatch
# Si el archivo no existe en el repositorio, el trabajo falla y lista los .gguf que sí hay.
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch trabajos/m6-descargar.sbatch
#SBATCH --job-name=val-m6-dl
#SBATCH --partition=debug
#SBATCH --nodelist=hpchead02
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=12:00:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m6-descargar_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar
REPO=${REPO:-unsloth/gpt-oss-20b-GGUF}
ARCHIVO=${ARCHIVO:-gpt-oss-20b-Q8_0.gguf}
mkdir -p "$VALID/modelos" "$VALID/m6"
DESTINO=$VALID/modelos/$(basename "$ARCHIVO")
date; hostname
ARBOL=$(curl -sf "https://huggingface.co/api/models/$REPO/tree/main?recursive=true")
ESPERADO=$(python -c '
import json, sys
for f in json.loads(sys.argv[1]):
    if f["path"] == sys.argv[2] and f.get("lfs"): print(f["lfs"]["oid"])' "$ARBOL" "$ARCHIVO")
if [ -z "$ESPERADO" ]; then
    echo "$ARCHIVO no está en $REPO. Archivos .gguf del repositorio:"
    python -c 'import json, sys; [print(" ", f["path"], f.get("size")) for f in json.loads(sys.argv[1]) if f["path"].endswith(".gguf")]' "$ARBOL"
    exit 1
fi
LICENCIA=$(curl -sf "https://huggingface.co/api/models/$REPO" | python -c '
import json, sys
d = json.load(sys.stdin)
print((d.get("cardData") or {}).get("license") or next((t[8:] for t in d.get("tags", []) if t.startswith("license:")), "sin declarar"))')
echo "$REPO/$ARCHIVO: licencia $LICENCIA, sha256 esperado $ESPERADO"

if [ -f "$DESTINO.sha256ok" ] && [ "$(cut -d' ' -f1 "$DESTINO.sha256ok")" = "$ESPERADO" ]; then
    echo "$(basename "$ARCHIVO"): ya comprobado"
else
    # Hugging Face corta conexiones largas: se reanuda desde donde quedó, hasta 100 veces (como 02_modelos de la 4L).
    for intento in $(seq 100); do
        if curl -fsSL -C - --speed-limit 1000000 --speed-time 120 -o "$DESTINO.part" \
                "https://huggingface.co/$REPO/resolve/main/$ARCHIVO"; then break; fi
        echo "$(date '+%F %T') intento $intento cortado en $(du -h "$DESTINO.part" | cut -f1); se reanuda en 30 s"
        sleep 30
    done
    OBTENIDO=$(sha256sum "$DESTINO.part" | cut -d' ' -f1)
    if [ "$OBTENIDO" != "$ESPERADO" ]; then echo "SHA-256 distinto ($OBTENIDO); se borra"; rm -f "$DESTINO.part"; exit 1; fi
    mv "$DESTINO.part" "$DESTINO" && echo "$ESPERADO  $(basename "$ARCHIVO")" > "$DESTINO.sha256ok"
fi
{
    echo "Descarga: trabajo $SLURM_JOB_ID en $(hostname -s)"
    echo "Modelo: $REPO/$ARCHIVO ($(du -h "$DESTINO" | cut -f1)), licencia declarada: $LICENCIA"
    echo ".sha256ok: $(cat "$DESTINO.sha256ok")"
} | tee "$VALID/m6/descarga.txt"
echo "$(basename "$ARCHIVO")" > "$VALID/m6/archivo.txt"
date
