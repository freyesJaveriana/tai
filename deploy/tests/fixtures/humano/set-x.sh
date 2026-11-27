#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -euo pipefail
set -x
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
