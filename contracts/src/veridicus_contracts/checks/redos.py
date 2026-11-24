"""Patrones sin retroceso catastrófico (security-design §4.5, NFR10.6; K-24).

Módulo guardia (100 % de ramas). Hace tres comprobaciones deterministas sobre cada `pattern` de los
contratos; la cuarta, de propiedades con Hypothesis y techo de 1 s, vive en `tests/checks/test_redos.py`.

1. **Recorrido completo del árbol** con `re._parser`: rechaza una repetición ilimitada dentro de otra,
   cualquier `BRANCH` dentro de una repetición ilimitada (se reescribe como clase de caracteres) y las
   referencias hacia atrás (`GROUPREF`, `GROUPREF_EXISTS`). Desciende por grupos, miradas, grupos atómicos y
   las dos ramas de `GROUPREF_EXISTS`.
2. **Subconjunto portátil**: la mitad TypeScript valida los mismos patrones con el motor de JavaScript, así
   que se rechazan `\\d`, `\\w`, `\\s` y `\\b` (en Python casan Unicode), los grupos con nombre, las banderas
   en línea y las miradas atrás, y todo patrón va anclado (`^…$`).
3. **Entrada acotada**: un `pattern` con repetición ilimitada exige `maxLength` con su `x-veridicus-limit`.

Depende de una API privada de Python 3.12: una prueba exige esa versión (sustituye a un falso verde).

Los mensajes nombran el archivo, el puntero y la regla, nunca el patrón.
"""

import importlib
import re
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._recorrido import documentos, nodos

_parser: Any = importlib.import_module("re._parser")
_c: Any = importlib.import_module("re._constants")

ANIDADA = "repetición ilimitada dentro de otra repetición ilimitada"
RAMA = "alternativa dentro de una repetición ilimitada (reescribir como clase de caracteres)"
REFERENCIA = "referencia hacia atrás"
CLASE = "clase abreviada \\d, \\w, \\s o \\b (no portátil)"
NOMBRADO = "grupo con nombre (no portátil)"
BANDERAS = "bandera en línea (no portátil)"
ATRAS = "mirada atrás (no portátil)"
SIN_ANCLAR = "patrón sin anclar con ^ y $"
NO_VALIDO = "patrón que no compila"
_ILIMITADA = "repetición ilimitada"  # marca interna, no es un hallazgo

# K-24, limitación declarada: varios `[a-z]*` contiguos son polinomiales y el recorrido del árbol no los ve
# (`^(a|a)+$` sí lo rechaza la regla de BRANCH). Los acota la regla de entrada acotada: un patrón con
# repetición ilimitada exige maxLength con su límite, y los patrones solo entran por PR.
LIMITACION_K24 = "K-24: cuantificadores contiguos sin anidar los acota maxLength, no el recorrido del árbol"

_ARBOL = frozenset({ANIDADA, RAMA, REFERENCIA})
_PORTABLES = frozenset({CLASE, NOMBRADO, BANDERAS, ATRAS, SIN_ANCLAR})
REGLA = "(NFR10.6)"


def _analizar(arbol: Any, ilimitada: bool, hallazgos: set[str]) -> None:
    for op, arg in arbol:
        if op in (_c.GROUPREF, _c.GROUPREF_EXISTS):
            hallazgos.add(REFERENCIA)
        if op == _c.AT:
            if arg in (_c.AT_BOUNDARY, _c.AT_NON_BOUNDARY):
                hallazgos.add(CLASE)
        elif op == _c.IN:
            if any(sub == _c.CATEGORY for sub, _ in arg):
                hallazgos.add(CLASE)
        elif op in (_c.MAX_REPEAT, _c.MIN_REPEAT, _c.POSSESSIVE_REPEAT):
            _, maximo, sub = arg
            propia = maximo == _c.MAXREPEAT
            if propia:
                hallazgos.add(_ILIMITADA)
            if propia and ilimitada:
                hallazgos.add(ANIDADA)
            _analizar(sub, ilimitada or propia, hallazgos)
        elif op == _c.BRANCH:
            if ilimitada:
                hallazgos.add(RAMA)
            for rama in arg[1]:
                _analizar(rama, ilimitada, hallazgos)
        elif op == _c.SUBPATTERN:
            if arg[1] or arg[2]:
                hallazgos.add(BANDERAS)
            _analizar(arg[3], ilimitada, hallazgos)
        elif op == _c.ATOMIC_GROUP:
            _analizar(arg, ilimitada, hallazgos)
        elif op in (_c.ASSERT, _c.ASSERT_NOT):
            if arg[0] == -1:
                hallazgos.add(ATRAS)
            _analizar(arg[1], ilimitada, hallazgos)
        elif op == _c.GROUPREF_EXISTS:
            _analizar(arg[1], ilimitada, hallazgos)
            if arg[2] is not None:
                _analizar(arg[2], ilimitada, hallazgos)


