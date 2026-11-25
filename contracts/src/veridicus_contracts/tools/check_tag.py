"""Etiqueta de la entrega de `contracts/` (BR12.2, precisión de E-32).

La etiqueta es `contracts-v` más `[project].version` de `pyproject.toml`: la versión del paquete es
igual a la de su etiqueta. La versión de cada contrato es otra cosa y no se mira aquí.

Sin `--tag` imprime la etiqueta esperada y sale con 0. Con `--tag ETIQUETA` sale con 0 solo si es
exactamente la esperada; si no, sale con 1 y un mensaje en español que nombra las dos. También sale
con 1 si `pyproject.toml` no se puede leer o si `[project].version` no tiene la forma
`MAYOR.MENOR.PARCHE`. Código 2: argumentos mal escritos, sin valor o repetidos.

Solo usa la biblioteca estándar, no abre la red y nunca escribe. Lee `pyproject.toml` del directorio de
trabajo (`uv run --directory contracts`) o el que indique `--pyproject RUTA`.
Uso: `python -m veridicus_contracts.tools.check_tag [--pyproject RUTA] [--tag ETIQUETA]`.
"""

import re
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

PREFIJO = "contracts-v"
CODIGO_CORRECTO = 0
CODIGO_ETIQUETA_INCORRECTA = 1
CODIGO_USO = 2

_VERSION_SEMANTICA = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
_USO = "uso: python -m veridicus_contracts.tools.check_tag [--pyproject RUTA] [--tag ETIQUETA]"


class VersionInvalida(ValueError):
    """`[project].version` falta o no tiene la forma `MAYOR.MENOR.PARCHE`."""


def etiqueta_esperada(pyproject: Path) -> str:
    """`contracts-v<versión>` con la `[project].version` del archivo.

    Lanza `VersionInvalida` si la versión falta o no es `MAYOR.MENOR.PARCHE` (sin ceros a la
    izquierda), y `OSError` o `tomllib.TOMLDecodeError` si el archivo no se puede leer.
    """
    with pyproject.open("rb") as archivo:
        datos = tomllib.load(archivo)
    proyecto = datos.get("project")
    version = proyecto.get("version") if isinstance(proyecto, dict) else None
    if not isinstance(version, str) or _VERSION_SEMANTICA.fullmatch(version) is None:
        raise VersionInvalida(
            f"[project].version de {pyproject} debe tener la forma MAYOR.MENOR.PARCHE y es {version!r}"
        )
    return PREFIJO + version


def _leer_argumentos(argv: Sequence[str]) -> dict[str, str] | None:
    """Valores de `--pyproject` y `--tag`.

    Devuelve `None` si hay un argumento desconocido, una opción sin valor o una opción repetida.
    """
    valores: dict[str, str] = {}
    posicion = 0
    while posicion < len(argv):
        opcion = argv[posicion]
        if opcion not in ("--pyproject", "--tag") or posicion + 1 >= len(argv) or opcion in valores:
            return None
        valores[opcion] = argv[posicion + 1]
        posicion += 2
    return valores


def main(argumentos: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida."""
    valores = _leer_argumentos(list(sys.argv[1:] if argumentos is None else argumentos))
    if valores is None:
        print(_USO, file=sys.stderr)
        return CODIGO_USO
    ruta = Path(valores.get("--pyproject", "pyproject.toml"))
    try:
        esperada = etiqueta_esperada(ruta)
    except (OSError, tomllib.TOMLDecodeError, VersionInvalida) as error:
        print(f"check_tag: no se pudo calcular la etiqueta: {error}", file=sys.stderr)
        return CODIGO_ETIQUETA_INCORRECTA
    recibida = valores.get("--tag")
    if recibida is None:
        print(esperada)
        return CODIGO_CORRECTO
    if recibida != esperada:
        print(
            f"check_tag: la etiqueta {recibida!r} no es la esperada {esperada!r} "
            f"(contracts-v más [project].version de {ruta})",
            file=sys.stderr,
        )
        return CODIGO_ETIQUETA_INCORRECTA
    return CODIGO_CORRECTO


if __name__ == "__main__":
    sys.exit(main())
