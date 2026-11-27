#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -euo pipefail
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT
manifiesto="$(mktemp)"
kubectl create secret generic x --from-file=api-key="$temporal" --dry-run=client -o yaml > "$manifiesto"
kubectl --namespace x apply -f "$manifiesto"
