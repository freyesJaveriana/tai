"""Lecturas de vuelta de U01-T18b (E-23): patrones acotados en los contratos fusionados.

NFR10.6 (§4.5): ningun patron de un contrato propio admite una entrada sin tope ni repeticiones
ilimitadas anidadas. Cada version o token de la lista conserva su `pattern` y recibe `maxLength: 128`
con `x-veridicus-limit: report_token_max_chars` (E-15). Los `code` de las colas pasan a la forma
`dominio.motivo` (un solo punto). Los controles negativos trabajan sobre copias en memoria; nunca se
escribe en los contratos versionados.
"""

import copy
from collections.abc import Callable
from typing import Any, NamedTuple

import pytest
from helpers import (
    cargar_fixture,
    errores_de,
    load_contract,
    puntero_de_cuerpo,
    puntero_de_mensaje,
    validador_de,
)

LIMITES = "limits.v1.yaml"
MARCA = "report_token_max_chars"
TOPE = 128
PATRON_CODE = r"^[a-z][a-z_]*\.[a-z][a-z_]*$"
PUNTERO_422 = "#/paths/~1internal~1v1~1speech/post/responses/422/content/application~1problem+json/schema"

RUNS = "queues/runs.v2.yaml"
RESULTS = "queues/results.v2.yaml"
SPEECH = "queues/speech.v2.yaml"
EFECTIVA = "profiles/effective-config.v1.yaml"
PROXY = "api/anonymizer-proxy.v1.yaml"
VOZ = "api/speech-internal.v1.yaml"


def _fixture(relativa: str, contrato: str) -> Callable[[], dict[str, Any]]:
    def base() -> dict[str, Any]:
        fixture = cargar_fixture(relativa, contrato)
        assert fixture["expectation"] == "accept"
        return copy.deepcopy(dict(fixture["payload"]))

    return base


def _problema_422() -> dict[str, Any]:
    return {"rule_id": "length", "code": "run.timeout"}


def _cuerpo_de_voz() -> dict[str, Any]:
    return {
        "observation_id": "c4e8b1f7-2d9a-4a6c-8b3e-d5f0a9c2e1b4",
        "tema": "tema de prueba",
        "template_version": "1.0.0",
    }


class Campo(NamedTuple):
    id: str
    archivo: str
    puntero: str  # puntero al esquema objeto que contiene el campo ("" = el documento)
    campo: str
    patron: str
    base: Callable[[], dict[str, Any]]  # instancia minima valida del esquema
    es_code: bool


