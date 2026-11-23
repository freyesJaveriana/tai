"""C19, el reporte de la CLI v2: sin texto libre y con los tres papeles del analizador (E28, E29).

Rojo hasta T12 (`cli/report.schema.v2.yaml`). Los campos de v2 que no cita el plan (`origin`,
`blocking`) se incluyen en el fixture válido; T12 puede completarlo con el resto de los campos
obligatorios de v2 conservando el escenario y el `fixture_id`.
"""

import pytest
from helpers import Caso, comprobar_caso, validador_de

pytestmark = pytest.mark.c19

C19 = "cli/report.schema.v2.yaml"
DIRECTORIO = "cli/fixtures"

CASOS = [
    Caso("report.valid.json", "C19"),
    Caso(
        "report.role-prueba-a.json",
        "C19",
        "BR10.2",
        ("enum", "$.runs[0].calls[0].role", None),
    ),
    Caso(
        "report.testimony-in-model.json",
        "C19",
        "BR10.1",
        ("pattern", "$.runs[0].calls[0].model", None),
    ),
    Caso(
        "report.testimony-in-price-table.json",
        "C19",
        "BR10.1",
        ("pattern", "$.totals.price_table_version", None),
    ),
]


@pytest.mark.parametrize("caso", [pytest.param(c, id=c.archivo) for c in CASOS])
def test_cada_fixture_de_c19_se_acepta_o_se_rechaza_por_su_regla(caso: Caso) -> None:
    comprobar_caso(DIRECTORIO, caso, validador_de(C19))
