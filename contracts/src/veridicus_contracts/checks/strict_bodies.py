"""Estrictez de cuerpos, mensajes y archivos (§4.3 de NFR Design; NFR10.1, NFR10.2, NFR10.7).

Módulo guardia (100 % de ramas). Comprueba, sobre los contratos ya cargados:

- los cuerpos de petición de C1: `additionalProperties: false` en cada objeto, y en los
  `multipart/form-data`, además, que cada parte de texto esté acotada (`maxLength`, `pattern`,
  `format`, `enum` o `const`) y que el cuerpo declare `x-veridicus-max-bytes`;
- los contratos estrictos: C6 (copia), C7, C18 (configuración efectiva) y C19 con
  `model-call.v1.yaml` declaran en cada objeto `additionalProperties: false` o
  `unevaluatedProperties: false` (BR1.4); C21 y la ruta interna de voz lo declaran en cada objeto de
  su petición y de sus respuestas;
- las entradas de mensajes fallidos de C2, C3 y C5: esquema estricto y sin campos de texto libre
  (NFRD-U1-07, NFR-U4-07, NFR-U9-03).

Un objeto es un esquema con `type: object` o con `properties`. Se recorren `properties`, `items`,
`prefixItems`, `allOf`, `anyOf`, `oneOf` y `$defs`; las condiciones `if/then/else` no declaran
objetos propios. Las referencias locales se siguen y las de otro contrato se dejan a la guardia de
ese contrato. Los mensajes dicen dónde falla y qué regla, nunca copian un valor del contrato.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._openapi import (
    cargar,
    cuerpos,
    escapar,
    objeto,
    operaciones,
    resolver,
)

REGLA = "§4.3"
REGLA_FALLIDOS = "NFRD-U1-07"
CONSOLA = "api/console.v2.yaml"
# C6 (copia), C7, C18 efectiva y C19 con model-call.v1.yaml.
ESQUEMAS_ESTRICTOS = (
    "analyzer/v1/entrada.schema.json",
    "analyzer/v1/salida.schema.json",
    "integrity/review-suggestion.v2.json",
    "profiles/effective-config.v1.yaml",
    "cli/report.schema.v2.yaml",
    "model_calls/model-call.v1.yaml",
)
# C21 y la ruta interna de voz.
OPENAPI_INTERNOS = ("api/anonymizer-proxy.v1.yaml", "api/speech-internal.v1.yaml")
# Archivo AsyncAPI -> mensaje de la cola de fallidos (C2, C3 y C5).
FALLIDOS = {
    "queues/runs.v2.yaml": "RunFailed",
    "queues/results.v2.yaml": "ResultFailed",
    "queues/speech.v2.yaml": "AudioFailed",
}
ACOTADO = ("maxLength", "pattern", "format", "enum", "const")
TEXTO_LIBRE = ("pattern", "format", "enum", "const")
SIN_ESQUEMAS_HIJOS = ("items",)
LISTAS_DE_ESQUEMAS = ("prefixItems", "allOf", "anyOf", "oneOf")
MAPAS_DE_ESQUEMAS = ("properties", "$defs")


def _hijas(esquema: dict[str, Any], puntero: str) -> Iterator[tuple[Any, str, bool]]:
    """Los subesquemas por los que se baja: (esquema, puntero, ¿refina al objeto padre?)."""
    for clave in MAPAS_DE_ESQUEMAS:
        for nombre, hija in objeto(esquema.get(clave)).items():
            yield hija, f"{puntero}/{clave}/{escapar(nombre)}", False
    for clave in SIN_ESQUEMAS_HIJOS:
        yield esquema.get(clave), f"{puntero}/{clave}", False
    for clave in LISTAS_DE_ESQUEMAS:
        for indice, hija in enumerate(esquema.get(clave, [])):
            yield hija, f"{puntero}/{clave}/{indice}", clave != "prefixItems"


def _recorrer(
    raiz: Any, esquema: Any, puntero: str, vistos: set[int], refina: bool = False
) -> Iterator[tuple[dict[str, Any], str, bool]]:
    """Cada esquema alcanzable, resuelto, con su puntero; una vez por esquema."""
    esquema = resolver(raiz, esquema)
    if not isinstance(esquema, dict) or id(esquema) in vistos:
        return
    vistos.add(id(esquema))
    yield esquema, puntero, refina
    for hija, sitio, refina_a_su_padre in _hijas(esquema, puntero):
        yield from _recorrer(raiz, hija, sitio, vistos, refina_a_su_padre)


def _esta_cerrado(nodo: dict[str, Any]) -> bool:
    """`additionalProperties` o `unevaluatedProperties` en `false`, o claves cerradas por un `enum`."""
    return (
        nodo.get("additionalProperties") is False
        or nodo.get("unevaluatedProperties") is False
        or "enum" in objeto(nodo.get("propertyNames"))
    )


def _objetos_abiertos(raiz: Any, esquema: Any) -> Iterator[str]:
    """Los punteros de los objetos que no están cerrados.

    Un objeto es un esquema con `type: object` o con `properties`; una rama de `allOf`, `anyOf` o
    `oneOf` que solo trae `properties` refina al objeto padre y no declara uno nuevo.
    """
    for nodo, puntero, refina in _recorrer(raiz, esquema, "", set()):
        es_objeto = nodo.get("type") == "object" or ("properties" in nodo and not refina)
        if es_objeto and not _esta_cerrado(nodo):
            yield puntero


def _parte_sin_acotar(parte: dict[str, Any]) -> bool:
    es_texto = parte.get("type") == "string" and parte.get("format") != "binary"
    return es_texto and not any(clave in parte for clave in ACOTADO)


def _del_cuerpo_de_c1(documento: Any, ruta: str, metodo: str, operacion: dict[str, Any]) -> Iterator[str]:
    for medio, cuerpo, esquema in cuerpos(documento, operacion):
        donde = f"{CONSOLA}: {metodo.upper()} {ruta} /requestBody/{medio}"
        for puntero in _objetos_abiertos(documento, esquema):
            yield f"{donde}{puntero}: objeto sin additionalProperties: false ({REGLA})"
        if medio.startswith("multipart/"):
            if "x-veridicus-max-bytes" not in cuerpo:
                yield f"{donde}: sin x-veridicus-max-bytes ({REGLA})"
            for parte, hija in objeto(objeto(resolver(documento, esquema)).get("properties")).items():
                if _parte_sin_acotar(objeto(resolver(documento, hija))):
                    yield f"{donde}/properties/{escapar(parte)}: parte de texto sin acotar ({REGLA})"


def comprobar_c1(documento: Any) -> list[str]:
    """Los cuerpos de petición de un C1 ya cargado."""
    return [
        problema
        for ruta, metodo, operacion in operaciones(documento)
        for problema in _del_cuerpo_de_c1(documento, ruta, metodo, operacion)
    ]


def comprobar_esquema(nombre: str, documento: Any) -> list[str]:
    """Un contrato que es un esquema JSON: todos sus objetos son cerrados."""
    return [
        f"{nombre}: {puntero or '/'}: objeto sin additionalProperties: false ({REGLA})"
        for puntero in _objetos_abiertos(documento, documento)
    ]


def comprobar_openapi_interno(nombre: str, documento: Any) -> list[str]:
    """C21 o la ruta de voz: todos los objetos de la petición y de las respuestas son cerrados."""
    problemas: list[str] = []
    for ruta, metodo, operacion in operaciones(documento):
        donde = f"{nombre}: {metodo.upper()} {ruta}"
        for medio, _, esquema in cuerpos(documento, operacion):
            problemas.extend(
                f"{donde} /requestBody/{medio}{p}: objeto sin additionalProperties: false ({REGLA})"
                for p in _objetos_abiertos(documento, esquema)
            )
        for estado, respuesta in objeto(operacion.get("responses")).items():
            for medio, contenido in objeto(objeto(respuesta).get("content")).items():
                problemas.extend(
                    f"{donde} /responses/{estado}/{medio}{p}: objeto sin additionalProperties: "
                    f"false ({REGLA})"
                    for p in _objetos_abiertos(documento, objeto(contenido).get("schema"))
                )
    return problemas


def comprobar_fallidos(nombre: str, documento: Any, mensaje: str) -> list[str]:
    """La entrada de mensajes fallidos: cerrada y sin campos de texto libre (NFRD-U1-07)."""
    carga = objeto(objeto(objeto(objeto(documento).get("components")).get("messages")).get(mensaje))
    esquema = carga.get("payload")
    if not isinstance(esquema, dict):
        return [f"{nombre}: {mensaje}: mensaje ausente ({REGLA_FALLIDOS})"]
    problemas = [
        f"{nombre}: {mensaje}: objeto sin additionalProperties: false ({REGLA_FALLIDOS})"
        for _ in _objetos_abiertos(documento, esquema)
    ]
    for campo, hija in objeto(esquema.get("properties")).items():
        propiedad = objeto(resolver(documento, hija))
        if propiedad.get("type") == "string" and not any(c in propiedad for c in TEXTO_LIBRE):
            problemas.append(
                f"{nombre}: {mensaje}: {campo} es un campo de texto libre ({REGLA_FALLIDOS})"
            )
    return problemas


def comprobar(contracts_root: Path) -> list[str]:
    """Todos los contratos de esta guardia bajo `contracts_root`; uno ausente es un problema."""
    cargados: dict[str, Any] = {}
    problemas: list[str] = []
    archivos = (*ESQUEMAS_ESTRICTOS, *OPENAPI_INTERNOS, CONSOLA, *FALLIDOS)
    for relativa in archivos:
        documento, faltas = cargar(contracts_root, relativa, REGLA)
        cargados[relativa] = documento
        problemas.extend(faltas)
    if problemas:
        return problemas
    for relativa in ESQUEMAS_ESTRICTOS:
        problemas.extend(comprobar_esquema(relativa, cargados[relativa]))
    for relativa in OPENAPI_INTERNOS:
        problemas.extend(comprobar_openapi_interno(relativa, cargados[relativa]))
    problemas.extend(comprobar_c1(cargados[CONSOLA]))
    for relativa, mensaje in FALLIDOS.items():
        problemas.extend(comprobar_fallidos(relativa, cargados[relativa], mensaje))
    return problemas
