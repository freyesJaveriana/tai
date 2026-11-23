"""C18, perfiles y configuración efectiva: fixtures, huella JCS y reglas del esquema (BR9.1–BR9.7).

Rojo hasta T09. La forma del perfil (`roles`, `role_aliases`, `purpose`, `permutation`) sigue
FD-U1-02; T09 puede ajustar los fixtures de forma conservando el escenario y el `fixture_id`.
"""

import pytest
from helpers import (
    Caso,
    cargar_fixture,
    comprobar_caso,
    load_contract,
    load_text,
    recorrer,
    validador_de,
)

from veridicus_contracts.canonical import sha256_jcs

pytestmark = pytest.mark.c18

DIRECTORIO = "profiles/fixtures"
EFECTIVA = "profiles/effective-config.v1.yaml"
BASE = "profiles/profile-base.schema.v1.yaml"
ANALIZADOR = "profiles/profiles.schema.v1.yaml"

CASOS = [
    pytest.param(EFECTIVA, Caso("effective-config.valid.json", "C18.effective-config"), id="efectiva"),
    pytest.param(BASE, Caso("profile-base.valid.yaml", "C18.profile-base"), id="e21-base"),
    pytest.param(
        ANALIZADOR,
        Caso(
            "analyzer-profile.extra-role.yaml",
            "C18.profiles",
            "BR9.3",
            (None, "*todo-local", "prueba_a"),
        ),
        id="e22-papel-extra",
    ),
]


@pytest.mark.parametrize(("esquema", "caso"), CASOS)
def test_cada_fixture_de_c18_se_acepta_o_se_rechaza_por_su_regla(esquema: str, caso: Caso) -> None:
    comprobar_caso(DIRECTORIO, caso, validador_de(esquema))


def test_la_huella_jcs_de_la_configuracion_efectiva_es_la_del_fixture() -> None:
    """BR9.7: el SHA-256 de la forma canónica coincide, y `profile_sha256` es el del perfil."""
    load_contract(EFECTIVA)
    fixture = cargar_fixture(f"{DIRECTORIO}/effective-config.valid.json", "C18.effective-config")
    esperada = load_text(f"{DIRECTORIO}/effective-config.valid.sha256").strip()
    assert sha256_jcs(fixture["payload"]) == esperada
    assert sha256_jcs(fixture["payload"]["profile"]) == fixture["payload"]["profile_sha256"]


@pytest.mark.parametrize("esquema", [BASE, ANALIZADOR])
def test_el_esquema_no_fija_el_prefijo_de_las_claves(esquema: str) -> None:
    """BR9.4, E25: el prefijo `VERIDICUS_` es un argumento de la validación, no del archivo."""
    documento = load_contract(esquema)
    patrones = [
        valor["pattern"]
        for _, clave, valor in recorrer(documento)
        if clave == "api_key_ref" and isinstance(valor, dict) and "pattern" in valor
    ]
    assert all("VERIDICUS" not in patron for patron in patrones)


def test_la_base_exige_la_forma_generica_de_api_key_ref() -> None:
    """BR9.4: `^[A-Z][A-Z0-9_]{2,63}$` en el perfil genérico."""
    documento = load_contract(BASE)
    patrones = [
        valor["pattern"]
        for _, clave, valor in recorrer(documento)
        if clave == "api_key_ref" and isinstance(valor, dict) and "pattern" in valor
    ]
    assert "^[A-Z][A-Z0-9_]{2,63}$" in patrones
