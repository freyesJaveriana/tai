"""Registro de una llamada a un modelo (`model-call.v1.yaml`): el papel es una cadena con patrón (BR9.1).

Rojo hasta T08. El fixture válido usa `prueba_a`; E27 usa `role: "Prueba A"`.
"""

import copy

import pytest
from helpers import (
    Caso,
    cargar_fixture,
    comprobar_caso,
    errores_de,
    load_contract,
    recorrer,
    validador_de,
)

pytestmark = pytest.mark.c13

MODEL_CALL = "model_calls/model-call.v1.yaml"
DIRECTORIO = "model_calls/fixtures"
PATRON_DEL_PAPEL = "^[a-z][a-z0-9_]{0,31}$"

CASOS = [
    Caso("model-call.valid.yaml", "model-call"),
    Caso("model-call.role-mayusculas.yaml", "model-call", "BR9.1", ("pattern", "$.role", None)),
]


@pytest.mark.parametrize("caso", [pytest.param(c, id=c.archivo) for c in CASOS])
def test_cada_fixture_de_llamada_se_acepta_o_se_rechaza_por_su_regla(caso: Caso) -> None:
    comprobar_caso(DIRECTORIO, caso, validador_de(MODEL_CALL))


@pytest.mark.parametrize(
    ("papel", "se_acepta"),
    [
        pytest.param("prueba_a", True, id="prueba_a"),
        pytest.param("prueba_b", True, id="prueba_b"),
        pytest.param("a" * 33, False, id="33-caracteres"),
        pytest.param("Prueba A", False, id="mayusculas"),
        pytest.param("1prueba", False, id="empieza-por-digito"),
    ],
)
def test_el_papel_solo_acepta_el_patron(papel: str, se_acepta: bool) -> None:
    validador = validador_de(MODEL_CALL)
    llamada = copy.deepcopy(cargar_fixture(f"{DIRECTORIO}/model-call.valid.yaml", "model-call"))
    llamada["payload"]["role"] = papel
    errores = errores_de(validador, llamada["payload"])
    assert (errores == []) is se_acepta, [e.message for e in errores]


def test_el_papel_no_es_una_lista_cerrada() -> None:
    """BR9.1: `role` declara el patrón y ningún `enum` de papeles."""
    documento = load_contract(MODEL_CALL)
    papel = documento["properties"]["role"]
    assert papel.get("pattern") == PATRON_DEL_PAPEL
    assert not any(
        clave == "enum" and "judge" in valor
        for _, clave, valor in recorrer(papel)
        if isinstance(valor, list)
    )