def _analisis(patron: str) -> set[str] | None:
    """Los hallazgos de un patrón (con la marca interna de repetición ilimitada), o `None` si no compila."""
    try:
        arbol = _parser.parse(patron)
    except re.error:
        return None
    hallazgos: set[str] = set()
    _analizar(arbol, False, hallazgos)
    if arbol.state.groupdict:
        hallazgos.add(NOMBRADO)
    if int(arbol.state.flags) & ~int(re.UNICODE):
        hallazgos.add(BANDERAS)
    if len(arbol) < 2 or arbol[0] != (_c.AT, _c.AT_BEGINNING) or arbol[-1] != (_c.AT, _c.AT_END):
        hallazgos.add(SIN_ANCLAR)
    return hallazgos


def violaciones_del_arbol(patron: str) -> list[str]:
    """Punto 1 de §4.5: repetición anidada, alternativa en repetición y referencias hacia atrás."""
    hallazgos = _analisis(patron)
    return [NO_VALIDO] if hallazgos is None else sorted(hallazgos & _ARBOL)


def violaciones_portables(patron: str) -> list[str]:
    """Punto 2 de §4.5: el subconjunto que corre igual en Python y en JavaScript, y todo anclado."""
    hallazgos = _analisis(patron)
    return [NO_VALIDO] if hallazgos is None else sorted(hallazgos & _PORTABLES)


def tiene_repeticion_ilimitada(patron: str) -> bool:
    """`*`, `+` o `{n,}` en cualquier parte del patrón; un patrón que no compila no tiene."""
    hallazgos = _analisis(patron)
    return hallazgos is not None and _ILIMITADA in hallazgos


def comprobar_patron(patron: str) -> list[str]:
    """Todos los hallazgos de un patrón, ordenados y sin repetir."""
    hallazgos = _analisis(patron)
    return [NO_VALIDO] if hallazgos is None else sorted(hallazgos - {_ILIMITADA})


def comprobar_esquema(esquema: dict[str, Any]) -> list[str]:
    """Punto 3 de §4.5: una repetición ilimitada exige `maxLength` con su `x-veridicus-limit`."""
    patron = esquema.get("pattern")
    if not isinstance(patron, str) or not tiene_repeticion_ilimitada(patron):
        return []
    if "maxLength" not in esquema:
        return ["repetición ilimitada sin maxLength"]
    if "x-veridicus-limit" not in esquema:
        return ["maxLength sin x-veridicus-limit"]
    return []


def comprobar_documento(documento: Any, nombre: str) -> list[str]:
    """Los problemas de cada `pattern` de un contrato ya cargado."""
    problemas: list[str] = []
    for puntero, nodo in nodos(documento):
        patron = nodo.get("pattern")
        if isinstance(patron, str):
            for texto in (*comprobar_patron(patron), *comprobar_esquema(nodo)):
                problemas.append(f"{nombre}#{puntero}: {texto} {REGLA}")
    return problemas


def patrones(raiz: Path) -> list[str]:
    """Los `pattern` distintos de los contratos legibles bajo `raiz`, ordenados."""
    vistos: set[str] = set()
    for _, documento, legible in documentos(raiz):
        if legible:
            vistos.update(n["pattern"] for _, n in nodos(documento) if isinstance(n.get("pattern"), str))
    return sorted(vistos)


def comprobar(raiz: Path) -> list[str]:
    """Comprueba los patrones de los contratos de `raiz` (sin `vendor/`, `fixtures/` ni `tests/`)."""
    problemas: list[str] = []
    for relativa, documento, legible in documentos(raiz):
        if legible:
            problemas.extend(comprobar_documento(documento, relativa))
        else:
            problemas.append(f"{relativa}: contrato ilegible {REGLA}")
    return problemas
