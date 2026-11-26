"""Ayudas comunes de las pruebas de U11: entradas sintéticas, un gateway guionado, un proveedor
guionado sobre el `Anonymizer` real y la validación contra C6.

Todo es sintético. Las funciones que llaman a un *stub* (`make_config`, `load_notice`, etc.) se
llaman dentro del cuerpo de cada prueba y nunca en un *fixture*, para que el rojo del paso 3 sea
`FAILED` y no `ERROR`.

Costuras que el rojo fija como contrato de U11-T02 a U11-T05 (ver los docstrings de los *stubs*):

- `execution_profiles.loader.load_config(profile_name, env)` y `load_profiles(path=None)`;
- `execution_profiles.validate.validate_profile(document, name, env) -> avisos`;
- `model_gateway.gateway.build(config, anonymizing_provider=None)`;
- `application.messages.load_response_schema(role, kind)` y `load_system_prompt(role)`;
- `veridicus_integrity_policy.notice.load_notice()`, llamada por nombre de módulo desde la CLI;
- `veridicus_anonymizer.application.generate.now` y `.pseudonymize`, `api.load_catalogs` y
  `api.limits`, las costuras de U10 para el presupuesto, la seudonimización y los catálogos.
"""

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from veridicus_contracts.model_calls import (
    GenerateRequest,
    GenerateResult,
    ModelCall,
)
from veridicus_contracts.registry import BASE_URI, build_registry, validator_for
from veridicus_execution_profiles.loader import EffectiveConfig, load_config

PROFILE = "demo-anthropic"
KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
# Canario inventado: nunca es una clave real.
KEY_CANARY = "sk-sintetico-canario-7f3a91c2d4e5"
MODEL = "claude-sonnet-5-5"
SALIDA_URI = BASE_URI + "veridicus/contracts/analyzer/v1/salida"

# Entidades sembradas (nombres inventados) de los turnos por omisión.
ENTITIES = [
    "Casilda Roncancio",
    "Casilda",
    "Roncancio",
    "Villa Rocamora",
    "Villa",
    "Rocamora",
    "Puerto Altamira",
    "Puerto",
    "Altamira",
    "Telésforo Ardila",
    "Telésforo",
    "Ardila",
]

T1 = "¿Dónde pasó usted la noche del suceso?"
T2 = "Casilda Roncancio llegó a Villa Rocamora antes del mediodía."
T3 = "¿Y dónde estaba usted entonces?"
T4 = "Yo estaba en Puerto Altamira antes del mediodía, con Telésforo Ardila."


