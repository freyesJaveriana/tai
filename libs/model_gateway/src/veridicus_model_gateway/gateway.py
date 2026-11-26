"""Armado del gateway por perfil (BR10.1, AUTONOMIA-04).

Estado: *stub* del paso 1 (U11-T01). Lo implementa U11-T03.
"""

from veridicus_contracts.model_calls import AnonymizingProvider
from veridicus_execution_profiles.loader import EffectiveConfig

from veridicus_model_gateway.port import ModelGateway


def build(
    config: EffectiveConfig, anonymizing_provider: AnonymizingProvider | None = None
) -> ModelGateway:
    """Arma el gateway de `config` antes de cualquier llamada.

    Un papel `scope: external` exige el `anonymizing_provider` inyectado y el piso de
    `model_call_timeout_s` (`floors.COMMERCIAL_MIN_CALL_TIMEOUT_S`); si falta alguno, lanza
    `GatewayConfigError`. Un papel `scope: local` también lo lanza en B11a (adaptador diferido).
    """
    raise NotImplementedError("build: lo implementa U11-T03 (paso 6)")
