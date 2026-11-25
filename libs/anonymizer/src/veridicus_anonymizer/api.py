"""API del módulo (C20): `Anonymizer.generate` y su construcción en la CLI (F3b).

STUB de U10-T02 (paso 2): lo implementa U10-T04 (paso 10). Contrato que fijan las pruebas rojas:

- `build_anonymizer(env, transport=None, *, catalogs=None, clock=None)`: `catalogs` y `clock` son
  solo de inyección en pruebas (catálogo alterado y reloj del presupuesto); no existe ningún
  parámetro que permita saltarse la seudonimización (PD-7).
- La clave se comprueba en `generate`, contra `request.destination.api_key_ref`, y su ausencia es
  `AnonymizerUnavailable` (BR2.1).
"""

from collections.abc import Callable, Mapping

import httpx
from veridicus_contracts.model_calls import GenerateRequest, GenerateResult

from veridicus_anonymizer.domain.catalogs import Catalogs


class Anonymizer:
    """Implementa `AnonymizingProvider` con una sola operación, `generate`."""

    def generate(self, request: GenerateRequest) -> GenerateResult:
        raise NotImplementedError("Anonymizer.generate lo implementa U10-T04")


def build_anonymizer(
    env: Mapping[str, str],
    transport: httpx.BaseTransport | None = None,
    *,
    catalogs: Catalogs | None = None,
    clock: Callable[[], float] | None = None,
) -> Anonymizer:
    """Construye el módulo con el entorno recibido (F3b, sin NER en B10a)."""
    raise NotImplementedError("build_anonymizer lo implementa U10-T04")
