"""Configuración común de la suite: rutas al árbol de contracts/ y perfil de Hypothesis."""

import hashlib
import json
from pathlib import Path

import pytest
from hypothesis import settings

# Perfil determinista, sin plazo por ejemplo (D6, D7).
settings.register_profile("contracts", derandomize=True, deadline=None)
settings.load_profile("contracts")

CONTRACTS_ROOT = Path(__file__).resolve().parent.parent

MENSAJE_F7 = (
    "La copia del contrato común no es la aprobada; "
    "los cambios se proponen en el repositorio principal"
)
ESQUEMAS_C6 = ("entrada.schema.json", "salida.schema.json")

# Huellas SHA-256 de los bytes de la copia aprobada de C6 (R-04, E-32). Solo cambian con un cambio de
# contrato aprobado en el repositorio principal, es decir, con una v2 nueva; nunca porque un PR
# recalcule `SHA256SUMS`.
HUELLAS_APROBADAS_C6 = {
    "entrada.schema.json": "28606016b51dd19d873e7ee8fae7d959f0a98c225ab2690d0fd935296c3c41a8",
    "salida.schema.json": "e1528b7de1db9b5a3ca8c6f3e8eacb0eeec92522423014d6644ab39918bedeaf",
}


def check_c6_copy(carpeta: Path) -> list[str]:
    """F7 (BR1.7): comprueba la copia de C6 en `carpeta`; lista vacía si es la aprobada.

    Exige `SHA256SUMS` de exactamente dos líneas, el SHA-256 de los bytes de cada esquema igual
    a su línea y a su huella aprobada (`HUELLAS_APROBADAS_C6`), cada línea de `SHA256SUMS` igual a
    esa huella y `contrato: { const: "1.0.0" }` en los dos. Solo lee; nunca escribe.
    """
    problemas: list[str] = []
    try:
        texto = (carpeta / "SHA256SUMS").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [f"{MENSAJE_F7}: SHA256SUMS ilegible: {error}"]
    lineas = [linea for linea in texto.splitlines() if linea]
    esperadas: dict[str, str] = {}
    for linea in lineas:
        huella, _, nombre = linea.partition("  ")
        esperadas[nombre] = huella
    if len(lineas) != 2 or set(esperadas) != set(ESQUEMAS_C6):
        problemas.append("SHA256SUMS debe tener exactamente dos líneas, una por esquema")
    for nombre in ESQUEMAS_C6:
        try:
            datos = (carpeta / nombre).read_bytes()
        except OSError as error:
            problemas.append(f"{nombre} ilegible: {error}")
            continue
        huella = hashlib.sha256(datos).hexdigest()
        if huella != esperadas.get(nombre):
            problemas.append(f"{nombre}: su SHA-256 no coincide con SHA256SUMS")
        if huella != HUELLAS_APROBADAS_C6[nombre]:
            problemas.append(f"{nombre}: su SHA-256 no es el de la versión aprobada")
        if esperadas.get(nombre) != HUELLAS_APROBADAS_C6[nombre]:
            problemas.append(
                f"{nombre}: su línea de SHA256SUMS no es la huella de la versión aprobada"
            )
        try:
            contrato = json.loads(datos)["properties"]["contrato"]
        except (ValueError, KeyError, TypeError):
            contrato = None
        if contrato != {"const": "1.0.0"}:
            problemas.append(f'{nombre}: falta contrato: {{ const: "1.0.0" }}')
    return [f"{MENSAJE_F7}: {problema}" for problema in problemas]


def pytest_sessionstart(session: pytest.Session) -> None:
    """F7 aborta la sesión si la copia de C6 no es la aprobada."""
    problemas = check_c6_copy(CONTRACTS_ROOT / "analyzer" / "v1")
    if problemas:
        pytest.exit("\n".join(problemas), returncode=3)


@pytest.fixture(scope="session")
def contracts_root() -> Path:
    """Raíz del árbol contracts/."""
    return CONTRACTS_ROOT
