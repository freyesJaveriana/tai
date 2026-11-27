#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Demo del bucle GitOps con un cambio visible y sin importancia: el color de la barra superior del visor.
# Este script solo PROPONE: crea una rama, hace el commit, la sube y abre el PR. No toca el clúster.
# La fusión del PR en GitHub es la aprobación humana; después Argo CD reconcilia solo, y
# scripts/humano/gitops-observar.sh (en la VM) muestra cuándo el pod nuevo ya tiene el color.
#
# Uso, desde una copia del repositorio con permiso de push y gh autenticado:
#   bash scripts/humano/gitops-color.sh '#c2410c'   # propone la barra en otro color (#rrggbb)
#   bash scripts/humano/gitops-color.sh --revertir  # propone el git revert del último cambio de color
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
archivo="deploy/demo-visor/apariencia.properties"
rama_inicial="$(git -C "$raiz" rev-parse --abbrev-ref HEAD)"
trap 'git -C "$raiz" switch --quiet "$rama_inicial" > /dev/null 2>&1 || true' EXIT

argumento="${1:-}"
if [ -z "$argumento" ]; then
  echo "Uso: bash scripts/humano/gitops-color.sh '#rrggbb' | --revertir" >&2
  exit 2
fi
if ! command -v gh > /dev/null; then
  echo "Falta gh (GitHub CLI) autenticado: sin él no se puede abrir el PR." >&2
  exit 2
fi
if [ -n "$(git -C "$raiz" status --porcelain)" ]; then
  echo "La copia tiene cambios sin commit: guárdelos o descártelos antes de proponer el cambio." >&2
  exit 2
fi

git -C "$raiz" fetch --quiet origin main
marca="$(date -u +%Y%m%d%H%M%S)"

if [ "$argumento" = "--revertir" ]; then
  commit="$(git -C "$raiz" log -1 --format=%H origin/main -- "$archivo")"
  if [ -z "$commit" ]; then
    echo "No hay en main ningún commit que cambie $archivo." >&2
    exit 2
  fi
  rama="chore/revertir-color-$marca"
  git -C "$raiz" switch --quiet --create "$rama" origin/main
  git -C "$raiz" revert --no-edit "$commit"
  titulo="revert(demo-visor): devuelve el color de la barra superior (bucle GitOps)"
  cuerpo="Revierte ${commit:0:7} con git revert, como manda la reversión del equipo. Al fusionar, Argo CD vuelve a aplicar el ConfigMap anterior."
else
  if ! [[ "$argumento" =~ ^#[0-9A-Fa-f]{6}$ ]]; then
    echo "El color debe tener la forma #rrggbb, por ejemplo '#c2410c' (con comillas, por el #)." >&2
    exit 2
  fi
  color="${argumento,,}"
  rama="chore/color-${color#\#}-$marca"
  git -C "$raiz" switch --quiet --create "$rama" origin/main
  printf 'VERIDICUS_VISOR_COLOR_BANDA=%s\n' "$color" > "$raiz/$archivo"
  if git -C "$raiz" diff --quiet -- "$archivo"; then
    echo "La barra ya es $color en main: no hay nada que proponer." >&2
    exit 2
  fi
  git -C "$raiz" add "$archivo"
  git -C "$raiz" commit --quiet -m "chore(demo-visor): barra superior en $color (prueba del bucle GitOps)"
  titulo="chore(demo-visor): barra superior en $color (bucle GitOps)"
  cuerpo="Solo cambia $archivo. Al fusionar, Argo CD aplica el ConfigMap con un sufijo nuevo, la plantilla del Deployment cambia y el pod se renueva. Nadie aplica nada a mano contra el clúster."
fi

git -C "$raiz" push --quiet --set-upstream origin "$rama"
url="$(gh pr create --repo freyesJaveriana/tai --base main --head "$rama" --title "$titulo" --body "$cuerpo")"

echo "PR abierto: $url"
echo "1. Revíselo y fusiónelo en GitHub cuando la CI esté en verde: esa fusión es la aprobación humana."
echo "2. En la VM: bash scripts/humano/gitops-observar.sh"
