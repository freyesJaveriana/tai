"""De punta a punta con el doble (paso 12; AC11.3.3, AC11.3.7).

La CLI corre por su punto de entrada (`run`) con el `Anonymizer` **real** de B10a y el `FakeTransport`
de B10a, con respuestas grabadas del juez y del verificador, sobre transcripciones sintéticas de
`tests/fixtures/`. Ninguna prueba abre red (`--disable-socket`).
"""

import json
from pathlib import Path
from typing import Any

import pytest
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

from tests.support import (
    ENTITIES,
    PROFILE,
    ScriptedProvider,
    anthropic_envelope,
    assert_no_entity_in_payload,
    c6_problems,
    echo_finding,
    env,
    finding,
    write_transcription,
)
from veridicus_incoherence_analyzer.cli.main import run

pytestmark = pytest.mark.cli

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
QUOTE_A = "Esa mañana salí de la casa a las ocho y caminé hasta el mercado."
QUOTE_B = "Esa mañana no salí de la casa, me quedé adentro hasta la tarde."
ALTERED_B = "Esa mañana no salí de la casa, me quedé adentro toda la tarde."


def _recorded(payload: object) -> FakeResponse:
    """Una respuesta grabada de la Messages API con la salida estructurada del modelo."""
    return FakeResponse.ok_json(anthropic_envelope(payload))


def _judge(*findings: dict[str, Any]) -> FakeResponse:
    return _recorded({"hallazgos": list(findings)})


def _verdict(confirms: bool = True) -> FakeResponse:
    return _recorded({"confirma": confirms})


def _analyze(entrada: Path, out: Path, transport: Any) -> int:
    return run(
        ["analyze", str(entrada), "--perfil", PROFILE, "--salida", str(out)],
        env(),
        transport=transport,
    )


def _written(out: Path, name: str) -> dict[str, Any]:
    document: dict[str, Any] = json.loads((out / name).read_text("utf-8"))
    return document


def test_a_seeded_contradiction_produces_a_finding_with_its_two_verified_quotes(
    tmp_path: Path,
) -> None:
    out = tmp_path / "salida"
    transport = FakeTransport(
        _judge(finding(a=(2, QUOTE_A), b=(4, QUOTE_B))), _verdict(), _verdict()
    )

    code = _analyze(FIXTURES / "contradiccion.json", out, transport)

    salida = _written(out, "contradiccion.salida.json")
    assert code == 0
    assert transport.request_count == 3, "juez, verificador y verificador permutado"
    assert salida["estado"] == "ok"
    assert len(salida["hallazgos"]) >= 1
    cited = json.dumps(salida["hallazgos"][0], ensure_ascii=False)
    assert QUOTE_A in cited and QUOTE_B in cited, "las dos citas literales, verificadas"
    assert c6_problems(salida) == []
    assert (out / "AVISO.txt").is_file()
    assert not (out / "reporte.json").exists(), "B11a no escribe reporte.json (CG-U11-13)"


def test_a_coherent_account_produces_no_findings_and_exit_0(tmp_path: Path) -> None:
    out = tmp_path / "salida"
    transport = FakeTransport(_judge())

    code = _analyze(FIXTURES / "coherente.json", out, transport)

    salida = _written(out, "coherente.salida.json")
    assert code == 0
    assert transport.request_count == 1, "sin candidatos no hay verificador"
    assert salida["estado"] == "ok"
    assert salida["hallazgos"] == []
    assert c6_problems(salida) == []


def test_a_judge_answer_with_an_altered_quote_is_discarded_and_nothing_leaves_with_it(
    tmp_path: Path,
) -> None:
    out = tmp_path / "salida"
    transport = FakeTransport(_judge(finding(a=(2, QUOTE_A), b=(4, ALTERED_B))))

    code = _analyze(FIXTURES / "contradiccion.json", out, transport)

    salida = _written(out, "contradiccion.salida.json")
    assert code == 0
    assert salida["estado"] == "ok"
    assert salida["hallazgos"] == [], "AUTONOMIA-05: una cita alterada no sale"
    assert len(salida["registro"]["descartes"]) == 1
    assert ALTERED_B not in json.dumps(salida["hallazgos"], ensure_ascii=False)
    assert transport.request_count == 1, "el candidato descartado no llega al verificador"
    assert c6_problems(salida) == []


def test_the_step_3_cli_with_seeded_entities_restores_the_quotes_and_leaks_nothing(
    tmp_path: Path,
) -> None:
    entrada = write_transcription(tmp_path)
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = _analyze(entrada, out, provider)

    salida = _written(out, "SINT-0001.salida.json")
    assert code == 0
    assert provider.request_count == 3
    assert_no_entity_in_payload(provider, ENTITIES)
    assert len(salida["hallazgos"]) == 1
    cited = json.dumps(salida["hallazgos"][0], ensure_ascii=False)
    assert "Casilda Roncancio" in cited and "Puerto Altamira" in cited, "citas restauradas"
    assert c6_problems(salida) == []
