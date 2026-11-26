"""Validación de un perfil de ejecución (BR2.1 a BR2.3, BR2.5, BR2.11, NFRD-U11-03).

Los mensajes nombran el perfil, el papel y el ajuste, y nunca un valor: la variable de una clave
(`api_key_ref`) es un nombre y se puede citar, su contenido no se lee más que para saber si existe.
"""

import ipaddress
import re
import socket
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from veridicus_contracts import limits, profiles
from veridicus_errors import ConfigInvalidLimitError, ConfigInvalidProfileError

from veridicus_execution_profiles.floors import COMMERCIAL_MIN_CALL_TIMEOUT_S

KEY_PREFIX = "VERIDICUS_"
SAME_FAMILY = "same_family"

_SAFE_NAME = re.compile(r"[A-Za-z0-9_.\-]{1,64}")
# Direcciones de la máquina y de redes privadas: RFC 1918 y fc00::/7 (BR2.3). Los nombres de
# servicio del clúster no llevan punto final de dominio público.
_PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
)
_CLUSTER_SUFFIXES = (".svc", ".svc.cluster.local")
# Un nombre sin punto es una etiqueta DNS que empieza por letra: nunca un número que el sistema lea
# como dirección.
_DNS_LABEL = re.compile(r"[a-z]([a-z0-9-]{0,61}[a-z0-9])?", re.IGNORECASE | re.ASCII)


def _safe(name: str) -> str:
    return name if _SAFE_NAME.fullmatch(name) else "?"


def _problem(profile: str, role: str, setting: str, reason: str) -> str:
    return f"perfil {_safe(profile)}, papel {role}, ajuste {setting}: {reason}"


def _numeric_ipv4(host: str) -> ipaddress.IPv4Address | None:
    """La dirección que el sistema lee en `host` con `inet_aton`, o `None` si no es numérico.

    `inet_aton` acepta formas que `ipaddress` no reconoce y que el sistema resuelve sin DNS:
    decimal entero (`134744072`), hexadecimal (`0x8080808`), octal (`010.8.8.8`) y abreviadas.
    """
    try:
        return ipaddress.IPv4Address(socket.inet_aton(host))
    except (OSError, ValueError):
        return None


def _is_internal_host(host: str | None) -> bool:
    """El destino es de la máquina o del clúster: loopback, red privada o servicio sin dominio."""
    if not host:
        return False
    address: ipaddress.IPv4Address | ipaddress.IPv6Address | None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = _numeric_ipv4(host)
    if address is None:
        # Un nombre: una etiqueta DNS que empieza por letra, o un servicio del clúster.
        return bool(_DNS_LABEL.fullmatch(host)) or host.endswith(_CLUSTER_SUFFIXES)
    return address.is_loopback or any(address in network for network in _PRIVATE_NETWORKS)


def _base_url_problem(name: str, role: str, destination: Mapping[str, Any]) -> list[str]:
    """BR2.3: un destino externo no lleva `base_url`; uno local solo una interna."""
    if "base_url" not in destination:
        return []
    if destination["scope"] == "external":
        return [_problem(name, role, "base_url", "un destino externo no admite base_url")]
    try:
        host = urlsplit(destination["base_url"]).hostname
    except ValueError:
        host = None
    if not _is_internal_host(host):
        return [_problem(name, role, "base_url", "un destino local solo admite un destino interno")]
    return []


def _key_problem(
    name: str, role: str, destination: Mapping[str, Any], env: Mapping[str, str]
) -> list[str]:
    """BR2.2: la variable de `api_key_ref` de un destino externo existe y no está vacía."""
    if destination["scope"] != "external":
        return []
    variable = destination.get("api_key_ref")
    if variable is None:
        return [_problem(name, role, "api_key_ref", "un destino externo necesita api_key_ref")]
    if not env.get(variable, "").strip():
        return [_problem(name, role, "api_key_ref", f"falta la variable de entorno {variable}")]
    return []


def _family_problems(
    name: str, profile: Mapping[str, Any], destinations: list[tuple[str, Mapping[str, Any]]]
) -> tuple[list[str], bool]:
    """BR2.5: los problemas de familia y si el perfil válido lleva el aviso `same_family`."""
    families = [
        destination["family"].casefold()
        for _, destination in destinations
        if "family" in destination
    ]
    shared = len(families) != len(set(families))
    declared = bool(profile.get("same_family_declared", False))
    demonstration = profile["purpose"] == "demonstration"
    problems: list[str] = []
    if declared and not demonstration:
        problems.append(
            _problem(name, "-", "same_family_declared", "solo un perfil de demostración lo declara")
        )
    if shared and not demonstration:
        problems.append(
            _problem(
                name, "-", "family", "un perfil de evaluación o producción exige familias distintas"
            )
        )
    elif shared and not declared:
        problems.append(
            _problem(
                name, "-", "same_family_declared", "dos papeles de la misma familia sin declararlo"
            )
        )
    return problems, shared and demonstration and declared


def _floor_problem(name: str, env: Mapping[str, str]) -> list[str]:
    """NFRD-U11-03: con un papel externo, `model_call_timeout_s` no baja de 270 s."""
    try:
        timeout = limits.load(env)["model_call_timeout_s"]
    except limits.LimitsConfigError as error:
        raise ConfigInvalidLimitError(str(error)) from error
    if timeout < COMMERCIAL_MIN_CALL_TIMEOUT_S:
        return [
            _problem(
                name,
                "-",
                "model_call_timeout_s",
                f"con un papel externo no puede bajar de {COMMERCIAL_MIN_CALL_TIMEOUT_S} s",
            )
        ]
    return []


def validate_profile(
    document: Mapping[str, Any], name: str, env: Mapping[str, str]
) -> tuple[str, ...]:
    """Valida el perfil `name` del archivo `document` y devuelve sus avisos (por ejemplo `same_family`).

    `document` es el archivo ya cargado (`schema_version` y `profiles`). Valida con
    `profiles.validate(..., key_prefix="VERIDICUS_", kind="analyzer")` de U1 y con las reglas de
    BR2: misma familia solo con `purpose: demonstration` y `same_family_declared` (BR2.5) y la
    variable de `api_key_ref` presente en `env` (BR2.2). Lanza `ConfigInvalidProfileError`
    (`config.invalid_profile`) con el perfil, el papel y el ajuste que fallan, nunca un valor.
    """
    try:
        validated = profiles.validate(document, key_prefix=KEY_PREFIX, kind="analyzer")
    except profiles.ProfileValidationError as error:
        raise ConfigInvalidProfileError(str(error)) from error
    if name not in validated:
        raise ConfigInvalidProfileError(f"perfil {_safe(name)}: no está en el archivo de perfiles")
    profile = validated[name]
    destinations: list[tuple[str, Mapping[str, Any]]] = list(profile["roles"].items())
    if "fallback_provider" in profile:
        destinations.append(("fallback_provider", profile["fallback_provider"]))
    problems: list[str] = []
    for role, destination in destinations:
        problems.extend(_base_url_problem(name, role, destination))
        problems.extend(_key_problem(name, role, destination, env))
    family_problems, warn = _family_problems(name, profile, destinations)
    problems.extend(family_problems)
    if any(destination["scope"] == "external" for _, destination in destinations):
        problems.extend(_floor_problem(name, env))
    if problems:
        raise ConfigInvalidProfileError("perfil no válido: " + "; ".join(problems))
    return (SAME_FAMILY,) if warn else ()
