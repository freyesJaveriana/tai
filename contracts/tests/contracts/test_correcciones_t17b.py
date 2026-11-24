"""Lecturas de vuelta de U01-T17b (E-22): patron unico de fecha en los contratos fusionados.

BR8.1 y NFR11.2 fijan un solo formato, AAAA-MM-DDTHH:MM:SSZ en UTC. El patron lo declara `DateTime`
de C1; aqui se lee de ese archivo y no se copia. Cada uno de los siete campos debe llevar
`format: date-time` y exactamente ese patron, y el validador real (con el registro de esquemas) debe
aceptar la fecha en forma unica y rechazar la que trae fracciones o desplazamiento. Los controles
negativos trabajan sobre copias en memoria; nunca se escribe en los contratos versionados.
"""

import copy
from typing import Any, NamedTuple

import pytest
from helpers import (
    cargar_fixture,
    errores_de,
    load_contract,
    puntero_de_mensaje,
    validador_de,
)

from veridicus_contracts.validators import extract_message_payloads

C1 = "api/console.v2.yaml"

VALIDA = "2026-10-02T21:40:00Z"
CON_FRACCION = "2026-10-02T21:40:00.123Z"
CON_DESPLAZAMIENTO = "2026-10-02T16:40:00-05:00"


class Campo(NamedTuple):
    id: str
    archivo: str
    mensaje: str | None  # nombre del mensaje AsyncAPI, o None si el documento es el esquema
    campo: str
    fixture: str
    contrato: str


CAMPOS = [
    Campo(
        "C2.enqueued_at",
        "queues/runs.v2.yaml",
        "RunRequested",
        "enqueued_at",
        "queues/fixtures/runs/run.valid.yaml",
        "C2.RunRequested",
    ),
    Campo(
        "C2.deadline_at",
        "queues/runs.v2.yaml",
        "RunRequested",
        "deadline_at",
        "queues/fixtures/runs/run.valid.yaml",
        "C2.RunRequested",
    ),
    Campo(
        "C3.finished_at",
        "queues/results.v2.yaml",
        "RunResult",
        "finished_at",
        "queues/fixtures/results/result.valid.yaml",
        "C3.RunResult",
    ),
    Campo(
        "C5.deadline_at",
        "queues/speech.v2.yaml",
        "AudioToTranscribe",
        "deadline_at",
        "queues/fixtures/speech/audio.valid.yaml",
        "C5.AudioToTranscribe",
    ),
    Campo(
        "C7.decided_at",
        "integrity/review-suggestion.v2.json",
        None,
        "decided_at",
        "integrity/fixtures/review-suggestion/valid.accepted.yaml",
        "C7",
    ),
    Campo(
        "llamada.at",
        "model_calls/model-call.v1.yaml",
        None,
        "at",
        "model_calls/fixtures/model-call.valid.yaml",
        "model-call",
    ),
    Campo(
        "C19.created_at",
        "cli/report.schema.v2.yaml",
        None,
        "created_at",
        "cli/fixtures/report.valid.json",
        "C19",
    ),
]
IDS = [c.id for c in CAMPOS]


def _patron_de_c1() -> str:
    patron = load_contract(C1)["components"]["schemas"]["DateTime"]["pattern"]
    assert isinstance(patron, str) and patron
    return patron


def _esquema_del_campo(documento: Any, campo: Campo) -> Any:
    raiz = documento
    if campo.mensaje is not None:
        cargas = extract_message_payloads(documento)
        ruta = next(r for r in cargas if r.endswith("/" + campo.mensaje))
        raiz = cargas[ruta]
    return raiz["properties"][campo.campo]


def comprobar_forma(documento: Any, campo: Campo, patron: str) -> list[str]:
    esquema = _esquema_del_campo(documento, campo)
    problemas: list[str] = []
    if esquema.get("format") != "date-time":
        problemas.append(f"{campo.id}: format {esquema.get('format')!r} en vez de date-time")
    if esquema.get("pattern") != patron:
        problemas.append(f"{campo.id}: pattern {esquema.get('pattern')!r} distinto del de C1")
    return problemas


