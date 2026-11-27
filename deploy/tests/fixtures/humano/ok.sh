#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Fixture sintético que cumple todas las reglas; las demás son copias con un solo defecto.
set -euo pipefail
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
grep -E '^LLAVE=' "$1" | cut -d= -f2- > "$temporal"
echo "listo"
