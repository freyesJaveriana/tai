#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -eu
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
grep -E '^LLAVE=' "$1" | cut -d= -f2- > "$temporal"
