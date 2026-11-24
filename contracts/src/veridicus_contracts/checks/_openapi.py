"""Ayudas comunes de las guardias de C1, C21 y la ruta interna de voz (paso 16).

Solo lectura: recorren el documento ya cargado y devuelven datos; nunca escriben. Las referencias
que resuelve son las locales (`#/...`); una referencia por `$id` a otro contrato se deja tal cual,
porque ese contrato tiene su propia guardia.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from veridicus_contracts.loaders import LoadError, load_file

METODOS = ("get", "put", "post", "delete", "patch")
PROFUNDIDAD_MAXIMA_DE_REFERENCIAS = 16


def objeto(valor: Any) -> dict[str, Any]:
    """El valor si es un objeto; si no, un objeto vacío (un documento mal formado no revienta)."""
    return valor if isinstance(valor, dict) else {}


def escapar(clave: Any) -> str:
    """Una clave como segmento de puntero JSON (RFC 6901)."""
    return str(clave).replace("~", "~0").replace("/", "~1")


def resolver(raiz: Any, nodo: Any) -> Any:
    """Sigue las referencias locales `#/...` de `nodo`; deja intacta cualquier otra."""
    for _ in range(PROFUNDIDAD_MAXIMA_DE_REFERENCIAS):
        referencia = nodo.get("$ref") if isinstance(nodo, dict) else None
        if not (isinstance(referencia, str) and referencia.startswith("#/")):
            return nodo
        destino = raiz
        for parte in referencia[2:].split("/"):
            clave = parte.replace("~1", "/").replace("~0", "~")
            destino = destino.get(clave) if isinstance(destino, dict) else None
        if not isinstance(destino, dict):
            return nodo
        nodo = destino
    return nodo


RESPUESTA_PROBLEM = "#/components/responses/Problem"
ESQUEMA_PROBLEM = "#/components/schemas/Problem"


def es_problem(respuesta: Any) -> bool:
    """`$ref` a la respuesta `Problem`, o `application/problem+json` con el esquema `Problem`."""
    contenido = objeto(objeto(respuesta).get("content"))
    esquema = objeto(objeto(contenido.get("application/problem+json")).get("schema"))
    return objeto(respuesta).get("$ref") == RESPUESTA_PROBLEM or (
        esquema.get("$ref") == ESQUEMA_PROBLEM
    )


def operaciones(documento: Any) -> Iterator[tuple[str, str, dict[str, Any]]]:
    """Cada operación de `paths`: (ruta, método en minúsculas, objeto de la operación)."""
    for ruta, elemento in objeto(objeto(documento).get("paths")).items():
        for metodo in METODOS:
            operacion = objeto(elemento).get(metodo)
            if isinstance(operacion, dict):
                yield ruta, metodo, operacion


def cuerpos(raiz: Any, operacion: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any], Any]]:
    """Los cuerpos de la petición: (tipo de medio, objeto del `requestBody`, esquema)."""
    cuerpo = objeto(resolver(raiz, operacion.get("requestBody")))
    for medio, contenido in objeto(cuerpo.get("content")).items():
        yield medio, cuerpo, objeto(contenido).get("schema")


def cargar(contracts_root: Path, relativa: str, regla: str) -> tuple[Any, list[str]]:
    """Lee un contrato de `contracts/`; si falta o no se lee, devuelve el problema y ningún documento."""
    ruta = contracts_root / relativa
    if not ruta.is_file():
        return None, [f"{relativa}: contrato ausente ({regla})"]
    try:
        return load_file(ruta), []
    except LoadError:
        return None, [f"{relativa}: contrato ilegible, no se pudo interpretar ({regla})"]
