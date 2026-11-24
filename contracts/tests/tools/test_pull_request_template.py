"""Plantilla de PR (NFRD-U1-13, security-design §4.11, U01-T19)."""

from pathlib import Path

import pytest

PLANTILLA = ".github/pull_request_template.md"


def leer(contracts_root: Path) -> str:
    ruta = contracts_root.parent / PLANTILLA
    if not ruta.is_file():
        pytest.fail(f"plantilla de PR ausente: {PLANTILLA}")
    return ruta.read_text(encoding="utf-8")


def test_la_plantilla_existe_y_conserva_el_apartado_de_la_huella_de_seguridad(
    contracts_root: Path,
) -> None:
    texto = leer(contracts_root)
    encabezados = [linea for linea in texto.splitlines() if linea.startswith("## ")]
    assert any("security-surface.json" in linea for linea in encabezados), encabezados


def test_la_plantilla_pide_la_evidencia_de_cada_tarea_y_esta_en_espanol(
    contracts_root: Path,
) -> None:
    texto = leer(contracts_root)
    assert "## Evidencia" in texto
    assert "comando de verificación" in texto
    assert "Resumen" in texto
    assert not texto.startswith("﻿")
    assert "\r" not in texto
