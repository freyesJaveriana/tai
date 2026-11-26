"""Plazo y cancelación de la corrida (BR7.2, PD-10), con reloj simulado.

La cancelación se consulta antes de cada llamada y el plazo antes y después de cada llamada. Un plazo
agotado da `tiempo_agotado` y nunca un resultado parcial; una cancelación lanza `CancelledError` sin
salida.
"""

from collections.abc import Callable

import pytest
from veridicus_errors import CancelledError

from tests.support import (
    ScriptedGateway,
    assert_error_output,
    env,
    finding,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.application import deadline
from veridicus_incoherence_analyzer.application.deadline import DeadlineExpired, RunClock

SHORT = env(
    VERIDICUS_LIMIT_RUN_DEADLINE_INCREMENTAL_S="50", VERIDICUS_LIMIT_RUN_DEADLINE_FINAL_S="100"
)


def _clock(*values: float) -> Callable[[], float]:
    """Un reloj que devuelve `values` en orden y después repite el último."""
    pending = list(values)

    def now() -> float:
        return pending.pop(0) if len(pending) > 1 else pending[0]

    return now


def _patch(monkeypatch: pytest.MonkeyPatch, *values: float) -> None:
    monkeypatch.setattr(deadline, "monotonic", _clock(*values))


# --- RunClock ----------------------------------------------------------------------------------------


def test_the_timeout_of_a_call_is_the_smaller_of_the_call_limit_and_the_time_left(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 10)
    clock = RunClock(300, 100)

    assert clock.before_call() == 90  # quedan 100 - 10 = 90 s, menos que los 300 s de la llamada


def test_the_call_limit_wins_when_there_is_time_left(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, 0, 10)

    assert RunClock(30, 100).before_call() == 30


def test_without_time_left_nothing_is_called(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, 0, 100)

    with pytest.raises(DeadlineExpired):
        RunClock(300, 100).before_call()


def test_a_call_that_ends_after_the_deadline_expires_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 99, 100)
    clock = RunClock(300, 100)

    clock.before_call()
    with pytest.raises(DeadlineExpired):
        clock.after_call()


def test_a_call_that_ends_before_the_deadline_does_not_expire_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 99.9)

    RunClock(300, 100).after_call()


def test_cancellation_is_checked_before_the_deadline() -> None:
    clock = RunClock(300, 100, cancelled=lambda: True)

    with pytest.raises(CancelledError):
        clock.before_call()


def test_a_cancel_check_that_says_no_lets_the_call_go() -> None:
    assert RunClock(300, 100, cancelled=lambda: False).before_call() > 0


# --- analyze ----------------------------------------------------------------------------------------


def test_the_request_carries_the_smaller_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, 0, 40, 41)  # inicio, antes de la llamada, después de la llamada
    gateway = ScriptedGateway()

    analyze(make_entrada(), make_config(SHORT), gateway)

    assert gateway.requests[0].timeout_s == 60.0  # 100 - 40


def test_the_request_carries_the_call_limit_when_the_run_has_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 1)
    gateway = ScriptedGateway()

    analyze(make_entrada(), make_config(), gateway)

    assert gateway.requests[0].timeout_s == 300.0


def test_with_the_deadline_spent_before_the_first_call_nothing_is_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 100)
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), make_config(SHORT), gateway)

    assert_error_output(salida, "tiempo_agotado")
    assert gateway.requests == []
    assert salida["registro"]["llamadas"] == []


def test_with_the_deadline_spent_between_two_calls_the_second_is_not_made(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 1, 2, 100)  # inicio, antes y después del juez, antes del verificador
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), make_config(SHORT), gateway)

    assert_error_output(salida, "tiempo_agotado")
    assert gateway.roles() == ["judge"]
    assert [llamada["papel"] for llamada in salida["registro"]["llamadas"]] == ["juez"]


def test_a_call_that_returns_after_the_deadline_ends_the_run_with_nothing_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 1, 100)  # el juez devuelve pasado el plazo
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), make_config(SHORT), gateway)

    assert_error_output(salida, "tiempo_agotado")
    assert gateway.roles() == ["judge"]
    assert len(salida["registro"]["llamadas"]) == 1, "la llamada que volvió sí cuenta"


def test_the_incident_wins_over_a_deadline_that_expired_on_the_same_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, 0, 1, 100)
    gateway = ScriptedGateway(findings=[finding()], anonymized_from=1)

    salida = analyze(make_entrada(), make_config(SHORT), gateway)

    assert_error_output(salida, "incidente_anonimizacion")


def test_a_cancellation_after_the_first_call_raises_and_makes_no_more_calls() -> None:
    gateway = ScriptedGateway(findings=[finding()])

    with pytest.raises(CancelledError):
        analyze(
            make_entrada(), make_config(), gateway, cancelled=lambda: len(gateway.requests) >= 1
        )

    assert gateway.roles() == ["judge"]


def test_a_cancellation_before_the_first_call_makes_no_call() -> None:
    gateway = ScriptedGateway(findings=[finding()])

    with pytest.raises(CancelledError):
        analyze(make_entrada(), make_config(), gateway, cancelled=lambda: True)

    assert gateway.requests == []


def test_a_cancel_check_that_never_fires_changes_nothing() -> None:
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), make_config(), gateway, cancelled=lambda: False)

    assert salida["estado"] == "ok"
    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]
