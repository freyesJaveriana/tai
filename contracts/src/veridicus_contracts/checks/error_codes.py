"""Catálogo único de errores y sus clases (§4.7 a–e de NFR Design, sin la parte de C1).

Módulo guardia (100 % de ramas). Compara `errors/error-codes.v2.yaml` con las clases de
`libs/errors/src/` **leyéndolas con `ast`, sin importarlas** (PD-7: `contracts/` no depende de
`veridicus_errors`) y comprueba la tabla de `error.codigo` de C6 (E34).

La parte de C1 (enum `ErrorCode`, estados de las respuestas y `$ref` a `Problem`) se completa en
el paso 16. Todas las funciones reciben rutas y devuelven la lista de problemas (vacía si todo
está bien); nunca escriben.
"""

import ast
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, NamedTuple

from veridicus_contracts.loaders import load_file

CODE = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*$")
# Claves de los contratos bajo las que se nombra un `code` del catálogo (C2, C3, C5, C21...).
CLAVES_DE_CODE = frozenset({"code", "error_code"})
# Contratos que se recorren en (b) cuando existen (los de C1 se suman en el paso 16).
CONTRATOS_CON_CODES = ("queues/*.yaml", "api/*.yaml")
CODE_C6_PROVEEDOR = ("proveedor", "analysis.provider")  # BR3.4


class ClaseLeida(NamedTuple):
    """Una clase del código fuente de `libs/errors/`, leída sin importarla."""

    nombre: str
    bases: tuple[str, ...]
    code: str | None
    con_logica: bool


def cargar_catalogo(ruta: Path) -> dict[str, dict[str, Any]]:
    """Las entradas `codes` del catálogo, por `code`."""
    codes: dict[str, dict[str, Any]] = load_file(ruta)["codes"]
    return codes


def _es_docstring(nodo: ast.stmt) -> bool:
    return (
        isinstance(nodo, ast.Expr)
        and isinstance(nodo.value, ast.Constant)
        and isinstance(nodo.value.value, str)
    )


def _code_de(nodo: ast.stmt) -> str | None:
    """El texto de `code = "x"` o `code: ClassVar[str] = "x"`; `None` si el nodo es otra cosa."""
    destinos: list[ast.expr]
    if isinstance(nodo, ast.AnnAssign):
        destinos = [nodo.target]
        valor = nodo.value
    elif isinstance(nodo, ast.Assign):
        destinos = list(nodo.targets)
        valor = nodo.value
    else:
        return None
    if (
        len(destinos) == 1
        and isinstance(destinos[0], ast.Name)
        and destinos[0].id == "code"
        and isinstance(valor, ast.Constant)
        and isinstance(valor.value, str)
    ):
        return valor.value
    return None


def _leer_clase(nodo: ast.ClassDef) -> ClaseLeida:
    bases = tuple(base.id for base in nodo.bases if isinstance(base, ast.Name))
    code: str | None = None
    con_logica = False
    for cuerpo in nodo.body:
        if _es_docstring(cuerpo):
            continue
        valor = _code_de(cuerpo)
        if valor is None:
            con_logica = True
        else:
            code = valor
    return ClaseLeida(nodo.name, bases, code, con_logica)


