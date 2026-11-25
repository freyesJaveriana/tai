"""AUTONOMIA-04, fallo cerrado (AC11.3.3, AC11.3.6, F7, BR1.8, BR2.1, BR2.6, PD-9).

Cada caso rompe UNA condición y comprueba: `AnonymizerUnavailable` sin `ModelCall`, un mensaje
que nombra el paso sin ningún valor (ni entidad, ni *canary*, ni modelo, dominio o nombre de la
clave) y el transporte con 0 peticiones. El control positivo repite el mismo escenario con esa
sola condición corregida y exige exactamente 1 petición.
"""

import pytest
from veridicus_contracts.model_calls import AnonymizerUnavailable, ModelCallError, ProviderError

from tests.support import (
    FAIL_CLOSED_CASES,
    KEY_CANARY,
    TESTIMONY_CANARY,
    FailClosedCase,
    boom,
    exception_texts,
    install_context,
    leaked_values,
    load_anthropic,
    load_seeded,
    make_ctx,
    make_harness,
    make_request,
    ok_response,
    turns_of,
)
from veridicus_anonymizer.application import generate as generate_module
from veridicus_anonymizer.domain import detection, masking

SEEDED = load_seeded()
TURNOS = [
    *turns_of(SEEDED),
    {"turno": 99, "hablante": "TES", "texto": f"Dijo {TESTIMONY_CANARY} en voz baja."},
]


@pytest.mark.parametrize("case", FAIL_CLOSED_CASES, ids=[c.name for c in FAIL_CLOSED_CASES])
def test_fails_closed_without_a_call_and_the_fixed_scenario_sends_exactly_one(
    case: FailClosedCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    broken = make_ctx(TURNOS)
    case.apply(broken, monkeypatch, True)
    install_context(broken, monkeypatch)
    harness = make_harness(ok_response(), env=broken.env)

    with pytest.raises(AnonymizerUnavailable) as excinfo:
        harness.anonymizer.generate(broken.request)

    message = str(excinfo.value).lower()
    assert message, "el mensaje debe nombrar el paso que falló"
    assert any(word in message for word in case.step_words), message
    for value in [*SEEDED["entidades"], TESTIMONY_CANARY, KEY_CANARY, *leaked_values(broken)]:
        assert value.lower() not in message, "el mensaje nombra un valor"
    assert not hasattr(excinfo.value, "call"), "AnonymizerUnavailable nunca lleva ModelCall"
    assert harness.transport.request_count == 0, "no debe salir ninguna petición"

    monkeypatch.undo()
    fixed = make_ctx(TURNOS)
    case.apply(fixed, monkeypatch, False)
    install_context(fixed, monkeypatch)
    control = make_harness(ok_response(), env=fixed.env)
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


# Escenarios de BR1.8: `con_entradas` dice si la tabla ya tiene formas cuando la llamada termina.
SCENARIOS = {
    "exito": True,
    "error_del_proveedor": True,
    "restauracion_que_lanza": True,
    "error_de_serializacion": True,
    "regla_que_lanza": False,
    "error_al_construir_la_tabla": False,
}


@pytest.mark.parametrize("scenario", list(SCENARIOS), ids=list(SCENARIOS))
def test_br18_the_mask_table_is_emptied_on_success_and_on_every_error_branch(
    scenario: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    tables: list[masking.MaskTable] = []
    sizes_at_clear: list[int] = []

    class RecordingTable(masking.MaskTable):
        def __init__(self) -> None:
            super().__init__()
            tables.append(self)

        def clear(self) -> None:
            sizes_at_clear.append(len(self))
            super().clear()

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

    if SCENARIOS[scenario]:
        assert tables, "la llamada debía haber creado una tabla"
        assert sizes_at_clear, "la tabla debía vaciarse con clear()"
        assert max(sizes_at_clear) >= 1, "la tabla debía tener formas antes de vaciarse"
    assert all(table.is_empty for table in tables), "la tabla debe quedar vacía al terminar"
