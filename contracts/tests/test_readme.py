"""README de `contracts/`: inventario, glosario, comandos V-* y línea de instalación (BR1.5, BR12.2, NFR14.1)."""

import re
from pathlib import Path

import pytest

from veridicus_contracts.loaders import load_file
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
# Versión de cada fila. Para los archivos de datos la prueba la compara además con la que declara el
# archivo; para los `.py` y SHA256SUMS (que no la declaran como dato) la fuente es el registro:
# contract-summary.md (`# contracts/python/<módulo>.py — vX.Y.Z`; C24 sube a 1.1.0 por NFRD-U13-08).
VERSION_POR_ARCHIVO = {
    "api/console.v2.yaml": "2.0.0",
    "queues/runs.v2.yaml": "2.0.0",
    "queues/results.v2.yaml": "2.0.0",
    "queues/speech.v2.yaml": "2.0.0",
    "analyzer/v1/entrada.schema.json": "1.0.0",
    "analyzer/v1/salida.schema.json": "1.0.0",
    "analyzer/v1/SHA256SUMS": "1.0.0",
    "integrity/review-suggestion.v2.json": "2.0.0",
    "integrity/forbidden-vocabulary.v2.yaml": "2.1.0",
    "integrity/neutral-clarification.v1.yaml": "1.1.0",
    "integrity/notice.v1.yaml": "1.0.0",
    "src/veridicus_contracts/human_review.py": "2.0.0",
    "src/veridicus_contracts/report_ports.py": "2.0.0",
    "src/veridicus_contracts/identity.py": "2.0.0",
    "src/veridicus_contracts/model_calls.py": "1.0.0",
    "metrics/review.v2.yaml": "2.0.0",
    "health/health.v2.yaml": "2.0.0",
    "profiles/profile-base.schema.v1.yaml": "1.0.0",
    "profiles/profiles.schema.v1.yaml": "1.0.0",
    "profiles/effective-config.v1.yaml": "1.0.0",
    "profiles/prices.schema.v1.yaml": "1.0.0",
    "cli/report.schema.v2.yaml": "2.0.0",
    "model_calls/model-call.v1.yaml": "1.0.0",
    "api/anonymizer-proxy.v1.yaml": "1.0.0",
    "src/veridicus_contracts/access_log.py": "1.0.0",
    "src/veridicus_contracts/retention.py": "1.1.0",
    "limits.v1.yaml": "1.0.0",
    "api/speech-internal.v1.yaml": "1.0.0",
    "integrity/testimony-warning-cases.v1.yaml": "1.0.0",
    "integrity/scan-cases.v1.yaml": "1.0.0",
    "ui/result-labels.v2.yaml": "2.0.0",
    "format/datetime.v1.yaml": "1.0.0",
    "errors/error-codes.v2.yaml": "2.0.0",
    "model_calls/role-translation.v1.yaml": "1.0.0",
    "metrics/text-flow.v1.yaml": "1.0.0",
    "metrics/voice.v1.yaml": "1.0.0",
    "metrics/session-lifecycle.v1.yaml": "1.0.0",
    "metrics/assistant-extras.v1.yaml": "1.0.0",
    "metrics/anonymizer.v1.yaml": "1.0.0",
}
# Qué workflow corre cada comando V-*; V-SURFACE va dentro de la suite y V-YAML lo corre repo-level0.
QUIEN_CORRE = {clave: "contracts-level0.yml" for clave in CLAVES_V}
QUIEN_CORRE["V-SURFACE"] = "la suite (`V-SUITE`)"
QUIEN_CORRE["V-YAML"] = "repo-level0.yml"
FILA_DEL_INVENTARIO = re.compile(
    r"^\|\s*(?P<id>[^|]+?)\s*\|[^|]*\|\s*`(?P<archivo>[^`|]+)`\s*\|\s*(?P<version>[^|]*?)\s*\|\s*$",
    re.MULTILINE,
)


