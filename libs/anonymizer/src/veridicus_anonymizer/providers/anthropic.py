"""Adaptador nativo de Anthropic (Messages API), por `httpx` directo (PD-1, BR5, F5).

Forma de la API, de la documentación oficial vigente (FD-U10-09):
`POST https://api.anthropic.com/v1/messages` con las cabeceras `x-api-key`, `anthropic-version` y
`content-type`; salida estructurada en `output_config.format` (`type: json_schema`, `schema`) y
esfuerzo en `output_config.effort`; un rechazo es un HTTP 200 con `stop_reason: "refusal"`.

Reglas que cumple este módulo:

- Envía **una sola vez** (BR2.4): ni reintenta ni sigue redirecciones; la URL es una constante (BR3.5).
- Lee la respuesta por bloques con un tope en bytes y un plazo total.
- La clave solo va en la cabecera `x-api-key` (BR5.4) y nunca en un mensaje de error.
- Devuelve el JSON ya parseado en modo estricto y validado contra `req.schema`, **sin restaurar**
  (PD-8): la restauración es de `application/`. Por eso este módulo no importa `domain/`.
- Todo error posterior al envío lleva su `ModelCall` (BR2.6); lo que ocurre antes de enviar o al
  abrir la conexión es `AnonymizerUnavailable`, sin `ModelCall`.

Los errores se lanzan **fuera** de los bloques `except`, para que ninguna excepción de la capa HTTP
quede encadenada como `__context__`.
"""

import json
import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Final, Literal, NoReturn

import httpx
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    GenerateRequest,
    InvalidOutput,
    Message,
    ModelCall,
    ModelCallError,
    ProviderError,
    Timeout,
)

ANTHROPIC_DOMAIN: Final = "api.anthropic.com"
API_URL: Final = f"https://{ANTHROPIC_DOMAIN}/v1/messages"
API_VERSION: Final = "2026-10-21"
# La Messages API exige `max_tokens`; el tope vive aquí y no sale de quien llama.
MAX_TOKENS: Final = 16000
CONNECT_TIMEOUT_S: Final = 10.0
MAX_COUNT: Final = 9007199254740991
_TOKEN = re.compile(r"[A-Za-z0-9._:/@+-]{1,128}")
_INVALID: Final = object()

Kind = Literal["unavailable", "timeout", "provider", "invalid", "blocked"]


@dataclass(frozen=True)
class ProviderReply:
    """El JSON ya parseado y validado, sin restaurar, y el `ModelCall` de la llamada."""

    content: dict[str, Any]
    call: ModelCall


@dataclass(frozen=True)
class _Failure:
    kind: Kind
    message: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class _Parsed:
    content: dict[str, Any]
    input_tokens: int
    output_tokens: int


_TYPED: Final[dict[str, Callable[[str, ModelCall], ModelCallError]]] = {
    "timeout": Timeout,
    "provider": ProviderError,
    "invalid": InvalidOutput,
    "blocked": ContentBlocked,
}


def _build_body(
    request: GenerateRequest,
    messages: Sequence[Message],
    structured_mode: str,
    effort_parameter: str,
) -> tuple[bytes, str | None]:
    """El cuerpo nativo y el esfuerzo; si algo no se puede construir, no se envía nada (BR2.1)."""
    if structured_mode != "json_schema_native":
        raise AnonymizerUnavailable("el modo de salida estructurada del modelo no está admitido")
    schema_ok = True
    try:
        Draft202012Validator.check_schema(request.schema)
    except SchemaError:
        schema_ok = False
    if not schema_ok:
        raise AnonymizerUnavailable("el esquema de la respuesta no es un esquema JSON válido")
    system = "\n\n".join(m.content for m in messages if m.role == "system")
    chat = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
    if not chat:
        raise AnonymizerUnavailable("la petición no trae ningún mensaje de conversación")
    effort = request.destination.parameters.get(effort_parameter)
    if effort is not None and not (isinstance(effort, str) and _TOKEN.fullmatch(effort)):
        raise AnonymizerUnavailable("el esfuerzo del perfil no tiene un valor admitido")
    output_config: dict[str, Any] = {"format": {"type": "json_schema", "schema": request.schema}}
    if effort is not None:
        output_config[effort_parameter] = effort
    body: dict[str, Any] = {
        "model": request.destination.model,
        "max_tokens": MAX_TOKENS,
        "messages": chat,
        "output_config": output_config,
    }
    if system:
        body["system"] = system
    try:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError):
        encoded = None
    if encoded is None:
        raise AnonymizerUnavailable("el cuerpo de la petición no se puede serializar como JSON")
    return encoded, effort


def _headers(api_key: str) -> dict[str, str]:
    """Lista cerrada de cabeceras; la clave solo va en `x-api-key`."""
    return {
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
        "content-type": "application/json",
        "accept": "application/json",
        "user-agent": "veridicus-anonymizer",
        "accept-encoding": "identity",
    }


