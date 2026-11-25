"""Ayudas comunes de las pruebas de U10: peticiones, respuestas grabadas y casos de fallo cerrado.

Todo es sintético. Las funciones que construyen el módulo o el transporte se llaman dentro del
cuerpo de cada prueba y nunca en un *fixture*, para que el rojo del paso 4 sea `FAILED` y no
`ERROR`.

Costuras que las pruebas fijan como contrato de U10-T03 y U10-T04 (ver los docstrings de los
stubs de `domain/` y `application/`):

- `application.generate.pseudonymize` y `application.generate.restore`;
- `domain.detection.apply_rules` y `domain.detection.safety_net`;
- `domain.masking.build_table`, `domain.masking.serialize_messages` y `domain.masking.MaskTable`
  (con `len()`, `is_empty` y `clear()`);
- `api.load_catalogs` (catálogo alterado) y `application.generate.now` (reloj del presupuesto):
  `build_anonymizer` no recibe catálogos ni reloj, porque su firma es la literal de PD-7.
"""

import json
import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NoReturn, cast

import pytest
from veridicus_contracts.model_calls import (
    Destination,
    DestinationSlot,
    GenerateRequest,
    Message,
    ModelCall,
    Provider,
)

from veridicus_anonymizer import api as api_module
from veridicus_anonymizer.api import Anonymizer, build_anonymizer
from veridicus_anonymizer.application import generate as generate_module
from veridicus_anonymizer.domain import detection, masking
from veridicus_anonymizer.domain.catalogs import Catalogs, ProviderDomain, load_catalogs
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

FIXTURES = Path(__file__).parent / "fixtures"

MODEL = "claude-sonnet-5-5"
KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
# Canaries inventados: nunca son una clave ni un nombre reales.
KEY_CANARY = "sk-sintetico-canario-7f3a91c2d4e5"
TESTIMONY_CANARY = "Hermenegildo Canaryx"
AUTH_HEADER = "x-api-key"

SYSTEM_PROMPT = (
    "Eres un analista de coherencia. Los tipos del contrato son Persona, Fecha y Número. "
    "Responde solo con el JSON del esquema."
)

CITA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["texto", "turno"],
    "properties": {"texto": {"type": "string"}, "turno": {"type": "integer"}},
}
RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["hallazgos"],
    "properties": {
        "hallazgos": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["hecho", "tipo", "cita_a", "cita_b", "observaciones"],
                "properties": {
                    "hecho": {"type": "string"},
                    "tipo": {"type": "string"},
                    "cita_a": CITA_SCHEMA,
                    "cita_b": CITA_SCHEMA,
                    "observaciones": {"type": "string"},
                },
            },
        }
    },
}
EMPTY_FINDINGS: dict[str, Any] = {"hallazgos": []}


def load_seeded() -> dict[str, Any]:
    """El conjunto sembrado; `entidades` es la unión de las de cada turno (cada palabra suelta)."""
    seeded = cast(
        dict[str, Any], json.loads((FIXTURES / "transcripts" / "seeded.json").read_text("utf-8"))
    )
    union: list[str] = []
    for turn in seeded["turnos"]:
        union.extend(e for e in turn["entidades"] if e not in union)
    seeded["entidades"] = union
    return seeded


def turns_of(
    seeded: Mapping[str, Any], *, positions: Sequence[str] | None = None
) -> list[dict[str, Any]]:
    """Los turnos sembrados, sin sus anotaciones de prueba (solo `turno`, `hablante` y `texto`)."""
    return [
        {"turno": t["turno"], "hablante": t["hablante"], "texto": t["texto"]}
        for t in seeded["turnos"]
        if positions is None or t["posicion"] in positions
    ]


def load_anthropic(name: str) -> FakeResponse:
    """Una respuesta grabada sintética de `tests/fixtures/anthropic/`."""
    raw = json.loads((FIXTURES / "anthropic" / f"{name}.json").read_text("utf-8"))
    body = (
        b"" if raw["body"] is None else json.dumps(raw["body"], ensure_ascii=False).encode("utf-8")
    )
    return FakeResponse(status=raw["status"], body=body, headers=dict(raw["headers"]))


