"""AUTONOMIA-04, fallo cerrado (AC11.3.3, AC11.3.6, F7, BR1.8, BR2.1, BR2.6, PD-9).

Cada caso rompe UNA condición y comprueba: `AnonymizerUnavailable` sin `ModelCall`, un mensaje
que nombra el paso sin ningún valor y el transporte con 0 peticiones. El control positivo repite
el mismo escenario con esa sola condición corregida y exige exactamente 1 petición.
"""

import pytest
from veridicus_contracts.model_calls import AnonymizerUnavailable, ModelCallError, ProviderError

from tests.support import (
    FAIL_CLOSED_CASES,
    KEY_CANARY,
    TESTIMONY_CANARY,
    Ctx,
    FailClosedCase,
    boom,
    constant_clock,
    default_env,
    exception_texts,
    load_anthropic,
    load_seeded,
    make_harness,
    make_request,
    ok_response,
    turns_of,
)
from veridicus_anonymizer.application import generate as generate_module
from veridicus_anonymizer.domain import detection, masking
from veridicus_anonymizer.domain.catalogs import load_catalogs

SEEDED = load_seeded()


def _context() -> Ctx:
    turnos = [
        *turns_of(SEEDED),
        {"turno": 99, "hablante": "TES", "texto": f"Dijo {TESTIMONY_CANARY} en voz baja."},
    ]
    return Ctx(
        request=make_request(turnos),
        env=default_env(),
        catalogs=load_catalogs(),
        clock=constant_clock,
    )


@pytest.mark.parametrize("case", FAIL_CLOSED_CASES, ids=[c.name for c in FAIL_CLOSED_CASES])
def test_fails_closed_without_a_call_and_the_fixed_scenario_sends_exactly_one(
    case: FailClosedCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    broken = _context()
    case.apply(broken, monkeypatch, True)
    harness = make_harness(
        ok_response(), env=broken.env, catalogs=broken.catalogs, clock=broken.clock
    )

    with pytest.raises(AnonymizerUnavailable) as excinfo:
        harness.anonymizer.generate(broken.request)

    message = str(excinfo.value).lower()
    assert message, "el mensaje debe nombrar el paso que falló"
    assert any(word in message for word in case.step_words), message
    for entity in [*SEEDED["entidades"], TESTIMONY_CANARY, KEY_CANARY]:
        assert entity.lower() not in message
    assert not hasattr(excinfo.value, "call"), "AnonymizerUnavailable nunca lleva ModelCall"
    assert harness.transport.request_count == 0, "no debe salir ninguna petición"

    monkeypatch.undo()
    fixed = _context()
    case.apply(fixed, monkeypatch, False)
    control = make_harness(ok_response(), env=fixed.env, catalogs=fixed.catalogs, clock=fixed.clock)
    control.anonymizer.generate(fixed.request)
    assert control.transport.request_count == 1, (
        "el control positivo debe enviar exactamente una vez"
    )


def test_an_unexpected_error_after_sending_is_a_provider_error_carrying_its_model_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(generate_module, "restore", boom)
    harness = make_harness(ok_response())

    with pytest.raises(ProviderError) as excinfo:
        harness.anonymizer.generate(make_request())

    assert harness.transport.request_count == 1
    assert excinfo.value.call.anonymized is True
    assert not any(
        e in text for text in exception_texts(excinfo.value) for e in SEEDED["entidades"]
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "exito",
        "error_del_proveedor",
        "restauracion_que_lanza",
        "regla_que_lanza",
        "error_de_serializacion",
        "error_al_construir_la_tabla",
    ],
)
def test_br18_the_mask_table_is_emptied_on_success_and_on_every_error_branch(
    scenario: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    tables: list[masking.MaskTable] = []

    class RecordingTable(masking.MaskTable):
        def __init__(self) -> None:
            super().__init__()
            tables.append(self)

    monkeypatch.setattr(masking, "MaskTable", RecordingTable)
    response = load_anthropic("error_503") if scenario == "error_del_proveedor" else ok_response()
    if scenario == "restauracion_que_lanza":
        monkeypatch.setattr(generate_module, "restore", boom)
    if scenario == "regla_que_lanza":
        monkeypatch.setattr(detection, "apply_rules", boom)
    if scenario == "error_de_serializacion":
        monkeypatch.setattr(masking, "serialize_messages", boom)
    if scenario == "error_al_construir_la_tabla":
        monkeypatch.setattr(masking, "build_table", boom)
    harness = make_harness(response)

    try:
        harness.anonymizer.generate(make_request())
    except ModelCallError:
        pass  # Cada rama termina en un error tipado de C13; cualquier otra excepción falla la prueba.

    if scenario in {"exito", "error_del_proveedor", "restauracion_que_lanza"}:
        assert tables, "la llamada debía haber creado una tabla"
    assert all(table.is_empty for table in tables), "la tabla debe quedar vacía al terminar"