def leer_clases(src: Path) -> list[ClaseLeida]:
    """Todas las clases de los `.py` bajo `src`, con `ast` (nunca importa el código)."""
    clases: list[ClaseLeida] = []
    for archivo in sorted(src.rglob("*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        clases.extend(_leer_clase(nodo) for nodo in ast.walk(arbol) if isinstance(nodo, ast.ClassDef))
    return clases


def comprobar_clases(catalogo: dict[str, dict[str, Any]], clases: list[ClaseLeida]) -> list[str]:
    """(e) y BR7.4: cada `code` tiene exactamente una clase sin lógica y cada clase su `code`."""
    problemas: list[str] = []
    por_code: dict[str, list[ClaseLeida]] = {}
    bases_usadas = {base for clase in clases for base in clase.bases}
    for clase in clases:
        if clase.con_logica:
            problemas.append(f"{clase.nombre}: define lógica o atributos distintos de code (BR7.4)")
        if clase.code is not None:
            por_code.setdefault(clase.code, []).append(clase)
        elif clase.nombre not in bases_usadas:
            problemas.append(f"{clase.nombre}: clase de excepción sin code (E31)")
    for code, entrada in catalogo.items():
        halladas = por_code.get(code, [])
        if not halladas:
            problemas.append(f"{code}: sin clase de excepción (E31, E44)")
        elif len(halladas) > 1:
            nombres = ", ".join(clase.nombre for clase in halladas)
            problemas.append(f"{code}: dos clases comparten el code: {nombres} (BR7.4)")
        elif halladas[0].nombre != entrada["class"]:
            problemas.append(
                f"{code}: la clase es {halladas[0].nombre} y el catálogo dice {entrada['class']}"
            )
    problemas.extend(
        f"{clase.nombre}: su code {code} no está en el catálogo (E31)"
        for code, halladas in por_code.items()
        if code not in catalogo
        for clase in halladas
    )
    return problemas


def comprobar_tabla_c6(catalogo: dict[str, dict[str, Any]], salida_c6: Path) -> list[str]:
    """E34, BR3.4: cada `error.codigo` de C6 tiene su `code`, uno a uno, `proveedor` incluido."""
    esquema = load_file(salida_c6)
    enum: list[str] = esquema["properties"]["error"]["properties"]["codigo"]["enum"]
    pares = [(entrada["c6"], code) for code, entrada in catalogo.items() if "c6" in entrada]
    traducidos = dict(pares)
    problemas: list[str] = []
    if len(pares) != len(traducidos):
        problemas.append("dos code traducen el mismo error.codigo de C6 (E34)")
    problemas.extend(
        f"error.codigo {codigo!r} de C6 sin code en el catálogo (E34)"
        for codigo in enum
        if codigo not in traducidos
    )
    problemas.extend(
        f"c6 {codigo!r} de {traducidos[codigo]} no es un error.codigo de C6 (E34)"
        for codigo in traducidos
        if codigo not in enum
    )
    clave, esperado = CODE_C6_PROVEEDOR
    if traducidos.get(clave) != esperado:
        problemas.append(f"error.codigo {clave!r} debe traducirse a {esperado} (BR3.4, E34)")
    return problemas


def _usados(nodo: Any, dentro: bool = False) -> Iterator[str]:
    """Los textos con forma de `code` bajo una clave `code` o `error_code`."""
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            yield from _usados(valor, dentro or clave in CLAVES_DE_CODE)
    elif isinstance(nodo, list):
        for valor in nodo:
            yield from _usados(valor, dentro)
    elif dentro and isinstance(nodo, str) and CODE.match(nodo):
        yield nodo


def comprobar_codes_usados(
    catalogo: dict[str, dict[str, Any]], documentos: Iterable[Path]
) -> list[str]:
    """(b), BR7.2: todo `code` usado en los contratos recorridos existe en el catálogo."""
    problemas: list[str] = []
    for documento in documentos:
        problemas.extend(
            f"{documento.name}: el code {code} no está en el catálogo (BR7.2)"
            for code in sorted(set(_usados(load_file(documento))))
            if code not in catalogo
        )
    return problemas


def comprobar(contracts_root: Path, errors_src: Path) -> list[str]:
    """Todas las comprobaciones de esta tarea sobre `contracts/` y `libs/errors/src/`."""
    catalogo = cargar_catalogo(contracts_root / "errors" / "error-codes.v2.yaml")
    documentos = [ruta for patron in CONTRATOS_CON_CODES for ruta in contracts_root.glob(patron)]
    return [
        *comprobar_clases(catalogo, leer_clases(errors_src)),
        *comprobar_tabla_c6(catalogo, contracts_root / "analyzer" / "v1" / "salida.schema.json"),
        *comprobar_codes_usados(catalogo, sorted(documentos)),
    ]
