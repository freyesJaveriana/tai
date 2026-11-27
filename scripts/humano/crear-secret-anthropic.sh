#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Crea el Secret veridicus-anthropic con la clave del proveedor, leída de un .env que no se versiona.
#
# Uso: bash scripts/humano/crear-secret-anthropic.sh <archivo .env>
#
# La clave nunca se guarda en una variable, no se imprime y no viaja como argumento de ningún
# comando (se vería en `ps`): va de grep a un archivo temporal 0600 y de ahí a kubectl con
# --from-file. El .env se analiza con grep y cut sobre una sola llave; no se hace source.
# Se aplica con --server-side: el apply del lado del cliente copiaría el valor del Secret a la
# anotación kubectl.kubernetes.io/last-applied-configuration, donde cualquiera que lea el Secret
# lo vería dos veces. Un Secret creado antes del lado del cliente conserva esa anotación (el
# servidor la mantiene): si existe con ella, el script termina sin aplicar y pide borrar el Secret
# y repetir.
set -euo pipefail

archivo="${1:-}"
if [ -z "$archivo" ] || [ ! -f "$archivo" ]; then
  echo "Uso: bash scripts/humano/crear-secret-anthropic.sh <archivo .env>" >&2
  exit 2
fi

namespace="veridicus-demo"

# leer <archivo> <llave>: el valor de la primera línea LLAVE=valor, sin comillas ni saltos de línea.
leer() {
  grep -m 1 -E "^$2=" "$1" | cut -d= -f2- | tr -d "\r\n\"'"
}

if ! grep -qE '^VERIDICUS_ANTHROPIC_API_KEY=.' "$archivo"; then
  echo "El archivo no trae la llave VERIDICUS_ANTHROPIC_API_KEY con un valor." >&2
  exit 2
fi

umask 077
temporal="$(mktemp)"
trap 'rm -f "$temporal"' EXIT

leer "$archivo" VERIDICUS_ANTHROPIC_API_KEY > "$temporal"
if [ ! -s "$temporal" ]; then
  echo "La llave VERIDICUS_ANTHROPIC_API_KEY está vacía." >&2
  exit 2
fi

if ! kubectl get namespace "$namespace" > /dev/null 2>&1; then
  kubectl create namespace "$namespace"
fi

# La plantilla imprime solo el literal «si» cuando la anotación existe: su valor se evalúa dentro de
# kubectl y nunca pasa por un pipe, una variable ni la salida (K-104).
if [ "$(kubectl get secret veridicus-anthropic --namespace "$namespace" -o go-template='{{if index .metadata.annotations "kubectl.kubernetes.io/last-applied-configuration"}}si{{end}}' 2> /dev/null)" = "si" ]; then
  echo "El Secret veridicus-anthropic ya existe con la anotación last-applied-configuration, que guarda el valor de la clave." >&2
  echo "Bórrelo y repita este script: kubectl delete secret veridicus-anthropic --namespace $namespace" >&2
  exit 2
fi

kubectl create secret generic veridicus-anthropic --namespace "$namespace" --from-file=api-key="$temporal" --dry-run=client -o yaml | kubectl apply --server-side -f -
echo "Secret veridicus-anthropic creado o actualizado en el namespace $namespace."
