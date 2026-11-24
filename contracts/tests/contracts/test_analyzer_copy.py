"""C6, el contrato común del analizador v1.0.0: copia sin editar y sus fixtures (paso 5, F1, F7).

Rojo hasta T04: `analyzer/v1/*.schema.json` y `SHA256SUMS` los copia el humano (PD-4).
"""

import hashlib
from pathlib import Path

import pytest
from helpers import (
    Caso,
    comprobar_caso,
    importar_o_fallar,
    load_contract,
    load_text,
    ruta_de,
    validador_de,
)

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


# U01-T24 (E-32, R-04): F7 compara el contenido con las huellas aprobadas en el repositorio principal,
# no solo con `SHA256SUMS`, que un PR puede recalcular.
NOMBRES_C6 = ("entrada.schema.json", "salida.schema.json")


def _conftest():  # type: ignore[no-untyped-def]
    return importar_o_fallar("conftest", "F7 vive en tests/conftest.py")


def _copia_de_c6(destino: Path, *, sumas: str | None = None, alterar: str | None = None) -> Path:
    """Copia el árbol aprobado en `destino`; `alterar` cambia un byte de ese esquema y recalcula `SHA256SUMS`."""
    destino.mkdir()
    for nombre in NOMBRES_C6:
        datos = bytearray(ruta_de(f"analyzer/v1/{nombre}").read_bytes())
        if nombre == alterar:
            marca = b'"description": "'
            posicion = bytes(datos).find(marca) + len(marca)
            datos[posicion] = ord("Y") if datos[posicion] == ord("X") else ord("X")
        (destino / nombre).write_bytes(bytes(datos))
    if sumas is None:
        sumas = "".join(
            f"{hashlib.sha256((destino / nombre).read_bytes()).hexdigest()}  {nombre}\n" for nombre in NOMBRES_C6
        )
    (destino / "SHA256SUMS").write_text(sumas, encoding="utf-8")
    return destino


@pytest.mark.parametrize("nombre", NOMBRES_C6)
def test_los_bytes_de_cada_esquema_dan_la_huella_aprobada(nombre: str) -> None:
    """E-32: los bytes del árbol son los de la versión aprobada en el principal."""
    aprobadas = _conftest().HUELLAS_APROBADAS_C6
    assert set(aprobadas) == set(NOMBRES_C6)
    assert hashlib.sha256(ruta_de(f"analyzer/v1/{nombre}").read_bytes()).hexdigest() == aprobadas[nombre]


def test_las_dos_lineas_de_sha256sums_dan_las_huellas_aprobadas() -> None:
    """E-32: `SHA256SUMS` repite las mismas huellas aprobadas."""
    aprobadas = _conftest().HUELLAS_APROBADAS_C6
    lineas = [linea for linea in load_text("analyzer/v1/SHA256SUMS").splitlines() if linea]
    en_sumas = {}
    for linea in lineas:
        huella, _, nombre = linea.partition("  ")
        en_sumas[nombre] = huella
    assert len(lineas) == 2
    assert en_sumas == aprobadas


def test_f7_acepta_una_copia_identica_a_la_aprobada(tmp_path: Path) -> None:
    """Precondición de los controles negativos: la copia sin alterar pasa."""
    assert _conftest().check_c6_copy(_copia_de_c6(tmp_path / "v1")) == []


@pytest.mark.parametrize("alterado", NOMBRES_C6)
def test_f7_rechaza_un_esquema_alterado_con_sha256sums_recalculado(tmp_path: Path, alterado: str) -> None:
    """R-04: un PR que cambia un esquema y recalcula `SHA256SUMS` ya no pasa, y el problema nombra el esquema."""
    modulo = _conftest()
    carpeta = _copia_de_c6(tmp_path / "v1", alterar=alterado)
    problemas = modulo.check_c6_copy(carpeta)
    assert problemas, "F7 debe rechazar un esquema alterado aunque SHA256SUMS coincida con sus bytes"
    assert any(alterado in problema and modulo.MENSAJE_F7 in problema for problema in problemas), problemas


def test_f7_rechaza_sha256sums_con_otra_huella_y_esquemas_intactos(tmp_path: Path) -> None:
    """Control negativo: esquemas aprobados, pero una línea de `SHA256SUMS` con otra huella."""
    modulo = _conftest()
    sumas = f"{'0' * 64}  entrada.schema.json\n{modulo.HUELLAS_APROBADAS_C6['salida.schema.json']}  salida.schema.json\n"
    problemas = modulo.check_c6_copy(_copia_de_c6(tmp_path / "v1", sumas=sumas))
    assert problemas, "F7 debe rechazar un SHA256SUMS con otra huella"
    assert any("entrada.schema.json" in problema and modulo.MENSAJE_F7 in problema for problema in problemas), problemas
