"""C6, el contrato común del analizador v1.0.0: copia sin editar y sus fixtures (paso 5, F1, F7).

Rojo hasta T04: `analyzer/v1/*.schema.json` y `SHA256SUMS` los copia el humano (PD-4).
"""

import hashlib

import pytest
from helpers import Caso, comprobar_caso, load_contract, load_text, ruta_de, validador_de

pytestmark = pytest.mark.c6

DIRECTORIO = "analyzer/v1/fixtures"
ESQUEMAS = {
    "entrada": "analyzer/v1/entrada.schema.json",
    "salida": "analyzer/v1/salida.schema.json",
}


def _sin(campo: str) -> tuple[str, str, str]:
    return ("required", "$.hallazgos[0]", f"'{campo}'")


SALIDA = [
    Caso("salida.valid.yaml", "C6.salida"),
    Caso("salida.error-with-finding.yaml", "C6.salida", "BR3.6", ("maxItems", "$.hallazgos", None)),
    Caso(
        "salida.is-truthful.yaml",
        "C6.salida",
        "BR3.1",
        ("additionalProperties", "$.hallazgos[0]", "is_truthful"),
    ),
    Caso("salida.tipo-falso.yaml", "C6.salida", "BR3.2", ("enum", "$.hallazgos[0].tipo", None)),
    Caso("salida.hallazgo-sin-hecho.yaml", "C6.salida", "BR3.1", _sin("hecho")),
    Caso("salida.hallazgo-sin-tipo.yaml", "C6.salida", "BR3.1", _sin("tipo")),
    Caso("salida.hallazgo-sin-cita-a.yaml", "C6.salida", "BR3.1", _sin("cita_a")),
    Caso("salida.hallazgo-sin-cita-b.yaml", "C6.salida", "BR3.1", _sin("cita_b")),
    Caso("salida.hallazgo-sin-observaciones.yaml", "C6.salida", "BR3.1", _sin("observaciones")),
    Caso("salida.anonimizador-no-disponible.yaml", "C6.salida"),
    Caso("salida.incidente-anonimizacion.yaml", "C6.salida"),
]

ENTRADA = [
    Caso("entrada.valid.yaml", "C6.entrada"),
    Caso(
        "entrada.corpus-sin-consentimiento.yaml",
        "C6.entrada",
        "BR3.5",
        ("required", "$.transcripcion", "'consentimiento'"),
    ),
    Caso("entrada.sintetico-sin-consentimiento.yaml", "C6.entrada"),
    Caso(
        "entrada.mandato-sin-constancia.yaml",
        "C6.entrada",
        "BR3.5",
        ("required", "$.transcripcion.consentimiento", "'constancia_mandato'"),
    ),
    Caso(
        "entrada.autoridad-sin-constancia.yaml",
        "C6.entrada",
        "BR3.5",
        ("required", "$.transcripcion.consentimiento", "'constancia'"),
    ),
]

CASOS = [pytest.param("salida", c, id=c.archivo) for c in SALIDA] + [
    pytest.param("entrada", c, id=c.archivo) for c in ENTRADA
]


@pytest.mark.parametrize(("esquema", "caso"), CASOS)
def test_cada_fixture_se_acepta_o_se_rechaza_por_su_regla(esquema: str, caso: Caso) -> None:
    validador = validador_de(ESQUEMAS[esquema])
    comprobar_caso(DIRECTORIO, caso, validador)


def test_sha256sums_tiene_dos_lineas_y_coincide_con_los_bytes() -> None:
    """BR1.7: exactamente dos líneas y el SHA-256 de los bytes de cada esquema."""
    lineas = [linea for linea in load_text("analyzer/v1/SHA256SUMS").splitlines() if linea]
    assert len(lineas) == 2, f"SHA256SUMS debe tener exactamente dos líneas: {len(lineas)}"
    esperadas = {}
    for linea in lineas:
        huella, _, nombre = linea.partition("  ")
        esperadas[nombre] = huella
    assert set(esperadas) == {"entrada.schema.json", "salida.schema.json"}
    for nombre, huella in esperadas.items():
        datos = ruta_de(f"analyzer/v1/{nombre}").read_bytes()
        assert hashlib.sha256(datos).hexdigest() == huella, f"{nombre} no coincide con SHA256SUMS"


@pytest.mark.parametrize("esquema", ["entrada", "salida"])
def test_los_dos_esquemas_declaran_contrato_1_0_0(esquema: str) -> None:
    """BR1.7: `contrato: { const: "1.0.0" }` en los dos."""
    documento = load_contract(ESQUEMAS[esquema])
    assert documento["properties"]["contrato"] == {"const": "1.0.0"}
