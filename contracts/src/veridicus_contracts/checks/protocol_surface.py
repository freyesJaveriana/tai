"""Superficie de la puerta única al exterior (§4.17 de NFR Design, BR9.9, E43).

Módulo guardia (100 % de ramas). Lee `model_calls.py` con `ast`, sin importarlo, y comprueba:

- el `Protocol` `AnonymizingProvider` declara solo `generate(self, request: GenerateRequest) ->
  GenerateResult` (sin `check_ready` ni atributos);
- el módulo solo importa de `veridicus_contracts`, `typing`, `dataclasses`, `enum` y `datetime`;
- existen `ModelCallError` y sus cinco subclases; `ContentBlocked`, `Timeout`, `ProviderError` e
  `InvalidOutput` declaran `call: ModelCall` y `AnonymizerUnavailable` no (FD-U10-04).

Devuelve la lista de problemas (vacía si todo está bien); nunca escribe.
"""

import ast
from pathlib import Path

IMPORTACIONES_PERMITIDAS = frozenset(
    {"veridicus_contracts", "typing", "dataclasses", "enum", "datetime"}
)
PUERTA = "AnonymizingProvider"
FIRMA_DE_GENERATE = ("self, request: GenerateRequest", "GenerateResult")
RAIZ = "ModelCallError"
ERRORES_CON_LLAMADA = ("ContentBlocked", "Timeout", "ProviderError", "InvalidOutput")
ERROR_SIN_LLAMADA = "AnonymizerUnavailable"


def _es_docstring(nodo: ast.stmt) -> bool:
    return (
        isinstance(nodo, ast.Expr)
        and isinstance(nodo.value, ast.Constant)
        and isinstance(nodo.value.value, str)
    )


def _importaciones_ajenas(arbol: ast.Module) -> list[str]:
    problemas: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres = [alias.name.split(".")[0] for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.level:
            problemas.append("importación relativa: usa el nombre completo del paquete (E43)")
            continue
        elif isinstance(nodo, ast.ImportFrom):
            nombres = [str(nodo.module).split(".")[0]]
        else:
            continue
        problemas.extend(
            f"importa fuera del paquete de contratos: {nombre} (E43)"
            for nombre in nombres
            if nombre not in IMPORTACIONES_PERMITIDAS
        )
    return problemas


def _comprobar_puerta(clase: ast.ClassDef) -> list[str]:
    problemas: list[str] = []
    if not any(ast.unparse(base) in {"Protocol", "typing.Protocol"} for base in clase.bases):
        problemas.append(f"{PUERTA} no es un Protocol (BR9.9)")
    miembros = [nodo for nodo in clase.body if not _es_docstring(nodo)]
    metodos = [n for n in miembros if isinstance(n, ast.FunctionDef) and n.name == "generate"]
    otros = [n for n in miembros if n not in metodos]
    if otros:
        detalle = "; ".join(ast.unparse(n).splitlines()[0] for n in otros)
        problemas.append(f"{PUERTA} declara miembros distintos de generate: {detalle} (BR9.9, E43)")
    if not metodos:
        problemas.append(f"{PUERTA} no declara generate (BR9.9)")
    for metodo in metodos:
        firma = (ast.unparse(metodo.args), ast.unparse(metodo.returns) if metodo.returns else "")
        if firma != FIRMA_DE_GENERATE:
            problemas.append(
                f"la firma de generate es ({firma[0]}) -> {firma[1]} y debe ser "
                f"({FIRMA_DE_GENERATE[0]}) -> {FIRMA_DE_GENERATE[1]} (BR9.9)"
            )
    return problemas


def _anotacion_de_call(clase: ast.ClassDef) -> str | None:
    """El tipo declarado para `call` en el cuerpo de la clase, o `None` si no lo declara."""
    for nodo in clase.body:
        if isinstance(nodo, ast.AnnAssign) and ast.unparse(nodo.target) == "call":
            return ast.unparse(nodo.annotation)
    return None


def _comprobar_errores(clases: dict[str, ast.ClassDef]) -> list[str]:
    problemas: list[str] = []
    if RAIZ not in clases:
        problemas.append(f"falta la clase {RAIZ} (BR9.9)")
    for nombre in (*ERRORES_CON_LLAMADA, ERROR_SIN_LLAMADA):
        if nombre not in clases:
            problemas.append(f"falta la clase {nombre} (BR9.9)")
            continue
        clase = clases[nombre]
        if RAIZ not in [ast.unparse(base) for base in clase.bases]:
            problemas.append(f"{nombre} debe heredar de {RAIZ} (BR9.9)")
        anotacion = _anotacion_de_call(clase)
        if nombre == ERROR_SIN_LLAMADA and anotacion is not None:
            problemas.append(f"{nombre} no debe declarar call: no salió ninguna llamada (FD-U10-04)")
        elif nombre != ERROR_SIN_LLAMADA and anotacion != "ModelCall":
            problemas.append(f"{nombre} debe declarar call: ModelCall (FD-U10-04)")
    return problemas


def comprobar_fuente(fuente: str) -> list[str]:
    """Todas las comprobaciones sobre el texto de `model_calls.py`."""
    arbol = ast.parse(fuente)
    clases = {nodo.name: nodo for nodo in arbol.body if isinstance(nodo, ast.ClassDef)}
    problemas = _importaciones_ajenas(arbol)
    if PUERTA in clases:
        problemas.extend(_comprobar_puerta(clases[PUERTA]))
    else:
        problemas.append(f"falta la clase {PUERTA} (BR9.9)")
    problemas.extend(_comprobar_errores(clases))
    return problemas


def comprobar(ruta: Path) -> list[str]:
    """Las comprobaciones sobre el archivo `model_calls.py` de `ruta`."""
    return comprobar_fuente(ruta.read_text(encoding="utf-8"))
