"""API de la biblioteca (C17): `analyze` e `IncoherenceAnalyzer` (PD-4, CG-U11-03).

`Entrada` y `Salida` no se agregan a `veridicus_contracts.analyzer.v1` (PD-4): son los diccionarios
de C6, que `analyze` valida contra el esquema común antes de llamar (la entrada) y antes de
devolver (la salida).
"""

from veridicus_execution_profiles.loader import EffectiveConfig
from veridicus_model_gateway.port import ModelGateway

from veridicus_incoherence_analyzer.application.analyze import Entrada, Salida, run_analysis
from veridicus_incoherence_analyzer.application.deadline import CancelCheck

__all__ = ["CancelCheck", "Entrada", "IncoherenceAnalyzer", "Salida", "analyze"]


def analyze(
    entrada: Entrada,
    config: EffectiveConfig,
    gateway: ModelGateway,
    cancelled: CancelCheck | None = None,
) -> Salida:
    """Analiza una transcripción y devuelve la salida C6, con hallazgos de dos citas verificadas o
    con `estado: error` y hallazgos vacíos (AUTONOMIA-05).

    Lanza una de las clases de `InputRejected` (la tupla de `veridicus_errors`) ante una entrada
    inválida (0 llamadas) y `CancelledError` si `cancelled()` es verdadero antes de una llamada.
    Nunca lanza una excepción por un fallo del modelo ni del anonimizador.
    """
    return run_analysis(entrada, config, gateway, cancelled)


class IncoherenceAnalyzer:
    """Cumple el `Protocol` de C17 y delega en `analyze`."""

    def analyze(
        self,
        entrada: Entrada,
        config: EffectiveConfig,
        gateway: ModelGateway,
        cancelled: CancelCheck | None = None,
    ) -> Salida:
        return analyze(entrada, config, gateway, cancelled)
