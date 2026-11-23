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


def test_sin_raiz_usa_los_datos_del_paquete_incluido_vendor() -> None:
    registro = build_registry()
    meta = registro.get_or_retrieve("https://json-schema.org/draft/2020-12/schema")
    assert meta.value.contents["$id"] == "https://json-schema.org/draft/2020-12/schema"
    asyncapi = registro.get_or_retrieve("http://asyncapi.com/definitions/3.0.0/asyncapi.json")
    assert asyncapi.value.contents["$id"].endswith("/asyncapi.json")
