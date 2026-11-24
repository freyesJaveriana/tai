"""Guardia de carga segura de YAML y de subprocesos (security-design §4.1 y §4.2, NFR10.4, NFR10.5).

`checks/loader_usage.py` recorre los `.py` de `src/` y `tests/` con `ast`. Incluye la lista cerrada de
excepciones de E-19 y la prueba AST de E32 (BR12.1): ningún módulo importa `contracts.` como nombre de
primer nivel.
"""

import ast
from pathlib import Path
from types import ModuleType

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

from veridicus_contracts.loaders import LoadError, load_yaml_text


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.loader_usage", "T18, paso 19")


def _modulo(raiz: Path, relativa: str, codigo: str) -> Path:
    ruta = raiz / relativa
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(codigo, encoding="utf-8")
    return ruta


def _problemas(guardia: ModuleType, raiz: Path, relativa: str, codigo: str) -> list[str]:
    archivo = _modulo(raiz, relativa, codigo)
    problemas: list[str] = guardia.scan([archivo], raiz=raiz)
    for problema in problemas:
        assert problema.startswith(f"{archivo.as_posix()}:"), problema
    return problemas


def test_el_repositorio_real_no_usa_pyyaml_ni_subprocesos_fuera_de_las_excepciones(
    guardia: ModuleType,
) -> None:
    visto = {ruta.name for ruta in guardia.archivos([CONTRACTS_ROOT / "src", CONTRACTS_ROOT / "tests"])}
    # La guardia no pasa en vacío: recorre el único módulo que crea el lector y las pruebas.
    assert {"loaders.py", "test_package_map.py", "test_loader_usage.py"} <= visto
    assert guardia.comprobar(CONTRACTS_ROOT) == []


def test_import_de_pyyaml_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    for codigo in ("import yaml\n", "from yaml import safe_load\n", "import yaml.constructor\n"):
        problemas = _problemas(guardia, tmp_path, "src/veridicus_contracts/otro.py", codigo)
        assert len(problemas) == 1 and "PyYAML" in problemas[0] and "(NFR10.4)" in problemas[0]
    # ruamel.yaml es la biblioteca permitida: importarla no es el defecto.
    assert _problemas(guardia, tmp_path, "src/veridicus_contracts/otro.py", "import ruamel.yaml\n") == []


def test_un_modulo_sintetico_con_yaml_unsafe_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    codigo = 'from ruamel.yaml import YAML\n\nlector = YAML(typ="unsafe")\n'
    problemas = _problemas(guardia, tmp_path, "src/veridicus_contracts/otro.py", codigo)
    assert len(problemas) == 2
    assert any("YAML(...) fuera de loaders.py" in p for p in problemas)
    assert any('typ distinto de "safe"' in p for p in problemas)
    assert all(p.split(": ", 1)[0].endswith(":3") for p in problemas)


def test_yaml_solo_se_crea_en_loaders_y_con_typ_safe(guardia: ModuleType, tmp_path: Path) -> None:
    loaders = "src/veridicus_contracts/loaders.py"
    seguro = 'from ruamel.yaml import YAML\n\nlector = YAML(typ="safe", pure=True)\n'
    assert _problemas(guardia, tmp_path, loaders, seguro) == []
    # Fuera de loaders.py, aun con typ="safe", la llamada es un defecto.
    fuera = _problemas(guardia, tmp_path, "tests/otro.py", seguro)
    assert len(fuera) == 1 and "YAML(...) fuera de loaders.py" in fuera[0]
    # La ruta completa a contracts/ es la que cuenta, no el final de la ruta.
    for parecida in ("src/otro/veridicus_contracts/loaders.py", "otro/src/veridicus_contracts/loaders.py"):
        problemas = _problemas(guardia, tmp_path, parecida, seguro)
        assert len(problemas) == 1 and "YAML(...) fuera de loaders.py" in problemas[0]
    # Dentro de loaders.py, sin typ, con otro typ o con un typ calculado, falla por el typ.
    for codigo in (
        "import ruamel.yaml\n\nlector = ruamel.yaml.YAML()\n",
        'import ruamel.yaml\n\nlector = ruamel.yaml.YAML(typ="rt")\n',
        'from ruamel.yaml import YAML\n\nTIPO = "safe"\nlector = YAML(typ=TIPO)\n',
    ):
        problemas = _problemas(guardia, tmp_path, loaders, codigo)
        assert len(problemas) == 1 and 'typ distinto de "safe"' in problemas[0]


