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


def check_c6_copy(carpeta: Path) -> list[str]:
    """F7 (BR1.7): comprueba la copia de C6 en `carpeta`; lista vacía si es la aprobada.

    Exige `SHA256SUMS` de exactamente dos líneas, el SHA-256 de los bytes de cada esquema igual
    a su línea y `contrato: { const: "1.0.0" }` en los dos. Solo lee; nunca escribe.
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
        if hashlib.sha256(datos).hexdigest() != esperadas.get(nombre):
            problemas.append(f"{nombre}: su SHA-256 no coincide con SHA256SUMS")
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
