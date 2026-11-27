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
if [ -d "$raiz/.github" ]; then
  rutas+=("$raiz/.github")
fi
# Excepción de U2 (DP-08): se excluye la ruta exacta scripts/humano, no cualquier carpeta que se
# llame humano. Por eso scripts/ se recorre entrada por entrada en vez de con --exclude-dir, que solo
# compara el nombre base de la carpeta.
if [ -d "$raiz/scripts" ]; then
  for ruta in "$raiz/scripts"/* "$raiz/scripts"/.[!.]*; do
    if [ -e "$ruta" ] && [ "$ruta" != "$raiz/scripts/humano" ]; then
      rutas+=("$ruta")
    fi
  done
fi

if [ "${#rutas[@]}" -eq 0 ]; then
  echo "check-no-cluster-apply: no hay .github/ ni scripts/ que revisar."
  exit 0
fi

# Verbos prohibidos. Se excluye este mismo archivo, que los nombra.
patron='kubectl[[:space:]]+(apply|create|replace|patch|delete|edit|scale|rollout)|helm[[:space:]]+(install|upgrade|uninstall|rollback)|terraform[[:space:]]+(apply|destroy)|argocd[[:space:]]+app[[:space:]]+sync|(^|[^[:alnum:]_])sbatch([^[:alnum:]_]|$)|(ssh|scp|rsync)[^#]*zine|KUBECONFIG|kubeconfig'

#
# Excepción de U2 (DP-08): scripts/humano/ es la única carpeta que puede nombrar esas operaciones,
# porque son los scripts que el humano revisa y ejecuta. deploy/tests/test_autonomia_01.py exige que
# cada uno abra con la marca «# Lo ejecuta el humano (AUTONOMIA-01)» y que ningún workflow los
# mencione, así que esa carpeta no queda sin vigilancia.
if hallazgos="$(grep -rInE --exclude=check-no-cluster-apply.sh "$patron" "${rutas[@]}")"; then
  echo "check-no-cluster-apply: AUTONOMIA-01 incumplida. Estas líneas aplican cambios a un clúster o envían trabajos a ZINE:"
  echo "$hallazgos"
  exit 1
fi

echo "check-no-cluster-apply: 0 apariciones en ${rutas[*]}."
