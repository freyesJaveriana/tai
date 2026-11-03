#!/bin/bash
# Validación US14.1, M1 (AC14.1.1): velocidad de Qwen3.6-35B-A3B Q8_0 en un SL250s con llama-bench (lectura de 2.048
# tokens y generación de 128, 16 hilos, 3 repeticiones). Las horas de la medición --array=8 de la 4L las resume
# aparte m1-resumen-4l.sbatch, que se puede volver a lanzar mientras esa medición sigue.
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch trabajos/m1-velocidad.sbatch
# Como la 4L ocupa los SL250s con --exclusive, este trabajo espera un nodo libre; con --dependency=afterany:<id> se
# encadena detrás de un trabajo concreto.
#SBATCH --job-name=val-m1
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --exclusive
#SBATCH --mem=58G
#SBATCH --time=04:00:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m1-velocidad_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar
preparar_salida m1
date; hostname; nproc
llama-bench --version 2>&1 | head -2 || true
MODELO=$(copiar_local "$MODELOS/$QWEN" /tmp/tg4L)
COMANDO="llama-bench -m $QWEN -t 16 -p 2048 -n 128 -r 3 -o json"
llama-bench -m "$MODELO" -t 16 -p 2048 -n 128 -r 3 -o json > "$SALIDA/bench.json"
cabecera "sbatch trabajos/m1-velocidad.sbatch ($COMANDO)" "SHA-256 del modelo: $(sha_modelo "$MODELOS/$QWEN")"
python "$TRABAJOS/resumir_bench.py" "$SALIDA/bench.json" | tee -a "$SALIDA/resumen.txt"
date