def _exchange(
    client: httpx.Client, body: bytes, headers: dict[str, str], timeout_s: float, max_bytes: int
) -> bytes | _Failure:
    """Una sola petición; devuelve el cuerpo leído con tope o la falla que corresponda."""
    deadline = monotonic() + timeout_s
    timeout = httpx.Timeout(timeout_s, connect=min(CONNECT_TIMEOUT_S, timeout_s))
    try:
        with client.stream(
            "POST", API_URL, content=body, headers=headers, timeout=timeout
        ) as response:
            if not response.is_success:
                return _Failure("provider", "el proveedor respondió con un error o una redirección")
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    return _Failure("provider", "la respuesta del proveedor pasa del tope de bytes")
                if monotonic() > deadline:
                    return _Failure("timeout", "se agotó el plazo leyendo la respuesta")
                chunks.append(chunk)
            return b"".join(chunks)
    except (httpx.ConnectError, httpx.ConnectTimeout):
        return _Failure("unavailable", "no se pudo abrir la conexión con el proveedor")
    except httpx.TimeoutException:
        return _Failure("timeout", "se agotó el plazo esperando al proveedor")
    except Exception:  # noqa: BLE001 - la petición ya salió: todo otro fallo es ProviderError
        return _Failure("provider", "se cortó la conexión con el proveedor")


def _reject_constant(name: str) -> NoReturn:
    raise ValueError(name)


def _parse_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(text)
    return value


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    if len({key for key, _ in pairs}) != len(pairs):
        raise ValueError("clave repetida")
    return dict(pairs)


def _load(source: bytes | str) -> Any:
    """JSON estricto: sin claves repetidas, sin NaN ni infinitos y sin comentarios."""
    try:
        return json.loads(
            source,
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except (ValueError, RecursionError):
        return _INVALID


def _count(value: Any) -> int:
    ok = isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= MAX_COUNT
    return int(value) if ok else 0


def _single_text(blocks: Any) -> str | None:
    """El texto del único bloque de `content`, o `None` si no hay uno solo y de tipo texto."""
    if not (isinstance(blocks, list) and len(blocks) == 1 and isinstance(blocks[0], dict)):
        return None
    text = blocks[0].get("text")
    return text if blocks[0].get("type") == "text" and isinstance(text, str) else None


def _interpret(raw: bytes, schema: dict[str, Any]) -> _Parsed | _Failure:
    envelope = _load(raw)
    if not isinstance(envelope, dict):
        return _Failure("invalid", "la respuesta del proveedor no es un objeto JSON")
    usage = envelope.get("usage")
    tokens = (0, 0)
    if isinstance(usage, dict):
        tokens = (_count(usage.get("input_tokens")), _count(usage.get("output_tokens")))
    stop_reason = envelope.get("stop_reason")
    if stop_reason == "refusal":
        return _Failure("blocked", "el proveedor rechazó el contenido", *tokens)
    if stop_reason != "end_turn":
        return _Failure("invalid", "la respuesta se cortó o terminó de forma inesperada", *tokens)
    text = _single_text(envelope.get("content"))
    if text is None:
        return _Failure("invalid", "la respuesta no trae un único bloque de texto", *tokens)
    payload = _load(text)
    if not isinstance(payload, dict):
        return _Failure("invalid", "el texto de la respuesta no es un objeto JSON", *tokens)
    if not Draft202012Validator(schema).is_valid(payload):
        return _Failure("invalid", "la salida no cumple el esquema pedido", *tokens)
    return _Parsed(payload, *tokens)


def _safe_interpret(raw: bytes, schema: dict[str, Any]) -> _Parsed | _Failure:
    try:
        return _interpret(raw, schema)
    except Exception:  # noqa: BLE001 - la llamada ya salió: un fallo al interpretar sigue contando
        return _Failure("provider", "error inesperado al interpretar la respuesta")


def send(
    *,
    client: httpx.Client,
    request: GenerateRequest,
    messages: Sequence[Message],
    structured_mode: str,
    effort_parameter: str,
    api_key: str,
    timeout_s: float,
    max_response_bytes: int,
) -> ProviderReply:
    """Envía una vez y devuelve el JSON validado, o lanza el error tipado de C13."""
    body, effort = _build_body(request, messages, structured_mode, effort_parameter)
    sent_at = datetime.now(UTC).replace(microsecond=0)
    outcome = _exchange(client, body, _headers(api_key), timeout_s, max_response_bytes)
    result = outcome if isinstance(outcome, _Failure) else _safe_interpret(outcome, request.schema)
    if isinstance(result, _Failure) and result.kind == "unavailable":
        raise AnonymizerUnavailable(result.message)
    call = ModelCall(
        role=request.role,
        provider="anthropic",
        model=request.destination.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        fallback_provider=request.destination_slot == "fallback",
        anonymized=True,
        at=sent_at,
        effort_or_quantization=effort,
    )
    if isinstance(result, _Failure):
        raise _TYPED[result.kind](result.message, call)
    return ProviderReply(result.content, call)
