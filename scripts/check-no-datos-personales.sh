#!/usr/bin/env bash
# K-75 (E-32, P-T30-1): el repositorio es publico y no debe llevar datos personales del autor.
# La guardia falla, nombrando archivo y línea (nunca el texto hallado), si un archivo versionado
# (git ls-files, sin binarios: git grep -I) contiene:
#   (a) un documento de identidad: una palabra de contexto (C.C., CC, cédula, cedula, documento de identidad,
#       sin distinguir mayúsculas) seguida, a menos de 20 caracteres, de un número de 6 a 10 dígitos, con o sin
#       puntos de miles;
#   (b) un correo del autor: cada correo que aparece en un archivo versionado se pasa a minúsculas y se calcula
#       su SHA-256; falla si el hash está en una lista cerrada de este script. La lista lleva SOLO hashes, nunca
#       el correo:
#         - el correo personal cuenta en todo el repositorio;
#         - el correo institucional solo cuenta en plan-aidlc.md y en research/06-documentacion-propia/, porque
#           P-T30-1 mantiene su uso en el pie de los documentos del curso.
#       Los correos de autores de artículos de terceros no cuentan: su hash no está en la lista.
#
# Límites conocidos: un nombre de archivo con dos puntos pierde el número de línea en la salida (la aparición sí
# se cuenta); un correo partido en varias líneas o con otra codificación no se detecta.
#
# Uso: bash scripts/check-no-datos-personales.sh [raíz]
# Imprime «N apariciones» y sale con 0 solo si N es 0 (1 si hay apariciones, 2 si la raíz no es un repositorio
# de Git o la búsqueda falla).
set -euo pipefail

raiz="${1:-.}"

# Lista cerrada de hashes SHA-256 (correo en minúsculas). Una entrada por correo; nunca el correo.
hashes_todo_el_repositorio=(
  "57fade48da68ab888cdc49243c93731a8b2591b4da704f4d5ba1b82003b77ac4"
)
hashes_solo_en_alcance=(
  "a3bc2c299f7bc16a72cd2f14fb43b4622be6e5c7487fce079f4c065fad39e71d"
)
# Exenciones de la regla (a) (P-T30-2): números inventados exactos, comparados sin la palabra de contexto.
# No se exime ninguna carpeta ni ningún archivo.
#   12345678        canario inventado de contracts/tests/checks/test_synthetic.py (prueba del escáner de literales).
#   1.234.567.890   cédula inventada del caso E1 de functional-spec.md del anonimizador (artefacto aprobado).
numeros_inventados=("12345678" "1.234.567.890")
# Prefijos de ruta (o rutas exactas) donde cuenta la segunda lista.
rutas_del_alcance=("plan-aidlc.md" "research/06-documentacion-propia/")

if ! git -C "$raiz" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "check-no-datos-personales: $raiz no es un repositorio de Git."
  exit 2
fi

salida="$(mktemp)"
hallados="$(mktemp)"
numeros="$(mktemp)"
errores="$(mktemp)"
trap 'rm -f "$salida" "$hallados" "$numeros" "$errores"' EXIT

# git grep: código 0 = hay coincidencias, 1 = no hay; otro código o stderr no vacío es un fallo.
buscar() {
  local destino="$1"
  shift
  local codigo=0
  git -C "$raiz" grep -n -I -P "$@" >> "$destino" 2>> "$errores" || codigo=$?
  if [ "$codigo" -gt 1 ] || [ -s "$errores" ]; then
    echo "check-no-datos-personales: FALLO al buscar (código de git grep: $codigo); no se puede afirmar 0 apariciones:"
    cat "$errores"
    exit 2
  fi
}

# (a) -i: sin distinguir mayúsculas. Salida archivo:línea:texto; solo se usan archivo y línea.
# \K deja solo el número en la salida (-o), para compararlo con la lista de exentos. La sigla CC cuenta solo
# como palabra suelta: ni barra, ni punto, ni guion, ni carácter de palabra antes o después (P-T30-2).
buscar "$numeros" -i -o \
  -e '(?:\bC\.C\.|(?<![\w/.\-])CC(?![\w/.\-])|\bc(?:é|e)dula|\bdocumento de identidad).{0,19}?\K(?<![\d.])(?:\d{6,10}|\d{1,3}(?:\.\d{3}){2,3})(?![\d])' \
  -- .
while IFS=: read -r archivo numero texto; do
  [ -n "$archivo" ] || continue
  exento=0
  for permitido in "${numeros_inventados[@]}"; do
    if [ "$texto" = "$permitido" ]; then
      exento=1
    fi
  done
  if [ "$exento" -eq 0 ]; then
    echo "$archivo:$numero:x" >> "$salida"
  fi
done < "$numeros"

# (b) -o: solo el correo. Se compara su hash, nunca el texto.
buscar "$hallados" -o -e '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+' -- .
while IFS=: read -r archivo numero correo; do
  [ -n "$archivo" ] || continue
  minuscula="${correo,,}"
  hash="$(printf '%s' "$minuscula" | sha256sum | cut -d' ' -f1)"
  marca=0
  for h in "${hashes_todo_el_repositorio[@]}"; do
    if [ "$hash" = "$h" ]; then
      marca=1
    fi
  done
  for h in "${hashes_solo_en_alcance[@]}"; do
    if [ "$hash" = "$h" ]; then
      for ruta in "${rutas_del_alcance[@]}"; do
        case "$archivo" in
          "$ruta"*) marca=1 ;;
        esac
      done
    fi
  done
  if [ "$marca" -eq 1 ]; then
    echo "$archivo:$numero:x" >> "$salida"
  fi
done < "$hallados"

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

echo "check-no-datos-personales: datos personales del autor en archivos versionados (solo archivo:línea):"
printf '%s' "$detalle"
echo "$n apariciones"
exit 1
