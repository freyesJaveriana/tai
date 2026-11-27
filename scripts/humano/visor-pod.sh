#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Construye la imagen del visor dentro de Minikube y lo despliega como un pod con NodePort, para usar
# la demo desde el navegador sin túnel ni python3 en la VM.
#
# Uso: bash scripts/humano/visor-pod.sh [ruta-del-escudo.png|jpg|svg]
#
# Antes: la demo del analizador aplicada al menos una vez (namespace veridicus-demo y sus dos Secrets).
# Solo para la demo: la imagen no la publica la CI y la página no pide contraseña. Se puede volver a
# correr tras cada git pull: reconstruye la imagen y reinicia el pod.
set -euo pipefail

namespace="veridicus-visor"
imagen="veridicus-visor:demo"
raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
escudo="${1:-}"
contexto="$(mktemp -d)"
trap 'rm -rf "$contexto"' EXIT

if ! kubectl get namespace veridicus-demo > /dev/null 2>&1; then
  echo "Falta el namespace veridicus-demo: aplique antes la demo con scripts/humano/demo-analyzer.sh." >&2
  exit 2
fi

case "$(uname -m)" in
  x86_64 | amd64) arquitectura="amd64" ;;
  aarch64 | arm64) arquitectura="arm64" ;;
  *)
    echo "Arquitectura no soportada: $(uname -m)." >&2
    exit 2
    ;;
esac
version_servidor="$(kubectl version -o json | python3 -c 'import json, sys; print(json.load(sys.stdin)["serverVersion"]["gitVersion"])')"

# El contexto de la imagen: el visor con la misma estructura que en el repositorio (busca
# deploy/demo-analyzer y los ejemplos a dos carpetas de su propia ruta) y, si se da, el escudo.
mkdir -p "$contexto/app/scripts/humano" "$contexto/app/deploy/demo-visor"
cp "$raiz/scripts/humano/visor-demo.py" "$contexto/app/scripts/humano/"
cp -r "$raiz/deploy/demo-analyzer" "$contexto/app/deploy/"
cp "$raiz/deploy/demo-visor/ejemplos.json" "$contexto/app/deploy/demo-visor/"
cp "$raiz/deploy/demo-visor/Dockerfile" "$contexto/"
if [ -n "$escudo" ]; then
  extension="${escudo##*.}"
  extension="${extension,,}"
  case "$extension" in
    png | jpg | jpeg | svg) cp "$escudo" "$contexto/app/escudo.$extension" ;;
    *)
      echo "El escudo debe ser PNG, JPG o SVG." >&2
      exit 2
      ;;
  esac
fi
chmod -R a+rX "$contexto/app"

echo "Construyendo $imagen en Minikube (kubectl $version_servidor, $arquitectura)..."
minikube image build -t "$imagen" \
  --build-opt="build-arg=KUBECTL_VERSION=$version_servidor" \
  --build-opt="build-arg=KUBECTL_ARCH=$arquitectura" \
  "$contexto"

kubectl apply -k "$raiz/deploy/demo-visor"
# La etiqueta es fija: el reinicio hace que el pod tome la imagen recién construida.
kubectl rollout restart deployment/veridicus-visor --namespace "$namespace"
kubectl rollout status deployment/veridicus-visor --namespace "$namespace" --timeout=180s

echo "Visor listo en http://$(minikube ip):30851"
