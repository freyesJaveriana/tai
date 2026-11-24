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
# Imprime «N apariciones» y sale con 0 solo si N es 0 (con 1 si hay apariciones, con 2 si la raíz no es un
# repositorio de Git).
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

# -F: cadena literal; -I: sin binarios. Código 1 de git grep = sin coincidencias.
hallazgos="$(git -C "$raiz" grep -n -I -F -e "$cadena" -- . "${excluir[@]}" || true)"

if [ -z "$hallazgos" ]; then
  echo "0 apariciones"
  exit 0
fi

n="$(printf '%s\n' "$hallazgos" | wc -l)"
echo "check-no-insumos: la ruta de insumos aparece en archivos versionados fuera de las exenciones (${exenciones[*]}):"
printf '%s\n' "$hallazgos" | cut -d: -f1 | sort -u | sed 's/^/  archivo: /'
echo "$n apariciones"
exit 1
