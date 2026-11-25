#!/usr/bin/env bash
# K-76 (R-11): autoprueba de las guardias del repositorio público.
# Cada caso arma, en un repositorio de Git temporal FUERA del árbol versionado, un archivo con una sonda
# sintética (o con su control negativo) y corre la guardia con esa raíz como argumento. Una sonda debe dar
# código 1 (la guardia la ve) y un control debe dar 0 (la guardia no da falso positivo). Cualquier otro código
# (por ejemplo 2, fallo de la guardia) cuenta como no detectado.
#
# Ninguna sonda queda escrita entera en este archivo: cada una se construye en tiempo de ejecución a partir de
# fragmentos, de modo que las propias guardias no se disparan sobre su autoprueba (P-T29-2). Los informes
# describen las sondas con palabras, nunca con su texto.
#
# Uso: bash scripts/tests/autoprueba-guardias.sh
# Imprime «sondas: D de N detectadas» y «controles: L de M limpios»; sale con 0 solo si todo coincide.
set -euo pipefail

aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts="$(dirname "$aqui")"
ids="$scripts/check-no-cluster-ids.sh"
datos="$scripts/check-no-datos-personales.sh"

trabajo="$(mktemp -d)"
trap 'rm -rf "$trabajo"' EXIT

sondas=0
detectadas=0
controles=0
limpios=0
fallos=""

# Fragmentos. Ninguno, por sí solo, tiene la forma que busca una guardia.
nodo="hp"; nodo+="c"; nodo+="11-z7"            # nombre de nodo no exento
nodo_exento="hp"; nodo_exento+="c99"; nodo_exento+="-w999"
param="\$Ser"; param+="vidor"                  # el nombre del parámetro del servidor
param_ambito="\$scr"; param_ambito+="ipt:Ser"; param_ambito+="vidor"
clave="Ser"; clave+="vidor"                    # la clave en un archivo de datos
raiz_cl="/zi"; raiz_cl+="ne/"                  # inicio de una ruta absoluta del clúster
copia="s"; copia+="cp"
puerto_a="usua"; puerto_a+="rio@nod"; puerto_a+="o7:"
host_a="no"; host_a+="do7"                     # host literal sin usuario
documento="c"; documento+="édula "
exento="1234"; exento+="5678"

# caso <S|C> <guardia> <ruta del archivo> <contenido> <descripción en palabras>
caso() {
  local tipo="$1" guardia="$2" ruta="$3" contenido="$4" descripcion="$5"
  local repo="$trabajo/repo"
  rm -rf "$repo"
  mkdir -p "$repo"
  git -C "$repo" init -q
  mkdir -p "$repo/$(dirname "$ruta")"
  printf '%s\n' "$contenido" > "$repo/$ruta"
  git -C "$repo" add -A
  local codigo=0
  bash "$guardia" "$repo" > /dev/null 2>&1 || codigo=$?
  if [ "$tipo" = "S" ]; then
    sondas=$((sondas + 1))
    if [ "$codigo" -eq 1 ]; then
      detectadas=$((detectadas + 1))
    else
      fallos+="  sonda no detectada (código $codigo): $descripcion"$'\n'
    fi
  else
    controles=$((controles + 1))
    if [ "$codigo" -eq 0 ]; then
      limpios=$((limpios + 1))
    else
      fallos+="  control con falso positivo (código $codigo): $descripcion"$'\n'
    fi
  fi
}

# --- Sondas de check-no-cluster-ids.sh -------------------------------------------------------------------
caso S "$ids" "scripts/a.ps1" "$param_ambito = 'otro-host'" \
  "asignación con ámbito del servidor (script:) con valor literal"
caso S "$ids" "docs/informe-$nodo.md" "texto sin nada especial" \
  "nombre de nodo en la ruta de un archivo versionado (contenido limpio)"
caso S "$ids" "config/valores.psd1" "@{ $clave = 'otro-host' }" \
  "archivo .psd1 con la clave del servidor y un valor literal"
caso S "$ids" "docs/enlace.md" "ver file:///${raiz_cl#/}proyectos/x" \
  "URL file: con tres barras hacia una ruta absoluta del clúster"
caso S "$ids" "scripts/b.ps1" "$param = \"\$usuario@\" + \"otro-host\"" \
  "host literal concatenado tras la arroba en la asignación del servidor"
caso S "$ids" "scripts/c.ps1" "$copia archivo.txt $puerto_a/tmp/" \
  "copia con destino de host literal y usuario"