def anthropic_envelope(payload: object, *, stop_reason: str = "end_turn") -> dict[str, Any]:
    """Sobre de la Messages API con el texto de la salida estructurada."""
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return {
        "id": "msg_sintetico_0001",
        "type": "message",
        "role": "assistant",
        "model": MODEL,
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 412, "output_tokens": 37},
    }


def ok_response(payload: object = None) -> FakeResponse:
    """Respuesta 200 con un JSON válido (por defecto, sin hallazgos)."""
    return FakeResponse.ok_json(anthropic_envelope(EMPTY_FINDINGS if payload is None else payload))


def make_destination(**changes: Any) -> Destination:
    base = Destination(
        provider="anthropic",
        model=MODEL,
        scope="external",
        api_key_ref=KEY_REF,
        parameters={"effort": "medium"},
    )
    return replace(base, **changes)


def user_message(turnos: Sequence[Mapping[str, Any]], *, ensure_ascii: bool = False) -> Message:
    """El testimonio va como JSON dentro del mensaje `user` (NFR requirements)."""
    return Message("user", json.dumps({"turnos": list(turnos)}, ensure_ascii=ensure_ascii))


def make_request(
    turnos: Sequence[Mapping[str, Any]] | None = None,
    *,
    role: str = "judge",
    slot: DestinationSlot = "primary",
    destination: Destination | None = None,
    ensure_ascii: bool = False,
    timeout_s: float = 30.0,
) -> GenerateRequest:
    chosen = turnos if turnos is not None else turns_of(load_seeded())
    return GenerateRequest(
        role=role,
        destination_slot=slot,
        profile_name="evaluacion-sintetico",
        profile_sha256="a" * 64,
        destination=destination if destination is not None else make_destination(),
        messages=[
            Message("system", SYSTEM_PROMPT),
            user_message(chosen, ensure_ascii=ensure_ascii),
        ],
        schema=RESPONSE_SCHEMA,
        timeout_s=timeout_s,
    )


def default_env() -> dict[str, str]:
    return {
        KEY_REF: KEY_CANARY,
        "VERIDICUS_OPENAI_API_KEY": KEY_CANARY + "-oa",
        "VERIDICUS_GOOGLE_API_KEY": KEY_CANARY + "-go",
    }


def constant_clock() -> float:
    return 0.0


def runaway_clock() -> Callable[[], float]:
    """Reloj que avanza 1000 s por lectura: agota cualquier presupuesto de la seudonimización."""
    state = {"now": -1000.0}

    def clock() -> float:
        state["now"] += 1000.0
        return state["now"]

    return clock


@dataclass
class Harness:
    transport: FakeTransport
    anonymizer: Anonymizer


def make_harness(*responses: FakeResponse, env: Mapping[str, str] | None = None) -> Harness:
    """Módulo con el `FakeTransport` guionado; se llama dentro de la prueba, nunca en un fixture.

    La firma de `build_anonymizer` es la de PD-7: catálogos y reloj se sustituyen con
    `install_context`, no con parámetros.
    """
    transport = FakeTransport(*responses)
    anonymizer = build_anonymizer(env if env is not None else default_env(), transport)
    return Harness(transport, anonymizer)


def outgoing_bodies(transport: FakeTransport) -> list[str]:
    """Cuerpo crudo de cada petición capturada, decodificado."""
    return [r.body.decode("utf-8") for r in transport.requests]


