#!/usr/bin/env bash
# K-68 (E-32, E-39, E-40, E-44): el repositorio es publico y no debe decir donde vive el trabajo en el clúster.
# La guardia falla, nombrando archivo y línea (nunca el texto hallado), si un archivo versionado bajo
# docs/validacion-zine/ contiene:
#   (a) un nombre de nodo con la forma de E-39 (hpc seguido de caracteres de palabra o guion, sin distinguir
#       mayúsculas), de entrada o de trabajo, también tras un guion bajo (nodo_hpc...);
#   (b) una ruta absoluta que empiece por /zine/ (esta sí distingue mayúsculas, como las rutas de Linux);
#   (c) en cualquier .ps1 de la carpeta, sin distinguir mayúsculas: un parámetro [string]$Servidor con valor por
#       defecto, o toda asignación literal de $Servidor entre comillas cuyo valor no empiece por $.
#
# Límites conocidos: se saltan los archivos binarios (git grep -I), y un nombre de archivo con dos puntos pierde
# el número de línea en la salida (la aparición sí se cuenta).
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

# (a) y (c) sin distinguir mayúsculas (-i): los nombres de host y PowerShell (tipos y variables) no las distinguen.
# (a): hpc no precedido de letra ni dígito, así que también detecta nodo_hpc... (el guion bajo no cuenta como límite).
buscar -i -e '(?<![A-Za-z0-9])hpc[\w-]+' -- "$carpeta"
# (b) distingue mayúsculas: las rutas de Linux sí las distinguen.
buscar -e '/zine/' -- "$carpeta"
# (c) en cualquier .ps1 de la carpeta: un parámetro [string]$Servidor con valor por defecto, o toda asignación literal
# de $Servidor entre comillas. El valor que empieza por $ (variable o sustitución, p. ej. el que antepone ZINE_USUARIO
# o el que lee ZINE_SERVIDOR) no es un servidor fijo y no cuenta.
buscar -i -e '\[string\]\s*\x24Servidor\s*=' -e '\x24Servidor\s*=\s*[\x27"](?!\x24)' -- "$carpeta/*.ps1"

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
