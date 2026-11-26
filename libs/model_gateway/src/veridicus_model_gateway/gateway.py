"""Armado del gateway por perfil (BR10.1, NFRD-U11-03, AUTONOMIA-04).

`build` falla antes de cualquier llamada, con `GatewayConfigError`:

- un papel (o el alterno) con `scope: local` en B11a, porque el adaptador local se difiere a B11b;
- un destino externo sin el `AnonymizingProvider` inyectado: el servicio no arranca sin el
  anonimizador delante;
- un plazo de llamada menor que el piso de 270 s con un destino externo
  (`veridicus_execution_profiles.floors`; el cargador ya lo rechaza, y el gateway lo repite como
  defensa en profundidad porque es la última puerta antes de salir).

`RecordingGateway` registra cada `ModelCall` en orden y mide la latencia de cada llamada en
memoria, fuera de C6 (NFRD-U11-07): solo los agregados llegan a C19.
"""

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from veridicus_contracts.model_calls import (
    AnonymizingProvider,
    GenerateRequest,
    GenerateResult,
    ModelCall,
    ModelCallError,
)
from veridicus_errors import GatewayConfigError
from veridicus_execution_profiles.floors import COMMERCIAL_MIN_CALL_TIMEOUT_S
from veridicus_execution_profiles.loader import EffectiveConfig

from veridicus_model_gateway.adapters.anonymizing import AnonymizingAdapter
from veridicus_model_gateway.port import ModelGateway


@dataclass(frozen=True)
class CallRecord:
    """Una llamada registrada con lo que tardó (segundos, en memoria)."""

    call: ModelCall
    latency_s: float


class RecordingGateway:
    """Envuelve el adaptador, rechaza todo destino que no sea externo y registra cada llamada."""

    def __init__(self, adapter: ModelGateway, clock: Callable[[], float] = time.monotonic) -> None:
        self._adapter = adapter
        self._clock = clock
        self._records: list[CallRecord] = []

    @property
    def records(self) -> tuple[CallRecord, ...]:
        return tuple(self._records)

    @property
    def calls(self) -> tuple[ModelCall, ...]:
        return tuple(record.call for record in self._records)

    def generate(self, request: GenerateRequest) -> GenerateResult:
        if request.destination.scope != "external":
            raise GatewayConfigError(
                "el gateway de B11a solo atiende destinos externos: el adaptador local "
                "se difiere a B11b"
            )
        started = self._clock()
        try:
            result = self._adapter.generate(request)
        except ModelCallError as error:
            self._record(getattr(error, "call", None), started)
            raise
        self._record(result.call, started)
        return result

    def _record(self, call: ModelCall | None, started: float) -> None:
        # AnonymizerUnavailable no trae registro: no sale ninguna llamada y no suma una fila (BR8.3).
        if call is not None:
            self._records.append(CallRecord(call, self._clock() - started))


def _destinations(config: EffectiveConfig) -> list[Mapping[str, Any]]:
    """Los destinos del perfil: cada papel y, si lo hay, el alterno."""
    profile = config.profile
    destinations: list[Mapping[str, Any]] = list(profile["roles"].values())
    if "fallback_provider" in profile:
        destinations.append(profile["fallback_provider"])
    return destinations


def build(
    config: EffectiveConfig, anonymizing_provider: AnonymizingProvider | None = None
) -> RecordingGateway:
    """Arma el gateway de `config` antes de cualquier llamada.

    Un papel `scope: external` exige el `anonymizing_provider` inyectado y el piso de
    `model_call_timeout_s` (`floors.COMMERCIAL_MIN_CALL_TIMEOUT_S`); si falta alguno, lanza
    `GatewayConfigError`. Un papel `scope: local` también lo lanza en B11a (adaptador diferido).
    """
    for destination in _destinations(config):
        if destination["scope"] != "external":
            raise GatewayConfigError(
                "un papel local no se puede armar en B11a: el adaptador local se difiere a B11b"
            )
    if anonymizing_provider is None:
        raise GatewayConfigError(
            "un destino externo exige el anonimizador inyectado: el gateway no arranca sin él"
        )
    if config.limits["model_call_timeout_s"] < COMMERCIAL_MIN_CALL_TIMEOUT_S:
        raise GatewayConfigError(
            f"con un destino externo model_call_timeout_s no puede bajar de "
            f"{COMMERCIAL_MIN_CALL_TIMEOUT_S} s"
        )
    return RecordingGateway(AnonymizingAdapter(anonymizing_provider))