# F-01 (ronda 2): el destino con host literal que ya veía la guardia anterior sigue viéndose.
caso S "$ids" "scripts/c.ps1" "$copia archivo.txt $puerto_a" \
  "copia con destino de host literal y usuario, sin ruta, al final de la línea"
caso S "$ids" "scripts/c.ps1" "$copia archivo.txt \"$host_a:\"" \
  "copia con destino de host literal entre comillas, sin ruta"
caso S "$ids" "scripts/c.ps1" "$copia archivo.txt $host_a: ruta/x" \
  "copia con destino de host literal y un espacio después de los dos puntos"
caso S "$ids" "docs/nota.md" "nodo de entrada $nodo para el trabajo" \
  "nombre de nodo en el contenido (regla previa)"
caso S "$ids" "docs/ruta.md" "datos en ${raiz_cl}proyectos/x" \
  "ruta absoluta del clúster en el contenido (regla previa)"

# --- Controles negativos de check-no-cluster-ids.sh ------------------------------------------------------
caso C "$ids" "scripts/a.ps1" "$param_ambito = \$env:DESTINO" \
  "asignación con ámbito del servidor tomada de una variable"
caso C "$ids" "docs/informe-$nodo_exento.md" "texto sin nada especial" \
  "nombre inventado de la lista de exenciones en la ruta"
caso C "$ids" "config/valores.psd1" "@{ Version = '1.0' }" \
  "archivo .psd1 sin servidor"
caso C "$ids" "docs/enlace.md" "ver file:///tmp/x y docs/${raiz_cl#/}x" \
  "URL file: con tres barras hacia otra ruta y ruta relativa que contiene el segmento"
caso C "$ids" "scripts/b.ps1" "$param = \"\$usuario@\" + \$otro" \
  "concatenación tras la arroba con una variable y no un literal"
caso C "$ids" "scripts/c.ps1" "Write-Error \"$copia falló: \$_\"" \
  "mensaje de error que nombra la copia y lleva dos puntos seguidos de espacio"
caso C "$ids" "scripts/d.ps1" "$copia \$origen \"\${usuario}@\${destino}:/tmp/\"" \
  "copia con destino armado desde variables"
caso C "$ids" "scripts/e.ps1" "$copia -v archivo.txt https://ejemplo.invalid/x" \
  "copia cuyo argumento es una URL y no un host"
# F-02 (ronda 2): los tres falsos positivos reales de F-05 de la revisión de T29.
caso C "$ids" "scripts/f.ps1" "$copia \$origen \$destino; Write-Host \"listo a las 12:30\"" \
  "línea de copia que lleva una hora"
caso C "$ids" "scripts/f.ps1" "$copia \$origen \$destino # nota:x" \
  "comentario con palabra, dos puntos y una letra pegada en la línea de la copia"
caso C "$ids" "scripts/f.ps1" "$copia \$origen \$destino:/tmp/" \
  "destino que sale de una variable sin llaves seguida de dos puntos, sin comillas"
caso C "$ids" "scripts/f.ps1" "$copia \$origen \"\$destino:/tmp/\"" \
  "destino que sale de una variable sin llaves seguida de dos puntos, entre comillas"
caso C "$ids" "scripts/f.ps1" "$copia \$origen \$env:DESTINO:/tmp/" \
  "destino que sale de una variable de entorno sin llaves seguida de dos puntos"
caso C "$ids" "scripts/f.ps1" "$copia \$origen \"\$env:DESTINO:/tmp/\"" \
  "destino de variable de entorno sin llaves seguida de dos puntos, entre comillas"

# --- Sondas de check-no-datos-personales.sh --------------------------------------------------------------
caso S "$datos" "docs/a.md" "${documento}${exento}.456" \
  "número exento seguido de punto y cifras tras la palabra de contexto (A-05)"
caso S "$datos" "docs/b.md" "${documento}987654321" \
  "documento con número no exento (regla previa)"

# --- Controles negativos de check-no-datos-personales.sh -------------------------------------------------
caso C "$datos" "docs/a.md" "${documento}${exento}. Siguiente frase." \
  "número exento seguido de un punto de fin de frase"
caso C "$datos" "docs/b.md" "${documento}${exento}" \
  "número exento solo"

echo "sondas: $detectadas de $sondas detectadas"
echo "controles: $limpios de $controles limpios"
if [ "$detectadas" -eq "$sondas" ] && [ "$limpios" -eq "$controles" ] \
  && [ "$sondas" -ge 7 ] && [ "$controles" -ge 7 ]; then
  exit 0
fi
printf '%s' "$fallos"
exit 1
