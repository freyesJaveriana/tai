"""Máquina de estados de la corrida y fallo cerrado (BR7.1, BR7.6): la precedencia del incidente."""

import pytest
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    InvalidOutput,
    ModelCallError,
    ProviderError,
    Timeout,
)

from tests.support import make_call
from veridicus_incoherence_analyzer.domain.run_state import (
    INCIDENT,
    Phase,
    RunState,
    error_code_for,
    is_incident,
)


def test_a_run_goes_through_the_four_phases_in_order() -> None:
    state = RunState()

    assert state.phase is Phase.JUDGING
    for phase in (Phase.FILTERING, Phase.VERIFYING, Phase.FINALIZING):
        state = state.advance(phase)
        assert state.phase is phase
    assert state.error_code is None
    assert not state.failed


@pytest.mark.parametrize(
    ("start", "target"),
    [
        (Phase.JUDGING, Phase.VERIFYING),
        (Phase.JUDGING, Phase.FINALIZING),
        (Phase.FILTERING, Phase.JUDGING),
        (Phase.VERIFYING, Phase.FILTERING),
        (Phase.FINALIZING, Phase.JUDGING),
    ],
)
def test_a_phase_cannot_skip_or_go_back(start: Phase, target: Phase) -> None:
    with pytest.raises(ValueError, match="transición"):
        RunState(start).advance(target)


def test_a_failed_run_cannot_advance() -> None:
    state = RunState().fail("proveedor")

    with pytest.raises(ValueError, match="transición"):
        state.advance(Phase.FILTERING)


@pytest.mark.parametrize("phase", list(Phase))
def test_any_phase_can_fail_closed_with_its_code(phase: Phase) -> None:
    state = RunState(phase).fail("tiempo_agotado")

    assert state.failed
    assert state.phase is Phase.ERROR
    assert state.error_code == "tiempo_agotado"


def test_the_incident_takes_precedence_over_a_previous_error() -> None:
    state = RunState().fail("proveedor").fail(INCIDENT)

    assert state.error_code == INCIDENT


def test_a_later_error_never_replaces_the_incident() -> None:
    state = RunState().fail(INCIDENT).fail("proveedor").fail("tiempo_agotado")

    assert state.error_code == INCIDENT


def test_without_an_incident_the_first_error_wins() -> None:
    state = RunState().fail("proveedor").fail("tiempo_agotado")

    assert state.error_code == "proveedor"


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (InvalidOutput("x", make_call("judge")), "salida_invalida"),
        (ContentBlocked("x", make_call("judge")), "bloqueo_contenido"),
        (Timeout("x", make_call("judge")), "tiempo_agotado"),
        (ProviderError("x", make_call("judge")), "proveedor"),
        (AnonymizerUnavailable("x"), "anonimizador_no_disponible"),
    ],
    ids=["invalid", "blocked", "timeout", "provider", "unavailable"],
)
def test_each_typed_error_maps_to_its_code(error: ModelCallError, code: str) -> None:
    assert error_code_for(error) == code


def test_a_subclass_of_a_typed_error_keeps_the_code_of_its_parent() -> None:
    class SlowProvider(ProviderError):
        pass

    assert error_code_for(SlowProvider("x", make_call("judge"))) == "proveedor"


def test_an_untyped_model_call_error_is_a_code_defect_and_has_no_code() -> None:
    with pytest.raises(TypeError):
        error_code_for(ModelCallError("sin tipo"))


@pytest.mark.parametrize(
    ("scope", "anonymized", "expected"),
    [
        ("external", False, True),
        ("external", True, False),
        ("local", False, False),
        ("local", True, False),
    ],
)
def test_only_an_external_call_that_came_back_unanonymized_is_an_incident(
    scope: str, anonymized: bool, expected: bool
) -> None:
    assert is_incident(scope, make_call("judge", anonymized=anonymized)) is expected


def test_a_call_that_left_no_record_is_never_an_incident() -> None:
    assert is_incident("external", None) is False
