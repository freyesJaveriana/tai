#!/usr/bin/env bash
set -euo pipefail
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
grep -E '^LLAVE=' "$1" | cut -d= -f2- > "$temporal"
