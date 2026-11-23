#!/usr/bin/env bash
# AUTONOMIA-01: ningún workflow ni script aplica cambios al clúster, a la base
# ni a la nube, ni envía trabajos a ZINE. Versión inicial de la tarea previa
# P0.1; U2 (B4) la amplía con la lista de excepciones de solo lectura
# (deploy/readonly-exec-allowlist.yaml) y más rutas.
#
# Uso: bash scripts/check-no-cluster-apply.sh [raíz]
# Sale con 0 si no hay apariciones y con 1 si encuentra alguna.
set -euo pipefail

raiz="${1:-.}"
rutas=()
for ruta in "$raiz/.github" "$raiz/scripts"; do
  if [ -d "$ruta" ]; then
    rutas+=("$ruta")
  fi
done

if [ "${#rutas[@]}" -eq 0 ]; then
  echo "check-no-cluster-apply: no hay .github/ ni scripts/ que revisar."
  exit 0
fi

# Verbos prohibidos. Se excluye este mismo archivo, que los nombra.
patron='kubectl[[:space:]]+(apply|create|replace|patch|delete|edit|scale|rollout)|helm[[:space:]]+(install|upgrade|uninstall|rollback)|terraform[[:space:]]+(apply|destroy)|argocd[[:space:]]+app[[:space:]]+sync|(^|[^[:alnum:]_])sbatch([^[:alnum:]_]|$)|(ssh|scp|rsync)[^#]*zine|KUBECONFIG|kubeconfig'

if hallazgos="$(grep -rInE --exclude=check-no-cluster-apply.sh "$patron" "${rutas[@]}")"; then
  echo "check-no-cluster-apply: AUTONOMIA-01 incumplida. Estas líneas aplican cambios a un clúster o envían trabajos a ZINE:"
  echo "$hallazgos"
  exit 1
fi

echo "check-no-cluster-apply: 0 apariciones en ${rutas[*]}."
