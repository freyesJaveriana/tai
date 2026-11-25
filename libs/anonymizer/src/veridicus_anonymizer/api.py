"""API del módulo (C20): `Anonymizer.generate` y su construcción en la CLI (F3b, PD-7).

- `build_anonymizer(env, transport=None)` tiene la firma literal de PD-7: ningún parámetro permite
  saltarse la seudonimización, cambiar los catálogos ni el reloj (F-07).
- Carga los catálogos con `load_catalogs()` por el nombre global de este módulo (`api.load_catalogs`);
  las pruebas lo sustituyen con `monkeypatch` para inyectar un catálogo alterado, igual que
  `testing.bypass`. Un catálogo o una cifra de límite inválidos lanzan su error de configuración
  (`CatalogError`, `LimitsConfigError`) antes de cualquier llamada (BR2.2).
- Sin `transport`, usa la fábrica de producción `providers.http.default_transport()`.
- La clave se comprueba en `generate`, contra `request.destination.api_key_ref`, y su ausencia es
  `AnonymizerUnavailable` (BR2.1).
"""

from collections.abc import Mapping

import httpx
from veridicus_contracts import limits
from veridicus_contracts.model_calls import GenerateRequest, GenerateResult

from veridicus_anonymizer.application.generate import GenerateSettings, generate_call
from veridicus_anonymizer.domain.catalogs import Catalogs, load_catalogs
from veridicus_anonymizer.providers.http import build_client, default_transport

__all__ = ["Anonymizer", "build_anonymizer", "load_catalogs"]


class Anonymizer:
    """Implementa `AnonymizingProvider` con una sola operación, `generate`."""

    def __init__(
        self,
        *,
        catalogs: Catalogs,
        env: Mapping[str, str],
        client: httpx.Client,
        settings: GenerateSettings,
    ) -> None:
        self._catalogs = catalogs
        self._env = dict(env)
        self._client = client
        self._settings = settings

    def __repr__(self) -> str:
        return "Anonymizer(<oculto>)"

    def generate(self, request: GenerateRequest) -> GenerateResult:
        """Seudonimiza, llama una vez al proveedor y restaura, o falla cerrado (F1)."""
        return generate_call(
            request,
            env=self._env,
            catalogs=self._catalogs,
            client=self._client,
            settings=self._settings,
        )


def build_anonymizer(
    env: Mapping[str, str], transport: httpx.BaseTransport | None = None
) -> Anonymizer:
    """Construye el módulo con el entorno recibido (F3b, sin NER en B10a)."""
    catalogs = load_catalogs()
    figures = limits.load(env)
    settings = GenerateSettings(
        response_max_bytes=int(figures["anonymizer_response_max_bytes"]),
        masking_budget_ratio=float(figures["anonymizer_masking_budget_ratio"]),
        call_timeout_cap_s=float(figures["model_call_timeout_s"]),
    )
    client = build_client(default_transport() if transport is None else transport)
    return Anonymizer(catalogs=catalogs, env=env, client=client, settings=settings)
