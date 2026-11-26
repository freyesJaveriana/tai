"""Raíz de composición de la CLI (PD-7): el único módulo del paquete que importa el anonimizador.

Módulo guardia (100 % de ramas). Arma, en el orden de RD (NFR10.15) y deteniéndose en el primer fallo,
lo que la corrida necesita antes de hacer cualquier llamada:

1. los límites de C25, bajados por `VERIDICUS_LIMIT_*` del entorno;
2. el perfil pedido, validado y aprobado, con la referencia versionada del *prompt*;
3. la huella de los bytes del *prompt*, igual a esa referencia;
4. el aviso de VE-01 (`notice.load_notice()`), que se anuncia antes de armar el gateway;
5. el gateway, con el piso de `model_call_timeout_s` si hay un papel externo.

`veridicus_anonymizer` se importa de forma diferida, solo si el perfil tiene un papel externo, y recibe
el entorno completo; `transport` (el `FakeTransport` de las pruebas) solo llega a `build_anonymizer`,
nunca por un argumento de la línea de comandos (PD-12). Un fallo de cualquiera de estos pasos lanza un
error de la familia de configuración (código 3) sin haber hecho ninguna llamada. Ningún `__init__`
reexporta este módulo: una prueba AST lo comprueba y `core-no-anonymizer` lo declara como la única
excepción.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from veridicus_contracts import limits
from veridicus_contracts.model_calls import AnonymizingProvider
from veridicus_errors import ConfigInvalidLimitError, ConfigInvalidProfileError, GatewayConfigError
from veridicus_execution_profiles.loader import EffectiveConfig, load_config
from veridicus_integrity_policy import notice
from veridicus_model_gateway.gateway import build
from veridicus_model_gateway.port import ModelGateway

from veridicus_incoherence_analyzer.application import messages

if TYPE_CHECKING:
    import httpx

# `announce` recibe el aviso de VE-01 y los identificadores de los avisos del perfil.
Announce = Callable[[notice.Notice, tuple[str, ...]], None]


@dataclass(frozen=True)
class Composition:
    """Lo que la CLI necesita para correr: configuración efectiva, gateway y cifras de C25."""

    config: EffectiveConfig
    gateway: ModelGateway
    limits: Mapping[str, float]


def _has_external_destination(config: EffectiveConfig) -> bool:
    destinations = [*config.profile["roles"].values(), config.profile.get("fallback_provider", {})]
    return any(destination.get("scope") == "external" for destination in destinations)


def _anonymizing_provider(
    config: EffectiveConfig, env: Mapping[str, str], transport: "httpx.BaseTransport | None"
) -> AnonymizingProvider | None:
    """El módulo de U10 si el perfil tiene un destino externo; si no, ninguno."""
    if not _has_external_destination(config):
        return None
    try:
        from veridicus_anonymizer.api import build_anonymizer  # importación diferida (PD-7)
    except ImportError as error:
        raise GatewayConfigError(
            "el anonimizador no está instalado: un destino externo no arranca sin él"
        ) from error
    return build_anonymizer(env, transport)


def compose(
    profile_name: str,
    env: Mapping[str, str],
    transport: "httpx.BaseTransport | None",
    *,
    announce: Announce,
) -> Composition:
    """Arma la composición en el orden de RD o lanza el error del primer paso que falle."""
    try:
        figures = limits.load(env)
    except limits.LimitsConfigError as error:
        raise ConfigInvalidLimitError(str(error)) from error
    config = load_config(profile_name, env, prompt_sha256=messages.load_prompt_reference())
    if messages.prompt_sha256() != config.prompt_sha256:
        raise ConfigInvalidProfileError("el prompt no coincide con su referencia versionada")
    announce(notice.load_notice(), config.warnings)
    provider = _anonymizing_provider(config, env, transport)
    gateway = build(config, anonymizing_provider=provider)
    return Composition(config=config, gateway=gateway, limits=figures)