# ---- 1. Lectura de vuelta de la forma ------------------------------------------------------------


def test_c1_declara_el_patron_unico_de_fecha() -> None:
    assert _patron_de_c1() == "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"


@pytest.mark.parametrize("campo", CAMPOS, ids=IDS)
def test_el_campo_lleva_date_time_y_el_patron_de_c1(campo: Campo) -> None:
    assert comprobar_forma(load_contract(campo.archivo), campo, _patron_de_c1()) == []


def test_at_de_la_llamada_a_modelo_toma_el_tope_y_la_marca_de_created_at_de_c19() -> None:
    """P-T17b-1: `at` lleva la misma forma que `created_at` de C19 (BR10.1 y K-16 exigen tope y marca)."""
    at = next(c for c in CAMPOS if c.id == "llamada.at")
    creado = next(c for c in CAMPOS if c.id == "C19.created_at")
    esquema = _esquema_del_campo(load_contract(at.archivo), at)
    referencia = _esquema_del_campo(load_contract(creado.archivo), creado)
    assert referencia["maxLength"] == 128
    assert referencia["x-veridicus-limit"] == "report_token_max_chars"
    for clave in ("format", "pattern", "maxLength", "x-veridicus-limit"):
        assert esquema.get(clave) == referencia.get(clave), clave


def test_control_negativo_c2_sin_pattern_en_deadline_at_se_detecta() -> None:
    campo = next(c for c in CAMPOS if c.id == "C2.deadline_at")
    copia = copy.deepcopy(load_contract(campo.archivo))
    _esquema_del_campo(copia, campo).pop("pattern", None)
    assert comprobar_forma(copia, campo, _patron_de_c1())


def test_control_negativo_otro_patron_o_sin_format_se_detecta() -> None:
    campo = next(c for c in CAMPOS if c.id == "C19.created_at")
    otro = copy.deepcopy(load_contract(campo.archivo))
    _esquema_del_campo(otro, campo)["pattern"] = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*$"
    assert comprobar_forma(otro, campo, _patron_de_c1())
    sin_format = copy.deepcopy(load_contract(campo.archivo))
    del _esquema_del_campo(sin_format, campo)["format"]
    assert comprobar_forma(sin_format, campo, _patron_de_c1())


# ---- 2. Lectura de vuelta con el validador real ----------------------------------------------------


def _con_fecha(campo: Campo, fecha: str) -> Any:
    fixture = cargar_fixture(campo.fixture, campo.contrato)
    assert fixture["expectation"] == "accept"
    mensaje = copy.deepcopy(fixture["payload"])
    assert campo.campo in mensaje, f"{campo.fixture}: sin {campo.campo}"
    mensaje[campo.campo] = fecha
    return mensaje


def _validador(campo: Campo) -> Any:
    puntero = "" if campo.mensaje is None else puntero_de_mensaje(campo.archivo, campo.mensaje)
    return validador_de(campo.archivo, puntero)


@pytest.mark.parametrize("campo", CAMPOS, ids=IDS)
def test_el_validador_acepta_la_fecha_sin_fracciones(campo: Campo) -> None:
    errores = errores_de(_validador(campo), _con_fecha(campo, VALIDA))
    assert errores == [], [e.message[:80] for e in errores]


@pytest.mark.parametrize(
    "fecha", [CON_FRACCION, CON_DESPLAZAMIENTO], ids=["fraccion", "desplazamiento"]
)
@pytest.mark.parametrize("campo", CAMPOS, ids=IDS)
def test_el_validador_rechaza_fracciones_y_desplazamientos(campo: Campo, fecha: str) -> None:
    errores = errores_de(_validador(campo), _con_fecha(campo, fecha))
    assert any(e.validator == "pattern" and campo.campo in e.json_path for e in errores), [
        (e.validator, e.json_path) for e in errores
    ]