def test_load_all_y_loader_son_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    casos = {
        "documentos = lector.load_all(texto)\n": "load_all",
        "from ruamel.yaml import load_all\n": "load_all",
        "datos = cargar(texto, Loader=Peligroso)\n": "Loader=",
    }
    for codigo, termino in casos.items():
        problemas = _problemas(guardia, tmp_path, "src/veridicus_contracts/otro.py", codigo)
        assert len(problemas) == 1 and termino in problemas[0] and "(NFR10.4)" in problemas[0]


@pytest.mark.parametrize(
    ("codigo", "modulo"),
    [
        ("import subprocess\n", "subprocess"),
        ("import subprocess as sp\n", "subprocess"),
        ("from subprocess import run\n", "subprocess"),
        ("import multiprocessing\n", "multiprocessing"),
        ("import multiprocessing.pool\n", "multiprocessing"),
        ("from multiprocessing import Pool\n", "multiprocessing"),
        ("import os\n\nos.system('x')\n", "os.system"),
        ("from os import system\n", "os.system"),
    ],
)
def test_subprocesos_en_src_y_tests_son_rojo(
    guardia: ModuleType, tmp_path: Path, codigo: str, modulo: str
) -> None:
    for relativa in ("src/veridicus_contracts/checks/otro.py", "tests/otro.py", "src/veridicus_contracts/x.py"):
        problemas = _problemas(guardia, tmp_path, relativa, codigo)
        assert len(problemas) == 1, (relativa, problemas)
        assert modulo in problemas[0] and "(NFR10.5)" in problemas[0]


def test_e19_la_lista_de_excepciones_es_cerrada_y_exacta(guardia: ModuleType) -> None:
    assert [(e.ruta, set(e.modulos)) for e in guardia.EXCEPCIONES] == [
        ("src/veridicus_contracts/tools/check_package.py", {"subprocess"}),
        ("tests/test_package_map.py", {"subprocess"}),
    ]
    assert all(e.motivo.strip() for e in guardia.EXCEPCIONES)
    assert isinstance(guardia.EXCEPCIONES, tuple)


def test_e19_cada_excepcion_admite_solo_su_modulo(guardia: ModuleType, tmp_path: Path) -> None:
    for excepcion in guardia.EXCEPCIONES:
        # Su módulo admitido sí pasa, bajo cualquier raíz que termine en su ruta.
        assert _problemas(guardia, tmp_path, excepcion.ruta, "import subprocess\n") == []
        assert _problemas(guardia, tmp_path, excepcion.ruta, "from subprocess import run\n") == []
        # Otro módulo prohibido en el mismo archivo sigue en rojo.
        for codigo, modulo in (
            ("import os\n\nos.system('x')\n", "os.system"),
            ("import multiprocessing\n", "multiprocessing"),
        ):
            problemas = _problemas(guardia, tmp_path, excepcion.ruta, codigo)
            assert len(problemas) == 1 and modulo in problemas[0]
        # La excepción no exime lo demás de la regla de carga segura.
        assert len(_problemas(guardia, tmp_path, excepcion.ruta, "import yaml\n")) == 1
    # Otro archivo con subprocess sigue en rojo, aunque se llame o termine igual (P-T18-7 no aceptada:
    # la excepción se compara por la ruta relativa completa a contracts/).
    for relativa in (
        "tests/test_otro.py",
        "tests/checks/test_package_map.py",
        "tests/test_package_map.pyi.py",
        "otro/tests/test_package_map.py",
        "services/x/tests/test_package_map.py",
        "otro/src/veridicus_contracts/tools/check_package.py",
    ):
        problemas = _problemas(guardia, tmp_path, relativa, "import subprocess\n")
        assert len(problemas) == 1 and "subprocess" in problemas[0], relativa
    # Sin una raíz, la excepción no exime nada: U10 y U11 no heredan las de contracts/.
    archivo = _modulo(tmp_path, "tests/test_package_map.py", "import subprocess\n")
    assert len(guardia.scan([archivo])) == 1
    # Una raíz que no contiene el archivo tampoco lo exime.
    assert len(guardia.scan([archivo], raiz=tmp_path / "otra")) == 1


