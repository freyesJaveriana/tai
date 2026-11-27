#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -euo pipefail
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
clave="$(grep -E '^LLAVE=' "$1" | cut -d= -f2-)"
kubectl create secret generic x --from-file=api-key=/dev/null --token "$clave"
