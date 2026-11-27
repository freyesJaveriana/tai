#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Prueba de cambio de modelo solo por configuración: corre la CLI del analizador sobre los 12 casos
# sintéticos de evaluation/cambio-modelo/ con dos perfiles que solo difieren en el modelo
# (demo-anthropic con claude-sonnet-5-5 y demo-anthropic-opus con claude-opus-5-5) y compara las dos
# corridas contra lo esperado de cada caso.
#
# Uso, desde cualquier carpeta del repositorio:
#   VERIDICUS_ANTHROPIC_API_KEY=... bash scripts/humano/cambio-modelo.sh
#
# Sale a internet y gasta saldo del proveedor: 2 corridas × 12 casos, cada una con 1 llamada del juez
# y 2 por candidato. Todo pasa por el anonimizador de la CLI (AUTONOMIA-04); los casos son sintéticos.
# Los resultados quedan en resultados-locales/cambio-modelo/<fecha>/, que Git ignora.
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
casos="$raiz/evaluation/cambio-modelo/casos"
esperado="$raiz/evaluation/cambio-modelo/esperado.json"
base="$raiz/resultados-locales/cambio-modelo/$(date -u +%Y%m%dT%H%M%SZ)"
perfiles=(demo-anthropic demo-anthropic-opus)
trap 'echo "La prueba de cambio de modelo no terminó: revise el último mensaje." >&2' ERR

if [ -z "${VERIDICUS_ANTHROPIC_API_KEY:-}" ]; then
  echo "Falta VERIDICUS_ANTHROPIC_API_KEY en el entorno: sin ella no sale ninguna llamada." >&2
  exit 2
fi
# El perfil comercial exige un plazo por llamada de al menos 270 s; la demostración usa 300.
export VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S="${VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S:-300}"

mkdir -p "$base"
argumentos=()
for perfil in "${perfiles[@]}"; do
  echo "== Corrida con el perfil $perfil"
  inicio="$(date +%s)"
  codigo=0
  uv run --frozen --offline --directory "$raiz/libs/incoherence_analyzer" --extra cli \
    veridicus analyze "$casos" --perfil "$perfil" --salida "$base/$perfil" || codigo=$?
  segundos=$(( $(date +%s) - inicio ))
  if [ "$codigo" -ne 0 ]; then
    echo "La CLI terminó con el código $codigo en el perfil $perfil; no se compara." >&2
    exit "$codigo"
  fi
  argumentos+=(--corrida "$perfil=$base/$perfil" --segundos "$perfil=$segundos")
done

uv run --frozen --offline --directory "$raiz/deploy" python -m veridicus_demo.cambio_modelo \
  --casos "$casos" --esperado "$esperado" "${argumentos[@]}" --reporte "$base/reporte.json"
