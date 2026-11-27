"""Pruebas del visor web de la demo (scripts/humano/visor-demo.py), sin kubectl ni red."""

import base64
import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest
from support import DEPLOY

RUTA = DEPLOY.parent / "scripts" / "humano" / "visor-demo.py"


def _visor() -> ModuleType:
    spec = importlib.util.spec_from_file_location("visor_demo", RUTA)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    antes = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # sin __pycache__ dentro de scripts/humano/
    try:
        spec.loader.exec_module(modulo)
    finally:
        sys.dont_write_bytecode = antes
    return modulo


visor = _visor()

LOGS = """Aviso: perfil de demostración con juez y verificador de la misma familia.
caso: estado=ok, 1 hallazgo
  hecho: Hora de llegada
  tipo: temporal
  cita A (turno T2): «llegué a las ocho»
  cita B (turno T4): «llegué al mediodía»
"""


def test_the_viewer_opens_with_the_human_mark() -> None:
    lineas = RUTA.read_text(encoding="utf-8").splitlines()
    # Sin shebang: se lanza con «python3 scripts/humano/visor-demo.py».
    assert lineas[0] == "# Lo ejecuta el humano (AUTONOMIA-01)"


def test_the_story_becomes_c6_turns_and_continuation_lines_join() -> None:
    caso = visor.caso_c6(
        "SINT-X1", "ENT: ¿Qué pasó?\nTEST: Llegué a las ocho\ny me fui.\n\nTEST: Otra cosa"
    )
    assert caso["origen"] == "sintetico"
    assert caso["turnos"] == [
        {"n": 1, "hablante": "ENT", "texto": "¿Qué pasó?"},
        {"n": 2, "hablante": "TEST", "texto": "Llegué a las ocho y me fui."},
        {"n": 3, "hablante": "TEST", "texto": "Otra cosa"},
    ]


@pytest.mark.parametrize(
    ("entrevista", "relato"),
    [
        ("REAL-1", "TEST: hola"),  # identificador sin SINT-
        ("SINT-1", "hola"),  # primera línea sin prefijo
        ("SINT-1", "ENT: solo pregunta"),  # sin relato TEST
        ("SINT-1", "TEST:   "),  # turno vacío
    ],
)
def test_an_invalid_case_is_rejected(entrevista: str, relato: str) -> None:
    with pytest.raises(visor.ErrorCaso):
        visor.caso_c6(entrevista, relato)


def test_the_logs_become_findings_with_both_quotes() -> None:
    leido = visor.leer_logs(LOGS)
    assert leido["errores"] == []
    assert leido["avisos"] == [
        "Aviso: perfil de demostración con juez y verificador de la misma familia."
    ]
    [bloque] = leido["bloques"]
    assert bloque["estado"] == "ok"
    assert bloque["hallazgos"] == [
        {
            "hecho": "Hora de llegada",
            "tipo": "temporal",
            "cita_a": {"turno": "T2", "cita": "llegué a las ocho"},
            "cita_b": {"turno": "T4", "cita": "llegué al mediodía"},
        }
    ]


def test_a_failed_run_shows_the_error_and_no_findings() -> None:
    logs = "El análisis terminó con el código 4; no se muestran hallazgos.\ncaso: estado=error, 0 hallazgos\n"
    pagina = visor.pagina_resultado(
        visor.caso_c6("SINT-1", "TEST: hola"), "fallido", logs, 3.0
    ).decode()
    assert "terminó con el código 4" in pagina
    assert "Sugerencia de revisión 1" not in pagina


def test_the_only_script_is_the_one_the_csp_allows_by_hash() -> None:
    pagina = visor.pagina_formulario("SINT-1", "TEST: hola").decode()
    scripts = re.findall(r"<script>(.*?)</script>", pagina, flags=re.DOTALL)
    assert scripts == [visor._GUION]
    digest = base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode()
    assert f"script-src 'sha256-{digest}'" in visor.CSP
    assert "unsafe-inline" not in visor.CSP.split("script-src")[1]


def test_the_form_shows_the_waiting_layer_and_the_course_credits() -> None:
    pagina = visor.pagina_formulario("SINT-1", "TEST: hola").decode()
    assert "<form id='analizar'" in pagina
    assert "id='cargando' class='cargando' hidden" in pagina and "Analizando…" in pagina
    assert "name='sintetico' value='si' required" in pagina
    for dato in (visor.UNIVERSIDAD, visor.AUTOR, visor.CORREO, visor.PROFESOR, "Tópicos"):
        assert dato in pagina


def test_the_logo_is_embedded_as_a_data_uri(tmp_path: Path) -> None:
    escudo = tmp_path / "escudo.png"
    escudo.write_bytes(b"\x89PNG")
    assert visor.logo_data_uri(escudo) == "data:image/png;base64,iVBORw=="
    with pytest.raises(SystemExit):
        visor.logo_data_uri(tmp_path / "escudo.gif")


def test_there_are_at_least_five_examples_and_each_one_is_a_valid_synthetic_case() -> None:
    lista = visor.ejemplos()
    assert len(lista) >= 5
    assert len({item["id"] for item in lista}) == len(lista)
    assert len({item["entrevista"] for item in lista}) == len(lista)
    for item in lista:
        caso = visor.caso_c6(item["entrevista"], item["relato"])
        assert caso["origen"] == "sintetico"
        assert len(caso["turnos"]) >= 6, item["id"]


def test_the_dropdown_lists_every_example_and_marks_the_chosen_one() -> None:
    lista = visor.ejemplos()
    pagina = visor.pagina_formulario("SINT-1", "TEST: hola", actual=lista[2]["id"]).decode()
    assert pagina.count("<option ") == len(lista) + 1
    assert f"<option value='{lista[2]['id']}' selected>" in pagina
    assert visor.ejemplo(lista[2]["id"]) == (lista[2]["entrevista"], lista[2]["relato"])
    assert visor.ejemplo("no-existe") is None


def test_the_result_page_escapes_html_and_highlights_quotes() -> None:
    caso = visor.caso_c6(
        "SINT-1",
        "ENT: <b>hola</b>\nTEST: llegué a las ocho\nENT: ¿y luego?\nTEST: llegué al mediodía",
    )
    pagina = visor.pagina_resultado(caso, "completo", LOGS, 40.0).decode()
    assert "<b>hola</b>" not in pagina
    assert "&lt;b&gt;hola&lt;/b&gt;" in pagina
    assert "<mark class='a'" in pagina and "<mark class='b'" in pagina
    assert "Sugerencia de revisión 1" in pagina
