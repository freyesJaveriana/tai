"""Orquestación de una llamada `generate` (F1, F7): destino, seudonimización, envío y restauración.

Orden fijo: comprobar el destino, seudonimizar, enviar **una sola vez** y restaurar (PD-8). Todo lo que
falla antes del envío sale como `AnonymizerUnavailable`, sin `ModelCall` y con 0 peticiones (BR2.1);
una excepción inesperada después del envío sale como `ProviderError` con su `ModelCall`, porque la
llamada ya salió y debe contar (PD-9, BR2.6). La tabla de correspondencia se vacía en todos los finales
(BR1.8) y los logs llevan solo identificadores y cifras (BR2.3).

`pseudonymize`, `restore` y `now` se leen por su nombre global de este módulo: las pruebas (y el
control negativo `testing.bypass`) los sustituyen con `monkeypatch`. `now` es el reloj del presupuesto
de la seudonimización (NFR3.5, F-12); el dominio no lee el reloj y recibe `has_budget`.

Los errores se lanzan fuera de los bloques `except`, para que ninguna excepción interna quede
encadenada como `__context__` en un error que sale hacia fuera.
"""

import logging
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from time import monotonic as now

import httpx
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    GenerateRequest,
    GenerateResult,
    Message,
    ModelCall,
    ModelCallError,
    ProviderError,
)

from veridicus_anonymizer.domain.catalogs import PROVIDERS, Capability, Catalogs
from veridicus_anonymizer.domain.masking import MaskingBudgetExceeded, MaskTable, pseudonymize
from veridicus_anonymizer.domain.restoration import restore
from veridicus_anonymizer.providers.anthropic import ANTHROPIC_DOMAIN, ProviderReply, send

__all__ = ["GenerateSettings", "generate_call", "now", "pseudonymize", "restore"]

logger = logging.getLogger("veridicus_anonymizer")

ALLOWED_PORT = 443


@dataclass(frozen=True)
class GenerateSettings:
    """Las cifras de C25 que usa una llamada (`limits.load`)."""

    response_max_bytes: int
    masking_budget_ratio: float
    call_timeout_cap_s: float


@dataclass
class _Trace:
    """Lo único que llega al log: cifras y códigos, nunca texto (BR2.3)."""

    outcome: str = "error"
    call: ModelCall | None = None
    replacements: str = "none"


def _check_destination(
    request: GenerateRequest, env: Mapping[str, str], catalogs: Catalogs
) -> tuple[str, Capability]:
    """Comprueba el destino y devuelve la clave y la capacidad del modelo; nunca nombra un valor."""
    destination = request.destination
    if destination.scope != "external" or destination.provider == "local":
        raise AnonymizerUnavailable("el destino no es externo: el módulo solo atiende proveedores")
    if destination.provider not in PROVIDERS:
        raise AnonymizerUnavailable("el proveedor del destino no está en la lista")
    if destination.provider != "anthropic":
        raise AnonymizerUnavailable("el proveedor del destino no tiene adaptador todavía")
    domain = catalogs.domains[destination.provider]
    if domain.domain != ANTHROPIC_DOMAIN:
        raise AnonymizerUnavailable("el dominio del proveedor no está en la lista permitida")
    if domain.port != ALLOWED_PORT:
        raise AnonymizerUnavailable("el dominio del proveedor no usa el 443 que se permite")
    capability = catalogs.capabilities.get((destination.provider, destination.model))
    if capability is None:
        raise AnonymizerUnavailable("el modelo del destino no está en la tabla de capacidades")
    key = env.get(destination.api_key_ref) if destination.api_key_ref else None
    if not key or not (key.isascii() and key.isprintable()):
        raise AnonymizerUnavailable(
            "la clave de API referenciada no está disponible o no es válida"
        )
    return key, capability


def _mask(
    messages: list[Message], catalogs: Catalogs, started: float, budget_s: float
) -> tuple[list[Message], MaskTable]:
    """Seudonimiza; cualquier fallo antes del envío es `AnonymizerUnavailable` (BR2.1)."""
    try:
        return pseudonymize(messages, catalogs, has_budget=lambda: now() - started <= budget_s)
    except MaskingBudgetExceeded:
        reason = "se agotó el presupuesto de plazo de la seudonimización"
    except Exception:  # noqa: BLE001 - toda falla antes del envío falla cerrado
        reason = "falló un paso inesperado de la seudonimización (detección, tabla o serialización)"
    raise AnonymizerUnavailable(reason)


