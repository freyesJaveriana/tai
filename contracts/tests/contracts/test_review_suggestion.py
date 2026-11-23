"""C7, la sugerencia de revisión v2: fixtures de BR4.1–BR4.4 y referencia canónica de las citas (E9, E35, E36).

Rojo hasta T06 (`integrity/review-suggestion.v2.json`).
"""

import json

import pytest
from helpers import Caso, comprobar_caso, load_contract, validador_de

pytestmark = pytest.mark.c7

C7 = "integrity/review-suggestion.v2.json"
DIRECTORIO = "integrity/fixtures/review-suggestion"
REF_CITA = "/veridicus/contracts/analyzer/v1/salida#/$defs/cita"


def _sin(campo: str) -> tuple[str, str, str]:
    return ("required", "$", f"'{campo}'")


CASOS = [
    Caso("valid.pending.yaml", "C7"),
    Caso("valid.accepted.yaml", "C7"),
    Caso("valid.dismissed.yaml", "C7"),
    Caso("valid.edited.yaml", "C7"),
    Caso("sin-hecho.yaml", "C7", "BR4.1", _sin("hecho")),
    Caso("sin-tipo.yaml", "C7", "BR4.1", _sin("tipo")),
    Caso("sin-cita-a.yaml", "C7", "BR4.1", _sin("cita_a")),
    Caso("sin-cita-b.yaml", "C7", "BR4.1", _sin("cita_b")),
    Caso("sin-observaciones.yaml", "C7", "BR4.1", _sin("observaciones")),
    Caso("vacio-hecho.yaml", "C7", "BR4.1", ("minLength", "$.hecho", None)),
    Caso("vacio-tipo.yaml", "C7", "BR4.1", ("enum", "$.tipo", None)),
    Caso("vacio-cita-a.yaml", "C7", "BR4.1", ("required", "$.cita_a", "'cita'")),
    Caso("vacio-cita-b.yaml", "C7", "BR4.1", ("required", "$.cita_b", "'cita'")),
    Caso("vacio-observaciones.yaml", "C7", "BR4.1", ("minLength", "$.observaciones", None)),
    Caso(
        "con-is-truthful.yaml",
        "C7",
        "BR4.2",
        ("additionalProperties", "$", "is_truthful"),
    ),
    Caso("accepted-sin-decided-by.yaml", "C7", "BR4.4", _sin("decided_by")),
    Caso("dismissed-sin-note.yaml", "C7", "BR4.4", _sin("note")),
    Caso("edited-sin-reformulation.yaml", "C7", "BR4.4", _sin("reformulation")),
    Caso("pending-con-decided-at.yaml", "C7", "BR4.4", ("not", "$", None)),
]


@pytest.mark.parametrize("caso", [pytest.param(c, id=c.archivo) for c in CASOS])
def test_cada_fixture_de_c7_se_acepta_o_se_rechaza_por_su_regla(caso: Caso) -> None:
    comprobar_caso(DIRECTORIO, caso, validador_de(C7))


@pytest.mark.parametrize("cita", ["cita_a", "cita_b"])
def test_las_citas_referencian_la_definicion_de_c6_por_id_canonico(cita: str) -> None:
    """BR4.3, E36: `$ref` exacto por `$id`; no hay segunda definición ni forma antigua."""
    documento = load_contract(C7)
    assert documento["properties"][cita]["$ref"] == REF_CITA
    assert "contracts/analyzer/v1/salida.schema.json" not in json.dumps(documento)
