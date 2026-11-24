"""Ninguna operación de C1 escribe configuración (§4.8 de NFR Design, BR7.1, E15).

Módulo guardia (100 % de ramas). Sustituye a `checks/threshold.py`, retirado con el cambio 01 (el
umbral de similitud salió): comprueba que ninguna operación `POST`, `PUT`, `PATCH` o `DELETE` de
`api/console.v2.yaml` nombra perfiles, proveedores, *prompts*, precios ni límites (ni sus formas en
español) en la ruta, en un parámetro (de la ruta o de la operación) o en el cuerpo, bajo todo
subesquema, sin distinguir mayúsculas ni tildes. La
excepción explícita es `profile_name`, que elige un perfil al crear o importar una sesión y no lo
escribe. Las lecturas (`GET`) pueden nombrarlos. Control negativo: E15 (`PUT /profiles`).

Los mensajes nombran la operación, el término y dónde aparece, nunca un valor del contrato.
"""

import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._openapi import (
    DEFINICION,
    PROPIEDAD,
    cargar,
    cuerpos,
    hijas,
    objeto,
    operaciones,
    resolver,
)

CONTRATO = "api/console.v2.yaml"
REGLA = "BR7.1"
METODOS_DE_ESCRITURA = ("post", "put", "patch", "delete")
TERMINOS = (
    "profile",
    "provider",
    "prompt",
    "price",
    "limit",
    "perfil",
    "proveedor",
    "precio",
    "limite",
)
EXCEPCION = "profile_name"


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def _termino(nombre: str) -> str | None:
    """El primer término de configuración que contiene `nombre`, o `None`."""
    if nombre == EXCEPCION:
        return None
    normalizado = _normalizar(nombre)
    return next((t for t in TERMINOS if t in normalizado), None)


def _nombres_del_esquema(raiz: Any, esquema: Any, vistos: set[int]) -> Iterator[str]:
    """Los nombres de propiedad de un esquema, siguiendo las referencias locales y sin repetir."""
    esquema = resolver(raiz, esquema)
    if not isinstance(esquema, dict) or id(esquema) in vistos:
        return
    vistos.add(id(esquema))
    for nombre, hija in objeto(esquema.get("properties")).items():
        yield nombre
        yield from _nombres_del_esquema(raiz, hija, vistos)
    for hija, _, papel in hijas(esquema, ""):
        if papel not in (PROPIEDAD, DEFINICION):  # los `$defs` se alcanzan por su `$ref`
            yield from _nombres_del_esquema(raiz, hija, vistos)


def _parametros(valor: Any) -> list[Any]:
    return valor if isinstance(valor, list) else []


def _de_operacion(
    documento: Any, ruta: str, metodo: str, operacion: dict[str, Any]
) -> Iterator[str]:
    nombre = f"{metodo.upper()} {ruta}"
    sitios: list[tuple[str, str]] = [(ruta, "la ruta")]
    de_la_ruta = objeto(objeto(documento.get("paths")).get(ruta)).get("parameters")
    for parametro in (*_parametros(de_la_ruta), *_parametros(operacion.get("parameters"))):
        resuelto = objeto(resolver(documento, parametro))
        sitios.append((str(resuelto.get("name", "")), "un parámetro"))
    for _, _, esquema in cuerpos(documento, operacion):
        sitios.extend((n, "el cuerpo") for n in _nombres_del_esquema(documento, esquema, set()))
    for texto, donde in sitios:
        termino = _termino(texto)
        if termino is not None:
            yield f"{nombre}: nombra «{termino}» en {donde} ({REGLA})"


def comprobar_documento(documento: Any) -> list[str]:
    """Los problemas de un C1 ya cargado."""
    return [
        problema
        for ruta, metodo, operacion in operaciones(documento)
        if metodo in METODOS_DE_ESCRITURA
        for problema in _de_operacion(documento, ruta, metodo, operacion)
    ]


def comprobar(contracts_root: Path) -> list[str]:
    """Lee `api/console.v2.yaml` bajo `contracts_root` y lo comprueba; si falta, es un problema."""
    documento, problemas = cargar(contracts_root, CONTRATO, REGLA)
    return problemas or comprobar_documento(documento)
