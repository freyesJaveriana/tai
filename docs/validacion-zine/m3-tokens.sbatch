#!/bin/bash
# Validación US14.1, M3 (AC14.1.3): tokens de Qwen de las entrevistas del piloto frente al contexto de 163.840. Las
# entrevistas (los .json reducidos del piloto) las copia enviar.ps1 por scp a validacion/entrevistas/; nunca entran a
# Git. llama-tokenize solo carga el vocabulario del GGUF, así que corre en hpchead02 sin ocupar un SL250s.
# Como prompt de referencia se cuenta el prompt v2 congelado de la 4L (el del analizador aún no existe); otro:
#   sbatch --export=ALL,PROMPT=/ruta/prompt.md,RESERVA=16384 trabajos/m3-tokens.sbatch
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch trabajos/m3-tokens.sbatch
# Si llama-tokenize no corre en hpchead02 (sin AVX), lanzarlo en un SL250s:
#   sbatch --nodelist=hpc02-w006 --exclusive --mem=58G trabajos/m3-tokens.sbatch
#SBATCH --job-name=val-m3
#SBATCH --partition=debug
#SBATCH --nodelist=hpchead02
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m3-tokens_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar
preparar_salida m3
date; hostname
PROMPT=${PROMPT:-$TG4L/repo/02-procedimientos/03-Corpus/salida/comparacion/prompt_codificador_v2.md}
RESERVA=${RESERVA:-16384}
cabecera "sbatch trabajos/m3-tokens.sbatch (contar_tokens.py con llama-tokenize -m $QWEN; reserva de salida $RESERVA)" \
    "SHA-256 del modelo: $(sha_modelo "$MODELOS/$QWEN")"
python "$TRABAJOS/contar_tokens.py" --modelo "$MODELOS/$QWEN" --entrevistas "$VALID/entrevistas" --prompt "$PROMPT" \
    --salida "$SALIDA" --contexto "$CONTEXTO_QWEN" --reserva-salida "$RESERVA" | tee "$SALIDA/conteo.log"
grep '^Resultado:' "$SALIDA/conteo.log" >> "$SALIDA/resumen.txt"
cat "$SALIDA/resumen.txt"
date
