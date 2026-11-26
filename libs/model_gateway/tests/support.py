"""Ayudas de las pruebas del gateway: configuración efectiva sintética y un proveedor espía.

Todo es sintético. La clave es el canario inventado de la unidad: nunca una clave real.
"""

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

from veridicus_contracts.model_calls import (
    Destination,
    GenerateRequest,
    GenerateResult,
    Message,
    ModelCall,
)
from veridicus_execution_profiles.loader import EffectiveConfig, load_config

PROFILE = "demo-anthropic"
KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
KEY_CANARY = "sk-sintetico-canario-7f3a91c2d4e5"
TIMEOUT_REF = "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S"
MODEL = "claude-sonnet-5-5"
# Texto de un testimonio inventado: nunca debe aparecer en un mensaje de error del gateway.
TESTIMONY = "Casilda Roncancio estuvo en Villa Rocamora la noche del suceso"


def make_config(timeout_s: int = 300) -> EffectiveConfig:
    """La configuración efectiva del perfil de demostración con el plazo de llamada dado."""
    return load_config(PROFILE, {KEY_REF: KEY_CANARY, TIMEOUT_REF: str(timeout_s)})


def with_timeout(config: EffectiveConfig, timeout_s: float) -> EffectiveConfig:
    """La misma configuración con otro plazo, sin pasar por el cargador.

    El cargador ya rechaza menos de 270 s con un papel externo (BR2); el gateway repite el piso
    como defensa en profundidad, y esta ayuda llega a él sin pasar por el cargador.
    """
    limits = MappingProxyType({**config.limits, "model_call_timeout_s": timeout_s})
    return replace(config, limits=limits)


def with_profile(config: EffectiveConfig, profile: Mapping[str, Any]) -> EffectiveConfig:
    """La misma configuración con otro perfil (sin pasar por la validación del cargador)."""
    return replace(config, profile=MappingProxyType(copy.deepcopy(dict(profile))))


def _thaw(value: Any) -> Any:
    """Copia mutable de lo que el cargador congeló (`MappingProxyType` y tuplas)."""
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def profile_with(**changes: Any) -> dict[str, Any]:
    """Copia mutable del perfil de demostración con los cambios pedidos."""
    profile: dict[str, Any] = _thaw(make_config().profile)
    profile.update(changes)
    return profile


def local_destination() -> dict[str, Any]:
    return {"provider": "local", "model": "modelo-local-sintetico", "scope": "local"}


def external_destination() -> dict[str, Any]:
    return {
        "provider": "anthropic",
        "model": MODEL,
        "scope": "external",
        "api_key_ref": KEY_REF,
    }


def make_call(role: str = "judge", *, anonymized: bool = True) -> ModelCall:
    return ModelCall(
        role=role,
        provider="anthropic",
        model=MODEL,
        input_tokens=10,
        output_tokens=5,
        fallback_provider=False,
        anonymized=anonymized,
        at=datetime(2026, 11, 26, 12, 0, 0, tzinfo=UTC),
    )


def make_request(role: str = "judge", *, scope: str = "external") -> GenerateRequest:
    provider = "anthropic" if scope == "external" else "local"
    return GenerateRequest(
        role=role,
        destination_slot="primary",
        profile_name=PROFILE,
        profile_sha256="0" * 64,
        destination=Destination(
            provider=provider,  # type: ignore[arg-type]  # motivo: ambos valores son del Literal
            model=MODEL,
            scope=scope,  # type: ignore[arg-type]  # motivo: ambos valores son del Literal
            api_key_ref=KEY_REF,
        ),
        messages=[Message("system", "instrucciones fijas"), Message("user", TESTIMONY)],
        schema={"type": "object"},
        timeout_s=300.0,
    )


def make_result(role: str = "judge") -> GenerateResult:
    return GenerateResult(content={"hallazgos": []}, altered_markers=[], call=make_call(role))


@dataclass
class SpyProvider:
    """Proveedor espía: cuenta las llamadas y devuelve un resultado o lanza lo que se le pida."""

    outcome: GenerateResult | Exception = field(default_factory=make_result)
    requests: list[GenerateRequest] = field(default_factory=list)

    def generate(self, request: GenerateRequest) -> GenerateResult:
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class StepClock:
    """Reloj simulado: cada lectura avanza una décima de segundo."""

    def __init__(self) -> None:
        self._now = 0.0

    def __call__(self) -> float:
        self._now += 0.1
        return self._now
