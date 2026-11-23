"""Registro de esquemas (§4.2, BR12.3, FD-U1-11): sin red, sin URI ajena."""

import json
from pathlib import Path

import pytest
from referencing.exceptions import Unresolvable, Unretrievable

from veridicus_contracts.registry import (
    BASE_URI,
    ForeignUriError,
    build_registry,
    validator_for,
)

DATOS = Path(__file__).resolve().parent / "data" / "registro"
BASE_A = BASE_URI + "veridicus/contracts/prueba/a"
BASE_B = BASE_URI + "veridicus/contracts/prueba/b"
BASE_ANTIGUA = BASE_URI + "veridicus/contracts/prueba/antigua"


def _esquema(ruta: Path, contenido: object) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido), encoding="utf-8")


def test_cada_esquema_se_registra_bajo_la_base_mas_su_id() -> None:
    registro = build_registry(DATOS)
    for uri in (BASE_A, BASE_B, BASE_ANTIGUA):
        assert registro.get_or_retrieve(uri).value.contents["$id"] == uri.removeprefix(
            BASE_URI.removesuffix("/")
        )


def test_ref_canonico_por_id_se_resuelve_contra_el_registro() -> None:
    validador = validator_for(build_registry(DATOS), BASE_B)
    assert validador.is_valid({"cita_a": {"texto": "hola", "turno": 3}})
    assert not validador.is_valid({"cita_a": {"texto": "hola"}})
    assert not validador.is_valid({"cita_a": {"texto": "hola", "turno": 3, "extra": 1}})


def test_la_forma_antigua_del_ref_no_se_resuelve_e36() -> None:
    validador = validator_for(build_registry(DATOS), BASE_ANTIGUA)
    with pytest.raises(Unresolvable) as excepcion:
        validador.is_valid({"cita": {"texto": "hola", "turno": 3}})
    assert excepcion.value.ref == "contracts/prueba/a.schema.json#/$defs/cita"


@pytest.mark.parametrize(
    "uri",
    ["https://example.com/esquema", "http://json-schema.org/draft-07/schema", "file:///etc/passwd"],
)
def test_una_uri_ajena_se_rechaza_sin_abrir_red(uri: str) -> None:
    registro = build_registry(DATOS)
    with pytest.raises(Unretrievable) as excepcion:
        registro.get_or_retrieve(uri)
    assert isinstance(excepcion.value.__cause__, ForeignUriError)
    assert uri in str(excepcion.value.__cause__)


def test_los_directorios_fixtures_no_se_registran(tmp_path: Path) -> None:
    _esquema(tmp_path / "ok.schema.json", {"$id": "/veridicus/contracts/x/ok", "type": "object"})
    _esquema(tmp_path / "x" / "fixtures" / "malo.schema.json", ["no es un esquema"])
    registro = build_registry(tmp_path)
    assert registro.get_or_retrieve(BASE_URI + "veridicus/contracts/x/ok").value is not None
    assert len(list(registro)) == 1


def test_id_ausente_o_ajeno_fuera_de_vendor_se_rechaza(tmp_path: Path) -> None:
    _esquema(tmp_path / "sin_id" / "a.schema.json", {"type": "object"})
    with pytest.raises(ValueError, match=r"\$id"):
        build_registry(tmp_path / "sin_id")
    _esquema(tmp_path / "no_objeto" / "a.schema.json", [1])
    with pytest.raises(ValueError, match=r"\$id"):
        build_registry(tmp_path / "no_objeto")
    _esquema(tmp_path / "ajeno" / "a.schema.json", {"$id": "https://example.com/a"})
    with pytest.raises(ValueError, match="vendor"):
        build_registry(tmp_path / "ajeno")


def test_un_schema_que_no_es_texto_se_rechaza_como_error_de_carga(tmp_path: Path) -> None:
    for valor in ([], 5, {"a": 1}):
        _esquema(
            tmp_path / "x" / "a.schema.json", {"$id": "/veridicus/contracts/x/a", "$schema": valor}
        )
        with pytest.raises(ValueError, match=r"\$schema"):
            build_registry(tmp_path / "x")


