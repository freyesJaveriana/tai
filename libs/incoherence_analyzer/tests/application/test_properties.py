"""Propiedades (Hypothesis) de las invariantes que toca U11-T04, sobre todas las formas de entrada.

- Rechazo previo (BR1): una entrada mal formada lanza una clase de `InputRejected` y deja el gateway
  en 0 peticiones; ninguna otra excepción escapa.
- AUTONOMIA-05 de punta a punta: sea lo que sea que diga el juez, cada cita de lo que sale verifica en
  su turno, un estado error nunca lleva hallazgos ni descartes y la salida siempre valida contra C6.
- Fallo cerrado: un error tipado en cualquier papel da error con su código, o no pasa nada si ese
  papel no se llamó.
- Plazo: con un reloj que avanza al azar, la salida es válida y un tiempo agotado no deja nada parcial.
"""

import copy
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    InvalidOutput,
    ModelCallError,
    ProviderError,
    Timeout,
)
from veridicus_errors import InputRejected

from tests.support import (
    T1,
    T2,
    T4,
    ScriptedGateway,
    c6_problems,
    default_turns,
    finding,
    make_call,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.application import deadline
from veridicus_incoherence_analyzer.domain.quotes import verify_quote

SETTINGS = settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)

JSON = st.recursive(
    st.none() | st.booleans() | st.integers(-5, 5) | st.text(max_size=8),
    lambda children: (
        st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=6), children, max_size=3)
    ),
    max_leaves=6,
)

# Las rutas donde se puede estropear una entrada válida: una clave de arriba, de la transcripción o de
# un turno. Cada una se borra o se reemplaza por un valor JSON cualquiera.
PATHS = [
    ("contrato",),
    ("modo",),
    ("perfil",),
    ("transcripcion",),
    ("transcripcion", "entrevista"),
    ("transcripcion", "origen"),
    ("transcripcion", "consentimiento"),
    ("transcripcion", "turnos"),
    ("transcripcion", "turnos", 0),
    ("transcripcion", "turnos", 1, "n"),
    ("transcripcion", "turnos", 1, "hablante"),
    ("transcripcion", "turnos", 1, "texto"),
    ("transcripcion", "turnos", 1, "estado"),
    ("transcripcion", "turnos", 1, "pagina"),
]


def _corrupt(path: tuple[str | int, ...], value: Any, delete: bool) -> dict[str, Any]:
    entrada = copy.deepcopy(make_entrada())
    parent: Any = entrada
    for part in path[:-1]:
        parent = parent[part]
    if delete and isinstance(parent, dict):
        parent.pop(path[-1], None)  # la clave opcional que no está no se borra dos veces
    elif delete:
        del parent[path[-1]]
    else:
        parent[path[-1]] = value
    return entrada


@SETTINGS
@given(entrada=JSON)
def test_property_any_json_value_is_rejected_without_calls_or_analyzed(entrada: Any) -> None:
    gateway = ScriptedGateway()
    try:
        salida = analyze(entrada, make_config(), gateway)
    except InputRejected:
        assert gateway.requests == []
    else:  # un JSON arbitrario casi nunca valida; si lo hace, la salida es válida
        assert c6_problems(salida) == []


@SETTINGS
@given(path=st.sampled_from(PATHS), value=JSON, delete=st.booleans())
def test_property_a_corrupted_valid_input_is_rejected_with_no_calls_or_gives_a_valid_output(
    path: tuple[str | int, ...], value: Any, delete: bool
) -> None:
    gateway = ScriptedGateway(findings=[finding()])
    entrada = _corrupt(path, value, delete)
    try:
        salida = analyze(entrada, make_config(), gateway)
    except InputRejected:
        assert gateway.requests == [], "ninguna llamada antes de rechazar"
    else:
        assert c6_problems(salida) == []


