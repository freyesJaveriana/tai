#!/bin/bash
# Validación US14.1, M5 (AC14.1.5), primera parte: arma la wheelhouse en hpchead02 (único nodo de cómputo con
# internet): las dependencias previstas de la biblioteca (pydantic, httpx, jsonschema, pyyaml) para el Python 3.12
# del entorno de la 4L y la rueda del paquete de prueba (paquete_prueba/, con un entry point). Después se lanza
# m5-instalar.sbatch, que instala sin internet en un SL250s.
#   cd /zine/HPC02S1/freyes/tg4L/validacion && sbatch trabajos/m5-wheelhouse.sbatch
#SBATCH --job-name=val-m5-wh
#SBATCH --partition=debug
#SBATCH --nodelist=hpchead02
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=/zine/HPC02S1/freyes/tg4L/validacion/logs/m5-wheelhouse_%j.out
set -euo pipefail
source /zine/HPC02S1/freyes/tg4L/validacion/trabajos/comun.sh
activar
SALIDA=$VALID/m5
mkdir -p "$SALIDA"
date; hostname
rm -rf "$SALIDA/wheelhouse" "$SALIDA/venv-descarga"
python -m venv "$SALIDA/venv-descarga"
PIP=$SALIDA/venv-descarga/bin/pip
"$PIP" download --only-binary=:all: -d "$SALIDA/wheelhouse" pydantic httpx jsonschema pyyaml
"$PIP" wheel --no-deps -w "$SALIDA/wheelhouse" "$TRABAJOS/paquete_prueba"
rm -rf "$SALIDA/venv-descarga"
(cd "$SALIDA/wheelhouse" && sha256sum ./*.whl) | tee "$SALIDA/wheelhouse.sha256"
{
    echo "Wheelhouse: trabajo $SLURM_JOB_ID en $(hostname -s), $(find "$SALIDA/wheelhouse" -name '*.whl' | wc -l) ruedas"
} | tee "$SALIDA/wheelhouse.txt"
date
