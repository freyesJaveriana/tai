"""Las fuentes literales del escáner son los textos de todos los turnos (BR9.3, F-06 de U11-T01).

Un tramo «…» de `hecho` u `observaciones` que aparece literal en cualquier turno de la entrada, esté
o no citado, no cuenta como vocabulario prohibido.
"""

from typing import Any

import pytest

from tests.support import (
    ScriptedGateway,
    c6_problems,
    default_turns,
    discard_reasons,
    finding,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze

UNCITED = "Dijo que eso era falso porque no lo vio."


def _turns() -> list[dict[str, Any]]:
    turns = default_turns()
    turns[2]["texto"] = UNCITED  # T3: un turno que ningún hallazgo cita
    return turns


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_a_literal_span_of_an_uncited_turn_is_not_scanned(campo: str) -> None:
    candidate = finding()  # cita T2 y T4
    candidate[campo] = "El relato de T3 dice «era falso» y los otros dos turnos lo contradicen."
    gateway = ScriptedGateway(findings=[candidate])

    salida = analyze(make_entrada(_turns()), make_config(), gateway)

    assert salida["estado"] == "ok"
    assert len(salida["hallazgos"]) == 1
    assert discard_reasons(salida) == [], "sin descartes"
    assert c6_problems(salida) == []


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_control_the_same_span_without_a_turn_that_has_it_is_discarded(campo: str) -> None:
    candidate = finding()
    candidate[campo] = "El relato de T3 dice «era falso» y los otros dos turnos lo contradicen."
    gateway = ScriptedGateway(findings=[candidate])

    salida = analyze(make_entrada(), make_config(), gateway)  # ningún turno trae «era falso»

    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["vocabulario_prohibido"]