TURN_LABELS = st.sampled_from(["T1", "T2", "T3", "T4", "T5", "T0", "x", "T", "T-1", "T" + "9" * 12])
QUOTES = st.one_of(
    st.sampled_from([T1, T2, T4, "Yo estaba en Puerto Altamira", "con Telésforo Ardila"]),
    st.sampled_from([T2, T4]).map(lambda text: text[: len(text) // 2]),
    st.sampled_from([T2, T4]).map(lambda text: text.replace("a", "Ω", 1)),
    st.sampled_from([f"{T2[:10]} […] {T2[20:30]}", f"{T4[20:30]} […] {T4[:10]}"]),
    st.text(max_size=20),
)
FREE_TEXT = st.one_of(
    st.text(max_size=20),
    st.sampled_from(
        ["Hecho", "Otro hecho", "   ", "\t\n", "La persona miente aquí", "«era falso»"]
    ),
)
TYPES = st.sampled_from(["fecha", "numero", "lugar", "persona", "negacion", "secuencia", "otro"])


@st.composite
def candidates(draw: st.DrawFn) -> dict[str, Any]:
    return {
        "hecho": draw(FREE_TEXT.filter(bool)),
        "tipo": draw(TYPES),
        "cita_a": {"cita": draw(QUOTES.filter(bool)), "turno": draw(TURN_LABELS)},
        "cita_b": {"cita": draw(QUOTES.filter(bool)), "turno": draw(TURN_LABELS)},
        "observaciones": draw(FREE_TEXT.filter(bool)),
    }


@SETTINGS
@given(
    found=st.lists(candidates(), max_size=4),
    verdict_direct=st.booleans(),
    verdict_permuted=st.booleans(),
    markers=st.lists(
        st.sampled_from(["/hallazgos/0/hecho", "/hallazgos/1/cita_a/cita", "/hallazgos/9/x", "/x"]),
        max_size=2,
    ),
)
def test_property_whatever_the_judge_says_only_verified_findings_leave(
    found: list[dict[str, Any]],
    verdict_direct: bool,
    verdict_permuted: bool,
    markers: list[str],
) -> None:
    entrada = make_entrada()
    turns = {turn["n"]: turn["texto"] for turn in default_turns()}
    gateway = ScriptedGateway(
        findings=found,
        verdict_direct=verdict_direct,
        verdict_permuted=verdict_permuted,
        altered_markers=markers,
    )

    salida = analyze(entrada, make_config(), gateway)

    assert c6_problems(salida) == []
    if salida["estado"] == "error":
        assert salida["hallazgos"] == []
        assert salida["registro"]["descartes"] == []
        assert "observaciones_conductor" not in salida
    for hallazgo in salida["hallazgos"]:
        for name in ("cita_a", "cita_b"):
            cita = hallazgo[name]
            number = int(cita["turno"][1:])
            assert verify_quote(turns[number], cita["cita"]) == "verified"
    verifier_calls = gateway.roles().count("verifier")
    assert gateway.roles().count("verifier_permuted") == verifier_calls
    if salida["estado"] == "ok":
        rejected = [
            d for d in salida["registro"]["descartes"] if d["motivo"].startswith("rechazado")
        ]
        assert len(salida["hallazgos"]) + len(rejected) == verifier_calls, "uno por sobreviviente"


ERRORS = {
    "invalid": (InvalidOutput, "salida_invalida"),
    "blocked": (ContentBlocked, "bloqueo_contenido"),
    "timeout": (Timeout, "tiempo_agotado"),
    "provider": (ProviderError, "proveedor"),
}


@SETTINGS
@given(
    role=st.sampled_from(["judge", "verifier", "verifier_permuted"]),
    kind=st.sampled_from([*ERRORS, "anonymizer"]),
)
def test_property_a_typed_error_in_any_role_closes_the_run_with_its_code(
    role: str, kind: str
) -> None:
    error: ModelCallError
    if kind == "anonymizer":
        error, code = AnonymizerUnavailable("caído"), "anonimizador_no_disponible"
    else:
        cls, code = ERRORS[kind]
        error = cls("fallo sintético", make_call(role))
    gateway = ScriptedGateway(findings=[finding()], fail={role: error})

    salida = analyze(make_entrada(), make_config(), gateway)

    assert salida["estado"] == "error"
    assert salida["error"]["codigo"] == code
    assert salida["hallazgos"] == []
    assert salida["registro"]["descartes"] == []
    assert c6_problems(salida) == []
    assert gateway.roles()[-1] == role, "la corrida termina en la llamada que falló"


@SETTINGS
@given(
    steps=st.lists(
        st.floats(min_value=0, max_value=100000, allow_nan=False), min_size=4, max_size=8
    )
)
def test_property_with_any_clock_the_output_is_valid_and_never_partial(steps: list[float]) -> None:
    ticks = iter(steps)
    last = steps[-1]

    def now() -> float:
        return next(ticks, last)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(deadline, "monotonic", now)
        gateway = ScriptedGateway(findings=[finding()])
        salida = analyze(make_entrada(), make_config(), gateway)

    assert c6_problems(salida) == []
    if salida["estado"] == "error":
        assert salida["error"]["codigo"] == "tiempo_agotado"
        assert salida["hallazgos"] == []
        assert salida["registro"]["descartes"] == []
    else:
        assert len(salida["hallazgos"]) == 1
