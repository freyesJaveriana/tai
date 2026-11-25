"""README de `contracts/`: inventario, glosario, comandos V-* y línea de instalación (BR1.5, BR12.2, NFR14.1)."""

import re
from pathlib import Path

import pytest

from veridicus_contracts.tools.check_tag import main as check_tag_main

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
SIN_NUMERO = "(sin número)"

# Tabla fija del registro: contract-summary.md (tabla de contratos y archivos «sin número de contrato»)
# y functional-spec.md §1 (inventario que entrega U1). Un ID que no esté aquí es un ID inventado.
ID_POR_ARCHIVO = {
    "api/console.v2.yaml": "C1",
    "queues/runs.v2.yaml": "C2",
    "queues/results.v2.yaml": "C3",
    "queues/speech.v2.yaml": "C5",
    "analyzer/v1/entrada.schema.json": "C6",
    "analyzer/v1/salida.schema.json": "C6",
    "analyzer/v1/SHA256SUMS": SIN_NUMERO,
    "integrity/review-suggestion.v2.json": "C7",
    "integrity/forbidden-vocabulary.v2.yaml": "C8",
    "integrity/neutral-clarification.v1.yaml": "C8",
    "integrity/notice.v1.yaml": "C8",
    "src/veridicus_contracts/human_review.py": "C10",
    "src/veridicus_contracts/report_ports.py": "C11",
    "src/veridicus_contracts/identity.py": "C12",
    "src/veridicus_contracts/model_calls.py": "C13",
    "metrics/review.v2.yaml": "C15",
    "health/health.v2.yaml": "C16",
    "profiles/profile-base.schema.v1.yaml": "C18",
    "profiles/profiles.schema.v1.yaml": "C18",
    "profiles/effective-config.v1.yaml": "C18",
    "profiles/prices.schema.v1.yaml": "C18",
    "cli/report.schema.v2.yaml": "C19",
    "model_calls/model-call.v1.yaml": "C19",
    "api/anonymizer-proxy.v1.yaml": "C21",
    "src/veridicus_contracts/access_log.py": "C23",
    "src/veridicus_contracts/retention.py": "C24",
    "limits.v1.yaml": "C25",
    "api/speech-internal.v1.yaml": SIN_NUMERO,
    "integrity/testimony-warning-cases.v1.yaml": SIN_NUMERO,
    "integrity/scan-cases.v1.yaml": SIN_NUMERO,
    "ui/result-labels.v2.yaml": SIN_NUMERO,
    "format/datetime.v1.yaml": SIN_NUMERO,
    "errors/error-codes.v2.yaml": SIN_NUMERO,
    "model_calls/role-translation.v1.yaml": SIN_NUMERO,
    "metrics/text-flow.v1.yaml": SIN_NUMERO,
    "metrics/voice.v1.yaml": SIN_NUMERO,
    "metrics/session-lifecycle.v1.yaml": SIN_NUMERO,
    "metrics/assistant-extras.v1.yaml": SIN_NUMERO,
    "metrics/anonymizer.v1.yaml": SIN_NUMERO,
}
# Qué workflow corre cada comando V-*; V-SURFACE va dentro de la suite y V-YAML lo corre repo-level0.
QUIEN_CORRE = {clave: "contracts-level0.yml" for clave in CLAVES_V}
QUIEN_CORRE["V-SURFACE"] = "la suite (`V-SUITE`)"
QUIEN_CORRE["V-YAML"] = "repo-level0.yml"
FILA_DEL_INVENTARIO = re.compile(
    r"^\|\s*(?P<id>[^|]+?)\s*\|[^|]*\|\s*`(?P<archivo>[^`|]+)`\s*\|[^|]*\|\s*$", re.MULTILINE
)


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


def discrepancias_del_inventario(texto: str, raiz: Path) -> list[str]:
    """Filas del inventario que no coinciden con `ID_POR_ARCHIVO` o con un archivo que existe."""
    filas = {
        fila["archivo"]: fila["id"]
        for fila in FILA_DEL_INVENTARIO.finditer(_seccion(texto, "Inventario de contratos"))
    }
    problemas = [f"falta la fila de {archivo}" for archivo in ID_POR_ARCHIVO if archivo not in filas]
    for archivo, identificador in filas.items():
        if archivo not in ID_POR_ARCHIVO:
            problemas.append(f"fila de {archivo} que no está en el registro")
        elif identificador != ID_POR_ARCHIVO[archivo]:
            problemas.append(
                f"{archivo}: ID {identificador} y el registro dice {ID_POR_ARCHIVO[archivo]}"
            )
        if not (raiz / archivo).is_file():
            problemas.append(f"{archivo} no existe")
    return problemas


