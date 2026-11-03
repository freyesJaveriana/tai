#!/bin/bash
# Validación US14.1, paso previo: entorno virtual propio (tg4L/validacion/venv) sobre el Python del entorno conda de
# la 4L, con jsonschema para validar las salidas de M2. No toca el entorno de la 4L. Corre en hpchead02 (único nodo de
# cómputo con internet). Volver a lanzarlo rehace el entorno.
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch trabajos/m0-entorno.sbatch
#SBATCH --job-name=val-m0
#SBATCH --partition=debug
#SBATCH --nodelist=hpchead02
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m0-entorno_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar
preparar_salida m0
date; hostname
rm -rf "$VENV"
python -m venv "$VENV"
"$VENV/bin/pip" install -q 'jsonschema==4.23.0'
"$VENV/bin/python" -c 'import sys; from importlib.metadata import version; print("python", sys.version.split()[0], "jsonschema", version("jsonschema"))' \
    | tee -a "$SALIDA/resumen.txt"
llama-server --version 2>&1 | grep -m1 version | tee -a "$SALIDA/resumen.txt"
date
