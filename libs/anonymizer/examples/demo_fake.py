"""Demostración del anonimizador con el `FakeTransport`: sin red, con una transcripción sintética.

Imprime (1) el cuerpo que saldría hacia el proveedor, que solo lleva marcas; (2) la respuesta ya
restaurada; (3) un destino `openai`, que en B10a falla cerrado con `AnonymizerUnavailable` y deja
`peticiones=0`.

Es evidencia, no garantía: la fuga cero la prueba `tests/guards/test_autonomia_04_payload.py` (R-13).
Todos los nombres, lugares y números de abajo son inventados.

Uso: `uv run --frozen --offline --directory libs/anonymizer python examples/demo_fake.py`.
"""

import json
from dataclasses import replace

from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    Destination,
    GenerateRequest,
    Message,
)

from veridicus_anonymizer import build_anonymizer
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
# Clave inventada: solo sirve para que el módulo vea que la variable existe.
ENV = {KEY_REF: "clave-sintetica-de-la-demostracion"}

TURNS = [
    {"turno": 1, "hablante": "TES", "texto": "Casilda Roncancio llegó a Villa Rocamora el martes."},
    {"turno": 2, "hablante": "TES", "texto": "Luego Aurelio Benavides la llamó al 3105550123."},
]
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["resumen"],
    "properties": {"resumen": {"type": "string"}},
}
# El proveedor sintético repite las marcas que recibió: `[ENTIDAD_1]` es la primera persona y
# `[LUGAR_1]` el primer lugar del cuerpo seudonimizado.
PROVIDER_TEXT = {"resumen": "[ENTIDAD_1] estuvo en [LUGAR_1]."}


def provider_envelope(payload: dict[str, str]) -> dict[str, object]:
    """Sobre de la Messages API con la salida estructurada, como lo graba el transporte falso."""
    return {
        "id": "msg_demostracion_0001",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-5-5",
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 120, "output_tokens": 18},
    }


def make_request(destination: Destination) -> GenerateRequest:
    return GenerateRequest(
        role="judge",
        destination_slot="primary",
        profile_name="demo-sintetico",
        profile_sha256="a" * 64,
        destination=destination,
        messages=[
            Message("system", "Eres un analista de coherencia. Responde solo con el JSON."),
            Message("user", json.dumps({"turnos": TURNS}, ensure_ascii=False)),
        ],
        schema=SCHEMA,
        timeout_s=30.0,
    )


def main() -> None:
    destination = Destination(
        provider="anthropic",
        model="claude-sonnet-5-5",
        scope="external",
        api_key_ref=KEY_REF,
        parameters={"effort": "medium"},
    )

    print("== 1. Destino anthropic: lo que saldría ==")
    transport = FakeTransport(FakeResponse.ok_json(provider_envelope(PROVIDER_TEXT)))
    anonymizer = build_anonymizer(ENV, transport)
    result = anonymizer.generate(make_request(destination))
    sent = json.loads(transport.requests[0].body)
    masked_user = json.loads(sent["messages"][0]["content"])
    for turn in masked_user["turnos"]:
        print(f"  turno {turn['turno']}: {turn['texto']}")
    print(f"  peticiones={transport.request_count}")

    print("== 2. Respuesta restaurada ==")
    print(f"  {result.content['resumen']}")
    print(f"  anonymized={result.call.anonymized}")

    print("== 3. Destino openai: falla cerrado en B10a ==")
    closed = FakeTransport()
    anonymizer = build_anonymizer(ENV, closed)
    blocked = replace(
        destination, provider="openai", model="gpt-demo", api_key_ref="VERIDICUS_OPENAI_API_KEY"
    )
    try:
        anonymizer.generate(make_request(blocked))
    except AnonymizerUnavailable as error:
        print(f"  AnonymizerUnavailable: {error}")
    print(f"  peticiones={closed.request_count}")


if __name__ == "__main__":
    main()
