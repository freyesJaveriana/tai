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


def desescapar(segmento: str) -> str:
    """Un segmento de puntero JSON como nombre (RFC 6901), el inverso de `escapar`."""
    return segmento.replace("~1", "/").replace("~0", "~")


def resolver(raiz: Any, nodo: Any) -> Any:
    """Sigue las referencias locales `#/...` de `nodo`; deja intacta cualquier otra."""
    for _ in range(PROFUNDIDAD_MAXIMA_DE_REFERENCIAS):
        referencia = nodo.get("$ref") if isinstance(nodo, dict) else None
        if not (isinstance(referencia, str) and referencia.startswith("#/")):
            return nodo
        destino = raiz
        for parte in referencia[2:].split("/"):
            clave = desescapar(parte)
            destino = destino.get(clave) if isinstance(destino, dict) else None
        if not isinstance(destino, dict):
            return nodo
        nodo = destino
    return nodo


RESPUESTA_PROBLEM = "#/components/responses/Problem"
ESQUEMA_PROBLEM = "#/components/schemas/Problem"
# Papel de un subesquema respecto de su padre (`hijas`).
PROPIEDAD = "propiedad"  # `properties`
DEFINICION = "definicion"  # `$defs`
VALOR = "valor"  # `items`, `prefixItems`, `patternProperties`, `additionalProperties` (esquema)
REFINA = "refina"  # `allOf`, `if`, `then`, `else`: condiciones sobre el mismo objeto
RAMA = "rama"  # `anyOf`, `oneOf`: alternativas que no refinan al padre
_MAPAS = (("properties", PROPIEDAD), ("$defs", DEFINICION), ("patternProperties", VALOR))
_UNO = (
    ("items", VALOR),
    ("additionalProperties", VALOR),
    ("if", REFINA),
    ("then", REFINA),
    ("else", REFINA),
)
_LISTAS = (
    ("prefixItems", VALOR),
    ("allOf", REFINA),
    ("anyOf", RAMA),
    ("oneOf", RAMA),
)


def es_problem(respuesta: Any) -> bool:
    """¿La respuesta de error cumple §4.7 (d)? (P-T15-3).

    Cumple con el `$ref` a `#/components/responses/Problem`. Una respuesta en línea solo cumple si
    es `application/problem+json`, su esquema es el `$ref` a `#/components/schemas/Problem` y
    declara cabeceras propias (`Retry-After`), que es lo que impide usar el `$ref` a la respuesta.
    """
    respuesta = objeto(respuesta)
    if respuesta.get("$ref") == RESPUESTA_PROBLEM:
        return True
    contenido = objeto(objeto(respuesta.get("content")).get("application/problem+json"))
    esquema = objeto(contenido.get("schema"))
    return esquema.get("$ref") == ESQUEMA_PROBLEM and bool(objeto(respuesta.get("headers")))


def es_tipo(esquema: dict[str, Any], tipo: str) -> bool:
    """`type` es `tipo` o una lista que lo incluye (`[string, 'null']`)."""
    declarado = esquema.get("type")
    return declarado == tipo or (isinstance(declarado, list) and tipo in declarado)


def hijas(esquema: dict[str, Any], puntero: str) -> Iterator[tuple[Any, str, str]]:
    """Los subesquemas de `esquema`: (subesquema, puntero, papel respecto de su padre).

    Baja por `properties`, `$defs`, `patternProperties`, `items`, `prefixItems`, `allOf`, `anyOf`,
    `oneOf`, `if`, `then`, `else` y por `additionalProperties` cuando es un esquema (no un booleano).
    Lo que no es un objeto o una lista donde debe serlo se ignora.
    """
    for clave, papel in _MAPAS:
        for nombre, hija in objeto(esquema.get(clave)).items():
            yield hija, f"{puntero}/{clave}/{escapar(nombre)}", papel
    for clave, papel in _UNO:
        if isinstance(esquema.get(clave), dict):
            yield esquema[clave], f"{puntero}/{clave}", papel
    for clave, papel in _LISTAS:
        lista = esquema.get(clave)
        for indice, hija in enumerate(lista if isinstance(lista, list) else []):
            yield hija, f"{puntero}/{clave}/{indice}", papel


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
