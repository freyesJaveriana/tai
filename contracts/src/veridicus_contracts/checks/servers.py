"""Soberanía de datos: `servers` internos en todo contrato (NFR1.1, §4.9 de NFR Design).

Módulo guardia (100 % de ramas). Recorre `servers[].url` y cada `variables.*.default` de los
OpenAPI (C1, C16, C21 y la ruta interna de voz) y el `host` de cada servidor de los AsyncAPI
(C2, C3 y C5). Acepta solo:

- una ruta relativa (`/api/v1`), que no empieza por `//`;
- el nombre corto `http://veridicus-<nombre>:<puerto>` (NFR-U1-06);
- un *host* que termina en `.svc.cluster.local`, con puerto opcional.

Siempre con el esquema `http`: dentro del clúster no hay `https` y cualquier otro destino (un
nombre de internet, una IP literal, un nombre sin el prefijo `veridicus-`) es externo. Todas las
funciones reciben rutas o documentos y devuelven la lista de problemas (vacía si todo está bien);
nunca escriben.
"""

import re
from pathlib import Path
from typing import Any

from veridicus_contracts.loaders import LoadError, load_file

PREFIJO = "veridicus-"
SUFIJO_DEL_CLUSTER = ".svc.cluster.local"
ETIQUETA = "[a-z0-9-]+"
PUERTO = "[0-9]{1,5}"
# `fullmatch` y no `match` con `$`: un salto de línea final no puede colarse.
NOMBRE_CORTO = re.compile(rf"http://{re.escape(PREFIJO)}{ETIQUETA}:{PUERTO}(/.*)?")
DENTRO_DEL_CLUSTER = re.compile(
    rf"http://{ETIQUETA}(\.{ETIQUETA})*{re.escape(SUFIJO_DEL_CLUSTER)}(:{PUERTO})?(/.*)?"
)
# Contratos con `servers` (§4.9). C14 y C22 no se copian a `contracts/`.
CONTRATOS = (
    "api/console.v2.yaml",
    "health/health.v2.yaml",
    "api/anonymizer-proxy.v1.yaml",
    "api/speech-internal.v1.yaml",
    "queues/runs.v2.yaml",
    "queues/results.v2.yaml",
    "queues/speech.v2.yaml",
)
REGLA = "NFR1.1, §4.9"


def es_interna(url: str) -> bool:
    """La dirección es una ruta relativa, un nombre corto `veridicus-*` o `*.svc.cluster.local`."""
    if url.startswith("/"):
        return not url.startswith("//")
    return (
        NOMBRE_CORTO.fullmatch(url) is not None or DENTRO_DEL_CLUSTER.fullmatch(url) is not None
    )


def _texto(valor: Any) -> str:
    return "" if valor is None else str(valor)


def _de_openapi(servidores: list[Any]) -> list[str]:
    direcciones: list[str] = []
    for servidor in servidores:
        if not isinstance(servidor, dict):
            direcciones.append("")
            continue
        direcciones.append(_texto(servidor.get("url")))
        variables = servidor.get("variables")
        if isinstance(variables, dict):
            for variable in variables.values():
                por_omision = variable.get("default") if isinstance(variable, dict) else None
                direcciones.append(_texto(por_omision))
    return direcciones


def _de_asyncapi(servidores: dict[str, Any]) -> list[str]:
    return [
        "http://" + (_texto(s.get("host")) if isinstance(s, dict) else "")
        for s in servidores.values()
    ]


def direcciones(documento: Any) -> list[str]:
    """Las direcciones que declara un contrato: `url` y valores por omisión, o `host` con `http://`."""
    servidores = documento.get("servers") if isinstance(documento, dict) else None
    if isinstance(servidores, list):  # OpenAPI 3.1: lista con `url` y `variables`
        return _de_openapi(servidores)
    if isinstance(servidores, dict):  # AsyncAPI 3.0: mapa nombre -> servidor
        return _de_asyncapi(servidores)
    return []


def comprobar_documento(nombre: str, documento: Any) -> list[str]:
    """Problemas de un contrato ya cargado: sin servidores, o con alguno que no es interno."""
    declaradas = direcciones(documento)
    if not declaradas:
        return [f"{nombre}: no declara ningún servidor en servers ({REGLA})"]
    return [
        f"{nombre}: dirección no interna: {direccion} ({REGLA})"
        for direccion in declaradas
        if not es_interna(direccion)
    ]


def comprobar(contracts_root: Path, contratos: tuple[str, ...] = CONTRATOS) -> list[str]:
    """Todos los contratos de `contratos` bajo `contracts_root`; uno ausente es un problema."""
    problemas: list[str] = []
    for relativa in contratos:
        ruta = contracts_root / relativa
        if not ruta.is_file():
            problemas.append(f"{relativa}: contrato ausente ({REGLA})")
            continue
        try:
            documento = load_file(ruta)
        except LoadError as error:
            problemas.append(f"{relativa}: contrato ilegible: {error}")
            continue
        problemas.extend(comprobar_documento(relativa, documento))
    return problemas
