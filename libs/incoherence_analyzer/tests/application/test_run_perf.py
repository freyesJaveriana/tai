"""Rendimiento de la corrida (R-09): 2 000 turnos en 6 s o menos con el doble del gateway.

La meta es 2 s; el margen es 3× para la CI. Se mide con `time.perf_counter` toda la llamada a
`analyze`: validación previa contra C6, juez, filtro con el escáner sobre los 2 000 turnos, el
verificador (directo y permutado) por cada sobreviviente y la validación de la salida.
"""

import time

from veridicus_model_gateway.testing.fake import FakeModelGateway

from tests.support import finding, make_config, make_entrada
from veridicus_incoherence_analyzer.api import analyze

TURNS = 2000
LIMIT_S = 6.0


def _turns() -> list[dict[str, object]]:
    return [
        {
            "n": n,
            "hablante": "ENT" if n % 2 else "TEST",
            "texto": f"Turno {n}: el relato dice que el dia {n % 28 + 1} estuvo en el lugar numero {n}.",
        }
        for n in range(1, TURNS + 1)
    ]


def test_two_thousand_turns_run_in_six_seconds_or_less() -> None:
    turns = _turns()
    texts = {turn["n"]: str(turn["texto"]) for turn in turns}
    findings = [
        finding(
            hecho=f"Hecho {k}",
            a=(2 * k, texts[2 * k]),
            b=(TURNS - 2 * k, texts[TURNS - 2 * k]),
        )
        for k in range(1, 21)
    ]
    gateway = FakeModelGateway(findings=findings)
    config = make_config()
    entrada = make_entrada(turns)

    started = time.perf_counter()
    salida = analyze(entrada, config, gateway)
    elapsed = time.perf_counter() - started

    assert salida["estado"] == "ok"
    assert len(salida["hallazgos"]) == 20
    assert len(gateway.requests) == 1 + 20 * 2
    assert elapsed <= LIMIT_S, f"{elapsed:.2f} s con 2 000 turnos"
