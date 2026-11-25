#!/usr/bin/env bash
# R-3 (cambio 05, E-32 y E-33): el repositorio es público y nada de /insumos debe entrar. La guardia falla,
# nombrando cada archivo, si un archivo versionado contiene la ruta de insumos fuera de la lista cerrada de
# exenciones de abajo.
#
# Exenciones (lista cerrada), cada una con su motivo:
#   aidlc/          artefactos de AI-DLC aprobados: citan de dónde vino un insumo y no se editan.
#   docs/           documentación que cita el origen de un insumo (decisiones, cambios, bitácoras).
#   plan-aidlc.md   plan del proyecto: documentación con el mismo motivo.
# Este mismo script arma la cadena buscada por partes para no contenerla literalmente.
#
# Uso: bash scripts/check-no-insumos.sh [raíz]
# Imprime «N apariciones» (N = archivos) y sale con 0 solo si N es 0 (con 1 si hay apariciones, con 2 si la raíz
# no es un repositorio de Git o la búsqueda falla).
set -euo pipefail

raiz="${1:-.}"
cadena="/insumos""/"
exenciones=(aidlc docs plan-aidlc.md)

if ! git -C "$raiz" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "check-no-insumos: $raiz no es un repositorio de Git."
  exit 2
fi

excluir=()
for exencion in "${exenciones[@]}"; do
  excluir+=(":(exclude)$exencion")
done

# -F: cadena literal. Sin -I: los binarios también se revisan. -l -z: nombres de archivo separados por NUL,
# sin comillas ni escapes (sirve para nombres con dos puntos o no ASCII). Código 0 = hay coincidencias,
# 1 = no hay; cualquier otro código, o cualquier mensaje en stderr (p. ej. un archivo ilegible), es un fallo.
salida="$(mktemp)"
errores="$(mktemp)"
trap 'rm -f "$salida" "$errores"' EXIT
codigo=0
git -C "$raiz" grep -l -z -F -e "$cadena" -- . "${excluir[@]}" > "$salida" 2> "$errores" || codigo=$?

if { [ "$codigo" -ne 0 ] && [ "$codigo" -ne 1 ]; } || [ -s "$errores" ]; then
  echo "check-no-insumos: FALLO al buscar (código de git grep: $codigo); no se puede afirmar 0 apariciones:"
  cat "$errores"
  exit 2
fi

if [ ! -s "$salida" ]; then
  echo "0 apariciones"
  exit 0
fi

n=0
echo "check-no-insumos: la ruta de insumos aparece en archivos versionados fuera de las exenciones (${exenciones[*]}):"
while IFS= read -r -d '' archivo; do
  printf '  archivo: %s\n' "$archivo"
  n=$((n + 1))
done < "$salida"
echo "$n apariciones (archivos)"
exit 1
