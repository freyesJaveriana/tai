"""Catálogo único de errores y sus clases (§4.7 a–e de NFR Design, sin la parte de C1).

Módulo guardia (100 % de ramas). Compara `errors/error-codes.v2.yaml` con las clases de
`libs/errors/src/` **leyéndolas con `ast`, sin importarlas** (PD-7: `contracts/` no depende de
`veridicus_errors`) y comprueba la tabla de `error.codigo` de C6 (E34).

La parte de C1, C21 y la ruta interna de voz (paso 16, T15) comprueba: (a) que el enum
`ErrorCode` de C1 y el catálogo coincidan; (b) que todo `code` usado exista, también cuando no va
bajo `code` o `error_code`: en el enum de `ErrorCode` y en la `description` de cada respuesta
(K-05, K-19, E44); (c) que la respuesta que nombra un `code` use el estado del catálogo (K-18);
(d) que toda 4xx y 5xx de C1 sea una referencia a `Problem`. Todas las funciones reciben rutas o
documentos y devuelven la lista de problemas (vacía si todo está bien); nunca escriben.
"""

import ast
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, NamedTuple

from veridicus_contracts.checks._openapi import cargar, es_problem, objeto, operaciones
from veridicus_contracts.loaders import load_file

CODE = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*$")
# Un token con la forma de un `code` dentro de un texto (la descripción de una respuesta). Solo
# cuenta si su dominio (lo que va antes del punto) existe en el catálogo (P-T15-4): «e.g.» no.
CODE_EN_TEXTO = re.compile(r"\b[a-z][a-z_]*\.[a-z][a-z_]*\b")
# Claves de los contratos bajo las que se nombra un `code` del catálogo (C2, C3, C5, C21...);
# `ErrorCode` es el esquema cuyo `enum` los lista en C1.
CLAVES_DE_CODE = frozenset({"code", "error_code", "ErrorCode"})
REGLA_API = "§4.7"
CATALOGO_RELATIVO = "errors/error-codes.v2.yaml"
CONSOLA = "api/console.v2.yaml"
# Contratos con respuestas que nombran `code` y a los que no se exige el `$ref` a `Problem`.
INTERNOS = ("api/anonymizer-proxy.v1.yaml", "api/speech-internal.v1.yaml")
# Contratos que se recorren en (b) cuando existen (los de C1 se suman en el paso 16).
CONTRATOS_CON_CODES = ("queues/*.yaml", "api/*.yaml")
RAIZ = "VeridicusError"  # raíz de la jerarquía única (BR7.4)
CODE_C6_PROVEEDOR = ("proveedor", "analysis.provider")  # BR3.4


class ClaseLeida(NamedTuple):
    """Una clase del código fuente de `libs/errors/`, leída sin importarla."""

    nombre: str
    bases: tuple[str, ...]
    code: str | None
    con_logica: bool
    code_no_textual: bool = False


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


def _valor_de_code(nodo: ast.stmt) -> ast.expr | None:
    """El valor de `code = ...` o `code: ClassVar[str] = ...`; `None` si el nodo es otra cosa."""
    destinos: list[ast.expr]
    if isinstance(nodo, ast.AnnAssign):
        destinos = [nodo.target]
        valor = nodo.value
    elif isinstance(nodo, ast.Assign):
        destinos = list(nodo.targets)
        valor = nodo.value
    else:
        return None
    if len(destinos) == 1 and isinstance(destinos[0], ast.Name) and destinos[0].id == "code":
        return valor
    return None


def _leer_clase(nodo: ast.ClassDef) -> ClaseLeida:
    bases = tuple(base.id for base in nodo.bases if isinstance(base, ast.Name))
    code: str | None = None
    con_logica = False
    no_textual = False
    for cuerpo in nodo.body:
        if _es_docstring(cuerpo):
            continue
        valor = _valor_de_code(cuerpo)
        if valor is None:
            con_logica = True
        elif isinstance(valor, ast.Constant) and isinstance(valor.value, str):
            code = valor.value
        else:
            no_textual = True
    return ClaseLeida(nodo.name, bases, code, con_logica, no_textual)


def _familia_de(code: str) -> str:
    """Nombre de la base de familia de un `code`: `session.blocked` -> `SessionFamilyError`."""
    partes = code.split(".")[0].split("_")
    return "".join(parte.capitalize() for parte in partes) + "FamilyError"


