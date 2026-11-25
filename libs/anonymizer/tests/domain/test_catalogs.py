"""Paso 6: listas y tablas versionadas (BR1.2, BR1.5, BR3.1, BR5.2).

Un ejemplo positivo y uno negativo por patrón (salen del propio archivo de reglas), ninguna entidad
sembrada ni nombre de pila común en `allowed-words`, y un archivo inválido que hace fallar cerrado
al cargador.
"""

import json
import shutil
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
from veridicus_contracts.loaders import load_file

from tests.support import FIXTURES, fold, load_seeded
from veridicus_anonymizer.domain.catalogs import (
    CatalogError,
    ProviderDomain,
    load_catalogs,
)
from veridicus_anonymizer.domain.regex import compile_pattern

DATA = files("veridicus_anonymizer") / "data"
GROUPS = ("person_patterns", "place_patterns", "case_number_patterns", "identifier_patterns")


def _document(stem: str) -> dict[str, Any]:
    loaded: dict[str, Any] = load_file(DATA / f"{stem}.v1.yaml")
    return loaded


RULES = [entry for group in GROUPS for entry in _document("detection-rules")[group]]
RULE_IDS = [r["id"] for r in RULES]


def _entities(pattern: str, text: str) -> list[str]:
    """Los tramos que enmascara un patrón: el grupo `entity` o, sin él, toda la coincidencia."""
    compiled = compile_pattern(pattern)
    index = compiled.groupindex.get("entity")
    spans = [m.span(index) if index else m.span() for m in compiled.finditer(text)]
    return [text[a:b] for a, b in spans]


@pytest.mark.parametrize("rule", RULES, ids=RULE_IDS)
def test_every_positive_example_of_a_pattern_is_masked(rule: dict[str, Any]) -> None:
    for example in rule["examples_positive"]:
        entities = _entities(rule["pattern"], example)
        assert entities, f"{rule['id']}: el ejemplo positivo no coincide"
        assert all(e.strip() for e in entities)
        assert all(e in example for e in entities)


@pytest.mark.parametrize("rule", RULES, ids=RULE_IDS)
def test_no_negative_example_of_a_pattern_is_masked(rule: dict[str, Any]) -> None:
    for example in rule["examples_negative"]:
        assert _entities(rule["pattern"], example) == [], f"{rule['id']}: el negativo coincide"


def test_the_treatment_and_place_prefixes_stay_outside_the_masked_entity() -> None:
    by_id = {r["id"]: r for r in RULES}
    assert _entities(by_id["treatment_name"]["pattern"], "dijo doña Casilda Roncancio hoy") == [
        "Casilda Roncancio"
    ]
    assert _entities(by_id["place_prefix"]["pattern"], "en la vereda La Esperanza hoy") == [
        "La Esperanza"
    ]
    assert _entities(by_id["case_number_dashed"]["pattern"], "radicado 110016000-2019-00123") == [
        "110016000-2019-00123"
    ]


def test_the_default_catalogs_load_with_the_four_files() -> None:
    catalogs = load_catalogs()

    assert {r.id for r in catalogs.rules} == set(RULE_IDS)
    assert {r.category for r in catalogs.rules} == {
        "PERSONA",
        "LUGAR",
        "EXPEDIENTE",
        "IDENTIFICADOR",
    }
    assert "Fiscalía" in catalogs.allowed_words
    assert catalogs.domains == {
        "anthropic": ProviderDomain("api.anthropic.com"),
        "google": ProviderDomain("generativelanguage.googleapis.com"),
        "openai": ProviderDomain("api.openai.com"),
    }
    assert all(d.port == 443 for d in catalogs.domains.values())
    capability = catalogs.capabilities[("anthropic", "claude-sonnet-5-5")]
    assert capability.structured_mode == "json_schema_native"
    assert capability.effort_parameter == "effort"
    assert len(catalogs.capabilities) == 1


def test_allowed_words_never_hold_a_seeded_entity_or_a_common_word_given_name() -> None:
    allowed = {fold(w) for w in load_catalogs().allowed_words}
    seeded = load_seeded()["entidades"]
    names = json.loads((FIXTURES / "common_word_names.json").read_text("utf-8"))["nombres"]

    assert "esperanza" in {fold(n) for n in names}
    for entity in seeded:
        for word in (w for w in entity.split() if w[0].isupper()):  # sin conectores («del»)
            assert fold(word) not in allowed, "una entidad sembrada está en allowed-words"
    for name in names:
        assert fold(name) not in allowed, "un nombre de pila está en allowed-words"


def test_allowed_words_cover_the_function_words_and_institutions_the_safety_net_spares() -> None:
    allowed = load_catalogs().allowed_words

    for word in ("El", "Entonces", "Yo", "Fiscalía", "Ejército", "Doña", "TES"):
        assert word in allowed


# --- Falla cerrado (BR2.2) ----------------------------------------------------------------------


def _copy(tmp_path: Path) -> Path:
    target = tmp_path / "data"
    shutil.copytree(str(DATA), target, ignore=shutil.ignore_patterns("__pycache__"))
    return target


def _rewrite(target: Path, stem: str, change: Callable[[dict[str, Any]], None]) -> None:
    document = _document(stem)
    change(document)
    (target / f"{stem}.v1.yaml").write_text(json.dumps(document, ensure_ascii=False), "utf-8")


def _duplicate_rule(document: dict[str, Any]) -> None:
    document["place_patterns"].append(dict(document["person_patterns"][0]))


def _bad_pattern(document: dict[str, Any]) -> None:
    document["person_patterns"][0]["pattern"] = "(?<=a)b"


def _wrong_providers(document: dict[str, Any]) -> None:
    document["entries"][1]["provider"] = "anthropic"


def _repeated_model(document: dict[str, Any]) -> None:
    document["entries"].append(dict(document["entries"][0]))


@pytest.mark.parametrize(
    ("stem", "change"),
    [
        ("detection-rules", _duplicate_rule),
        ("detection-rules", _bad_pattern),
        ("allowed-domains", _wrong_providers),
        ("capabilities", _repeated_model),
    ],
    ids=["regla_repetida", "patron_que_no_compila", "proveedores_distintos", "modelo_repetido"],
)
def test_the_loader_fails_closed_on_a_semantically_invalid_file(
    stem: str, change: Callable[[dict[str, Any]], None], tmp_path: Path
) -> None:
    target = _copy(tmp_path)
    _rewrite(target, stem, change)

    with pytest.raises(CatalogError):
        load_catalogs(target)


def test_the_loader_fails_closed_on_a_missing_file(tmp_path: Path) -> None:
    target = _copy(tmp_path)
    (target / "allowed-words.v1.yaml").unlink()

    with pytest.raises(CatalogError, match="allowed-words"):
        load_catalogs(target)


def test_the_loader_fails_closed_on_a_file_that_is_not_valid_yaml(tmp_path: Path) -> None:
    target = _copy(tmp_path)
    (target / "capabilities.v1.yaml").write_text("entries: [sin cerrar", "utf-8")

    with pytest.raises(CatalogError, match="capabilities"):
        load_catalogs(target)


def test_the_loader_reads_a_valid_copy_of_the_data_directory(tmp_path: Path) -> None:
    assert load_catalogs(_copy(tmp_path)) == load_catalogs()
