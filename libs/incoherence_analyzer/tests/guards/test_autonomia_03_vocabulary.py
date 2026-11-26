"""AUTONOMIA-03, vocabulario prohibido y aviso (BR9.1 a BR9.5; AC5.5.1, AC5.5.2, VE-01, VE-02).

El escáner descarta un candidato con vocabulario de C8 en `hecho` u `observaciones` y no toca las
citas literales; la salida no tiene ningún campo de veracidad; la CLI avisa o no corre.
Las pruebas que pasan por `cli.main.run` llevan `@pytest.mark.cli`.
"""

from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
from veridicus_anonymizer.api import build_anonymizer
from veridicus_contracts.loaders import load_file
from veridicus_errors import ConfigInvalidProfileError
from veridicus_integrity_policy import notice
from veridicus_model_gateway.gateway import build

from tests.support import (
    ScriptedGateway,
    ScriptedProvider,
    all_keys,
    c6_problems,
    default_turns,
    discard_reasons,
    echo_finding,
    env,
    finding,
    make_config,
    make_entrada,
    write_transcription,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.application.messages import load_response_schema
from veridicus_incoherence_analyzer.cli.main import run


def _forbidden_field_names() -> set[str]:
    """`categories_forbidden_in_schemas` de C8, leídas de `veridicus_contracts` (F-04)."""
    document = load_file(
        files("veridicus_contracts") / "integrity" / "forbidden-vocabulary.v2.yaml"
    )
    return {str(name) for name in document["categories_forbidden_in_schemas"]}


FORBIDDEN_FIELD_NAMES = _forbidden_field_names()


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_forbidden_vocabulary_discards_the_candidate_and_the_run_goes_on(campo: str) -> None:
    config = make_config()
    flagged = finding(hecho="Hecho distinto")
    flagged[campo] = "La persona miente sobre este punto"
    gateway = ScriptedGateway(findings=[flagged, finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert salida["estado"] == "ok"
    assert discard_reasons(salida) == ["vocabulario_prohibido"]
    assert len(salida["hallazgos"]) == 1, "el candidato válido sale"
    assert c6_problems(salida) == []


def test_a_forbidden_term_inside_a_literal_quote_does_not_discard_the_candidate() -> None:
    config = make_config()
    turns = default_turns()
    turns[1]["texto"] = "Dijo que eso era falso porque estaba en la casa de su hermana."
    gateway = ScriptedGateway(findings=[finding(a=(2, turns[1]["texto"]))])

    salida = analyze(make_entrada(turns), config, gateway)

    assert len(salida["hallazgos"]) == 1
    assert salida["registro"]["descartes"] == []


LITERAL_TURN = "Dijo que eso era falso porque estaba en la casa de su hermana."


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_a_quoted_span_that_is_literal_in_a_turn_is_not_scanned_in_hecho_or_observaciones(
    campo: str,
) -> None:
    config = make_config()
    turns = default_turns()
    turns[1]["texto"] = LITERAL_TURN
    candidate = finding(a=(2, LITERAL_TURN))
    candidate[campo] = "El relato dice «era falso» y el otro turno lo contradice."
    gateway = ScriptedGateway(findings=[candidate])

    salida = analyze(make_entrada(turns), config, gateway)

    assert salida["estado"] == "ok"
    assert len(salida["hallazgos"]) == 1, "el hallazgo sale"
    assert salida["registro"]["descartes"] == []


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_a_quoted_span_that_is_in_no_turn_is_scanned_and_discards_the_candidate(
    campo: str,
) -> None:
    config = make_config()
    turns = default_turns()
    turns[1]["texto"] = LITERAL_TURN
    candidate = finding(a=(2, LITERAL_TURN))
    candidate[campo] = "El relato dice «miente ahí» y el otro turno lo contradice."
    gateway = ScriptedGateway(findings=[candidate])

    salida = analyze(make_entrada(turns), config, gateway)

    assert salida["estado"] == "ok"
    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["vocabulario_prohibido"]


@pytest.mark.parametrize("role", ["judge", "verifier"])
@pytest.mark.parametrize("kind", ["wire", "local"])
def test_the_response_schemas_have_no_truthfulness_field(role: str, kind: str) -> None:
    schema = load_response_schema(role, kind)  # type: ignore[arg-type]  # motivo: parametrizado

    names: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            names.update(node.get("properties", {}))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)
    assert names.isdisjoint(FORBIDDEN_FIELD_NAMES)


def test_an_output_never_carries_a_truthfulness_field() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    keys = all_keys(salida)
    assert "hallazgos" in keys and "cita_a" in keys, "se recorrió el árbol completo"
    assert keys.isdisjoint(FORBIDDEN_FIELD_NAMES)
    assert "veracidad" not in str(salida).lower()


@pytest.mark.cli
def test_the_notice_and_the_same_family_warning_go_to_stderr_and_to_the_notice_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    aviso = notice.load_notice()
    entrada = write_transcription(tmp_path)
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = run(
        ["analyze", str(entrada), "--perfil", "demo-anthropic", "--salida", str(out)],
        env(),
        transport=provider,
    )

    stderr = capsys.readouterr().err
    notice_file = (out / "AVISO.txt").read_text("utf-8")
    assert code == 0
    for texto in (stderr, notice_file):
        assert aviso.text in texto
        assert aviso.version in texto
        assert "same_family" in texto


@pytest.mark.cli
def test_without_the_notice_the_cli_ends_with_3_and_makes_no_call(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing() -> notice.Notice:
        raise ConfigInvalidProfileError("El aviso de propósito limitado no está disponible.")

    monkeypatch.setattr(notice, "load_notice", missing)
    entrada = write_transcription(tmp_path)
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = run(
        ["analyze", str(entrada), "--perfil", "demo-anthropic", "--salida", str(out)],
        env(),
        transport=provider,
    )

    assert code == 3
    assert provider.request_count == 0
    assert not list(tmp_path.rglob("*.salida.json")), "ninguna salida escrita"
    assert not (out / "AVISO.txt").exists(), "ni siquiera AVISO.txt (BR11.2)"
    assert capsys.readouterr().err, "un mensaje en español nombra el problema"


def test_the_composite_run_through_the_real_anonymizer_emits_no_truthfulness_label() -> None:
    config = make_config()
    provider = ScriptedProvider(echo_finding)
    gateway = build(config, anonymizing_provider=build_anonymizer(env(), provider))

    salida = analyze(make_entrada(), config, gateway)

    assert salida["estado"] == "ok"
    assert c6_problems(salida) == []
    assert "veracidad" not in str(salida).lower()