CAMPOS = [
    Campo(
        "C2.RunRequested.schema_version", RUNS, puntero_de_mensaje(RUNS, "RunRequested"),
        "schema_version", r"^2\.[0-9]+\.[0-9]+$",
        _fixture("queues/fixtures/runs/run.valid.yaml", "C2.RunRequested"), False,
    ),
    Campo(
        "C2.RunFailed.code", RUNS, puntero_de_mensaje(RUNS, "RunFailed"),
        "code", PATRON_CODE,
        _fixture("queues/fixtures/runs/failed.valid.yaml", "C2.RunFailed"), True,
    ),
    Campo(
        "C3.RunResult.schema_version", RESULTS, puntero_de_mensaje(RESULTS, "RunResult"),
        "schema_version", r"^2\.[0-9]+\.[0-9]+$",
        _fixture("queues/fixtures/results/result.valid.yaml", "C3.RunResult"), False,
    ),
    Campo(
        "C3.ResultFailed.code", RESULTS, puntero_de_mensaje(RESULTS, "ResultFailed"),
        "code", PATRON_CODE,
        _fixture("queues/fixtures/results/failed.valid.yaml", "C3.ResultFailed"), True,
    ),
    Campo(
        "C5.AudioToTranscribe.schema_version", SPEECH, puntero_de_mensaje(SPEECH, "AudioToTranscribe"),
        "schema_version", r"^1\.[0-9]+\.[0-9]+$",
        _fixture("queues/fixtures/speech/audio.valid.yaml", "C5.AudioToTranscribe"), False,
    ),
    Campo(
        "C5.TranscriptResult.schema_version", SPEECH, puntero_de_mensaje(SPEECH, "TranscriptResult"),
        "schema_version", r"^1\.[0-9]+\.[0-9]+$",
        _fixture("queues/fixtures/speech/transcript.valid.yaml", "C5.TranscriptResult"), False,
    ),
    Campo(
        "C5.AudioFailed.code", SPEECH, puntero_de_mensaje(SPEECH, "AudioFailed"),
        "code", PATRON_CODE,
        _fixture("queues/fixtures/speech/failed.valid.yaml", "C5.AudioFailed"), True,
    ),
    Campo(
        "C18.analyzer_version", EFECTIVA, "",
        "analyzer_version", r"^[0-9]+\.[0-9]+\.[0-9]+$",
        _fixture("profiles/fixtures/effective-config.valid.json", "C18.effective-config"), False,
    ),
    Campo(
        "C21.schema_version", PROXY, puntero_de_cuerpo("/v1/generate", "post"),
        "schema_version", r"^1\.[0-9]+\.[0-9]+$",
        _fixture("api/fixtures/anonymizer-proxy/request.valid.yaml", "C21.request"), False,
    ),
    Campo(
        "voz.template_version", VOZ, puntero_de_cuerpo("/internal/v1/speech", "post"),
        "template_version", r"^[0-9]+\.[0-9]+\.[0-9]+$",
        _cuerpo_de_voz, False,
    ),
    Campo(
        "voz.422.code", VOZ, PUNTERO_422,
        "code", PATRON_CODE,
        _problema_422, True,
    ),
]
IDS = [c.id for c in CAMPOS]
CODES = [c for c in CAMPOS if c.es_code]
CODES_DE_COLAS = [c for c in CODES if c.archivo.startswith("queues/")]


def _navegar(documento: Any, puntero: str) -> Any:
    nodo = documento
    for parte in puntero.removeprefix("#").strip("/").split("/"):
        if parte == "":
            continue
        nodo = nodo[parte.replace("~1", "/").replace("~0", "~")]
    return nodo


def _esquema_del_campo(documento: Any, campo: Campo) -> Any:
    return _navegar(documento, campo.puntero)["properties"][campo.campo]


def comprobar_forma(documento: Any, campo: Campo) -> list[str]:
    esquema = _esquema_del_campo(documento, campo)
    problemas: list[str] = []
    if esquema.get("maxLength") != TOPE:
        problemas.append(f"{campo.id}: maxLength {esquema.get('maxLength')!r} en vez de {TOPE}")
    if esquema.get("x-veridicus-limit") != MARCA:
        problemas.append(f"{campo.id}: x-veridicus-limit {esquema.get('x-veridicus-limit')!r}")
    if esquema.get("pattern") != campo.patron:
        problemas.append(f"{campo.id}: pattern {esquema.get('pattern')!r} en vez de {campo.patron!r}")
    return problemas


# ---- 1. Lectura de vuelta de la forma ------------------------------------------------------------


@pytest.mark.parametrize("campo", CAMPOS, ids=IDS)
def test_el_campo_lleva_tope_marca_y_conserva_su_patron(campo: Campo) -> None:
    assert comprobar_forma(load_contract(campo.archivo), campo) == []


@pytest.mark.parametrize("campo", CODES, ids=[c.id for c in CODES])
def test_los_code_llevan_exactamente_el_patron_dominio_punto_motivo(campo: Campo) -> None:
    esquema = _esquema_del_campo(load_contract(campo.archivo), campo)
    assert esquema["pattern"] == PATRON_CODE


def test_c25_suma_solo_los_contratos_que_vigila_4_4_a_report_token_max_chars() -> None:
    """E-25: C3 y C18 llevan el tope y la marca (§4.5) pero no entran en `used_in` (`limits_match` no los recorre)."""
    catalogo = load_contract(LIMITES)
    assert catalogo["limits"][MARCA]["used_in"] == ["C2", "C5", "C19", "C21"]
    assert catalogo["limits"][MARCA]["value"] == TOPE


