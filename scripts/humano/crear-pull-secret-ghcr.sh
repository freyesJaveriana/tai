#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Crea el Secret veridicus-ghcr, del tipo docker-registry, para que el clúster descargue la imagen
# privada de GHCR. Usa el usuario y un token de solo lectura de paquetes, leídos de un .env que no
# se versiona.
#
# Uso: bash scripts/humano/crear-pull-secret-ghcr.sh <archivo .env>
#      con las llaves VERIDICUS_GHCR_USER y VERIDICUS_GHCR_TOKEN.
#
# El token nunca se guarda en una variable, no se imprime y no viaja como argumento de ningún
# comando: se arma el archivo de configuración de Docker con grep y cut directamente en un archivo
# temporal 0600 y kubectl lo lee con --from-file. El .env no se carga con source.
# Se aplica con --server-side para que el valor del Secret no se copie a la anotación
# kubectl.kubernetes.io/last-applied-configuration. Si un Secret anterior se creó del lado del
# cliente y kubectl avisa de un conflicto de propietario del campo, borre ese Secret y vuelva a
# correr el script.
set -euo pipefail

archivo="${1:-}"
if [ -z "$archivo" ] || [ ! -f "$archivo" ]; then
  echo "Uso: bash scripts/humano/crear-pull-secret-ghcr.sh <archivo .env>" >&2
  exit 2
fi

namespace="veridicus-demo"

# leer <archivo> <llave>: el valor de la primera línea LLAVE=valor, sin comillas ni saltos de línea.
leer() {
  grep -m 1 -E "^$2=" "$1" | cut -d= -f2- | tr -d "\r\n\"'"
}

usuario="$(leer "$archivo" VERIDICUS_GHCR_USER || true)"
if ! printf '%s' "$usuario" | grep -Eq '^[A-Za-z0-9-]+$'; then
  echo "El archivo no trae VERIDICUS_GHCR_USER con un usuario válido de GitHub." >&2
  exit 2
fi
if ! leer "$archivo" VERIDICUS_GHCR_TOKEN | grep -Eq '^[A-Za-z0-9_-]+$'; then
  echo "El archivo no trae VERIDICUS_GHCR_TOKEN con un token (solo letras, cifras, guion y guion bajo)." >&2
  exit 2
fi

umask 077
config="$(mktemp)"
trap 'rm -f "$config"' EXIT

{
  printf '{"auths":{"ghcr.io":{"username":"%s","password":"' "$usuario"
  leer "$archivo" VERIDICUS_GHCR_TOKEN
  printf '","auth":"'
  { printf '%s:' "$usuario"; leer "$archivo" VERIDICUS_GHCR_TOKEN; } | base64 -w0
  printf '"}}}\n'
} > "$config"

if ! kubectl get namespace "$namespace" > /dev/null 2>&1; then
  kubectl create namespace "$namespace"
fi

kubectl create secret docker-registry veridicus-ghcr --namespace "$namespace" --from-file=.dockerconfigjson="$config" --dry-run=client -o yaml | kubectl apply --server-side -f -
echo "Secret veridicus-ghcr creado o actualizado en el namespace $namespace."
