"""Contratos de datos del módulo: cada archivo de `data/` valida contra su esquema versionado.

Los cuatro archivos (reglas, palabras permitidas, dominios y capacidades) los escribe U10-T03.
Hasta entonces el cargador lanza `NotImplementedError` y estas pruebas están en rojo. Un archivo
con un campo de más se rechaza, tanto por su esquema como por el cargador (falla cerrado).
"""

import json
import shutil
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from veridicus_contracts.loaders import load_file

from veridicus_anonymizer.domain.catalogs import CatalogError, load_catalogs

STEMS = ["detection-rules", "allowed-words", "allowed-domains", "capabilities"]
DATA = files("veridicus_anonymizer") / "data"


def _schema(stem: str) -> dict[str, Any]:
    text = (DATA / "schemas" / f"{stem}.schema.v1.json").read_text(encoding="utf-8")
    parsed: dict[str, Any] = json.loads(text)
    return parsed


def _instance(stem: str) -> dict[str, Any]:
    loaded: dict[str, Any] = load_file(DATA / f"{stem}.v1.yaml")
    return loaded


@pytest.mark.parametrize("stem", STEMS)
def test_the_data_file_validates_against_its_versioned_schema(stem: str) -> None:
    load_catalogs()  # el cargador valida todo; lanza NotImplementedError hasta U10-T03

    Draft202012Validator.check_schema(_schema(stem))
    Draft202012Validator(_schema(stem)).validate(_instance(stem))


@pytest.mark.parametrize("stem", STEMS)
def test_a_data_file_with_an_extra_field_is_rejected_by_its_schema(stem: str) -> None:
    load_catalogs()
    validator = Draft202012Validator(_schema(stem))
    instance = _instance(stem)

    assert validator.is_valid(instance)
    assert not validator.is_valid({**instance, "campo_de_mas": 1})


@pytest.mark.parametrize("stem", STEMS)
def test_the_loader_fails_closed_on_a_data_file_with_an_extra_field(
    stem: str, tmp_path: Path
) -> None:
    load_catalogs()
    copy = tmp_path / "data"
    shutil.copytree(str(DATA), copy)
    target = copy / f"{stem}.v1.yaml"
    broken = {**_instance(stem), "campo_de_mas": 1}
    target.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(CatalogError):
        load_catalogs(copy)
