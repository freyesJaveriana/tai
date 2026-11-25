"""API del módulo (C20): `Anonymizer.generate` y su construcción en la CLI (F3b).

STUB de U10-T02 (paso 2): lo implementa U10-T04 (paso 10). Contrato que fijan las pruebas rojas:

- `build_anonymizer(env, transport=None)` tiene la firma literal de PD-7: ningún parámetro
  permite saltarse la seudonimización, cambiar los catálogos ni el reloj (F-07).
- `build_anonymizer` obtiene los catálogos llamando a `load_catalogs()` por el nombre global de
  este módulo (`api.load_catalogs`); las pruebas lo sustituyen con `monkeypatch` para inyectar
  un catálogo alterado, igual que `testing.bypass`.
- El reloj del presupuesto es `application.generate.now`, que las pruebas también sustituyen.
- La clave se comprueba en `generate`, contra `request.destination.api_key_ref`, y su ausencia es
  `AnonymizerUnavailable` (BR2.1).
"""

from collections.abc import Mapping

import httpx
from veridicus_contracts.model_calls import GenerateRequest, GenerateResult

from veridicus_anonymizer.domain.catalogs import load_catalogs  # noqa: F401 - costura de pruebas


class Anonymizer:
    """Implementa `AnonymizingProvider` con una sola operación, `generate`."""

    def generate(self, request: GenerateRequest) -> GenerateResult:
        raise NotImplementedError("Anonymizer.generate lo implementa U10-T04")


def build_anonymizer(
    env: Mapping[str, str], transport: httpx.BaseTransport | None = None
) -> Anonymizer:
    """Construye el módulo con el entorno recibido (F3b, sin NER en B10a)."""
    raise NotImplementedError("build_anonymizer lo implementa U10-T04")
