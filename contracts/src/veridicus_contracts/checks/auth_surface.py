"""Superficie de C1: sesión, anti-CSRF, roles y rutas que encolan (§4.6 de NFR Design, NFRD-U1-12).

Módulo guardia (100 % de ramas). Recorre cada operación de `api/console.v2.yaml` y comprueba:

- la seguridad efectiva es `sessionCookie`; solo `POST /auth/login` y `GET /notice` son públicas
  (D-1: el aviso de VE-01 se ve también al iniciar sesión);
- todo `POST` y `PATCH` (salvo el inicio de sesión) lleva el parámetro `X-CSRF-Token` con
  `minLength` de al menos 32;
- toda operación declara `x-veridicus-roles` con valores de `Role`, salvo `/auth/login`,
  `/auth/logout`, `/auth/me` y la lista pública;
- toda operación con seguridad declara `401` y la que declara roles, además `403`, las dos con
  `$ref` a `Problem` (en la respuesta o en el esquema de su cuerpo `application/problem+json`);
- ningún `PUT` ni `DELETE`;
- las operaciones que encolan trabajo de IA (constante `ENCOLAN`, por `operationId`) solo declaran
  `202` como 2xx;
- solo existen las extensiones `x-veridicus-*` de la lista cerrada.

Los mensajes nombran la operación, el puntero y la regla, nunca un valor del contrato. Todas las
funciones devuelven la lista de problemas (vacía si todo está bien); nunca escriben.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._openapi import (
    cargar,
    es_problem,
    escapar,
    objeto,
    operaciones,
    resolver,
)

CONTRATO = "api/console.v2.yaml"
REGLA = "§4.6"
ROLES = ("analista", "admin", "investigador")
# Lista pública: el inicio de sesión (aún no hay sesión) y el aviso de propósito limitado (VE-01),
# que debe verse también antes de iniciar sesión (D-1, FD-U4-08). Una ruta pública nueva es un hallazgo.
PUBLICAS = frozenset({("post", "/auth/login"), ("get", "/notice")})
SIN_ROLES = frozenset({"/auth/login", "/auth/logout", "/auth/me"} | {r for _, r in PUBLICAS})
SIN_CSRF = ("post", "/auth/login")
# Las seis operaciones que publican en C2 o C5 (NFR3.1): solo pueden responder 202.
ENCOLAN = frozenset(
    {
        "create_turn",
        "paste_transcript",
        "launch_final_run",
        "retry_run",
        "set_analysis_paused",
        "create_voice_turn",
    }
)
EXTENSIONES = frozenset(
    {
        "x-veridicus-roles",
        "x-veridicus-owner-only",
        "x-veridicus-owner-only-for-role",
        "x-veridicus-access-log",
        "x-veridicus-demo",
        "x-veridicus-priority",
        "x-veridicus-limit",
        "x-veridicus-max-bytes",
        "x-veridicus-cookie",
    }
)
PARAMETRO_CSRF = "X-CSRF-Token"
LONGITUD_MINIMA_CSRF = 32


def _tiene_csrf(documento: Any, operacion: dict[str, Any]) -> bool:
    for parametro in operacion.get("parameters", []):
        resuelto = objeto(resolver(documento, parametro))
        longitud = objeto(resuelto.get("schema")).get("minLength", 0)
        if (
            resuelto.get("name") == PARAMETRO_CSRF
            and resuelto.get("in") == "header"
            and isinstance(longitud, int)
            and longitud >= LONGITUD_MINIMA_CSRF
        ):
            return True
    return False


def _roles_validos(roles: Any) -> bool:
    return isinstance(roles, list) and bool(roles) and all(rol in ROLES for rol in roles)


def _de_operacion(
    documento: Any, ruta: str, metodo: str, operacion: dict[str, Any]
) -> Iterator[str]:
    nombre = f"{metodo.upper()} {ruta}"
    respuestas = objeto(operacion.get("responses"))
    if metodo in ("put", "delete"):
        yield f"{nombre}: operación que reemplaza o borra ({REGLA})"
    if operacion.get("security", objeto(documento).get("security")):
        if not es_problem(respuestas.get("401")):
            yield f"{nombre}: 401 sin $ref a Problem (NFRD-U1-12)"
    elif (metodo, ruta) not in PUBLICAS:
        yield f"{nombre}: ruta pública fuera de la lista (login y notice; {REGLA}, D-1)"
    if ruta not in SIN_ROLES and not _roles_validos(operacion.get("x-veridicus-roles")):
        yield f"{nombre}: sin x-veridicus-roles con valores de Role (NFRD-U1-12)"
    if "x-veridicus-roles" in operacion and not es_problem(respuestas.get("403")):
        yield f"{nombre}: 403 sin $ref a Problem (NFRD-U1-12)"
    sin_csrf = metodo in ("post", "patch") and (metodo, ruta) != SIN_CSRF
    if sin_csrf and not _tiene_csrf(documento, operacion):
        yield (
            f"{nombre}: escritura sin {PARAMETRO_CSRF} de al menos "
            f"{LONGITUD_MINIMA_CSRF} caracteres ({REGLA})"
        )
    if operacion.get("operationId") in ENCOLAN and any(
        str(estado).startswith("2") and str(estado) != "202" for estado in respuestas
    ):
        yield f"{nombre}: operación que encola con un 2xx distinto de 202 ({REGLA}, NFR3.1)"


def _extensiones_ajenas(nodo: Any, puntero: str = "") -> Iterator[str]:
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            sitio = f"{puntero}/{escapar(clave)}"
            if clave.startswith("x-veridicus-") and clave not in EXTENSIONES:
                yield f"{sitio}: extensión fuera de la lista cerrada ({REGLA})"
            yield from _extensiones_ajenas(valor, sitio)
    elif isinstance(nodo, list):
        for indice, valor in enumerate(nodo):
            yield from _extensiones_ajenas(valor, f"{puntero}/{indice}")


def comprobar_documento(documento: Any) -> list[str]:
    """Los problemas de un C1 ya cargado."""
    problemas: list[str] = []
    identificadores: set[str] = set()
    for ruta, metodo, operacion in operaciones(documento):
        problemas.extend(_de_operacion(documento, ruta, metodo, operacion))
        identificadores.add(str(operacion.get("operationId")))
    problemas.extend(
        f"operación que encola ausente: {faltante} ({REGLA}; sumar una ruta exige actualizar "
        "la constante)"
        for faltante in sorted(ENCOLAN - identificadores)
    )
    problemas.extend(_extensiones_ajenas(documento))
    return problemas


def comprobar(contracts_root: Path) -> list[str]:
    """Lee `api/console.v2.yaml` bajo `contracts_root` y lo comprueba; si falta, es un problema."""
    documento, problemas = cargar(contracts_root, CONTRATO, REGLA)
    return problemas or comprobar_documento(documento)