def filas_de_comandos_v(texto: str) -> dict[str, str]:
    """Fila completa de cada clave `V-*` de la sección de comandos."""
    filas: dict[str, str] = {}
    for linea in _seccion(texto, "Comandos V-*").splitlines():
        for clave in CLAVES_V:
            if linea.startswith(f"| `{clave}` |"):
                filas[clave] = linea
    return filas


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


def test_el_inventario_coincide_con_la_tabla_del_registro(readme: str, contracts_root: Path) -> None:
    assert discrepancias_del_inventario(readme, contracts_root) == []


def test_todo_archivo_de_contrato_del_arbol_esta_en_la_tabla_del_registro(
    contracts_root: Path,
) -> None:
    del_arbol = {
        ruta.relative_to(contracts_root).as_posix() for ruta in _archivos_de_contratos(contracts_root)
    }
    assert sorted(del_arbol - ID_POR_ARCHIVO.keys()) == []


@pytest.mark.parametrize("archivo", sorted(ID_POR_ARCHIVO))
def test_control_negativo_un_id_inventado_en_una_fila_se_detecta(
    readme: str, contracts_root: Path, archivo: str
) -> None:
    lineas = readme.splitlines()
    posiciones = [i for i, linea in enumerate(lineas) if f"| `{archivo}` |" in linea]
    assert len(posiciones) == 1
    celdas = lineas[posiciones[0]].split("|")
    celdas[1] = " C99 "
    lineas[posiciones[0]] = "|".join(celdas)
    problemas = discrepancias_del_inventario("\n".join(lineas), contracts_root)
    assert problemas == [f"{archivo}: ID C99 y el registro dice {ID_POR_ARCHIVO[archivo]}"]


@pytest.mark.parametrize("archivo", sorted(ID_POR_ARCHIVO))
def test_control_negativo_una_fila_que_falta_se_detecta(
    readme: str, contracts_root: Path, archivo: str
) -> None:
    sin_la_fila = "\n".join(
        linea for linea in readme.splitlines() if f"| `{archivo}` |" not in linea
    )
    assert discrepancias_del_inventario(sin_la_fila, contracts_root) == [
        f"falta la fila de {archivo}"
    ]


def test_control_negativo_una_fila_inventada_se_detecta(readme: str, contracts_root: Path) -> None:
    inventada = readme.replace(
        "| ID | Contrato | Archivo | Versión |\n",
        "| ID | Contrato | Archivo | Versión |\n| C30 | Inventado | `api/inventado.v1.yaml` | 1.0.0 |\n",
    )
    assert discrepancias_del_inventario(inventada, contracts_root) == [
        "fila de api/inventado.v1.yaml que no está en el registro",
        "api/inventado.v1.yaml no existe",
    ]


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


def test_cada_comando_v_dice_que_workflow_lo_corre(readme: str) -> None:
    filas = filas_de_comandos_v(readme)
    assert sorted(filas) == sorted(CLAVES_V)
    equivocadas = {
        clave: QUIEN_CORRE[clave] for clave, fila in filas.items() if QUIEN_CORRE[clave] not in fila
    }
    assert equivocadas == {}


def test_control_negativo_v_yaml_atribuido_a_otro_workflow_se_detecta(readme: str) -> None:
    fila = filas_de_comandos_v(readme)["V-YAML"]
    assert QUIEN_CORRE["V-YAML"] in fila
    assert QUIEN_CORRE["V-YAML"] not in fila.replace("repo-level0.yml", "contracts-level0.yml")


def test_la_instalacion_usa_la_etiqueta_que_imprime_check_tag(
    readme: str,
    contracts_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(contracts_root)
    assert check_tag_main([]) == 0
    etiqueta = capsys.readouterr().out.strip()
    assert re.fullmatch(r"contracts-v\d+\.\d+\.\d+", etiqueta)
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