def _seccion(texto: str, titulo: str) -> str:
    """Cuerpo de la sección `## titulo` hasta el siguiente encabezado de nivel 2 (vacío si falta)."""
    patron = re.compile(rf"^## {re.escape(titulo)}\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    encontrada = patron.search(texto)
    return encontrada.group(1) if encontrada else ""


def terminos_que_faltan(texto: str) -> list[str]:
    """Términos del glosario único (`docs/glosario.md`) que no están en la sección `Contratos (U1)`."""
    glosario = _seccion(texto, "Contratos (U1)")
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
    """Filas del inventario que no coinciden con las tablas fijas o con un archivo que existe.

    Compara el ID y la versión de cada fila, rechaza un archivo repetido (con cualquier ID) y
    exige que cada archivo exista.
    """
    filas = [
        (fila["archivo"], fila["id"], fila["version"])
        for fila in FILA_DEL_INVENTARIO.finditer(_seccion(texto, "Inventario de contratos"))
    ]
    nombres = [archivo for archivo, _, _ in filas]
    problemas = [
        f"falta la fila de {archivo}" for archivo in ID_POR_ARCHIVO if archivo not in nombres
    ]
    for archivo in dict.fromkeys(nombres):
        if nombres.count(archivo) > 1:
            problemas.append(f"fila repetida de {archivo}")
    for archivo, identificador, version in filas:
        if archivo not in ID_POR_ARCHIVO:
            problemas.append(f"fila de {archivo} que no está en el registro")
        else:
            if identificador != ID_POR_ARCHIVO[archivo]:
                problemas.append(
                    f"{archivo}: ID {identificador} y el registro dice {ID_POR_ARCHIVO[archivo]}"
                )
            if version != VERSION_POR_ARCHIVO[archivo]:
                problemas.append(
                    f"{archivo}: versión {version} y el registro dice {VERSION_POR_ARCHIVO[archivo]}"
                )
        if not (raiz / archivo).is_file():
            problemas.append(f"{archivo} no existe")
    return problemas


def version_declarada(ruta: Path) -> str | None:
    """Versión que declara un archivo de datos, o `None` si no declara ninguna (`.py`, SHA256SUMS)."""
    if ruta.suffix not in SUFIJOS:
        return None
    datos = load_file(ruta)
    candidatas = (
        datos.get("x-veridicus-version"),
        datos.get("schema_version"),
        datos.get("version"),
        (datos.get("info") or {}).get("version"),
        ((datos.get("properties") or {}).get("contrato") or {}).get("const"),
    )
    return next((valor for valor in candidatas if isinstance(valor, str)), None)


def versiones_del_arbol_que_no_coinciden(raiz: Path, tabla: dict[str, str]) -> list[str]:
    """Archivos de datos cuya versión declarada difiere de la de `tabla`."""
    problemas = []
    for archivo, esperada in tabla.items():
        declarada = version_declarada(raiz / archivo)
        if declarada is not None and declarada != esperada:
            problemas.append(f"{archivo}: declara {declarada} y la tabla dice {esperada}")
    return problemas


def workflows_que_no_coinciden(texto: str) -> dict[str, str]:
    """Claves V-* cuya fila no nombra el workflow de `QUIEN_CORRE`, con lo que se esperaba."""
    filas = filas_de_comandos_v(texto)
    faltantes = {clave: "falta la fila" for clave in CLAVES_V if clave not in filas}
    equivocadas = {
        clave: QUIEN_CORRE[clave]
        for clave, fila in filas.items()
        if QUIEN_CORRE[clave] not in fila.split("|")[-2]
    }
    return {**faltantes, **equivocadas}


def con_celda_cambiada(texto: str, archivo: str, columna: int, valor: str) -> str:
    """Copia del README con la celda `columna` (1 = ID, 4 = versión) de la fila de `archivo` cambiada."""
    lineas = texto.splitlines()
    posiciones = [i for i, linea in enumerate(lineas) if f"| `{archivo}` |" in linea]
    assert len(posiciones) == 1
    celdas = lineas[posiciones[0]].split("|")
    celdas[columna] = f" {valor} "
    lineas[posiciones[0]] = "|".join(celdas)
    return "\n".join(lineas)


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


@pytest.fixture(scope="module")
def glosario(contracts_root: Path) -> str:
    """El glosario único del repositorio (`team.md`, Code Style): `docs/glosario.md`."""
    ruta = contracts_root.parent / "docs" / "glosario.md"
    assert ruta.is_file(), "falta docs/glosario.md"
    return ruta.read_text(encoding="utf-8")


def test_el_glosario_tiene_los_cinco_terminos(glosario: str) -> None:
    assert terminos_que_faltan(glosario) == []


@pytest.mark.parametrize("termino", TERMINOS_DEL_GLOSARIO)
def test_control_negativo_un_glosario_sin_un_termino_falla(glosario: str, termino: str) -> None:
    sin_el_termino = glosario.replace(f"`{termino}`", "")
    assert terminos_que_faltan(sin_el_termino) == [termino]


def test_el_readme_enlaza_el_glosario_unico_y_no_lo_repite(readme: str) -> None:
    seccion = _seccion(readme, "Glosario de identificadores")
    assert "../docs/glosario.md" in seccion
    assert [t for t in TERMINOS_DEL_GLOSARIO if f"| `{t}` |" in readme] == []


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


def test_el_inventario_coincide_con_la_tabla_del_registro(
    readme: str, contracts_root: Path
) -> None:
    assert discrepancias_del_inventario(readme, contracts_root) == []


def test_todo_archivo_de_contrato_del_arbol_esta_en_la_tabla_del_registro(
    contracts_root: Path,
) -> None:
    del_arbol = {
        ruta.relative_to(contracts_root).as_posix()
        for ruta in _archivos_de_contratos(contracts_root)
    }
    assert sorted(del_arbol - ID_POR_ARCHIVO.keys()) == []


@pytest.mark.parametrize("archivo", sorted(ID_POR_ARCHIVO))
def test_control_negativo_un_id_inventado_en_una_fila_se_detecta(
    readme: str, contracts_root: Path, archivo: str
) -> None:
    alterado = con_celda_cambiada(readme, archivo, 1, "C99")
    problemas = discrepancias_del_inventario(alterado, contracts_root)
    assert problemas == [f"{archivo}: ID C99 y el registro dice {ID_POR_ARCHIVO[archivo]}"]


@pytest.mark.parametrize("archivo", sorted(VERSION_POR_ARCHIVO))
def test_control_negativo_una_version_equivocada_en_una_fila_se_detecta(
    readme: str, contracts_root: Path, archivo: str
) -> None:
    alterado = con_celda_cambiada(readme, archivo, 4, "7.0.0")
    problemas = discrepancias_del_inventario(alterado, contracts_root)
    assert problemas == [
        f"{archivo}: versión 7.0.0 y el registro dice {VERSION_POR_ARCHIVO[archivo]}"
    ]


def test_las_tablas_fijas_tienen_los_mismos_archivos() -> None:
    assert sorted(VERSION_POR_ARCHIVO) == sorted(ID_POR_ARCHIVO)


def test_la_version_de_cada_archivo_de_datos_es_la_de_la_tabla_fija(contracts_root: Path) -> None:
    assert versiones_del_arbol_que_no_coinciden(contracts_root, VERSION_POR_ARCHIVO) == []
    declaradas = [
        archivo
        for archivo in VERSION_POR_ARCHIVO
        if version_declarada(contracts_root / archivo) is not None
    ]
    assert len(declaradas) >= 30


def test_control_negativo_una_version_de_la_tabla_que_no_es_la_del_archivo_se_detecta(
    contracts_root: Path,
) -> None:
    alterada = {**VERSION_POR_ARCHIVO, "limits.v1.yaml": "7.0.0"}
    assert versiones_del_arbol_que_no_coinciden(contracts_root, alterada) == [
        "limits.v1.yaml: declara 1.0.0 y la tabla dice 7.0.0"
    ]


@pytest.mark.parametrize("archivo", sorted(ID_POR_ARCHIVO))
@pytest.mark.parametrize("identificador", ["C99", None])
def test_control_negativo_un_archivo_repetido_se_detecta(
    readme: str, contracts_root: Path, archivo: str, identificador: str | None
) -> None:
    lineas = readme.splitlines()
    fila = next(linea for linea in lineas if f"| `{archivo}` |" in linea)
    repetida = (
        fila if identificador is None else con_celda_cambiada(fila, archivo, 1, identificador)
    )
    alterado = readme.replace(fila, fila + "\n" + repetida, 1)
    problemas = discrepancias_del_inventario(alterado, contracts_root)
    esperados = [f"fila repetida de {archivo}"]
    if identificador is not None:
        esperados.append(f"{archivo}: ID C99 y el registro dice {ID_POR_ARCHIVO[archivo]}")
    assert problemas == esperados


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
    assert workflows_que_no_coinciden(readme) == {}


@pytest.mark.parametrize("clave", CLAVES_V)
def test_control_negativo_un_comando_v_atribuido_a_otro_workflow_se_detecta(
    readme: str, clave: str
) -> None:
    otro = "otro-workflow.yml"
    lineas = readme.splitlines()
    for i, linea in enumerate(lineas):
        if linea.startswith(f"| `{clave}` |"):
            celdas = linea.split("|")
            celdas[-2] = f" {otro} "
            lineas[i] = "|".join(celdas)
    alterado = "\n".join(lineas)
    assert workflows_que_no_coinciden(alterado) == {clave: QUIEN_CORRE[clave]}


def test_control_negativo_v_yaml_en_contracts_level0_se_detecta(readme: str) -> None:
    alterado = "\n".join(
        linea.replace("repo-level0.yml", "contracts-level0.yml")
        if linea.startswith("| `V-YAML` |")
        else linea
        for linea in readme.splitlines()
    )
    assert workflows_que_no_coinciden(alterado) == {"V-YAML": QUIEN_CORRE["V-YAML"]}


def test_v_yaml_aclara_lo_que_corre_repo_level0(readme: str) -> None:
    fila = filas_de_comandos_v(readme)["V-YAML"]
    assert "yamllint -s .github/" in fila
    assert ".pre-commit-config.yaml" in fila.split("|")[-2]


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