def test_un_archivo_que_no_se_puede_interpretar_es_un_problema(guardia: ModuleType, tmp_path: Path) -> None:
    problemas = _problemas(guardia, tmp_path, "src/veridicus_contracts/roto.py", "def (:\n")
    assert len(problemas) == 1 and "no se pudo interpretar" in problemas[0]


def test_scan_recorre_directorios_y_archivos_y_ignora_lo_que_no_es_python(
    guardia: ModuleType, tmp_path: Path
) -> None:
    _modulo(tmp_path, "src/veridicus_contracts/a.py", "import yaml\n")
    _modulo(tmp_path, "src/veridicus_contracts/sub/b.py", "import subprocess\n")
    _modulo(tmp_path, "src/veridicus_contracts/leeme.txt", "import yaml\n")
    suelto = _modulo(tmp_path, "suelto.py", "import yaml\n")
    problemas = guardia.scan([tmp_path / "src", suelto])
    assert len(problemas) == 3
    assert problemas == sorted(problemas)
    assert guardia.scan([str(tmp_path / "src" / "veridicus_contracts" / "leeme.txt")]) == []


def test_controles_del_cargador_yaml_de_4_1(guardia: ModuleType) -> None:
    """Un C8 con una clave repetida y un YAML con `!!python/object` no se cargan (§4.1).

    El control del término repetido de la lista de C8 es otro y vive en
    `test_veracity.py::test_c8_con_un_termino_nuevo_o_repetido_da_br51`.
    """
    texto = (CONTRACTS_ROOT / "integrity" / "forbidden-vocabulary.v2.yaml").read_text(encoding="utf-8")
    assert load_contract("integrity/forbidden-vocabulary.v2.yaml")["schema_version"] == "2.0.0"
    with pytest.raises(LoadError):
        load_yaml_text(texto + "schema_version: 2.0.0\n")
    with pytest.raises(LoadError):
        load_yaml_text("a: !!python/object:os.system x\n")


def _importa_contracts(codigo: str) -> bool:
    for nodo in ast.walk(ast.parse(codigo)):
        if isinstance(nodo, ast.Import) and any(a.name.split(".")[0] == "contracts" for a in nodo.names):
            return True
        if isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and (nodo.module or "").split(".")[0] == "contracts":
            return True
    return False


def test_e32_ningun_modulo_importa_contracts_como_nombre_de_primer_nivel() -> None:
    """BR12.1: el paquete se importa como `veridicus_contracts`, nunca como `contracts`."""
    archivos = sorted((CONTRACTS_ROOT / "src").rglob("*.py")) + sorted((CONTRACTS_ROOT / "tests").rglob("*.py"))
    assert len(archivos) > 20
    infractores = [
        a.relative_to(CONTRACTS_ROOT).as_posix()
        for a in archivos
        if _importa_contracts(a.read_text(encoding="utf-8"))
    ]
    assert infractores == []
    # Controles negativos: la prueba sí detecta las formas prohibidas y no se confunde con el paquete.
    assert _importa_contracts("import contracts\n")
    assert _importa_contracts("import contracts.analyzer\n")
    assert _importa_contracts("from contracts.analyzer import x\n")
    assert not _importa_contracts("from veridicus_contracts import loaders\n")
    assert not _importa_contracts("from . import contracts\n")
