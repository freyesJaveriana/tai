"""Entradas sintéticas de la demo (CA-1): C6 válidas, sintéticas y con relato suficiente."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from support import ENTRADA_DIR, QUOTE_A, QUOTE_B
from veridicus_contracts.registry import BASE_URI, build_registry, validator_for

ENTRADA_URI = BASE_URI + "veridicus/contracts/analyzer/v1/entrada"
NAMES = ["coherente", "contradiccion"]


def _document(name: str) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads((ENTRADA_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return loaded


def _problems(transcripcion: dict[str, Any]) -> list[str]:
    """Problemas de la transcripción envuelta en la entrada C6 que arma la CLI."""
    entrada = {
        "contrato": "1.0.0",
        "transcripcion": transcripcion,
        "modo": "final",
        "perfil": "demo-anthropic",
    }
    validator = validator_for(build_registry(), ENTRADA_URI)
    return [error.message for error in validator.iter_errors(entrada)]


def test_the_demo_input_directory_has_exactly_the_two_synthetic_files() -> None:
    found = sorted(path.stem for path in ENTRADA_DIR.glob("*.json"))

    assert found == NAMES


@pytest.mark.parametrize("name", NAMES)
def test_each_input_is_a_valid_synthetic_c6_transcription(name: str) -> None:
    document = _document(name)

    assert _problems(document) == []
    assert document["origen"] == "sintetico"
    assert "consentimiento" not in document, "una entrada sintética no lleva consentimiento"


@pytest.mark.parametrize("name", NAMES)
def test_each_input_has_at_least_six_turns_of_the_witness_and_consecutive_numbers(
    name: str,
) -> None:
    turns = _document(name)["turnos"]

    assert sum(1 for turn in turns if turn["hablante"] == "TEST") >= 6
    assert [turn["n"] for turn in turns] == list(range(1, len(turns) + 1))


def test_the_seeded_contradiction_carries_both_quotes_in_their_turns() -> None:
    by_number = {turn["n"]: turn for turn in _document("contradiccion")["turnos"]}

    assert by_number[4]["hablante"] == "TEST" and by_number[4]["texto"] == QUOTE_A
    assert by_number[10]["hablante"] == "TEST" and by_number[10]["texto"] == QUOTE_B


def test_the_coherent_account_does_not_repeat_the_second_quote() -> None:
    texts = [turn["texto"] for turn in _document("coherente")["turnos"]]

    assert QUOTE_A in texts
    assert QUOTE_B not in texts


def test_negative_control_a_turn_without_text_fails_the_validation() -> None:
    document = copy.deepcopy(_document("contradiccion"))
    del document["turnos"][3]["texto"]

    assert _problems(document) != []


def test_negative_control_a_witness_speaker_outside_the_enum_fails_the_validation() -> None:
    document = copy.deepcopy(_document("coherente"))
    document["turnos"][1]["hablante"] = "OTRO"

    assert _problems(document) != []


def test_the_inputs_are_plain_json_files_under_the_deploy_tree() -> None:
    assert ENTRADA_DIR == Path(__file__).resolve().parents[1] / "demo-analyzer" / "entrada"
