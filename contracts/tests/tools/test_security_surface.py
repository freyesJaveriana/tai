"""Huella de seguridad `security-surface.json` (security-design §4.11, DS3, U01-T19).

Cada prueba carga la herramienta con `importar_o_fallar`: mientras no exista, el rojo es un fallo
de la prueba y no un error de recolección (paso 5, R-14 de la revisión 2).
"""

import copy
import difflib
import hashlib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import importar_o_fallar, load_contract, ruta_de

from veridicus_contracts.loaders import load_yaml_text

SECCIONES = {"operations", "schemas", "cookie", "servers", "limits", "metrics", "integrity"}
C1 = "api/console.v2.yaml"
C8 = "integrity/forbidden-vocabulary.v2.yaml"
C25 = "limits.v1.yaml"
VERSIONADA = "security-surface.json"


def herramienta() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.tools.security_surface", "U01-T19")


def diferencia(esperado: bytes, actual: bytes) -> str:
    lineas = difflib.unified_diff(
        esperado.decode("utf-8").splitlines(),
        actual.decode("utf-8").splitlines(),
        "versionada",
        "regenerada",
        lineterm="",
        n=1,
    )
    return "\n".join(list(lineas)[:40])


def secciones_distintas(base: dict[str, Any], otra: dict[str, Any]) -> set[str]:
    return {nombre for nombre in base if base[nombre] != otra[nombre]}


def test_la_huella_tiene_exactamente_las_siete_secciones(contracts_root: Path) -> None:
    huella = herramienta().construir(contracts_root)
    # `schema_version` es la versión que BR1.1 exige a todo contrato propio: no es una sección.
    assert set(huella) == SECCIONES | {"schema_version"}
    assert huella["schema_version"] == "1.0.0"


def test_la_huella_regenerada_es_igual_a_la_versionada(contracts_root: Path) -> None:
    herramientas = herramienta()
    ruta = ruta_de(VERSIONADA)
    if not ruta.is_file():
        pytest.fail(f"huella versionada ausente: {VERSIONADA}")
    versionada = ruta.read_bytes()
    regenerada = herramientas.serializar(herramientas.construir(contracts_root))
    assert regenerada == versionada, diferencia(versionada, regenerada)


def test_dos_generaciones_seguidas_dan_bytes_identicos(contracts_root: Path) -> None:
    herramientas = herramienta()
    primera = herramientas.serializar(herramientas.construir(contracts_root))
    segunda = herramientas.serializar(herramientas.construir(contracts_root))
    assert primera == segunda
    assert primera.endswith(b"}\n")
    assert not primera.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in primera


def test_cubre_los_cuatro_contratos_de_operaciones_y_marca_las_que_encolan(
    contracts_root: Path,
) -> None:
    operaciones = herramienta().construir(contracts_root)["operations"]
    assert set(operaciones) == {"C1", "C16", "C21", "voz_interna"}
    c1 = operaciones["C1"]
    assert c1["POST /auth/login"]["security"] == []
    assert c1["POST /auth/login"]["csrf"] is False
    assert c1["GET /auth/me"]["security"] == ["sessionCookie"]
    encolan = {nombre for nombre, op in c1.items() if op["encola"]}
    assert len(encolan) == 6
    voz = operaciones["voz_interna"]["POST /internal/v1/speech"]
    assert voz["security"] == ["bearerAuth"]
    assert "speech_audio_max_bytes" in voz["limit_marks"]["max_bytes"]


def test_las_secciones_de_cookie_servidores_limites_y_metricas_traen_su_contenido(
    contracts_root: Path,
) -> None:
    huella = herramienta().construir(contracts_root)
    cookie = huella["cookie"]["sessionCookie"]
    assert cookie["x-veridicus-cookie"]["same_site"] == "Strict"
    assert huella["servers"]["C1"] == [{"url": "/api/v1", "variables": {}}]
    catalogo = load_contract(C25)
    assert set(huella["limits"]["limits"]) == set(catalogo["limits"])
    assert huella["limits"]["limits"]["turn_max_chars"]["used_in"] == ["C1", "C2", "C5"]
    assert len(huella["limits"]["relations"]) == len(catalogo["relations"])
    assert all(nombre.startswith("veridicus_") for nombre in huella["metrics"])
    assert huella["metrics"]


