#!/bin/bash
# Validación US14.1, M2 y M4 (AC14.1.2 y AC14.1.4) con un solo llama-server de conda-forge en un SL250s: así el
# modelo (36,9 GB) se carga una vez. M2 sondea la API compatible con OpenAI (esquema JSON o gramática, seed, caché del
# prompt, razonamiento encendido y apagado; 20 peticiones por caso) y M4 la repetibilidad con --parallel 1. Escribe
# en validacion/m2/ y validacion/m4/. Requiere m0-entorno.sbatch (jsonschema).
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch trabajos/m2-api-servidor.sbatch
#   sbatch --export=ALL,N=5 trabajos/m2-api-servidor.sbatch          prueba corta (5 peticiones por caso)
# Duración: con el razonamiento encendido cada petición puede generar hasta 4.096 tokens; a ~6 tokens/s el trabajo
# completo puede pasar de 15 horas.
#SBATCH --job-name=val-m2-m4
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --exclusive
#SBATCH --mem=58G
#SBATCH --time=3-00:00:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m2-api-servidor_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar_venv
preparar_salida m2
preparar_salida m4
date; hostname; nproc
VERSION=$(llama-server --version 2>&1 | grep -m1 version || true)
echo "llama.cpp: $VERSION"
MODELO=$(copiar_local "$MODELOS/$QWEN" /tmp/tg4L)
PUERTO=18100
HILOS=${SLURM_CPUS_PER_TASK:-16}
# Mismos argumentos de muestreo que la 4L (plan_local.json); contexto corto porque el prompt sintético es pequeño.
ARGUMENTOS="-c 16384 -t $HILOS -np 1 --jinja --reasoning-format deepseek --temp 0.6 --top-p 0.95 --top-k 20"
LOG_SERVIDOR=$VALID/logs/m2-api-servidor_${SLURM_JOB_ID}_servidor.log
# shellcheck disable=SC2086
llama-server -m "$MODELO" $ARGUMENTOS --host 127.0.0.1 --port "$PUERTO" > "$LOG_SERVIDOR" 2>&1 &
SERVIDOR=$!
trap 'kill $SERVIDOR 2>/dev/null || true' EXIT
esperar_servidor "$PUERTO" "$SERVIDOR" "$LOG_SERVIDOR"
echo "$(date '+%F %T') servidor listo"

SHA="SHA-256 del modelo: $(sha_modelo "$MODELOS/$QWEN")"
COMANDO="sbatch trabajos/m2-api-servidor.sbatch (llama-server $QWEN $ARGUMENTOS; sondeo_api.py --n ${N:-20})"
cabecera "$COMANDO" "$SHA" "$VALID/m2/resumen.txt"
cabecera "$COMANDO" "$SHA" "$VALID/m4/resumen.txt"
echo "Servidor: $VERSION, $HILOS hilos, --parallel 1" | tee -a "$VALID/m2/resumen.txt" >> "$VALID/m4/resumen.txt"
python "$TRABAJOS/sondeo_api.py" --url "http://127.0.0.1:$PUERTO" --m2 "$VALID/m2" --m4 "$VALID/m4" --n "${N:-20}"
cat "$VALID/m2/resumen.txt" "$VALID/m4/resumen.txt"
date
