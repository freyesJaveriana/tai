"""Pruebas de la compuerta de cobertura de U11 (paso 14): dos casos verdes y los controles negativos (R-09)."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from veridicus_incoherence_analyzer.testing import coverage_gate as gate

PACKAGES = (
    "veridicus_incoherence_analyzer",
    "veridicus_model_gateway",
    "veridicus_execution_profiles",
    "veridicus_integrity_policy",
)


def _entry(
    statements: int = 10, covered: int = 10, branches: int = 4, hit: int = 4
) -> dict[str, Any]:
    return {
        "summary": {
            "num_statements": statements,
            "covered_lines": covered,
            "num_branches": branches,
            "covered_branches": hit,
        }
    }


def _report(package: str, **overrides: dict[str, Any]) -> dict[str, Any]:
    """Un informe sano: cada módulo guardia del paquete al 100 % y un archivo ordinario al 90 %."""
    prefix = f"src/{package}/"
    files: dict[str, Any] = {f"{prefix}{name}": _entry() for name in gate.GUARD_MODULES[package]}
    files[f"{prefix}otro.py"] = _entry(statements=10, covered=9, branches=2, hit=1)
    for name, entry in overrides.items():
        files[f"{prefix}{name}"] = entry
    return {"files": files}


def _healthy() -> list[dict[str, Any]]:
    return [_report(package) for package in PACKAGES]


def _write(tmp_path: Path, reports: list[Mapping[str, Any]]) -> list[str]:
    paths = []
    for index, report in enumerate(reports):
        path = tmp_path / f"coverage{index}.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        paths.append(str(path))
    return paths


def test_los_nueve_modulos_guardia_del_plan() -> None:
    todos = {f"{p}/{m}" for p, modulos in gate.GUARD_MODULES.items() for m in modulos}
    assert todos == {
        "veridicus_incoherence_analyzer/domain/quotes.py",
        "veridicus_incoherence_analyzer/domain/filter.py",
        "veridicus_incoherence_analyzer/domain/run_state.py",
        "veridicus_incoherence_analyzer/domain/output.py",
        "veridicus_incoherence_analyzer/application/preflight.py",
        "veridicus_incoherence_analyzer/cli/composition.py",
        "veridicus_model_gateway/adapters/anonymizing.py",
        "veridicus_integrity_policy/scan.py",
        "veridicus_execution_profiles/validate.py",
    }


def test_verde_informes_sanos_pasan() -> None:
    assert gate.evaluate(_healthy()) == []


def test_verde_main_con_cuatro_archivos_sale_con_0(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert gate.main(_write(tmp_path, list(_healthy()))) == 0
    assert "compuerta de cobertura" in capsys.readouterr().out


def test_negativo_un_modulo_guardia_al_99_por_ciento_de_ramas_falla() -> None:
    informes = _healthy()
    informes[0] = _report(PACKAGES[0], **{"domain/quotes.py": _entry(branches=100, hit=99)})
    fallos = gate.evaluate(informes)
    assert len(fallos) == 1
    assert "domain/quotes.py" in fallos[0]
    assert "1 de 100" in fallos[0]


def test_negativo_un_modulo_guardia_ausente_del_informe_falla_cerrado() -> None:
    informes = _healthy()
    del informes[2]["files"]["src/veridicus_execution_profiles/validate.py"]
    fallos = gate.evaluate(informes)
    assert any("validate.py" in f and "no trae" in f for f in fallos)


def test_negativo_main_sale_con_1_si_falta_un_guardia(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    informes = _healthy()
    del informes[1]["files"]["src/veridicus_model_gateway/adapters/anonymizing.py"]
    assert gate.main(_write(tmp_path, list(informes))) == 1
    assert "anonymizing.py" in capsys.readouterr().err


def test_negativo_menos_del_80_por_ciento_de_lineas_en_un_paquete_falla() -> None:
    informes = _healthy()
    informes[3] = _report(PACKAGES[3], **{"otro.py": _entry(statements=1000, covered=0)})
    assert any("líneas del paquete" in f for f in gate.evaluate(informes))


def test_el_umbral_de_lineas_es_80_exacto() -> None:
    informes = _healthy()
    # Los 6 guardias del analizador suman 60 sentencias cubiertas; con 100 más son 160 y el 80 % es 128.
    assert len(gate.GUARD_MODULES[PACKAGES[0]]) == 6
    en_el_umbral = _entry(statements=100, covered=68, branches=0, hit=0)
    bajo_el_umbral = _entry(statements=100, covered=67, branches=0, hit=0)
    informes[0] = _report(PACKAGES[0], **{"otro.py": en_el_umbral})
    assert gate.evaluate(informes) == []
    informes[0] = _report(PACKAGES[0], **{"otro.py": bajo_el_umbral})
    assert any("líneas del paquete" in f for f in gate.evaluate(informes))


def test_negativo_faltan_informes_o_sobran_falla() -> None:
    assert gate.evaluate(_healthy()[:3]) != []
    assert gate.evaluate([*_healthy(), {"files": {}}]) != []


def test_negativo_un_informe_sin_archivos_del_paquete_falla() -> None:
    informes = _healthy()
    informes[1] = {"files": {"src/otro_paquete/x.py": _entry()}}
    assert gate.evaluate(informes) != []


@pytest.mark.parametrize(
    "entrada",
    [
        None,
        {},
        {"summary": None},
        {"summary": {"num_statements": "10"}},
        {
            "summary": {
                "num_statements": -1,
                "covered_lines": 0,
                "num_branches": 0,
                "covered_branches": 0,
            }
        },
    ],
)
def test_negativo_cifras_ilegibles_fallan(entrada: Any) -> None:
    informes = _healthy()
    informes[0]["files"]["src/veridicus_incoherence_analyzer/domain/output.py"] = entrada
    assert gate.evaluate(informes) != []


def test_negativo_informe_vacio_o_sin_mapa_de_archivos_falla() -> None:
    informes = _healthy()
    informes[0] = {}
    assert gate.evaluate(informes) != []
    informes[0] = {"files": []}
    assert gate.evaluate(informes) != []


def test_negativo_main_con_uso_incorrecto_sale_con_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert gate.main(["uno.json"]) == 2
    assert "uso:" in capsys.readouterr().err


def test_negativo_main_con_archivo_inexistente_o_ilegible_sale_con_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rutas = _write(tmp_path, list(_healthy()))
    rutas[2] = str(tmp_path / "no-existe.json")
    assert gate.main(rutas) == 1
    assert "no se pudo leer" in capsys.readouterr().err
    (tmp_path / "malo.json").write_text("{no es json", encoding="utf-8")
    rutas[2] = str(tmp_path / "malo.json")
    assert gate.main(rutas) == 1


def test_negativo_main_con_json_que_no_es_objeto_sale_con_1(tmp_path: Path) -> None:
    rutas = _write(tmp_path, list(_healthy()))
    (tmp_path / "lista.json").write_text("[]", encoding="utf-8")
    rutas[0] = str(tmp_path / "lista.json")
    assert gate.main(rutas) == 1


def test_el_informe_real_de_otra_ruta_se_lee_por_el_marcador_del_paquete() -> None:
    informes = _healthy()
    informes[0]["files"] = {
        f"/ruta/larga/libs/incoherence_analyzer/{k}": v for k, v in informes[0]["files"].items()
    }
    assert gate.evaluate(informes) == []