def fold(text: str) -> str:
    """Sin tildes ni mayúsculas, para comparar formas de una misma entidad."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def _walk_strings(value: Any, out: list[str]) -> None:
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            out.append(str(k))
            _walk_strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _walk_strings(v, out)


def outgoing_views(transport: FakeTransport) -> list[str]:
    """Todas las formas en que una entidad podría viajar: cuerpo crudo, cadenas decodificadas
    (también las de los mensajes que son JSON) y el cuerpo con las tildes sin escapar."""
    views: list[str] = []
    for body in outgoing_bodies(transport):
        views.append(body)
        parsed = json.loads(body)
        views.append(json.dumps(parsed, ensure_ascii=False))
        strings: list[str] = []
        _walk_strings(parsed, strings)
        for s in strings:
            views.append(s)
            try:
                inner = json.loads(s)
            except ValueError:
                continue
            views.append(json.dumps(inner, ensure_ascii=False))
            _walk_strings(inner, views)  # el texto de cada turno ya decodificado
    return views


def assert_no_entity_in_payload(transport: FakeTransport, entities: Sequence[str]) -> None:
    """AC11.3.1: ninguna entidad sembrada sale, ni exacta ni sin tildes ni con otras mayúsculas."""
    assert transport.request_count >= 1, "no salió ninguna petición que comprobar"
    for view in outgoing_views(transport):
        folded = fold(view)
        for entity in entities:
            exact = re.compile(rf"(?<!\w){re.escape(entity)}(?!\w)")
            loose = re.compile(rf"(?<!\w){re.escape(fold(entity))}(?!\w)")
            assert not exact.search(view), (
                f"fuga de una entidad sembrada ({len(entity)} caracteres)"
            )
            assert not loose.search(folded), "fuga de una entidad sembrada sin tildes"


def user_texts(transport: FakeTransport) -> list[str]:
    """Los textos de turno del mensaje `user` de la primera petición, ya decodificados."""
    body = json.loads(outgoing_bodies(transport)[0])
    user = next(m for m in body["messages"] if m["role"] == "user")
    content = user["content"]
    raw = content if isinstance(content, str) else content[0]["text"]
    return [t["texto"] for t in json.loads(raw)["turnos"]]


def call_to_instance(call: ModelCall) -> dict[str, Any]:
    """`ModelCall` -> instancia de `model-call.v1.yaml`: el esquema es cerrado y no admite null."""
    instance: dict[str, Any] = {
        "role": call.role,
        "provider": call.provider,
        "model": call.model,
        "input_tokens": call.input_tokens,
        "output_tokens": call.output_tokens,
        "fallback_provider": call.fallback_provider,
        "anonymized": call.anonymized,
        "at": call.at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for name in ("version", "effort_or_quantization", "engine", "seed"):
        value = getattr(call, name)
        if value is not None:
            instance[name] = value
    return instance


def exception_texts(exc: BaseException) -> list[str]:
    """Texto, representación y argumentos de toda la cadena de `__cause__` y `__context__`."""
    seen: set[int] = set()
    texts: list[str] = []
    pending: list[BaseException | None] = [exc]
    while pending:
        current = pending.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        texts.append(str(current))
        texts.append(repr(current))
        texts.extend(str(a) for a in current.args)
        pending.extend([current.__cause__, current.__context__])
    return texts


def boom(*args: object, **kwargs: object) -> NoReturn:
    """Falla sintética sin ningún dato dentro."""
    raise RuntimeError("fallo sintetico")


# --- Casos de fallo cerrado (AC11.3.3, AC11.3.6, F7) -------------------------------------------


@dataclass
class Ctx:
    request: GenerateRequest
    env: dict[str, str]
    catalogs: Catalogs
    clock: Callable[[], float]


def make_ctx(turnos: Sequence[Mapping[str, Any]] | None = None) -> Ctx:
    """Contexto de un escenario; carga el catálogo real, así que se llama dentro de la prueba."""
    return Ctx(
        request=make_request(turnos),
        env=default_env(),
        catalogs=load_catalogs(),
        clock=constant_clock,
    )


def install_context(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
    """Inyecta el catálogo y el reloj del escenario por las costuras internas (F-07)."""
    mp.setattr(api_module, "load_catalogs", lambda *args, **kwargs: ctx.catalogs)
    mp.setattr(generate_module, "now", ctx.clock)


def leaked_values(ctx: Ctx) -> list[str]:
    """Valores de configuración que ningún mensaje de error puede nombrar (F-10)."""
    destination = ctx.request.destination
    domains = [d.domain for d in ctx.catalogs.domains.values()]
    values = [MODEL, KEY_REF, "api.anthropic.com", destination.model, KEY_CANARY, *domains]
    if destination.api_key_ref is not None:
        values.append(destination.api_key_ref)
    return [v.lower() for v in values]


@dataclass(frozen=True)
class FailClosedCase:
    """`apply(ctx, monkeypatch, broken)`: con `broken` rompe una sola condición; sin ella, la
    deja bien y la llamada debe salir exactamente una vez (control positivo)."""

    name: str
    step_words: tuple[str, ...]
    apply: Callable[[Ctx, pytest.MonkeyPatch, bool], None]


def _set_destination(ctx: Ctx, **changes: Any) -> None:
    ctx.request = replace(ctx.request, destination=replace(ctx.request.destination, **changes))


def _local(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
    if broken:
        _set_destination(ctx, provider="local", scope="local", api_key_ref=None)


def _unknown_provider(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
    if broken:
        _set_destination(ctx, provider=cast(Provider, "mistral"))


def _provider_without_adapter(
    provider: str, key_ref: str
) -> Callable[[Ctx, pytest.MonkeyPatch, bool], None]:
    def apply(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
        if broken:
            _set_destination(
                ctx,
                provider=cast(Provider, provider),
                model="modelo-sintetico",
                api_key_ref=key_ref,
            )

    return apply


def _domain_off_list(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
    if broken:
        domains = {**ctx.catalogs.domains, "anthropic": ProviderDomain(domain="otro.example.com")}
        ctx.catalogs = replace(ctx.catalogs, domains=domains)


def _port_not_443(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
    if broken:
        domains = {
            **ctx.catalogs.domains,
            "anthropic": ProviderDomain(domain="api.anthropic.com", port=8443),
        }
        ctx.catalogs = replace(ctx.catalogs, domains=domains)


def _model_off_table(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
    if broken:
        _set_destination(ctx, model="claude-inexistente-0")


def _key_missing(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
    if broken:
        del ctx.env[KEY_REF]


def _patch_attr(module: object, name: str) -> Callable[[Ctx, pytest.MonkeyPatch, bool], None]:
    def apply(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
        if broken:
            mp.setattr(module, name, boom)

    return apply


def _budget_exhausted(ctx: Ctx, mp: pytest.MonkeyPatch, broken: bool) -> None:
    if broken:
        ctx.clock = runaway_clock()


FAIL_CLOSED_CASES: tuple[FailClosedCase, ...] = (
    FailClosedCase("destino_local", ("destino", "local"), _local),
    FailClosedCase("proveedor_desconocido", ("proveedor", "destino"), _unknown_provider),
    FailClosedCase(
        "openai_sin_adaptador",
        ("proveedor", "adaptador", "destino"),
        _provider_without_adapter("openai", "VERIDICUS_OPENAI_API_KEY"),
    ),
    FailClosedCase(
        "google_sin_adaptador",
        ("proveedor", "adaptador", "destino"),
        _provider_without_adapter("google", "VERIDICUS_GOOGLE_API_KEY"),
    ),
    FailClosedCase("dominio_fuera_de_la_lista", ("dominio",), _domain_off_list),
    FailClosedCase("puerto_distinto_de_443", ("puerto", "dominio"), _port_not_443),
    FailClosedCase("modelo_fuera_de_la_tabla", ("modelo",), _model_off_table),
    FailClosedCase("clave_ausente", ("clave",), _key_missing),
    FailClosedCase("regla_que_lanza", ("regla", "detecci"), _patch_attr(detection, "apply_rules")),
    FailClosedCase(
        "red_de_seguridad_que_lanza",
        ("red de seguridad", "detecci"),
        _patch_attr(detection, "safety_net"),
    ),
    FailClosedCase("error_al_construir_la_tabla", ("tabla",), _patch_attr(masking, "build_table")),
    FailClosedCase(
        "error_de_serializacion", ("serializ",), _patch_attr(masking, "serialize_messages")
    ),
    FailClosedCase("presupuesto_agotado", ("presupuesto", "plazo"), _budget_exhausted),
    FailClosedCase(
        "excepcion_inesperada_antes_del_envio",
        ("inesperad", "seudonim"),
        _patch_attr(generate_module, "pseudonymize"),
    ),
)