def test_control_negativo_c2_sin_maxlength_en_schema_version_se_detecta() -> None:
    campo = next(c for c in CAMPOS if c.id == "C2.RunRequested.schema_version")
    copia = copy.deepcopy(load_contract(campo.archivo))
    _esquema_del_campo(copia, campo).pop("maxLength", None)
    assert comprobar_forma(copia, campo)


def test_control_negativo_sin_marca_o_con_otro_patron_se_detecta() -> None:
    campo = next(c for c in CAMPOS if c.id == "C2.RunFailed.code")
    sin_marca = copy.deepcopy(load_contract(campo.archivo))
    _esquema_del_campo(sin_marca, campo).pop("x-veridicus-limit", None)
    assert comprobar_forma(sin_marca, campo)
    anidado = copy.deepcopy(load_contract(campo.archivo))
    _esquema_del_campo(anidado, campo)["pattern"] = r"^[a-z][a-z_]*(\.[a-z][a-z_]*)+$"
    assert comprobar_forma(anidado, campo)


# ---- 2. Lectura de vuelta con el validador real ----------------------------------------------------


def _validador(campo: Campo) -> Any:
    return validador_de(campo.archivo, campo.puntero)


def _con_valor(campo: Campo, valor: str) -> dict[str, Any]:
    instancia = campo.base()
    assert campo.campo in instancia, f"{campo.id}: la base no trae {campo.campo}"
    instancia[campo.campo] = valor
    return instancia


def _de_longitud(campo: Campo, longitud: int) -> str:
    """Un valor que casa con el patron del campo y mide exactamente `longitud`."""
    if campo.es_code:
        return "run." + "a" * (longitud - 4)
    valido = campo.base()[campo.campo]
    return valido + "0" * (longitud - len(valido))


@pytest.mark.parametrize("campo", CAMPOS, ids=IDS)
def test_el_validador_acepta_la_instancia_minima_valida(campo: Campo) -> None:
    errores = errores_de(_validador(campo), campo.base())
    assert errores == [], [e.message[:80] for e in errores]


@pytest.mark.parametrize("campo", CAMPOS, ids=IDS)
def test_el_validador_acepta_el_valor_de_128_caracteres(campo: Campo) -> None:
    valor = _de_longitud(campo, TOPE)
    assert len(valor) == TOPE
    errores = errores_de(_validador(campo), _con_valor(campo, valor))
    assert errores == [], [e.message[:80] for e in errores]


@pytest.mark.parametrize("campo", CAMPOS, ids=IDS)
def test_el_validador_rechaza_por_maxlength_el_valor_de_129_caracteres(campo: Campo) -> None:
    valor = _de_longitud(campo, TOPE + 1)
    assert len(valor) == TOPE + 1
    errores = errores_de(_validador(campo), _con_valor(campo, valor))
    assert any(e.validator == "maxLength" and campo.campo in e.json_path for e in errores), [
        (e.validator, e.json_path) for e in errores
    ]


@pytest.mark.parametrize("campo", CODES, ids=[c.id for c in CODES])
def test_el_validador_acepta_run_timeout_y_rechaza_dos_puntos(campo: Campo) -> None:
    assert errores_de(_validador(campo), _con_valor(campo, "run.timeout")) == []
    errores = errores_de(_validador(campo), _con_valor(campo, "run.timeout.extra"))
    assert any(e.validator == "pattern" and campo.campo in e.json_path for e in errores), [
        (e.validator, e.json_path) for e in errores
    ]


def test_los_code_reales_de_las_colas_siguen_aceptandose() -> None:
    """Parada de la tarea: ningun `code` de los fixtures ni del catalogo puede tener mas de un punto."""
    catalogo = load_contract("errors/error-codes.v2.yaml")["codes"]
    nombres = list(catalogo) if isinstance(catalogo, dict) else [c["code"] for c in catalogo]
    assert nombres
    assert [n for n in nombres if n.count(".") != 1] == []
    campo = CODES_DE_COLAS[0]
    for nombre in nombres:
        assert errores_de(_validador(campo), _con_valor(campo, nombre)) == [], nombre