def _replacements(table: MaskTable) -> str:
    """Número de reemplazos por categoría, p. ej. `LUGAR:1,PERSONA:2`; sin valores."""
    markers = (table.marker_for(form) or "" for form in table.forms())
    counts = Counter(marker[1 : marker.rindex("_")] for marker in markers)
    return ",".join(f"{category}:{n}" for category, n in sorted(counts.items())) or "none"


def _restore(reply: ProviderReply, table: MaskTable) -> GenerateResult:
    """Restaura antes de devolver (AUTONOMIA-05); un fallo aquí ya es posterior al envío (PD-9)."""
    try:
        outcome = restore(reply.content, table)
    except Exception:  # noqa: BLE001 - la llamada ya salió y debe contar
        outcome = None
    if outcome is None:
        raise ProviderError("falló un paso inesperado al restaurar la respuesta", reply.call)
    return GenerateResult(
        content=outcome.content, altered_markers=outcome.altered_markers, call=reply.call
    )


def _release(table: MaskTable | None) -> None:
    if table is not None:
        table.clear()


def _prepare(
    request: GenerateRequest,
    env: Mapping[str, str],
    catalogs: Catalogs,
    settings: GenerateSettings,
    started: float,
    trace: _Trace,
) -> tuple[str, Capability, list[Message], MaskTable, float]:
    """Toda la región previa al envío: cualquier fallo, previsto o no, es `AnonymizerUnavailable`.

    Un error inesperado se traduce fuera del `except` y sin ningún valor en el mensaje (F-01); si ya
    había una tabla, se vacía antes de salir (BR1.8).
    """
    table: MaskTable | None = None
    try:
        key, capability = _check_destination(request, env, catalogs)
        effective_s = min(request.timeout_s, settings.call_timeout_cap_s)
        budget_s = settings.masking_budget_ratio * effective_s
        masked, table = _mask(request.messages, catalogs, started, budget_s)
        trace.replacements = _replacements(table)
        remaining_s = effective_s - (now() - started)
        if remaining_s <= 0:
            raise AnonymizerUnavailable("se agotó el plazo antes de enviar")
        return key, capability, masked, table, remaining_s
    except AnonymizerUnavailable:
        _release(table)
        raise
    except Exception:  # noqa: BLE001 - toda falla antes del envío falla cerrado
        _release(table)
    raise AnonymizerUnavailable(
        "falló un paso inesperado antes del envío; no salió ninguna llamada"
    )


def _run(
    request: GenerateRequest,
    *,
    env: Mapping[str, str],
    catalogs: Catalogs,
    client: httpx.Client,
    settings: GenerateSettings,
    started: float,
    trace: _Trace,
) -> GenerateResult:
    key, capability, masked, table, remaining_s = _prepare(
        request, env, catalogs, settings, started, trace
    )
    try:
        reply = send(
            client=client,
            request=request,
            messages=masked,
            structured_mode=capability.structured_mode,
            effort_parameter=capability.effort_parameter,
            api_key=key,
            timeout_s=remaining_s,
            max_response_bytes=settings.response_max_bytes,
        )
        trace.call = reply.call
        return _restore(reply, table)
    finally:
        table.clear()


def generate_call(
    request: GenerateRequest,
    *,
    env: Mapping[str, str],
    catalogs: Catalogs,
    client: httpx.Client,
    settings: GenerateSettings,
) -> GenerateResult:
    """Una llamada completa; solo sale un error tipado de C13 (BR2.1, BR2.6)."""
    started = now()
    trace = _Trace()
    try:
        result = _run(
            request,
            env=env,
            catalogs=catalogs,
            client=client,
            settings=settings,
            started=started,
            trace=trace,
        )
        trace.outcome = "ok"
        return result
    except ModelCallError as error:
        trace.outcome = type(error).__name__
        trace.call = getattr(error, "call", None)
        raise
    finally:
        _log(request, trace, now() - started)


def _log(request: GenerateRequest, trace: _Trace, elapsed_s: float) -> None:
    call = trace.call
    logger.info(
        "generate outcome=%s role=%s slot=%s provider=%s model=%s profile=%s replacements=%s "
        "tokens_in=%d tokens_out=%d duration_ms=%d",
        trace.outcome,
        request.role,
        request.destination_slot,
        request.destination.provider,
        request.destination.model,
        request.profile_name,
        trace.replacements,
        call.input_tokens if call else 0,
        call.output_tokens if call else 0,
        int(elapsed_s * 1000),
    )
