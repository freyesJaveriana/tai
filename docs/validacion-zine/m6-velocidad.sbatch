#!/bin/bash
# Validación US14.1, M6 (AC14.1.6), segunda parte: velocidad del modelo de otra familia (el que bajó
# m6-descargar.sbatch) en un SL250s con llama-bench, con los mismos parámetros que M1.
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch --dependency=afterok:<descarga> trabajos/m6-velocidad.sbatch
#SBATCH --job-name=val-m6
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --exclusive
#SBATCH --mem=58G
#SBATCH --time=04:00:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m6-velocidad_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar
preparar_salida m6
date; hostname; nproc
ARCHIVO=$(cat "$VALID/m6/archivo.txt")
MODELO=$(copiar_local "$VALID/modelos/$ARCHIVO" /tmp/tg4L-validacion)
COMANDO="llama-bench -m $ARCHIVO -t 16 -p 2048 -n 128 -r 3 -o json"
llama-bench -m "$MODELO" -t 16 -p 2048 -n 128 -r 3 -o json > "$SALIDA/bench.json"
cabecera "sbatch trabajos/m6-descargar.sbatch y trabajos/m6-velocidad.sbatch ($COMANDO)" \
    "SHA-256 del modelo: $(sha_modelo "$VALID/modelos/$ARCHIVO")"
cat "$SALIDA/descarga.txt" >> "$SALIDA/resumen.txt"
python "$TRABAJOS/resumir_bench.py" "$SALIDA/bench.json" | tee -a "$SALIDA/resumen.txt"
cat "$SALIDA/resumen.txt"
date
