#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
set -euo pipefail
kubectl apply -k deploy/demo-analyzer
