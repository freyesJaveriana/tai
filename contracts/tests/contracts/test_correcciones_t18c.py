"""Lecturas de vuelta de U01-T18c (E-29): version semantica en los contratos propios (BR1.1).

Siete esquemas llevan `x-veridicus-version: "N.0.0"` en su raiz (N = el `.vN` de su `$id` y de su
archivo) y el catalogo de errores lleva `version: "2.0.0"`. La clave `x-` es una anotacion: no cambia
que documentos se aceptan. Los controles negativos trabajan sobre copias en memoria.
"""

import copy
import re
from typing import Any

import pytest
from helpers import (
    cargar_fixture,
    errores_de,
    load_contract,
    registro_de_contratos,
    ruta_de,
    uri_de,
)
from jsonschema import Draft202012Validator
from referencing import Resource
from referencing.jsonschema import DRAFT202012

CLAVE = "x-veridicus-version"
FORMA = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
ESQUEMAS = [
    "cli/report.schema.v2.yaml",
    "integrity/review-suggestion.v2.json",
    "model_calls/model-call.v1.yaml",
    "profiles/effective-config.v1.yaml",
    "profiles/prices.schema.v1.yaml",
    "profiles/profile-base.schema.v1.yaml",
    "profiles/profiles.schema.v1.yaml",
]
CATALOGO = "errors/error-codes.v2.yaml"
C7 = "integrity/review-suggestion.v2.json"


def comprobar_version(documento: Any, archivo: str) -> list[str]:
    """Problemas de la version del esquema: ausente, mal formada o con otra mayor que su `$id`."""
    valor = documento.get(CLAVE) if isinstance(documento, dict) else None
    if not isinstance(valor, str) or not FORMA.match(valor):
        return [f"{archivo}: {CLAVE} {valor!r} no es MAYOR.MENOR.PARCHE"]
    mayor_id = re.search(r"[./]v([0-9]+)$", str(documento["$id"]))
    mayor_archivo = re.search(r"\.v([0-9]+)\.(?:yaml|json)$", archivo)
    assert mayor_id and mayor_archivo, archivo
    if mayor_id.group(1) != mayor_archivo.group(1):
        return [f"{archivo}: el $id y el archivo no coinciden en la mayor"]
    if valor.split(".")[0] != mayor_id.group(1):
        return [f"{archivo}: mayor {valor.split('.')[0]} distinta de la del $id ({mayor_id.group(1)})"]
    return []


# ---- 1. Lectura de vuelta -------------------------------------------------------------------------


@pytest.mark.parametrize("archivo", ESQUEMAS)
def test_el_esquema_lleva_su_version_semantica_con_la_mayor_de_su_id(archivo: str) -> None:
    assert comprobar_version(load_contract(archivo), archivo) == []


@pytest.mark.parametrize("archivo", ESQUEMAS)
def test_la_version_es_mayor_punto_cero_punto_cero(archivo: str) -> None:
    mayor = re.search(r"\.v([0-9]+)\.", archivo).group(1)  # type: ignore[union-attr]
    assert load_contract(archivo).get(CLAVE) == f"{mayor}.0.0"


def test_el_catalogo_de_errores_lleva_version_como_cadena() -> None:
    assert load_contract(CATALOGO)["version"] == "2.0.0"


# ---- 2. Controles negativos -----------------------------------------------------------------------


def test_control_negativo_mayor_distinta_del_id_da_rojo() -> None:
    copia = copy.deepcopy(load_contract(C7))
    copia[CLAVE] = "3.0.0"
    assert comprobar_version(copia, C7)


@pytest.mark.parametrize("valor", ["2.0", "v2.0.0", "2.0.0.0", 2, None, ""])
def test_control_negativo_version_mal_formada_da_rojo(valor: Any) -> None:
    copia = copy.deepcopy(load_contract(C7))
    copia[CLAVE] = valor
    assert comprobar_version(copia, C7)


def test_control_negativo_sin_la_clave_da_rojo() -> None:
    copia = copy.deepcopy(load_contract(C7))
    copia.pop(CLAVE, None)
    assert comprobar_version(copia, C7)


# ---- 3. Nada cambia para el validador --------------------------------------------------------------


def _fixtures_de_c7() -> list[str]:
    carpeta = ruta_de("integrity/fixtures/review-suggestion")
    return sorted(f"integrity/fixtures/review-suggestion/{p.name}" for p in carpeta.glob("*.yaml"))