def test_la_huella_de_c6_es_el_sha256_de_los_bytes_de_sha256sums(contracts_root: Path) -> None:
    integridad = herramienta().construir(contracts_root)["integrity"]
    esperada = hashlib.sha256(ruta_de("analyzer/v1/SHA256SUMS").read_bytes()).hexdigest()
    assert integridad["analyzer_v1_sha256sums"] == esperada
    assert set(integridad) == {
        "analyzer_v1_sha256sums",
        "error_codes",
        "forbidden_vocabulary",
        "limits",
        "result_labels",
    }
    assert all(len(valor) == 64 for valor in integridad.values())


def test_quitar_la_seguridad_de_una_operacion_cambia_solo_operations(
    contracts_root: Path,
) -> None:
    herramientas = herramienta()
    base = herramientas.construir(contracts_root)
    c1 = copy.deepcopy(load_contract(C1))
    c1["paths"]["/auth/me"]["get"]["security"] = []
    cambiada = herramientas.construir(contracts_root, {C1: c1})
    assert secciones_distintas(base, cambiada) == {"operations"}
    assert cambiada["operations"]["C1"]["GET /auth/me"]["security"] == []


def test_anadir_un_servidor_cambia_solo_servers(contracts_root: Path) -> None:
    herramientas = herramienta()
    base = herramientas.construir(contracts_root)
    c1 = copy.deepcopy(load_contract(C1))
    c1["servers"].append({"url": "https://externo.invalido"})
    cambiada = herramientas.construir(contracts_root, {C1: c1})
    assert secciones_distintas(base, cambiada) == {"servers"}


def test_cambiar_una_cifra_de_c25_cambia_limits_e_integrity(contracts_root: Path) -> None:
    herramientas = herramienta()
    base = herramientas.construir(contracts_root)
    catalogo = copy.deepcopy(load_contract(C25))
    catalogo["limits"]["turn_max_chars"]["value"] += 1
    cambiada = herramientas.construir(contracts_root, {C25: catalogo})
    assert secciones_distintas(base, cambiada) == {"limits", "integrity"}
    assert base["integrity"]["limits"] != cambiada["integrity"]["limits"]


def test_un_comentario_o_un_espacio_del_yaml_no_cambia_la_huella(contracts_root: Path) -> None:
    herramientas = herramienta()
    base = herramientas.construir(contracts_root)
    sustituciones = {}
    for relativa in (C8, C25, "errors/error-codes.v2.yaml", "ui/result-labels.v2.yaml"):
        texto = ruta_de(relativa).read_text(encoding="utf-8")
        retocado = "# comentario nuevo\n\n" + texto.replace("\n", "   \n\n", 3) + "\n# final\n"
        assert retocado != texto
        sustituciones[relativa] = load_yaml_text(retocado)
    assert herramientas.construir(contracts_root, sustituciones) == base


def test_check_sale_con_uno_sobre_una_copia_cambiada_y_muestra_la_diferencia(
    contracts_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    herramientas = herramienta()
    copia = tmp_path / VERSIONADA
    copia.write_bytes(ruta_de(VERSIONADA).read_bytes())
    assert herramientas.main(["--check", "--output", str(copia)]) == 0
    capsys.readouterr()
    copia.write_bytes(copia.read_bytes().replace(b"Strict", b"Lax", 1))
    assert herramientas.main(["--check", "--output", str(copia)]) == 1
    salida = capsys.readouterr().out
    assert "Lax" in salida
    assert "Strict" in salida
    assert herramientas.main(["--output", str(copia)]) == 1  # sin argumentos equivale a --check
    assert herramientas.main(["--check", "--output", str(tmp_path / "ausente.json")]) == 1


def test_solo_write_escribe_el_archivo(contracts_root: Path, tmp_path: Path) -> None:
    herramientas = herramienta()
    destino = tmp_path / VERSIONADA
    assert herramientas.main(["--check", "--output", str(destino)]) == 1
    assert not destino.exists()
    assert herramientas.main(["--write", "--output", str(destino)]) == 0
    assert destino.read_bytes() == ruta_de(VERSIONADA).read_bytes()
    assert herramientas.main(["--check", "--output", str(destino)]) == 0


def test_la_herramienta_rechaza_check_y_write_juntos(tmp_path: Path) -> None:
    herramientas = herramienta()
    with pytest.raises(SystemExit) as salida:
        herramientas.main(["--check", "--write", "--output", str(tmp_path / "x.json")])
    assert salida.value.code == 2
