#!/usr/bin/env bash
# K-68, K-73 (E-32, E-39, E-40, E-44, E-45): el repositorio es publico y no debe decir donde vive el trabajo en el clúster.
# La guardia falla, nombrando archivo y línea (nunca el texto hallado), si un archivo versionado de TODO el repositorio
# (git ls-files) contiene:
#   (a) un nombre de nodo con la forma de E-39 (hpc seguido de caracteres de palabra o guion, sin distinguir
#       mayúsculas), de entrada o de trabajo, también tras un guion bajo (nodo_hpc...), salvo los nombres inventados
#       de la lista de exenciones;
#   (b) una ruta ABSOLUTA que empiece por /zine/ y siga con un carácter de palabra (distingue mayúsculas, como las
#       rutas de Linux). No cuenta si lo precede un carácter de palabra, un punto, un guion o una barra (así que las
#       rutas relativas como docs/zine/x no cuentan), ni la mención entre comillas invertidas, porque tras la barra
#       final no hay un carácter de palabra;
#   (c) en cualquier .ps1, sin distinguir mayúsculas:
#       - un parámetro [string]$Servidor con valor por defecto, o toda asignación literal de $Servidor entre comillas
#         cuyo valor no empiece por $;
#       - una asignación de $Servidor cuyo valor lleve un literal de palabra justo después de @ (F-05: un valor que
#         empieza por $ pero deja el host fijo);
#       - un scp cuyo destino sea un host literal (palabra: o usuario@palabra:) y no salga de una variable (F-06).
#
# Límites conocidos: se saltan los archivos binarios (git grep -I), y un nombre de archivo con dos puntos pierde
# el número de línea en la salida (la aparición sí se cuenta).
#
# Exenciones: una lista cerrada, por cadena y no por carpeta ni por archivo.
#   Nombres inventados (se comparan como palabra completa y sin distinguir mayúsculas). Se usan en tareas, bitácoras,
#   controles negativos, informes y en la autoprueba de comprobar_reporte.py, que necesita un nombre con la forma de
#   E-39 para comprobar que la expresión lo reconoce:
#     hpc99-w999       nombre de trabajo inventado de los controles negativos y las bitácoras.
#     hpc-nodo-ejemplo nombre inventado de la autoprueba de comprobar_reporte.py.
#     hpcNN-wNNN       forma genérica con marcadores, para describir el patrón sin escribir un nombre.
#     hpchead99        nombre inventado de nodo de entrada que usan las sondas de los informes de T27 (P-T29-1).
#   No se exime ninguna carpeta ni ningún archivo entero.
#
# Uso: bash scripts/check-no-cluster-ids.sh [raíz]
# Imprime «N apariciones» y sale con 0 solo si N es 0 (1 si hay apariciones, 2 si la raíz no es un
# repositorio de Git o la búsqueda falla).
set -euo pipefail

raiz="${1:-.}"
nombres_inventados=("hpc99-w999" "hpc-nodo-ejemplo" "hpcnn-wnnn" "hpchead99")

if ! git -C "$raiz" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "check-no-cluster-ids: $raiz no es un repositorio de Git."
  exit 2
fi

salida="$(mktemp)"
nodos="$(mktemp)"
errores="$(mktemp)"
trap 'rm -f "$salida" "$nodos" "$errores"' EXIT

# git grep -n: código 0 = hay coincidencias, 1 = no hay; otro código o stderr no vacío es un fallo.
# El primer argumento es el archivo de destino; el resto va a git grep.
buscar() {
  local destino="$1"
  shift
  local codigo=0
  git -C "$raiz" grep -n -I -P "$@" >> "$destino" 2>> "$errores" || codigo=$?
  if [ "$codigo" -gt 1 ] || [ -s "$errores" ]; then
    echo "check-no-cluster-ids: FALLO al buscar (código de git grep: $codigo); no se puede afirmar 0 apariciones:"
    cat "$errores"
    exit 2
  fi
}

# (a) sin distinguir mayúsculas (-i): los nombres de host no las distinguen. hpc no precedido de letra ni dígito,
# así que también detecta nodo_hpc... (el guion bajo no cuenta como límite). -o imprime solo lo hallado, para
# poder comparar cada nombre con la lista de exenciones.
buscar "$nodos" -o -i -e '(?<![A-Za-z0-9])hpc[\w-]+' -- .
while IFS=: read -r archivo numero texto; do
  [ -n "$archivo" ] || continue
  exento=0
  minuscula="${texto,,}"
  for permitido in "${nombres_inventados[@]}"; do
    if [ "$minuscula" = "$permitido" ]; then
      exento=1
    fi
  done
  if [ "$exento" -eq 0 ]; then
    echo "$archivo:$numero:x" >> "$salida"
  fi
done < "$nodos"

# (b) distingue mayúsculas: las rutas de Linux sí las distinguen. Solo una ruta absoluta (sin carácter de palabra,
# punto, guion ni barra delante) seguida de un carácter de palabra.
buscar "$salida" -e '(?<![\w.\-/])/zine/\w' -- .

# (c) en cualquier .ps1 del repositorio, sin distinguir mayúsculas.
#   1. Un parámetro [string]$Servidor con valor por defecto, o toda asignación literal de $Servidor entre comillas.
#      El valor que empieza por $ (variable o sustitución) no es un servidor fijo por sí solo.
#   2. F-05: una asignación de $Servidor con un literal de palabra justo después de @ (el host fijo detrás de una
#      sustitución). El valor que antepone ZINE_USUARIO y deja @ seguido de $Servidor no cuenta.
#   3. F-06: un scp con un destino de host literal: palabra: o usuario@palabra:, sin $ ni llaves delante.
buscar "$salida" -i \
  -e '\[string\]\s*\x24Servidor\s*=' \
  -e '\x24Servidor\s*=\s*[\x27"](?!\x24)' \
  -e '\x24Servidor\s*=[^#]*@[A-Za-z]' \
  -e '\bscp\b.*(?<![\w\x24.{}\-])[\x27"]?(?:[\w.\-]+@)?[A-Za-z][\w.\-]*:(?![\\/])' \
  -- '*.ps1'

n=0
detalle=""
while IFS=: read -r archivo numero texto; do
  [ -n "$archivo" ] || continue
  detalle+="  $archivo:$numero"$'\n'
  n=$((n + 1))
done < "$salida"

if [ "$n" -eq 0 ]; then
  echo "0 apariciones"
  exit 0
fi

echo "check-no-cluster-ids: nodo, ruta /zine/ o servidor fijo en archivos versionados (solo archivo:línea):"
printf '%s' "$detalle"
echo "$n apariciones"
exit 1
