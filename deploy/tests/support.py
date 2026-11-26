"""Ayudas de las pruebas de la demo: entorno, respuestas guionadas del proveedor y rutas.

Todo es sintético. La clave canario es inventada y nunca es una clave real.
"""

import json
import shutil
from pathlib import Path
from typing import Any

from veridicus_anonymizer.testing.fake_transport import FakeResponse

DEPLOY = Path(__file__).resolve().parents[1]
ENTRADA_DIR = DEPLOY / "demo-analyzer" / "entrada"

KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
KEY_CANARY = "sk-sintetico-canario-7f3a91c2d4e5"
TURN_CANARY = "CANARIO-TURNO-QUE-NO-ES-CITA-5d2e"
MODEL = "claude-sonnet-5-5"

# Citas literales de deploy/demo-analyzer/entrada/contradiccion.json (turnos 4 y 10).
QUOTE_A = (
    "Por la mañana subí al pueblo de San Isidro a vender queso y regresé a la finca "
    "a las cuatro de la tarde."
)
QUOTE_B = (
    "Yo nunca bajé a la finca ese día, pasé toda la jornada en San Isidro hasta que oscureció."
)
HECHO = "Dónde estuvo la compareciente durante la tarde de la crecida"


def env(entrada: Path, salida: Path, **extra: str) -> dict[str, str]:
    """Entorno de una corrida: clave canario, plazo de 300 s y las dos rutas de la demo."""
    return {
        KEY_REF: KEY_CANARY,
        "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "300",
        "VERIDICUS_DEMO_ENTRADA": str(entrada),
        "VERIDICUS_DEMO_SALIDA": str(salida),
        **extra,
    }


def stage_input(tmp_path: Path, *names: str) -> Path:
    """Copia entradas de la demo a un directorio nuevo y devuelve ese directorio."""
    directory = tmp_path / "entrada"
    directory.mkdir()
    for name in names:
        shutil.copy(ENTRADA_DIR / f"{name}.json", directory / f"{name}.json")
    return directory


def anthropic_envelope(payload: object) -> dict[str, Any]:
    """Sobre de la Messages API con el texto de la salida estructurada."""
    return {
        "id": "msg_sintetico_0001",
        "type": "message",
        "role": "assistant",
        "model": MODEL,
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 412, "output_tokens": 37},
    }


def recorded(payload: object) -> FakeResponse:
    return FakeResponse.ok_json(anthropic_envelope(payload))


def finding(
    a: tuple[int, str] = (4, QUOTE_A), b: tuple[int, str] = (10, QUOTE_B)
) -> dict[str, Any]:
    """Un candidato del juez con la forma del esquema local."""
    return {
        "hecho": HECHO,
        "tipo": "lugar",
        "cita_a": {"cita": a[1], "turno": f"T{a[0]}"},
        "cita_b": {"cita": b[1], "turno": f"T{b[0]}"},
        "observaciones": "Las dos citas ubican a la compareciente en lugares distintos a la misma hora.",
    }


def judge(*findings: dict[str, Any]) -> FakeResponse:
    return recorded({"hallazgos": list(findings)})


def verdict(confirms: bool = True) -> FakeResponse:
    return recorded({"confirma": confirms})
