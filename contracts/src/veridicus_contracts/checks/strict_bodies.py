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

Un objeto es un esquema con `type: object` (o una lista de tipos que lo incluye) o con
`properties`. Se baja por todo subesquema (`_openapi.hijas`): `properties`, `$defs`,
`patternProperties`, `items`, `prefixItems`, `additionalProperties` cuando es un esquema, `allOf`,
`anyOf`, `oneOf`, `if`, `then` y `else`. Las referencias locales se siguen y las de otro contrato
se dejan a la guardia de ese contrato.

Un objeto está cerrado con `additionalProperties: false`, con `unevaluatedProperties: false` o, solo
si los valores también son un esquema que la guardia revisa, con `propertyNames.enum` (P-T15-1). Una
rama de `allOf`, `if`, `then` o `else` que solo trae `properties` refina al objeto padre únicamente
si el padre está cerrado y declara cada propiedad de la rama; en cualquier otro caso es un objeto
abierto. En `anyOf` y `oneOf` no hay refinamiento: cada rama es un objeto (P-T15-2). Los objetos
abiertos que un contrato admite a propósito están en `ABIERTOS_ADMITIDOS`, cada uno con su motivo
(E-13). Los mensajes dicen dónde falla y qué regla, nunca copian un valor del contrato.
"""

from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from veridicus_contracts.checks._openapi import (
    REFINA,
    cargar,
    cuerpos,
    es_tipo,
    escapar,
    hijas,
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
C21 = "api/anonymizer-proxy.v1.yaml"
# E-13: los únicos objetos abiertos admitidos, por (contrato, sitio en la operación). C21 lleva en
# `schema` el esquema de salida que pide el llamador y en `content` la salida del modelo; ninguno
# de los dos tiene forma propia que cerrar. Cada entrada nueva se justifica en el PR.
ABIERTOS_ADMITIDOS = {
    (C21, "POST /v1/generate /requestBody/application/json/properties/schema"): (
        "es el esquema de salida del llamador (JSON Schema): su forma la fija cada análisis"
    ),
    (C21, "POST /v1/generate /responses/200/application/json/properties/content"): (
        "es la salida del modelo, validada después contra el esquema de salida del llamador"
    ),
}

Nodo = tuple[dict[str, Any], str, bool]
SIN_PADRE: Mapping[str, Any] = MappingProxyType({})


def ids_de(documentos: Iterable[Any]) -> dict[str, Any]:
    """Los esquemas que declaran `$id`, por ese `$id` sin la barra inicial.

    Sirve para resolver una `$ref` a otro contrato (`/veridicus/contracts/...`) que es la rama
    hermana de un refinamiento (P-T15-5).
    """
    return {
        str(documento["$id"]).lstrip("/"): documento
        for documento in documentos
        if isinstance(documento, dict) and "$id" in documento
    }


def _hermanas(
    raiz: Any, contenedor: Mapping[str, Any], rama: Any, externos: Mapping[str, Any]
) -> Iterator[Mapping[str, Any]]:
    """Las demás ramas del `allOf` de `contenedor`, con su `$ref` local o por `$id` resuelto."""
    for hermana in contenedor.get("allOf", []):
        resuelta = resolver(raiz, hermana)
        referencia = objeto(resuelta).get("$ref")
        if isinstance(referencia, str):
            resuelta = externos.get(referencia.lstrip("/"), resuelta)
        if isinstance(resuelta, dict) and resuelta is not rama:
            yield resuelta


def _recorrer(
    raiz: Any,
    esquema: Any,
    puntero: str,
    vistos: set[int],
    externos: Mapping[str, Any],
    anfitrion: Mapping[str, Any] = SIN_PADRE,
    papel: str = "",
    contenedor: Mapping[str, Any] = SIN_PADRE,
) -> Iterator[Nodo]:
    """Cada esquema alcanzable, resuelto, con su puntero; una vez por esquema.

    El tercer valor dice si el esquema es un refinamiento válido del objeto al que se aplica, su
    anfitrión (P-T15-2). Las ramas de `allOf`, `if`, `then` y `else` se aplican al mismo objeto
    que su padre: si el padre es a su vez una de ellas, el anfitrión es el del padre. Si la rama
    es de un `allOf`, `contenedor` es el esquema que lo declara y sus otras ramas pueden cerrar el
    objeto (P-T15-5).
    """
    esquema = resolver(raiz, esquema)
    if not isinstance(esquema, dict) or id(esquema) in vistos:
        return
    vistos.add(id(esquema))
    hermanas = _hermanas(raiz, contenedor, esquema, externos)
    yield esquema, puntero, papel == REFINA and _refina(esquema, anfitrion, hermanas)
    propio = anfitrion if papel == REFINA else esquema
    for hija, sitio, papel_de_hija in hijas(esquema, puntero):
        de_allof = esquema if sitio.startswith(f"{puntero}/allOf/") else SIN_PADRE
        yield from _recorrer(raiz, hija, sitio, vistos, externos, propio, papel_de_hija, de_allof)


def _refina(
    rama: Mapping[str, Any], anfitrion: Mapping[str, Any], hermanas: Iterable[Mapping[str, Any]]
) -> bool:
    """Una rama sin `type` con `properties` refina al objeto cerrado que las declara todas.

    Ese objeto es el anfitrión o, dentro de un `allOf`, una rama hermana (P-T15-2, P-T15-5).
    """
    if "type" in rama or "properties" not in rama:
        return False
    propias = objeto(rama["properties"])
    return any(
        _esta_cerrado(candidato)
        and all(nombre in objeto(candidato.get("properties")) for nombre in propias)
        for candidato in (anfitrion, *hermanas)
    )


def _esta_cerrado(nodo: Mapping[str, Any]) -> bool:
    """`additionalProperties` o `unevaluatedProperties` en `false`, o claves cerradas por un `enum`.

    Con `propertyNames.enum` los valores deben ser un esquema no vacío (P-T15-1); `_recorrer` baja
    a revisarlo.
    """
    valores = nodo.get("additionalProperties")
    return (
        valores is False
        or nodo.get("unevaluatedProperties") is False
        or ("enum" in objeto(nodo.get("propertyNames")) and isinstance(valores, dict) and bool(valores))
    )


def _objetos_abiertos(
    raiz: Any, esquema: Any, externos: Mapping[str, Any] = SIN_PADRE
) -> Iterator[str]:
    """Los punteros de los objetos que no están cerrados.

    Un objeto es un esquema con `type: object` o con `properties`; una rama de `allOf`, `if`,
    `then` o `else` que solo trae `properties` refina al objeto padre y no declara uno nuevo solo
    en las condiciones de `_refina`. `externos` resuelve, por `$id`, las ramas hermanas de otro
    contrato (`ids_de`).
    """
    for nodo, puntero, refina in _recorrer(raiz, esquema, "", set(), externos):
        es_objeto = es_tipo(nodo, "object") or "properties" in nodo
        if es_objeto and not refina and not _esta_cerrado(nodo):
            yield puntero


def _parte_sin_acotar(parte: dict[str, Any]) -> bool:
    es_texto = es_tipo(parte, "string") and parte.get("format") != "binary"
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


def comprobar_esquema(
    nombre: str, documento: Any, externos: Mapping[str, Any] = SIN_PADRE
) -> list[str]:
    """Un contrato que es un esquema JSON: todos sus objetos son cerrados.

    `externos` son los demás contratos por `$id` (`ids_de`): una rama de refinamiento puede cerrarse
    con una hermana de otro contrato (P-T15-5).
    """
    return [
        f"{nombre}: {puntero or '/'}: objeto sin additionalProperties: false ({REGLA})"
        for puntero in _objetos_abiertos(documento, documento, externos)
    ]


def comprobar_openapi_interno(nombre: str, documento: Any) -> list[str]:
    """C21 o la ruta de voz: todos los objetos de la petición y de las respuestas son cerrados."""
    problemas: list[str] = []
    for ruta, metodo, operacion in operaciones(documento):
        operacion_en_texto = f"{metodo.upper()} {ruta}"
        sitios: list[tuple[str, Any]] = [
            (f"/requestBody/{medio}", esquema) for medio, _, esquema in cuerpos(documento, operacion)
        ]
        for estado, respuesta in objeto(operacion.get("responses")).items():
            for medio, contenido in objeto(objeto(respuesta).get("content")).items():
                sitios.append((f"/responses/{estado}/{medio}", objeto(contenido).get("schema")))
        for lugar, esquema in sitios:
            problemas.extend(
                f"{nombre}: {operacion_en_texto} {lugar}{p}: objeto sin additionalProperties: "
                f"false ({REGLA})"
                for p in _objetos_abiertos(documento, esquema)
                if (nombre, f"{operacion_en_texto} {lugar}{p}") not in ABIERTOS_ADMITIDOS
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
        if es_tipo(propiedad, "string") and not any(c in propiedad for c in TEXTO_LIBRE):
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
    externos = ids_de(cargados[relativa] for relativa in ESQUEMAS_ESTRICTOS)
    for relativa in ESQUEMAS_ESTRICTOS:
        problemas.extend(comprobar_esquema(relativa, cargados[relativa], externos))
    for relativa in OPENAPI_INTERNOS:
        problemas.extend(comprobar_openapi_interno(relativa, cargados[relativa]))
    problemas.extend(comprobar_c1(cargados[CONSOLA]))
    for relativa, mensaje in FALLIDOS.items():
        problemas.extend(comprobar_fallidos(relativa, cargados[relativa], mensaje))
    return problemas
