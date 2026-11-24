#!/bin/bash
# Validación US14.1, M1 (AC14.1.1), segunda parte: cifras de la medición --array=8 de la 4L (llamadas, tokens y horas
# de registro_4L_8.csv y velocidad del log de llama-server). Solo lee los archivos de la 4L. Se puede lanzar mientras
# la medición sigue (cifras parciales) y otra vez cuando termine. Corre en el nodo de entrada (ZINE_NODO): no ocupa
# un SL250s. Variables y salida relativa: ver m0-entorno.sbatch y README.md.
#   cd "$ZINE_BASE/validacion" && sbatch --nodelist="$ZINE_NODO" trabajos/m1-resumen-4l.sbatch
#SBATCH --job-name=val-m1-4l
#SBATCH --partition=debug
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:15:00
#SBATCH --output=logs/m1-resumen-4l_%j.out
set -euo pipefail
source "${ZINE_BASE:?fije ZINE_BASE}/validacion/trabajos/comun.sh"
activar
SALIDA=$VALID/m1
mkdir -p "$SALIDA"
COMPARACION=$TG4L/repo/02-procedimientos/02-Construccion_matriz/piloto/comparacion
date
{
    echo "Comando: sbatch trabajos/m1-resumen-4l.sbatch (lee registro_4L_8.csv y logs/4L_8_*)"
    echo "Trabajo SLURM: $SLURM_JOB_ID"
    echo "Fecha del resumen: $(date '+%F %T')"
    python "$TRABAJOS/resumen_4l.py" --registro "$COMPARACION/registro_4L_8.csv" --logs "$TG4L/logs" --indice 8
} | tee "$SALIDA/resumen_4l.txt"
