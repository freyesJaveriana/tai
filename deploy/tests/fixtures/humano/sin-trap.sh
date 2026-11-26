#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -euo pipefail
temporal="$(mktemp)"
grep -E '^LLAVE=' "$1" | cut -d= -f2- > "$temporal"
