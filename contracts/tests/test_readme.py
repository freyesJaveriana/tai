"""README de `contracts/`: inventario, glosario, comandos V-* y línea de instalación (BR1.5, BR12.2, NFR14.1)."""

import re
from pathlib import Path

import pytest

from veridicus_contracts.tools.check_tag import etiqueta_esperada

TERMINOS_DEL_GLOSARIO = (
    "cancel_token",
    "view_outdated",
    "review_report",
    "review_suggestion",
    "undocumented_fact",
)
CLAVES_V = (
    "V-INSTALL",
    "V-SUITE",
    "V-GUARD",
    "V-TYPES",
    "V-LINT",
    "V-AUDIT",
    "V-GEN",
    "V-SURFACE",
    "V-TS",
    "V-TS-AUDIT",
    "V-PKG",
    "V-ERRORS",
    "V-YAML",
)
DIRECTORIOS_DE_CONTRATOS = (
    "analyzer",
    "api",
    "cli",
    "errors",
    "format",
    "health",
    "integrity",
    "metrics",
    "model_calls",
    "profiles",
    "queues",
    "ui",
)
SUFIJOS = (".yaml", ".json")


def _seccion(texto: str, titulo: str) -> str:
    """Cuerpo de la sección `## titulo` hasta el siguiente encabezado de nivel 2 (vacío si falta)."""
    patron = re.compile(rf"^## {re.escape(titulo)}\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    encontrada = patron.search(texto)
    return encontrada.group(1) if encontrada else ""


def terminos_que_faltan(texto: str) -> list[str]:
    """Términos del glosario que no están en la sección `Glosario de identificadores`."""
    glosario = _seccion(texto, "Glosario de identificadores")
    return [termino for termino in TERMINOS_DEL_GLOSARIO if f"`{termino}`" not in glosario]


def _archivos_de_contratos(raiz: Path) -> list[Path]:
    archivos = [raiz / "limits.v1.yaml"]
    for nombre in DIRECTORIOS_DE_CONTRATOS:
        for ruta in sorted((raiz / nombre).rglob("*")):
            partes = ruta.relative_to(raiz).parts
            if ruta.is_file() and ruta.suffix in SUFIJOS and "fixtures" not in partes:
                archivos.append(ruta)
    return archivos


@pytest.fixture(scope="module")
def readme(contracts_root: Path) -> str:
    ruta = contracts_root / "README.md"
    assert ruta.is_file(), "falta contracts/README.md"
    return ruta.read_text(encoding="utf-8")


def test_el_glosario_tiene_los_cinco_terminos(readme: str) -> None:
    assert terminos_que_faltan(readme) == []


@pytest.mark.parametrize("termino", TERMINOS_DEL_GLOSARIO)
def test_control_negativo_un_readme_sin_un_termino_falla(readme: str, termino: str) -> None:
    sin_el_termino = readme.replace(f"`{termino}`", "")
    assert terminos_que_faltan(sin_el_termino) == [termino]


def test_control_negativo_sin_seccion_de_glosario_faltan_todos() -> None:
    assert terminos_que_faltan("# README\n\n## Otra cosa\n`cancel_token`\n") == list(
        TERMINOS_DEL_GLOSARIO
    )


def test_el_inventario_nombra_cada_archivo_de_contrato(readme: str, contracts_root: Path) -> None:
    inventario = _seccion(readme, "Inventario de contratos")
    assert inventario, "falta la sección Inventario de contratos"
    archivos = _archivos_de_contratos(contracts_root)
    assert len(archivos) >= 30
    faltan = [
        ruta.relative_to(contracts_root).as_posix()
        for ruta in archivos
        if ruta.relative_to(contracts_root).as_posix() not in inventario
    ]
    assert faltan == []


def test_el_readme_tiene_las_secciones_pedidas(readme: str) -> None:
    for titulo in (
        "Inventario de contratos",
        "Cómo cambiar un contrato",
        "La copia de C6",
        "Uso desde un servicio",
        "Comandos V-*",
        "Glosario de identificadores",
        "Instalar desde otro repositorio",
    ):
        assert _seccion(readme, titulo), f"falta la sección: {titulo}"


def test_los_comandos_v_estan_documentados(readme: str) -> None:
    comandos = _seccion(readme, "Comandos V-*")
    assert [clave for clave in CLAVES_V if f"`{clave}`" not in comandos] == []


def test_la_instalacion_usa_la_etiqueta_que_imprime_check_tag(
    readme: str, contracts_root: Path
) -> None:
    etiqueta = etiqueta_esperada(contracts_root / "pyproject.toml")
    instalacion = _seccion(readme, "Instalar desde otro repositorio")
    fuente = (
        'veridicus-contracts = { git = "https://github.com/freyesJaveriana/tai", '
        f'tag = "{etiqueta}", subdirectory = "contracts" }}'
    )
    assert fuente in instalacion
    assert f"--tag {etiqueta}" in instalacion
    assert "#subdirectory=contracts" in instalacion


def test_la_instalacion_no_usa_la_forma_vieja_de_etiqueta(readme: str) -> None:
    instalacion = _seccion(readme, "Instalar desde otro repositorio")
    assert re.search(r'tag = "v\d', instalacion) is None
