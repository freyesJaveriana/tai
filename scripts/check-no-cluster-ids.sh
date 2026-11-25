#!/usr/bin/env bash
# K-68 (E-32, E-39, E-40, E-44): el repositorio es publico y no debe decir donde vive el trabajo en el clúster.
# La guardia falla, nombrando archivo y línea (nunca el texto hallado), si un archivo versionado bajo
# docs/validacion-zine/ contiene:
#   (a) un nombre de nodo con la forma de E-39 (hpc seguido de caracteres de palabra o guion), de entrada o de trabajo;
#   (b) una ruta absoluta que empiece por /zine/;
#   (c) en enviar.ps1, un parámetro [string]$Servidor con valor por defecto.
#
# Única excepción, por archivo y por línea exacta (no por archivo entero): la línea de la autoprueba de
# comprobar_reporte.py que usa un nombre de nodo inventado para comprobar que la expresión de E-39 / P-T25-1
# lo reconoce. Existe para detectar esos nombres. Un nombre en cualquier otra línea de ese archivo sí falla,
# y también si esa línea cambia de texto.
#
# Uso: bash scripts/check-no-cluster-ids.sh [raíz]
# Imprime «N apariciones» y sale con 0 solo si N es 0 (1 si hay apariciones, 2 si la raíz no es un
# repositorio de Git o la búsqueda falla).
set -euo pipefail

raiz="${1:-.}"
carpeta="docs/validacion-zine"
exento_archivo="docs/validacion-zine/comprobar_reporte.py"
exento_linea='    if check(SAMPLE.replace("Nodo: ZINE_NODO", "Nodo: hpc-nodo-ejemplo", 1), review=True):'

if ! git -C "$raiz" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "check-no-cluster-ids: $raiz no es un repositorio de Git."
  exit 2
fi

salida="$(mktemp)"
errores="$(mktemp)"
trap 'rm -f "$salida" "$errores"' EXIT

# git grep -n: código 0 = hay coincidencias, 1 = no hay; otro código o stderr no vacío es un fallo.
buscar() {
  local codigo=0
  git -C "$raiz" grep -n -I -P "$@" >> "$salida" 2>> "$errores" || codigo=$?
  if [ "$codigo" -gt 1 ] || [ -s "$errores" ]; then
    echo "check-no-cluster-ids: FALLO al buscar (código de git grep: $codigo); no se puede afirmar 0 apariciones:"
    cat "$errores"
    exit 2
  fi
}

buscar -e '\bhpc[\w-]+' -e '/zine/' -- "$carpeta"
buscar -e '\[string\]\s*\x24Servidor\s*=' -- "$carpeta/enviar.ps1"

n=0
detalle=""
while IFS=: read -r archivo numero texto; do
  [ -n "$archivo" ] || continue
  if [ "$archivo" = "$exento_archivo" ] && [ "$texto" = "$exento_linea" ]; then
    continue
  fi
  detalle+="  $archivo:$numero"$'\n'
  n=$((n + 1))
done < "$salida"

if [ "$n" -eq 0 ]; then
  echo "0 apariciones"
  exit 0
fi

echo "check-no-cluster-ids: nodo, ruta /zine/ o servidor fijo en archivos versionados de $carpeta/ (solo archivo:línea):"
printf '%s' "$detalle"
echo "$n apariciones"
exit 1