def env(**extra: str) -> dict[str, str]:
    """Entorno de una corrida con el perfil de demostración: la clave canario y el plazo de 300 s."""
    return {KEY_REF: KEY_CANARY, "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "300", **extra}


def make_config(environ: Mapping[str, str] | None = None) -> EffectiveConfig:
    """La configuración efectiva del perfil de demostración (llama al *stub* `load_config`)."""
    return load_config(PROFILE, env() if environ is None else environ)


def default_turns() -> list[dict[str, Any]]:
    return [
        {"n": 1, "hablante": "ENT", "texto": T1},
        {"n": 2, "hablante": "TEST", "pagina": 1, "texto": T2},
        {"n": 3, "hablante": "ENT", "texto": T3},
        {"n": 4, "hablante": "TEST", "pagina": 2, "texto": T4},
    ]


def make_transcription(
    turns: Sequence[Mapping[str, Any]] | None = None, *, entrevista: str = "SINT-0001"
) -> dict[str, Any]:
    """El objeto `transcripcion` de C6; es también el contenido del archivo de entrada de la CLI."""
    chosen = default_turns() if turns is None else [dict(t) for t in turns]
    return {"entrevista": entrevista, "origen": "sintetico", "turnos": chosen}


def make_entrada(
    turns: Sequence[Mapping[str, Any]] | None = None, *, entrevista: str = "SINT-0001"
) -> dict[str, Any]:
    return {
        "contrato": "1.0.0",
        "transcripcion": make_transcription(turns, entrevista=entrevista),
        "modo": "final",
        "perfil": PROFILE,
    }


def finding(
    *,
    hecho: str = "Lugar donde estaba antes del mediodía",
    tipo: str = "lugar",
    a: tuple[int, str] = (2, T2),
    b: tuple[int, str] = (4, T4),
    observaciones: str = "Las dos citas ubican la misma hora en lugares distintos.",
) -> dict[str, Any]:
    """Un candidato del juez, con la forma del esquema local (BR3.4)."""
    return {
        "hecho": hecho,
        "tipo": tipo,
        "cita_a": {"cita": a[1], "turno": f"T{a[0]}"},
        "cita_b": {"cita": b[1], "turno": f"T{b[0]}"},
        "observaciones": observaciones,
    }


def make_call(role: str, *, anonymized: bool = True, input_tokens: int = 120) -> ModelCall:
    return ModelCall(
        role=role,
        provider="anthropic",
        model=MODEL,
        input_tokens=input_tokens,
        output_tokens=30,
        fallback_provider=False,
        anonymized=anonymized,
        at=datetime(2026, 11, 26, 12, 0, 0, tzinfo=UTC),
    )


@dataclass
class ScriptedGateway:
    """Gateway guionado: devuelve lo que se le pide por papel y registra cada petición.

    `fail` lanza un error en las llamadas de un papel; `anonymized_from` hace que, desde la llamada
    con ese número (1 es la primera), el registro diga `anonymized=False`; `altered_markers` son los
    punteros RFC 6901 que informa el juez (BR5.3), por ejemplo `/hallazgos/0/observaciones`.
    """

    findings: list[dict[str, Any]] = field(default_factory=list)
    verdict_direct: bool = True
    verdict_permuted: bool = True
    judge_content: dict[str, Any] | None = None
    verifier_content: dict[str, Any] | None = None
    fail: dict[str, Exception] = field(default_factory=dict)
    anonymized_from: int | None = None
    altered_markers: list[str] = field(default_factory=list)
    input_tokens: int = 120
    requests: list[GenerateRequest] = field(default_factory=list)

    def generate(self, request: GenerateRequest) -> GenerateResult:
        self.requests.append(request)
        number = len(self.requests)
        if request.role in self.fail:
            raise self.fail[request.role]
        anonymized = self.anonymized_from is None or number < self.anonymized_from
        content: dict[str, Any]
        if request.role == "judge":
            content = (
                self.judge_content
                if self.judge_content is not None
                else {"hallazgos": list(self.findings)}
            )
        elif request.role == "verifier":
            content = self.verifier_content or {"confirma": self.verdict_direct}
        else:
            content = self.verifier_content or {"confirma": self.verdict_permuted}
        return GenerateResult(
            content=content,
            altered_markers=list(self.altered_markers) if request.role == "judge" else [],
            call=make_call(request.role, anonymized=anonymized, input_tokens=self.input_tokens),
        )

    def roles(self) -> list[str]:
        return [request.role for request in self.requests]


def all_keys(node: Any) -> set[str]:
    """Todas las claves de un documento JSON, a cualquier profundidad."""
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(str(key))
            keys |= all_keys(value)
    elif isinstance(node, list):
        for item in node:
            keys |= all_keys(item)
    return keys


def c6_problems(salida: Mapping[str, Any]) -> list[str]:
    """Problemas de una salida frente al esquema C6 de salida (vacío si valida)."""
    validator = validator_for(build_registry(), SALIDA_URI)
    return [error.message for error in validator.iter_errors(dict(salida))]


def discard_reasons(salida: Mapping[str, Any]) -> list[str]:
    return [descarte["motivo"] for descarte in salida["registro"]["descartes"]]


def assert_error_output(salida: Mapping[str, Any], code: str) -> None:
    """Fallo cerrado (BR7.1, AUTONOMIA-05): estado error, su código, nada parcial y C6 válido."""
    assert salida["estado"] == "error"
    assert salida["error"]["codigo"] == code
    assert salida["hallazgos"] == []
    assert salida["registro"]["descartes"] == []
    assert "observaciones_conductor" not in salida
    assert c6_problems(salida) == []


# --- Proveedor guionado sobre el Anonymizer real (AUTONOMIA-04, AUTONOMIA-05) -----------------------


def anthropic_envelope(payload: object) -> dict[str, Any]:
    """Sobre de la Messages API con el texto de la salida estructurada."""
    return {
        "id": "msg_sintetico_0001",
        "type": "message",
        "role": "assistant",
        "model": MODEL,
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 412, "output_tokens": 37},
    }


