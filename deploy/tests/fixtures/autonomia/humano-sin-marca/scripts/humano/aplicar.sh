#!/usr/bin/env bash
# Falta la marca del humano: este script no debe pasar.
set -euo pipefail
kubectl apply -k deploy/demo-analyzer
