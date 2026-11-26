"""Demostración del analizador con el `FakeTransport` de B10a: sin red y con una entrevista sintética.

Corre la CLI (`cli.main.run`) con el `Anonymizer` real y respuestas grabadas del juez y del verificador:
el juez propone un candidato con sus dos citas literales y el verificador lo confirma dos veces (en
orden y permutado). Imprime la ruta de la salida `.salida.json` y el número de hallazgos.

Es evidencia, no garantía: las guardias las prueban `tests/guards/` y `tests/e2e/`. La entrevista, la
clave y las respuestas de abajo son inventadas; no hay ningún dato real.

Uso, desde la raíz del repositorio:
`uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli python examples/demo_fake.py`.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

from veridicus_incoherence_analyzer.cli.main import run

PROFILE = "demo-anthropic"
# Clave inventada: solo sirve para que el perfil de demostración arranque. Nunca sale por la red.
ENV = {
    "VERIDICUS_ANTHROPIC_API_KEY": "sk-sintetico-canario-7f3a91c2d4e5",
    "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "300",
}
QUOTE_A = "Esa mañana salí de la casa a las ocho y caminé hasta el mercado."
QUOTE_B = "Esa mañana no salí de la casa, me quedé adentro hasta la tarde."
TRANSCRIPTION = {
    "entrevista": "SINT-DEMO-01",
    "origen": "sintetico",
    "turnos": [
        {"n": 1, "hablante": "ENT", "texto": "¿Qué hizo usted esa mañana?"},
        {"n": 2, "hablante": "TEST", "pagina": 1, "texto": QUOTE_A},
        {"n": 3, "hablante": "ENT", "texto": "¿Y después qué pasó?"},
        {"n": 4, "hablante": "TEST", "pagina": 2, "texto": QUOTE_B},
    ],
}
CANDIDATE = {
    "hecho": "Si salió de la casa esa mañana",
    "tipo": "lugar",
    "cita_a": {"cita": QUOTE_A, "turno": "T2"},
    "cita_b": {"cita": QUOTE_B, "turno": "T4"},
    "observaciones": "Una cita dice que salió de la casa y la otra que se quedó adentro.",
}


def _recorded(payload: object) -> FakeResponse:
    """Una respuesta grabada de la Messages API con la salida estructurada del modelo."""
    envelope: dict[str, Any] = {
        "id": "msg_demostracion_0001",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-5-5",
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 120, "output_tokens": 18},
    }
    return FakeResponse.ok_json(envelope)


def main() -> int:
    transport = FakeTransport(
        _recorded({"hallazgos": [CANDIDATE]}),
        _recorded({"confirma": True}),
        _recorded({"confirma": True}),
    )
    with tempfile.TemporaryDirectory(prefix="veridicus-demo-") as work:
        entrada = Path(work) / "entrevista-sintetica.json"
        entrada.write_text(json.dumps(TRANSCRIPTION, ensure_ascii=False), encoding="utf-8")
        salida_dir = Path(work) / "salida"
        code = run(
            ["analyze", str(entrada), "--perfil", PROFILE, "--salida", str(salida_dir)],
            ENV,
            transport=transport,
        )
        if code != 0:
            print(f"la corrida terminó con el código {code}", file=sys.stderr)
            return code
        salida = salida_dir / "entrevista-sintetica.salida.json"
        document = json.loads(salida.read_text(encoding="utf-8"))
        print(f"salida: {salida.name} (en {salida_dir}, se borra al terminar la demostración)")
        print(f"estado: {document['estado']}")
        print(f"hallazgos: {len(document['hallazgos'])}")
        print(f"llamadas al proveedor falso: {transport.request_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
