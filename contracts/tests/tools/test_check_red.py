"""`check_red`: sale con 0 solo si el informe de pytest trae fallos y ningún error (CA-4, A-3)."""

from pathlib import Path

import pytest

from veridicus_contracts.tools.check_red import (
    CODIGO_INFORME_ILEGIBLE,
    CODIGO_NO_ES_ROJO_COMPROBABLE,
    CODIGO_ROJO_COMPROBABLE,
    InformeIlegible,
    leer_cifras,
    main,
)


def _informe(carpeta: Path, errores: str, fallos: str, nombre: str = "red.xml") -> Path:
    ruta = carpeta / nombre
    ruta.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<testsuites><testsuite name="pytest" errors="{errores}" failures="{fallos}" '
        'skipped="0" tests="3"><testcase classname="a" name="b"/></testsuite></testsuites>',
        encoding="utf-8",
    )
    return ruta


def test_fallos_sin_errores_es_rojo_comprobable(tmp_path: Path) -> None:
    assert main([str(_informe(tmp_path, "0", "4"))]) == CODIGO_ROJO_COMPROBABLE


def test_cualquier_error_no_es_rojo_comprobable(tmp_path: Path) -> None:
    assert main([str(_informe(tmp_path, "2", "4"))]) == CODIGO_NO_ES_ROJO_COMPROBABLE


def test_cero_fallos_no_es_rojo_comprobable(tmp_path: Path) -> None:
    assert main([str(_informe(tmp_path, "0", "0"))]) == CODIGO_NO_ES_ROJO_COMPROBABLE


def test_un_archivo_ausente_sale_distinto_de_cero(tmp_path: Path) -> None:
    codigo = main([str(tmp_path / "no-existe.xml")])
    assert codigo == CODIGO_INFORME_ILEGIBLE != CODIGO_ROJO_COMPROBABLE


def test_un_xml_mal_formado_sale_distinto_de_cero(tmp_path: Path) -> None:
    ruta = tmp_path / "roto.xml"
    ruta.write_text("<testsuites><testsuite errors='0'", encoding="utf-8")
    assert main([str(ruta)]) == CODIGO_INFORME_ILEGIBLE
    with pytest.raises(InformeIlegible):
        leer_cifras(ruta)


def test_un_informe_sin_cifras_sale_distinto_de_cero(tmp_path: Path) -> None:
    ruta = tmp_path / "vacio.xml"
    ruta.write_text("<testsuites><testsuite name='pytest'/></testsuites>", encoding="utf-8")
    assert main([str(ruta)]) == CODIGO_INFORME_ILEGIBLE


def test_errors_distinto_de_la_cadena_cero_no_cuenta_como_cero(tmp_path: Path) -> None:
    """`errors="00"` o `"0.0"` no son la cadena exacta "0" que exige la tarea."""
    assert main([str(_informe(tmp_path, "00", "4"))]) == CODIGO_NO_ES_ROJO_COMPROBABLE


def test_sin_argumentos_sale_distinto_de_cero() -> None:
    assert main([]) == CODIGO_INFORME_ILEGIBLE
