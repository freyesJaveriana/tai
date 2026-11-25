"""Confirma que la suite está en rojo por fallos y no por errores (paso 5, R-14 de la revisión 2).

Lee el informe JUnit que escribe `pytest --junitxml` y termina con código 0 solo si `errors` es
`"0"` en todas las suites y `failures` suma más de cero. Código 1: el rojo no es comprobable
(errores de recolección o ejecución, o ningún fallo). Código 2: el informe falta o no se puede
leer. Uso: `python -m veridicus_contracts.tools.check_red build/red.xml`.
"""

import sys
from collections.abc import Sequence
from pathlib import Path
from xml.etree import ElementTree

CODIGO_ROJO_COMPROBABLE = 0
CODIGO_NO_ES_ROJO_COMPROBABLE = 1
CODIGO_INFORME_ILEGIBLE = 2


class InformeIlegible(ValueError):
    """El informe no existe, no es XML o no trae las cifras de pytest."""


def leer_cifras(ruta: Path) -> tuple[list[str], int]:
    """Valores de `errors` (tal cual) de cada suite y suma de `failures` de un informe JUnit."""
    try:
        arbol = ElementTree.parse(ruta)  # noqa: S314  # motivo: informe JUnit local generado por pytest, no es entrada externa
    except FileNotFoundError as error:
        raise InformeIlegible(f"no existe el informe: {ruta}") from error
    except (ElementTree.ParseError, OSError) as error:
        raise InformeIlegible(f"el informe no es XML legible: {ruta}: {error}") from error
    suites = list(arbol.getroot().iter("testsuite"))
    if not suites:
        raise InformeIlegible(f"el informe no tiene ningún testsuite: {ruta}")
    errores: list[str] = []
    fallos = 0
    for suite in suites:
        valor_errores = suite.get("errors")
        valor_fallos = suite.get("failures")
        if valor_errores is None or valor_fallos is None:
            raise InformeIlegible(f"un testsuite no declara errors y failures: {ruta}")
        try:
            fallos += int(valor_fallos)
        except ValueError as error:
            raise InformeIlegible(f"failures no es un entero: {valor_fallos!r}") from error
        errores.append(valor_errores)
    return errores, fallos


def main(argumentos: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida."""
    argv = list(sys.argv[1:] if argumentos is None else argumentos)
    if len(argv) != 1:
        print("uso: python -m veridicus_contracts.tools.check_red <informe.xml>", file=sys.stderr)
        return CODIGO_INFORME_ILEGIBLE
    try:
        errores, fallos = leer_cifras(Path(argv[0]))
    except InformeIlegible as error:
        print(f"check_red: {error}", file=sys.stderr)
        return CODIGO_INFORME_ILEGIBLE
    if any(valor != "0" for valor in errores):
        print(f"check_red: hay errores de pytest (errors={errores}); el rojo no es comprobable")
        return CODIGO_NO_ES_ROJO_COMPROBABLE
    if fallos == 0:
        print("check_red: ningún fallo; sin rojo no hay prueba escrita antes del contrato")
        return CODIGO_NO_ES_ROJO_COMPROBABLE
    print(f"check_red: rojo comprobable: {fallos} fallos y 0 errores")
    return CODIGO_ROJO_COMPROBABLE


if __name__ == "__main__":
    sys.exit(main())
