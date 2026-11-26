"""API de la biblioteca (C17): `analyze` y `IncoherenceAnalyzer` (PD-4).

Estado: *stubs* del paso 1 (U11-T01). Los implementa U11-T04.

`Entrada` y `Salida` no se agregan a `veridicus_contracts.analyzer.v1` (PD-4): son los diccionarios
de C6, que `analyze` valida con `validate_instance`.
"""

from collections.abc import Callable
from typing import Any

from veridicus_execution_profiles.loader import EffectiveConfig
from veridicus_model_gateway.port import ModelGateway

Entrada = dict[str, Any]
Salida = dict[str, Any]
CancelCheck = Callable[[], bool]


def analyze(
    entrada: Entrada,
    config: EffectiveConfig,
    gateway: ModelGateway,
    cancelled: CancelCheck | None = None,
) -> Salida:
    """Analiza una transcripción y devuelve la salida C6, con hallazgos de dos citas verificadas o
    con `estado: error` y hallazgos vacíos (AUTONOMIA-05).

    Lanza una de las clases de `InputRejected` (la tupla de `veridicus_errors`) ante una entrada
    inválida (0 llamadas) y `Cancelled` si `cancelled()` es
    verdadero. Nunca lanza una excepción por un fallo del modelo.
    """
    raise NotImplementedError("analyze: lo implementa U11-T04 (paso 9)")


class IncoherenceAnalyzer:
    """Cumple el `Protocol` de C17 y delega en `analyze`."""

    def analyze(
        self,
        entrada: Entrada,
        config: EffectiveConfig,
        gateway: ModelGateway,
        cancelled: CancelCheck | None = None,
    ) -> Salida:
        raise NotImplementedError("IncoherenceAnalyzer.analyze: lo implementa U11-T04 (paso 9)")
