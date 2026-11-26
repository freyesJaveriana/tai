"""Esquemas de respuesta del juez y del verificador (BR3.4, PD-11).

Se prueban siempre a través de `load_response_schema(role, kind)`, nunca leyendo el archivo (R-07).
El esquema local es el estricto con el que se valida la respuesta; el de cable es el que viaja en
`GenerateRequest.schema` y no lleva las palabras clave que la API de Anthropic no admite.
"""

import copy
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from tests.support import finding
from veridicus_incoherence_analyzer.application.messages import load_response_schema

TIPOS = ["fecha", "numero", "lugar", "persona", "negacion", "secuencia", "otro"]
# Palabras clave de validación que la salida estructurada de Anthropic no admite (PD-11).
UNSUPPORTED = {"minLength", "maxLength", "pattern", "minimum", "maximum"}


def unsupported_keywords(node: Any, path: str = "$") -> list[str]:
    """Rutas de las palabras clave no admitidas en un esquema de cable."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in UNSUPPORTED or key == "minItems" and isinstance(value, int) and value > 1:
                found.append(f"{path}.{key}")
            found.extend(unsupported_keywords(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            found.extend(unsupported_keywords(item, f"{path}[{index}]"))
    return found


def _accepts(schema: dict[str, Any], instance: Any) -> bool:
    return Draft202012Validator(schema).is_valid(instance)


def _judge_answer(**changes: Any) -> dict[str, Any]:
    candidate = finding()
    candidate.update(changes)
    return {"hallazgos": [candidate]}


def test_the_local_judge_schema_accepts_a_well_formed_answer_and_an_empty_list() -> None:
    schema = load_response_schema("judge", "local")

    Draft202012Validator.check_schema(schema)
    assert _accepts(schema, _judge_answer())
    assert _accepts(schema, {"hallazgos": []})


def test_the_local_judge_schema_is_closed_at_every_level() -> None:
    schema = load_response_schema("judge", "local")

    with_extra_candidate = _judge_answer(is_truthful=False)
    with_extra_quote = _judge_answer()
    with_extra_quote["hallazgos"][0]["cita_a"]["pagina"] = 1
    with_extra_root = {**_judge_answer(), "comentario": "texto libre"}

    assert not _accepts(schema, with_extra_candidate)
    assert not _accepts(schema, with_extra_quote)
    assert not _accepts(schema, with_extra_root)


@pytest.mark.parametrize("campo", ["hecho", "tipo", "cita_a", "cita_b", "observaciones"])
def test_the_local_judge_schema_requires_every_field(campo: str) -> None:
    schema = load_response_schema("judge", "local")
    answer = _judge_answer()
    del answer["hallazgos"][0][campo]

    assert not _accepts(schema, answer)


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_the_local_judge_schema_rejects_empty_strings_and_null(campo: str) -> None:
    schema = load_response_schema("judge", "local")

    assert not _accepts(schema, _judge_answer(**{campo: ""}))
    assert not _accepts(schema, _judge_answer(**{campo: None}))


def test_the_local_judge_schema_has_exactly_the_seven_types() -> None:
    schema = load_response_schema("judge", "local")

    for tipo in TIPOS:
        assert _accepts(schema, _judge_answer(tipo=tipo)), tipo
    assert not _accepts(schema, _judge_answer(tipo="falso"))
    assert not _accepts(schema, _judge_answer(tipo="temporal"))


def test_the_local_verifier_schema_is_exactly_one_boolean() -> None:
    schema = load_response_schema("verifier", "local")

    assert _accepts(schema, {"confirma": True})
    assert _accepts(schema, {"confirma": False})
    assert not _accepts(schema, {"confirma": "si"})
    assert not _accepts(schema, {"confirma": True, "texto": "libre"})
    assert not _accepts(schema, {})


@pytest.mark.parametrize("role", ["judge", "verifier"])
def test_the_wire_schemas_carry_no_keyword_the_provider_does_not_support(role: str) -> None:
    schema = load_response_schema(role, "wire")  # type: ignore[arg-type]  # motivo: parametrizado

    Draft202012Validator.check_schema(schema)
    assert unsupported_keywords(schema) == []


@pytest.mark.parametrize("role", ["judge", "verifier"])
def test_negative_control_a_wire_schema_with_min_length_fails_the_check(role: str) -> None:
    schema = copy.deepcopy(load_response_schema(role, "wire"))  # type: ignore[arg-type]  # motivo: parametrizado
    schema["minLength"] = 1

    assert unsupported_keywords(schema) == ["$.minLength"]