# (esquema, fixture, valor de `contract` del fixture)
CASOS = [
    ("cli/report.schema.v2.yaml", "cli/fixtures/report.valid.json", "C19"),
    ("cli/report.schema.v2.yaml", "cli/fixtures/report.role-prueba-a.json", "C19"),
    ("cli/report.schema.v2.yaml", "cli/fixtures/report.testimony-in-model.json", "C19"),
    ("cli/report.schema.v2.yaml", "cli/fixtures/report.testimony-in-price-table.json", "C19"),
    ("model_calls/model-call.v1.yaml", "model_calls/fixtures/model-call.valid.yaml", "model-call"),
    (
        "model_calls/model-call.v1.yaml",
        "model_calls/fixtures/model-call.role-mayusculas.yaml",
        "model-call",
    ),
    (
        "profiles/effective-config.v1.yaml",
        "profiles/fixtures/effective-config.valid.json",
        "C18.effective-config",
    ),
    (
        "profiles/profile-base.schema.v1.yaml",
        "profiles/fixtures/profile-base.valid.yaml",
        "C18.profile-base",
    ),
    (
        "profiles/profiles.schema.v1.yaml",
        "profiles/fixtures/analyzer-profile.extra-role.yaml",
        "C18.profiles",
    ),
] + [(C7, f, "C7") for f in _fixtures_de_c7()]


def _validador(archivo: str, con_clave: bool) -> Draft202012Validator:
    documento = copy.deepcopy(load_contract(archivo))
    if not con_clave:
        documento.pop(CLAVE, None)
    uri = uri_de(archivo, documento)
    recurso = Resource.from_contents(documento, default_specification=DRAFT202012)
    registro = registro_de_contratos().with_resource(uri, recurso)
    return Draft202012Validator(
        {"$ref": uri}, registry=registro, format_checker=Draft202012Validator.FORMAT_CHECKER
    )


def _firma(errores: list[Any]) -> list[tuple[str, str, str]]:
    return sorted((e.validator or "", e.json_path, e.message) for e in errores)


def test_la_lista_de_casos_incluye_los_fixtures_de_c7() -> None:
    assert len(_fixtures_de_c7()) >= 15


@pytest.mark.parametrize(("esquema", "fixture", "contrato"), CASOS, ids=[c[1] for c in CASOS])
def test_el_validador_da_el_mismo_resultado_con_y_sin_la_clave(
    esquema: str, fixture: str, contrato: str
) -> None:
    caso = cargar_fixture(fixture, contrato)
    con = errores_de(_validador(esquema, True), caso["payload"])
    sin = errores_de(_validador(esquema, False), caso["payload"])
    assert _firma(con) == _firma(sin)
    if caso["expectation"] == "accept":
        assert con == []
    else:
        assert con, f"{fixture}: debia rechazarse"


@pytest.mark.parametrize("esquema", ESQUEMAS)
def test_la_clave_solo_anota_no_restringe_el_esquema(esquema: str) -> None:
    documento = load_contract(esquema)
    Draft202012Validator.check_schema(documento)


# ---- 4. El validador de esquemas admite la clave solo en la raiz (E-30) ----------------------------


def test_validate_json_schema_acepta_x_veridicus_version_en_la_raiz() -> None:
    from veridicus_contracts.validators import validate_json_schema

    validate_json_schema({"type": "object", CLAVE: "1.0.0", "properties": {"a": {"type": "string"}}})


@pytest.mark.parametrize(
    "esquema",
    [
        {"type": "object", "properties": {"a": {"type": "string", CLAVE: "1.0.0"}}},
        {"type": "object", "$defs": {"d": {"type": "string", CLAVE: "1.0.0"}}},
        {"type": "array", "items": {"type": "string", CLAVE: "1.0.0"}},
        {"allOf": [{"type": "string", CLAVE: "1.0.0"}]},
    ],
    ids=["properties", "defs", "items", "allOf"],
)
def test_control_negativo_x_veridicus_version_anidada_se_rechaza(esquema: dict[str, Any]) -> None:
    from veridicus_contracts.validators import ValidationFailure, validate_json_schema

    with pytest.raises(ValidationFailure, match="palabra clave desconocida"):
        validate_json_schema(esquema)


def test_control_negativo_otra_clave_x_en_la_raiz_se_rechaza() -> None:
    from veridicus_contracts.validators import ValidationFailure, validate_json_schema

    with pytest.raises(ValidationFailure, match="palabra clave desconocida"):
        validate_json_schema({"type": "object", "x-veridicus-limit": "report_token_max_chars"})
