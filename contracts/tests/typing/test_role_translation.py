"""Tabla de papeles del analizador a `registro.llamadas` de C6 (BR9.6)."""

import pytest
from helpers import load_contract, recorrer

pytestmark = pytest.mark.c13

TABLA = "model_calls/role-translation.v1.yaml"
C6_SALIDA = "analyzer/v1/salida.schema.json"
ESPERADA = {
    "judge": "juez",
    "verifier": "verificador",
    "verifier_permuted": "verificador_permutado",
}


def test_la_tabla_traduce_solo_los_tres_papeles_del_analizador_y_coincide_con_c6() -> None:
    """BR9.6: exactamente tres filas, y cada destino es un valor del enum `papel` de C6."""
    tabla = load_contract(TABLA)
    assert tabla["translation"] == ESPERADA
    c6 = load_contract(C6_SALIDA)
    enums_de_papel = [
        valor["properties"]["papel"]["enum"]
        for _, _, valor in recorrer(c6)
        if isinstance(valor, dict) and "papel" in (valor.get("properties") or {})
    ]
    assert enums_de_papel, "C6 ya no declara el papel de registro.llamadas"
    assert all(set(ESPERADA.values()) == set(enum) for enum in enums_de_papel)
