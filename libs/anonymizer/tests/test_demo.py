"""La demostración `examples/demo_fake.py` es evidencia, no garantía (R-13): esta prueba solo evita
que se rompa en silencio y comprueba que su cuerpo de salida lleva marcas y no entidades."""

import json
import runpy
from pathlib import Path

import pytest

DEMO = Path(__file__).parent.parent / "examples" / "demo_fake.py"
INVENTED_ENTITIES = (
    "Casilda",
    "Roncancio",
    "Villa",
    "Rocamora",
    "Aurelio",
    "Benavides",
    "3105550123",
)


def run_demo(capsys: pytest.CaptureFixture[str]) -> str:
    runpy.run_path(str(DEMO), run_name="__main__")
    return capsys.readouterr().out


def test_the_body_that_would_leave_only_carries_markers(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run_demo(capsys)
    leaving = out.split("== 2.")[0]
    assert "[ENTIDAD_1]" in leaving
    assert "peticiones=1" in leaving
    # F-05: se imprime el cuerpo serializado completo, no solo el texto de los turnos.
    line = next(row for row in leaving.splitlines() if row.strip().startswith("cuerpo: "))
    body = json.loads(line.strip().removeprefix("cuerpo: "))
    assert {"model", "system", "messages", "output_config"} <= set(body)
    assert body["system"].startswith("Eres un analista")
    for entity in INVENTED_ENTITIES:
        assert entity not in leaving


def test_the_reply_is_restored_and_the_unsupported_provider_fails_closed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = run_demo(capsys)
    assert "Casilda Roncancio estuvo en Villa Rocamora." in out.split("== 2.")[1].split("== 3.")[0]
    closed = out.split("== 3.")[1]
    assert "AnonymizerUnavailable" in closed
    assert "peticiones=0" in closed
