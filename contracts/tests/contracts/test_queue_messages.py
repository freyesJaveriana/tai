"""Mensajes de cola C2, C3 y C5 (AsyncAPI 3.0): fixtures y reglas de BR1.1–BR1.3, BR2.1, BR2.3.

Verde desde T05. Supuestos que T05 cumple:
- cada AsyncAPI declara los mensajes `RunRequested` (C2), `RunResult` (C3), `AudioToTranscribe` y
  `TranscriptResult` (C5), y los de entradas fallidas `RunFailed`, `ResultFailed` y `AudioFailed`,
  estrictos y con solo `message_id`, el ID de la corrida o del turno, `attempt` y `code`
  (NFRD-U1-07);
- `effective_config` se valida contra C18 (`profiles/effective-config.v1.yaml`): el caso
  `test_effective_config_de_c2_cumple_c18` lleva el marcador `c18` y pasa a verde en T05 (E-5).
"""

import pytest
from helpers import (
    Caso,
    cargar_fixture,
    comprobar_caso,
    errores_de,
    load_contract,
    puntero_de_mensaje,
    validador_de,
)

from veridicus_contracts.canonical import sha256_jcs
from veridicus_contracts.validators import extract_message_payloads

pytestmark = pytest.mark.asyncapi

RUNS = "queues/runs.v2.yaml"
RESULTS = "queues/results.v2.yaml"
SPEECH = "queues/speech.v2.yaml"

CORRIDAS = [
    Caso("run.valid.yaml", "C2.RunRequested"),
    Caso(
        "run.sin-entrada.yaml",
        "C2.RunRequested",
        "BR2.1",
        ("required", "$", "'entrada'"),
    ),
    Caso(
        "run.mayor-desconocido.yaml",
        "C2.RunRequested",
        "BR1.2",
        ("pattern", "$.schema_version", None),
    ),
    Caso("run.menor-campo-nuevo.yaml", "C2.RunRequested"),
    Caso("failed.valid.yaml", "C2.RunFailed"),
    Caso(
        "failed.con-texto.yaml",
        "C2.RunFailed",
        "NFRD-U1-07",
        ("additionalProperties", "$", "text"),
    ),
]

RESULTADOS = [
    Caso("result.valid.yaml", "C3.RunResult"),
    Caso(
        "result.salida-no-cumple-c6.yaml",
        "C3.RunResult",
        "BR2.3",
        ("required", "$.salida", "'registro'"),
    ),
    Caso("failed.valid.yaml", "C3.ResultFailed"),
    Caso(
        "failed.con-texto.yaml",
        "C3.ResultFailed",
        "NFRD-U1-07",
        ("additionalProperties", "$", "text"),
    ),
]

VOZ = [
    Caso("audio.valid.yaml", "C5.AudioToTranscribe"),
    Caso(
        "audio.sin-obligatorio.yaml",
        "C5.AudioToTranscribe",
        "NFR10.2",
        ("required", "$", "'audio_base64'"),
    ),
    Caso(
        "audio.mayor-desconocido.yaml",
        "C5.AudioToTranscribe",
        "BR1.2",
        ("pattern", "$.schema_version", None),
    ),
    Caso("transcript.valid.yaml", "C5.TranscriptResult"),
    Caso("failed.valid.yaml", "C5.AudioFailed"),
    Caso(
        "failed.con-texto.yaml",
        "C5.AudioFailed",
        "NFRD-U1-07",
        ("additionalProperties", "$", "text"),
    ),
]

TABLAS = [
    ("C2", RUNS, "queues/fixtures/runs", CORRIDAS),
    ("C3", RESULTS, "queues/fixtures/results", RESULTADOS),
    ("C5", SPEECH, "queues/fixtures/speech", VOZ),
]
CASOS = [
    pytest.param(documento, directorio, caso, id=f"{cola}-{caso.archivo}-{caso.contrato}")
    for cola, documento, directorio, casos in TABLAS
    for caso in casos
]


@pytest.mark.parametrize(("documento", "directorio", "caso"), CASOS)
def test_cada_fixture_de_cola_se_acepta_o_se_rechaza_por_su_regla(
    documento: str, directorio: str, caso: Caso
) -> None:
    mensaje = caso.contrato.split(".")[1]
    validador = validador_de(documento, puntero_de_mensaje(documento, mensaje))
    comprobar_caso(directorio, caso, validador)


@pytest.mark.c18
def test_effective_config_de_c2_cumple_c18() -> None:
    """E-5: `effective_config` de C2 cumple C18 y su huella JCS es `config_sha256` (BR9.7)."""
    validador = validador_de("profiles/effective-config.v1.yaml")
    mensaje = cargar_fixture("queues/fixtures/runs/run.valid.yaml", "C2.RunRequested")["payload"]
    assert errores_de(validador, mensaje["effective_config"]) == []
    assert sha256_jcs(mensaje["effective_config"]) == mensaje["config_sha256"]
    de_c18 = cargar_fixture("profiles/fixtures/effective-config.valid.json", "C18.effective-config")
    assert mensaje["effective_config"] == de_c18["payload"]


def test_audio_base64_declara_su_limite_de_c25() -> None:
    """T05: `audio_base64` lleva `x-veridicus-limit: audio_base64_max_chars` (se compara en T14)."""
    cargas = extract_message_payloads(load_contract(SPEECH))
    ruta = next((r for r in cargas if r.endswith("/AudioToTranscribe")), None)
    assert ruta is not None, "mensaje ausente en queues/speech.v2.yaml: AudioToTranscribe"
    campo = cargas[ruta]["properties"]["audio_base64"]
    assert campo["x-veridicus-limit"] == "audio_base64_max_chars"
