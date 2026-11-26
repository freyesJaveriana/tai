#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Fixture sintético: el único lugar donde se puede aplicar al clúster.
set -euo pipefail
kubectl apply -k deploy/demo-analyzer
