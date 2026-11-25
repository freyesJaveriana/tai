"""`check_tag`: la etiqueta es `contracts-v` más `[project].version`, sin red (BR12.2, E-32)."""

from pathlib import Path

import pytest

from veridicus_contracts.tools.check_tag import VersionInvalida, etiqueta_esperada, main


def _pyproject(carpeta: Path, version: str) -> Path:
    ruta = carpeta / "pyproject.toml"
    ruta.write_text(f'[project]\nname = "demo"\nversion = "{version}"\n', encoding="utf-8")
    return ruta


def test_la_etiqueta_igual_a_la_esperada_pasa(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ruta = _pyproject(tmp_path, "1.2.3")
    assert main(["--pyproject", str(ruta), "--tag", "contracts-v1.2.3"]) == 0
    assert capsys.readouterr().err == ""


def test_otra_version_falla_y_nombra_las_dos_etiquetas(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ruta = _pyproject(tmp_path, "1.2.3")
    assert main(["--pyproject", str(ruta), "--tag", "contracts-v1.2.4"]) == 1
    mensaje = capsys.readouterr().err
    assert "contracts-v1.2.4" in mensaje
    assert "contracts-v1.2.3" in mensaje


def test_la_forma_vieja_con_solo_v_falla(tmp_path: Path) -> None:
    ruta = _pyproject(tmp_path, "0.1.0")
    assert main(["--pyproject", str(ruta), "--tag", "v0.1.0"]) == 1


def test_otro_prefijo_falla(tmp_path: Path) -> None:
    ruta = _pyproject(tmp_path, "0.1.0")
    assert main(["--pyproject", str(ruta), "--tag", "analyzer-v0.1.0"]) == 1


@pytest.mark.parametrize("version", ["1.2", "1.2.3.4", "1.2.x", "v1.2.3", "01.2.3", ""])
def test_una_version_sin_forma_semantica_falla(
    tmp_path: Path, version: str, capsys: pytest.CaptureFixture[str]
) -> None:
    ruta = _pyproject(tmp_path, version)
    with pytest.raises(VersionInvalida):
        etiqueta_esperada(ruta)
    assert main(["--pyproject", str(ruta), "--tag", f"contracts-v{version}"]) == 1
    assert "MAYOR.MENOR.PARCHE" in capsys.readouterr().err


def test_sin_tag_imprime_la_esperada(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ruta = _pyproject(tmp_path, "3.4.5")
    assert main(["--pyproject", str(ruta)]) == 0
    assert capsys.readouterr().out.strip() == "contracts-v3.4.5"


def test_un_pyproject_sin_version_o_ilegible_falla(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sin_version = tmp_path / "pyproject.toml"
    sin_version.write_text('[project]\nname = "demo"\n', encoding="utf-8")
    assert main(["--pyproject", str(sin_version)]) == 1
    roto = tmp_path / "roto.toml"
    roto.write_text("[project\n", encoding="utf-8")
    assert main(["--pyproject", str(roto)]) == 1
    assert main(["--pyproject", str(tmp_path / "no-existe.toml")]) == 1
    assert capsys.readouterr().err.count("check_tag:") == 3


def test_un_argumento_desconocido_falla(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--otra-cosa"]) == 2
    assert "uso:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argumentos",
    [
        ["--tag", "x", "--tag", "contracts-v1.2.3"],
        ["--tag", "contracts-v1.2.3", "--tag", "x"],
        ["--pyproject", "a.toml", "--pyproject", "b.toml"],
    ],
)
def test_una_opcion_repetida_sale_con_codigo_2(
    tmp_path: Path, argumentos: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    ruta = _pyproject(tmp_path, "1.2.3")
    completos = argumentos if "--pyproject" in argumentos else ["--pyproject", str(ruta), *argumentos]
    assert main(completos) == 2
    assert "uso:" in capsys.readouterr().err


def test_por_omision_lee_el_pyproject_del_directorio_de_trabajo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], contracts_root: Path
) -> None:
    monkeypatch.chdir(contracts_root)
    assert main([]) == 0
    esperada = etiqueta_esperada(contracts_root / "pyproject.toml")
    assert capsys.readouterr().out.strip() == esperada
    assert esperada.startswith("contracts-v")