class ScriptedProvider(httpx.MockTransport):
    """Transporte HTTP falso del `Anonymizer`: captura cada cuerpo crudo y responde según la
    petición. Al juez le devuelve `findings_for(turnos)`, con los turnos tal como salieron
    (seudonimizados); al verificador, `{"confirma": confirm}`. Nunca abre red."""

    def __init__(
        self,
        findings_for: Callable[[dict[int, str]], list[dict[str, Any]]],
        *,
        confirm: bool = True,
    ) -> None:
        self.bodies: list[bytes] = []
        self._findings_for = findings_for
        self._confirm = confirm
        super().__init__(self._handle)

    @property
    def request_count(self) -> int:
        return len(self.bodies)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        raw = request.read()
        self.bodies.append(raw)
        body = json.loads(raw)
        user = next(m for m in body["messages"] if m["role"] == "user")
        content = user["content"]
        text = content if isinstance(content, str) else "".join(b["text"] for b in content)
        payload = json.loads(text)
        reply: dict[str, Any]
        if "turnos" in payload:
            turns = {int(t["n"]): str(t["texto"]) for t in payload["turnos"]}
            reply = {"hallazgos": self._findings_for(turns)}
        else:
            reply = {"confirma": self._confirm}
        return httpx.Response(200, json=anthropic_envelope(reply))


def echo_finding(turns: dict[int, str]) -> list[dict[str, Any]]:
    """Un hallazgo que cita los turnos 2 y 4 tal como llegaron al proveedor (con marcas)."""
    return [finding(a=(2, turns[2]), b=(4, turns[4]))]


def _strings(value: Any, out: list[str]) -> None:
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            out.append(str(key))
            _strings(item, out)
    elif isinstance(value, list):
        for item in value:
            _strings(item, out)


def outgoing_views(provider: ScriptedProvider) -> list[str]:
    """Todas las formas en que una entidad podría viajar: el cuerpo crudo, cada cadena ya
    decodificada y el JSON interior de los mensajes."""
    views: list[str] = []
    for raw in provider.bodies:
        body = raw.decode("utf-8")
        views.append(body)
        parsed = json.loads(body)
        strings: list[str] = []
        _strings(parsed, strings)
        for text in strings:
            views.append(text)
            try:
                inner = json.loads(text)
            except ValueError:
                continue
            inner_strings: list[str] = []
            _strings(inner, inner_strings)
            views.extend(inner_strings)
    return views


def assert_no_entity_in_payload(provider: ScriptedProvider, entities: Sequence[str]) -> None:
    """AC11.3.7: ninguna entidad sembrada sale en ningún cuerpo capturado."""
    assert provider.request_count >= 1, "no salió ninguna petición que comprobar"
    for view in outgoing_views(provider):
        for entity in entities:
            assert entity not in view, "fuga de una entidad sembrada"


def write_transcription(directory: Path, name: str = "SINT-0001.json") -> Path:
    """El archivo de entrada de la CLI: el objeto `transcripcion` de C6."""
    path = directory / name
    path.write_text(json.dumps(make_transcription(), ensure_ascii=False), encoding="utf-8")
    return path