def leer_clases(src: Path) -> list[ClaseLeida]:
    """Todas las clases de los `.py` bajo `src`, con `ast` (nunca importa el código)."""
    clases: list[ClaseLeida] = []
    for archivo in sorted(src.rglob("*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        clases.extend(
            _leer_clase(nodo) for nodo in ast.walk(arbol) if isinstance(nodo, ast.ClassDef)
        )
    return clases


def comprobar_clases(catalogo: dict[str, dict[str, Any]], clases: list[ClaseLeida]) -> list[str]:
    """(e) y BR7.4: cada `code` tiene exactamente una clase sin lógica y cada clase su `code`."""
    problemas: list[str] = []
    por_code: dict[str, list[ClaseLeida]] = {}
    bases_usadas = {base for clase in clases for base in clase.bases}
    for clase in clases:
        if clase.con_logica:
            problemas.append(f"{clase.nombre}: define lógica o atributos distintos de code (BR7.4)")
        if clase.code_no_textual:
            problemas.append(f"{clase.nombre}: su code no es un texto literal (E31)")
        if clase.code is not None:
            por_code.setdefault(clase.code, []).append(clase)
            if _familia_de(clase.code) not in clase.bases:
                problemas.append(
                    f"{clase.nombre}: su base debe ser {_familia_de(clase.code)} (BR7.4)"
                )
        elif clase.nombre not in bases_usadas:
            problemas.append(f"{clase.nombre}: clase de excepción sin code (E31)")
    por_nombre = {clase.nombre: clase for clase in clases}
    for familia in sorted({_familia_de(code) for code in por_code}):
        if familia not in por_nombre or RAIZ not in por_nombre[familia].bases:
            problemas.append(f"{familia}: la base de familia debe heredar de {RAIZ} (BR7.4)")
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


def comprobar_enum_error_code(
    catalogo: dict[str, dict[str, Any]], nombre: str, documento: Any
) -> list[str]:
    """(a): el enum `ErrorCode` de C1 es exactamente el de los `code` con `http: true`."""
    esquema = objeto(objeto(objeto(documento).get("components")).get("schemas")).get("ErrorCode")
    enum = objeto(esquema).get("enum", [])
    esperados = [code for code, entrada in catalogo.items() if entrada.get("http")]
    problemas = [
        f"{nombre}: el enum ErrorCode no trae {code} ({REGLA_API} a)"
        for code in esperados
        if code not in enum
    ]
    problemas.extend(
        f"{nombre}: el enum ErrorCode trae {code} y el catálogo no lo declara con http: true "
        f"({REGLA_API} a)"
        for code in sorted(set(enum) - set(esperados))
    )
    return problemas


def comprobar_respuestas(
    catalogo: dict[str, dict[str, Any]], nombre: str, documento: Any, exigir_problem: bool
) -> list[str]:
    """(b), (c) y (d): los `code` nombrados en la descripción de cada respuesta y su estado.

    Un `code` de la descripción debe existir y declarar el estado de la respuesta que lo nombra. Con
    `exigir_problem`, toda 4xx y 5xx debe ser una referencia a `Problem` (C1).
    """
    problemas: list[str] = []
    dominios = {code.split(".")[0] for code in catalogo}
    for ruta, metodo, operacion in operaciones(documento):
        for clave, respuesta in objeto(operacion.get("responses")).items():
            estado = str(clave)
            donde = f"{nombre}: {metodo.upper()} {ruta} {estado}"
            descripcion = objeto(respuesta).get("description")
            texto = descripcion if isinstance(descripcion, str) else ""
            citados = [c for c in CODE_EN_TEXTO.findall(texto) if c.split(".")[0] in dominios]
            for code in dict.fromkeys(citados):
                entrada = catalogo.get(code)
                if entrada is None:
                    problemas.append(f"{donde}: el code {code} no está en el catálogo (BR7.2, E44)")
                elif "status" not in entrada:
                    problemas.append(
                        f"{donde}: el code {code} no tiene estado HTTP en el catálogo "
                        f"({REGLA_API} c)"
                    )
                elif estado != str(entrada["status"]):
                    problemas.append(
                        f"{donde}: el code {code} lleva el estado {estado} y el catálogo dice "
                        f"{entrada['status']} ({REGLA_API} c)"
                    )
            if exigir_problem and estado[:1] in ("4", "5") and not es_problem(respuesta):
                problemas.append(
                    f"{donde}: respuesta de error sin $ref a Problem ({REGLA_API} d)"
                )
    return problemas


def comprobar_api(contracts_root: Path) -> list[str]:
    """La parte de C1, C21 y la ruta de voz sobre `contracts/`; un contrato ausente es un problema."""
    problemas: list[str] = []
    documentos: dict[str, Any] = {}
    for relativa in (CATALOGO_RELATIVO, CONSOLA, *INTERNOS):
        documentos[relativa], faltas = cargar(contracts_root, relativa, REGLA_API)
        problemas.extend(faltas)
    if problemas:
        return problemas
    catalogo: dict[str, dict[str, Any]] = documentos[CATALOGO_RELATIVO]["codes"]
    problemas = comprobar_enum_error_code(catalogo, CONSOLA, documentos[CONSOLA])
    problemas.extend(comprobar_respuestas(catalogo, CONSOLA, documentos[CONSOLA], True))
    for relativa in INTERNOS:
        problemas.extend(comprobar_respuestas(catalogo, relativa, documentos[relativa], False))
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
