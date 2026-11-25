#!/usr/bin/env bash
# K-68, K-73 (E-32, E-39, E-40, E-44, E-45): el repositorio es publico y no debe decir donde vive el trabajo en el clúster.
# La guardia falla, nombrando archivo y línea (nunca el texto hallado), si un archivo versionado de TODO el repositorio
# (git ls-files) contiene:
#   (a) un nombre de nodo con la forma de E-39 (hpc seguido de caracteres de palabra o guion, sin distinguir
#       mayúsculas), de entrada o de trabajo, también tras un guion bajo (nodo_hpc...), salvo los nombres inventados
#       de la lista de exenciones;
#   (b) una ruta ABSOLUTA que empiece por /zine/ y siga con un carácter de palabra (distingue mayúsculas, como las
#       rutas de Linux), también con barras repetidas o con un segmento punto que Linux resuelve igual. No cuenta si lo precede un carácter de palabra,
#       un punto, un guion o una barra (así que las rutas relativas como docs/zine/x no cuentan), ni la mención entre
#       comillas invertidas, porque tras la barra final no hay un carácter de palabra, ni una URL (http://zine/x);
#   (c) en cualquier .ps1 o .psm1 (también en mayúsculas), sin distinguir mayúsculas:
#       - un parámetro [string]$Servidor con valor por defecto, o toda asignación literal de $Servidor entre comillas
#         cuyo valor no empiece por $;
#       - una asignación de $Servidor cuyo valor lleve un literal de palabra o dígito (nombre o IP) justo después de @
#         (F-05: un valor que empieza por $ pero deja el host fijo);
#       - un scp cuyo destino sea un host literal (palabra: o usuario@palabra:, también una IP, con ruta remota
#         relativa o absoluta) que no salga de una variable (F-06). Se excluye solo una letra de unidad suelta de
#         Windows seguida de barra (C:\x, C:/x).
#
#   (d) K-76: un nombre de nodo con la forma de (a) en la RUTA de un archivo versionado (se informa su número en
#       git ls-files, nunca la ruta); una URL file: con tres barras o más hacia /zine/; en .ps1, .psm1 y .psd1, la
#       asignación del servidor con ámbito ($script:Servidor), el host concatenado tras la arroba y, en .psd1, la
#       clave Servidor con un valor literal. La regla del destino de scp no cambia respecto de 8732623.
#
# Límites conocidos: se saltan los archivos binarios (git grep -I), y un nombre de archivo con dos puntos pierde
# el número de línea en la salida (la aparición sí se cuenta). Un scp partido en varias líneas con una continuación
# (una comilla invertida al final de línea) no se detecta: el destino queda en otra línea que no lleva la palabra scp.
# La regla de scp FALLA CERRADO ante ciertas líneas inocentes que contienen la palabra scp: una hora (12:30), un
# comentario con «palabra:x», un destino que sale de una variable de entorno sin llaves seguida de dos puntos
# ($env:X:/ruta, con comillas o sin ellas), un mensaje con una palabra seguida de dos puntos en la misma línea (por ejemplo, después de ;) y una URL.
# Esas líneas se reescriben (por ejemplo, con llaves: ${env:X}). El refinamiento queda para después de la
# demostración (F-05 a F-07 de T29).
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
# También cuentan las barras repetidas al inicio (que no sigan a dos puntos: no es una URL), en medio, y un segmento
# punto: Linux los resuelve igual.
buscar "$salida" -e '(?<![\w.\-/])(?:/|(?<!:)//+)zine/(?:\.?/)*\w' -- .
# K-76 (F-07): una URL file: con tres barras o más deja una barra delante del segmento, que la regla anterior no
# cuenta. Sin distinguir mayúsculas solo en «file:».
buscar "$salida" -e '(?i:file:)/{3,}(?:\.?/)*zine/(?:\.?/)*\w' -- .

# (a') K-76: un nombre de nodo en la RUTA de un archivo versionado. Misma forma y misma lista de exenciones que (a).
# Nunca se imprime la ruta (el informe iría a un registro público): se imprime su número en la salida de git ls-files.
indice=0
while IFS= read -r ruta; do
  indice=$((indice + 1))
  while IFS= read -r nombre; do
    [ -n "$nombre" ] || continue
    exento=0
    minuscula="${nombre,,}"
    for permitido in "${nombres_inventados[@]}"; do
      if [ "$minuscula" = "$permitido" ]; then
        exento=1
      fi
    done
    if [ "$exento" -eq 0 ]; then
      echo "ruta#$indice:0:x" >> "$salida"
    fi
  done < <(printf '%s\n' "$ruta" | grep -o -i -P '(?<![A-Za-z0-9])hpc[\w-]+' || true)
done < <(git -c core.quotePath=false -C "$raiz" ls-files)

# (c) en cualquier .ps1, .psm1 o .psd1 del repositorio (también en mayúsculas), sin distinguir mayúsculas.
#   1. Un parámetro [string]$Servidor con valor por defecto, o toda asignación literal de $Servidor entre comillas,
#      también con ámbito (K-76: $script:Servidor, $global:Servidor...).
#      El valor que empieza por $ (variable o sustitución) no es un servidor fijo por sí solo.
#   2. F-05: una asignación de $Servidor con un literal de palabra o dígito (una IP) justo después de @ (el host fijo
#      detrás de una sustitución), o concatenado tras la arroba ("...@" + "host", F-07). El valor que antepone
#      ZINE_USUARIO y deja @ seguido de $Servidor no cuenta.
#   3. F-06: un scp con un destino de host literal: palabra: o usuario@palabra:, con ruta remota o sin ella (host:,
#      host:x, host:/x, "host:", host: ruta) y también una IP, sin $ ni llaves delante. No cuenta una letra de unidad
#      suelta de Windows (C:\x, C:/x).
#      Es la regla de 8732623, sin cambios: en la misma línea, tras la palabra scp, cualquier argumento que sea una
#      palabra (o usuario@palabra) seguida de dos puntos y que no lleve $, llaves, punto ni guion delante. Por eso
#      también ve el destino con sudo, con una asignación o con la ruta del binario delante. Falla cerrado ante
#      líneas inocentes (ver «Límites conocidos»).
buscar "$salida" -i \
  -e '\[string\]\s*\x24(?:\w+:)?Servidor\s*=' \
  -e '\x24(?:\w+:)?Servidor\s*=\s*[\x27"](?!\x24)' \
  -e '\x24(?:\w+:)?Servidor\s*=[^#]*@\w' \
  -e '\x24(?:\w+:)?Servidor\s*=[^#]*@[\x27"]?\s*\+\s*[\x27"]\w' \
  -e '\bscp\b.*(?<![\w\x24.{}\-])[\x27"]?(?![A-Za-z]:[\\/])(?:[\w.\-]+@)?\w[\w.\-]*:' \
  -- ':(icase)*.ps1' ':(icase)*.psm1' ':(icase)*.psd1'
# K-76: en un .psd1 el servidor es una clave de la tabla («Servidor = '...'»), sin $.
buscar "$salida" -i -e '(?<![\w\x24])Servidor\s*=\s*[\x27"](?!\x24)' -- ':(icase)*.psd1'

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
