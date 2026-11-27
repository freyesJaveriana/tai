#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -euo pipefail
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
secreto="$(grep -E '^LLAVE=' "$1" | cut -d= -f2-)"
echo "el valor es $secreto"
