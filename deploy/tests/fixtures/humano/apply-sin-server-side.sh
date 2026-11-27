#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -euo pipefail
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
grep -E '^LLAVE=' "$1" | cut -d= -f2- > "$temporal"
kubectl create secret generic x --from-file=api-key="$temporal" --dry-run=client -o yaml | kubectl apply -f -