def test_un_id_absoluto_solo_se_admite_bajo_vendor(tmp_path: Path) -> None:
    _esquema(
        tmp_path / "vendor" / "meta.schema.json",
        {"$id": "https://json-schema.org/draft/2020-12/schema", "type": ["object", "boolean"]},
    )
    registro = build_registry(tmp_path)
    assert registro.get_or_retrieve("https://json-schema.org/draft/2020-12/schema").value


RELATIVOS = Path(__file__).resolve().parent / "data" / "registro_relativo"
EJEMPLO_A = BASE_URI + "veridicus/contracts/ejemplo/v1/a"
EJEMPLO_B = BASE_URI + "veridicus/contracts/ejemplo/v1/b"


def test_un_id_relativo_sin_barra_se_registra_bajo_la_base() -> None:
    registro = build_registry(RELATIVOS)
    recurso = registro.get_or_retrieve(EJEMPLO_A).value
    assert recurso.contents["$id"] == "veridicus/contracts/ejemplo/v1/a"


def test_una_referencia_hacia_un_id_relativo_se_resuelve_y_valida() -> None:
    validador = validator_for(build_registry(RELATIVOS), EJEMPLO_B)
    assert validador.is_valid({"cita": {"texto": "hola"}})
    assert not validador.is_valid({"cita": {"texto": 5}})
    assert not validador.is_valid({"cita": {"texto": "hola", "extra": 1}})


def test_un_id_relativo_que_sale_de_la_base_se_rechaza(tmp_path: Path) -> None:
    for identificador in ("../x", "a/../../x", "//example.com/x"):
        _esquema(tmp_path / "a.schema.json", {"$id": identificador})
        with pytest.raises(ValueError, match="sale de la base"):
            build_registry(tmp_path)


@pytest.mark.parametrize("identificador", ["", "#frag", "?q=1", "veridicus/a#frag", "veridicus/a?q=1"])
def test_un_id_vacio_con_fragmento_o_consulta_se_rechaza(
    tmp_path: Path, identificador: str
) -> None:
    _esquema(tmp_path / "a.schema.json", {"$id": identificador})
    with pytest.raises(ValueError, match="vacío, con fragmento o con consulta"):
        build_registry(tmp_path)


@pytest.mark.parametrize(
    ("id_a", "id_b"),
    [
        ("veridicus/contracts/ejemplo/v1/a", "/veridicus/contracts/ejemplo/v1/a"),
        ("/veridicus/contracts/ejemplo/v1/a", "/veridicus/contracts/ejemplo/v1/a"),
    ],
)
def test_dos_archivos_con_la_misma_uri_se_rechazan_nombrando_ambos(
    tmp_path: Path, id_a: str, id_b: str
) -> None:
    _esquema(tmp_path / "uno.schema.json", {"$id": id_a})
    _esquema(tmp_path / "dos.schema.json", {"$id": id_b})
    with pytest.raises(ValueError, match="repetida") as excepcion:
        build_registry(tmp_path)
    assert "uno.schema.json" in str(excepcion.value)
    assert "dos.schema.json" in str(excepcion.value)


def test_un_id_absoluto_ajeno_fuera_de_vendor_sigue_rechazado(tmp_path: Path) -> None:
    _esquema(tmp_path / "a.schema.json", {"$id": "https://example.com/x"})
    with pytest.raises(ValueError, match="vendor"):
        build_registry(tmp_path)


def test_sin_raiz_usa_los_datos_del_paquete_incluido_vendor() -> None:
    registro = build_registry()
    meta = registro.get_or_retrieve("https://json-schema.org/draft/2020-12/schema")
    assert meta.value.contents["$id"] == "https://json-schema.org/draft/2020-12/schema"
    asyncapi = registro.get_or_retrieve("http://asyncapi.com/definitions/3.0.0/asyncapi.json")
    assert asyncapi.value.contents["$id"].endswith("/asyncapi.json")
