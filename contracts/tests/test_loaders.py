"""Carga de YAML y JSON (D5, §4.1): único punto de lectura de los contratos."""

from pathlib import Path

import pytest

from veridicus_contracts.loaders import LoadError, load_file, load_json_text, load_yaml_text


def test_yaml_valido_se_lee_como_estructuras_de_json() -> None:
    datos = load_yaml_text("nombre: prueba\nlista: [1, 2.5, true, null]\nanidado:\n  clave: valor\n")
    assert datos == {
        "nombre": "prueba",
        "lista": [1, 2.5, True, None],
        "anidado": {"clave": "valor"},
    }


def test_clave_duplicada_se_rechaza_en_yaml() -> None:
    with pytest.raises(LoadError, match="clave"):
        load_yaml_text("a: 1\na: 2\n")


def test_etiqueta_de_objeto_python_se_rechaza() -> None:
    with pytest.raises(LoadError):
        load_yaml_text("a: !!python/object:os.system x\n")


def test_no_y_on_son_texto_en_yaml_1_2() -> None:
    assert load_yaml_text("a: no\nb: on\nc: yes\nd: off\n") == {
        "a": "no",
        "b": "on",
        "c": "yes",
        "d": "off",
    }


def test_fecha_sin_comillas_se_rechaza_porque_no_es_json() -> None:
    with pytest.raises(LoadError, match="comillas"):
        load_yaml_text("fecha: 2024-01-02\n")
    with pytest.raises(LoadError, match="comillas"):
        load_yaml_text("lista:\n  - 2024-01-02T10:00:00Z\n")


def test_json_valido_y_con_clave_duplicada_o_constante_no_finita() -> None:
    assert load_json_text('{"a": [1, {"b": null}]}') == {"a": [1, {"b": None}]}
    with pytest.raises(LoadError, match="clave"):
        load_json_text('{"a": 1, "a": 2}')
    with pytest.raises(LoadError, match="NaN"):
        load_json_text('{"a": NaN}')
    with pytest.raises(LoadError):
        load_json_text("{no es json")


def test_load_file_elige_el_lector_por_sufijo(tmp_path: Path) -> None:
    (tmp_path / "a.yaml").write_text("x: no\n", encoding="utf-8")
    (tmp_path / "b.yml").write_text("x: on\n", encoding="utf-8")
    (tmp_path / "c.json").write_text('{"x": 1}', encoding="utf-8")
    (tmp_path / "d.txt").write_text("x", encoding="utf-8")
    assert load_file(tmp_path / "a.yaml") == {"x": "no"}
    assert load_file(tmp_path / "b.yml") == {"x": "on"}
    assert load_file(tmp_path / "c.json") == {"x": 1}
    with pytest.raises(LoadError, match="sufijo"):
        load_file(tmp_path / "d.txt")


def test_un_archivo_que_no_es_utf8_sale_como_load_error(tmp_path: Path) -> None:
    (tmp_path / "e.json").write_bytes(b"\xff\xfe{}")
    with pytest.raises(LoadError, match="UTF-8"):
        load_file(tmp_path / "e.json")
