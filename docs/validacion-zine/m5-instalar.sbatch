#!/bin/bash
# Validación US14.1, M5 (AC14.1.5), segunda parte: en un SL250s sin internet, crea un entorno virtual sobre el Python
# del entorno conda de la 4L, instala el paquete de prueba solo desde la wheelhouse (pip install --no-index
# --find-links) y ejecuta su entry point. Termina con código 0 solo si todo eso funciona. Al final cuenta en el log
# del trabajo las líneas de descarga de internet, que deben ser 0.
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch --dependency=afterok:<wheelhouse> trabajos/m5-instalar.sbatch
#SBATCH --job-name=val-m5-inst
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --exclusive
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m5-instalar_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar
preparar_salida m5
date; hostname
LOG=$VALID/logs/m5-instalar_${SLURM_JOB_ID}.out
if curl -sS --max-time 10 -o /dev/null https://pypi.org/simple/ 2>/dev/null; then
    RED="el nodo SÍ tiene salida a internet"
else
    RED="el nodo no tiene salida a internet (esperado)"
fi
echo "Red: $RED"
rm -rf "$SALIDA/venv"
python -m venv "$SALIDA/venv"
export PIP_NO_INDEX=1
"$SALIDA/venv/bin/pip" install --no-index --find-links "$SALIDA/wheelhouse" veridicus-prueba-zine
VERSIONES=$("$SALIDA/venv/bin/veridicus-prueba-zine")
echo "$VERSIONES" | tee "$SALIDA/versiones.json"
DESCARGAS=$(grep -c -E "Downloading|Collecting .* from https?://" "$LOG" || true)
cabecera "sbatch trabajos/m5-wheelhouse.sbatch y trabajos/m5-instalar.sbatch (pip install --no-index --find-links wheelhouse veridicus-prueba-zine)" \
    "No aplica: M5 no usa un modelo"
cat "$SALIDA/wheelhouse.txt" >> "$SALIDA/resumen.txt" 2>/dev/null || true
{
    echo "Resultado: entry point con código 0; $RED; líneas de descarga en el log: $DESCARGAS"
    echo "Resultado: versiones instaladas: $VERSIONES"
} >> "$SALIDA/resumen.txt"
cat "$SALIDA/resumen.txt"
date
