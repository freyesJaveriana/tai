"""Módulo guardia del catálogo C25: forma, tipos, derivadas y relaciones (§4.4; E33, E37).

Los controles negativos trabajan sobre copias en memoria o en `tmp_path`; nunca se toca el
catálogo versionado.
"""

import copy
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

CATALOGO = "limits.v1.yaml"


def _guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.limits_catalog", "paso 12 (T10)")


def _doc() -> dict[str, Any]:
    return copy.deepcopy(load_contract(CATALOGO))


def _problemas(doc: Any) -> list[str]:
    problemas: list[str] = _guardia().comprobar_catalogo(doc)
    return problemas


def _con(doc: dict[str, Any], *fragmentos: str) -> None:
    problemas = _problemas(doc)
    assert problemas, "debía haber problemas"
    texto = "\n".join(problemas)
    for fragmento in fragmentos:
        assert fragmento in texto, (fragmento, problemas)


# ---- el catálogo versionado ----------------------------------------------------------------


def test_el_catalogo_versionado_pasa_la_guardia() -> None:
    assert _problemas(_doc()) == []
    assert _guardia().comprobar(CONTRACTS_ROOT / CATALOGO) == []


def test_las_cifras_nuevas_de_las_tareas_vecinas_estan_con_su_dueno() -> None:
    limites = _doc()["limits"]
    esperadas = {
        "transcript_body_max_bytes": (1_004_096, "bytes", "U6"),
        "import_body_max_bytes": (2_113_536, "bytes", "U6"),
        "cursor_max_chars": (128, "chars", "U4"),
        "voice_body_max_bytes": (6_016_384, "bytes", "U9"),
        "research_report_read_timeout_s": (30, "s", "U12"),
    }
    for nombre, (valor, unidad, dueno) in esperadas.items():
        assert (limites[nombre]["value"], limites[nombre]["unit"], limites[nombre]["owner"]) == (
            valor,
            unidad,
            dueno,
        )
    assert limites["import_file_max_bytes"]["value"] < limites["import_body_max_bytes"]["value"]
    assert limites["audio_base64_max_chars"]["value"] == 8_000_000


def test_el_archivo_se_lee_por_ruta_y_un_archivo_sin_forma_no_pasa(tmp_path: Path) -> None:
    ruta = tmp_path / "limits.yaml"
    ruta.write_text("- uno\n- dos\n", encoding="utf-8")
    assert _guardia().comprobar(ruta)


# ---- forma ---------------------------------------------------------------------------------


@pytest.mark.parametrize("documento", [None, [], "texto", 3])
def test_la_raiz_debe_ser_un_objeto(documento: Any) -> None:
    _con(documento, "objeto")


def test_secciones_de_la_raiz() -> None:
    doc = _doc()
    del doc["relations"]
    _con(doc, "relations")
    doc = _doc()
    doc["extra"] = 1
    _con(doc, "extra")


def test_schema_version_semver() -> None:
    doc = _doc()
    doc["schema_version"] = "uno"
    _con(doc, "schema_version")
    doc = _doc()
    doc["schema_version"] = 1
    _con(doc, "schema_version")


@pytest.mark.parametrize("limites", [None, [], {}, "x"])
def test_limits_debe_ser_un_objeto_no_vacio(limites: Any) -> None:
    doc = _doc()
    doc["limits"] = limites
    _con(doc, "limits")


def test_relations_debe_ser_una_lista() -> None:
    doc = _doc()
    doc["relations"] = {"a": 1}
    _con(doc, "relations")


def test_entrada_que_no_es_un_objeto() -> None:
    doc = _doc()
    doc["limits"]["turn_max_chars"] = 20000
    _con(doc, "turn_max_chars")


def test_entrada_sin_una_clave_obligatoria() -> None:
    for clave in ("value", "unit", "owner", "used_in"):
        doc = _doc()
        del doc["limits"]["turn_max_chars"][clave]
        _con(doc, "turn_max_chars", clave)


def test_entrada_con_una_clave_de_mas() -> None:
    doc = _doc()
    doc["limits"]["turn_max_chars"]["nota"] = "x"
    _con(doc, "turn_max_chars", "nota")


def test_nombre_de_limite_invalido() -> None:
    doc = _doc()
    doc["limits"]["Turn-Max"] = {"value": 1, "unit": "chars", "owner": "U4", "used_in": []}
    _con(doc, "Turn-Max")


def test_valor_nulo() -> None:
    doc = _doc()
    doc["limits"]["turn_max_chars"]["value"] = None
    _con(doc, "turn_max_chars", "value")


@pytest.mark.parametrize("unidad", ["caracteres", "", None, 3])
def test_unidad_fuera_de_la_lista_cerrada(unidad: Any) -> None:
    doc = _doc()
    doc["limits"]["turn_max_chars"]["unit"] = unidad
    _con(doc, "turn_max_chars", "unit")


@pytest.mark.parametrize("dueno", ["u4", "U", "Cuatro", None, 4])
def test_dueno_invalido(dueno: Any) -> None:
    doc = _doc()
    doc["limits"]["turn_max_chars"]["owner"] = dueno
    _con(doc, "turn_max_chars", "owner")


@pytest.mark.parametrize("usos", [None, "C1", ["c1"], ["C1", 2], [None]])
def test_used_in_invalido(usos: Any) -> None:
    doc = _doc()
    doc["limits"]["turn_max_chars"]["used_in"] = usos
    _con(doc, "turn_max_chars", "used_in")


@pytest.mark.parametrize("origen", ["no_existe", "turn_max_chars", None, 5])
def test_derived_from_debe_nombrar_otra_entrada(origen: Any) -> None:
    doc = _doc()
    doc["limits"]["turn_max_chars"]["derived_from"] = origen
    _con(doc, "turn_max_chars", "derived_from")


def test_presencia_de_las_cifras_obligatorias() -> None:
    for nombre in (
        "transcript_body_max_bytes",
        "import_body_max_bytes",
        "import_file_max_bytes",
        "cursor_max_chars",
        "voice_body_max_bytes",
        "research_report_read_timeout_s",
        "audio_max_bytes",
        "audio_base64_max_chars",
    ):
        doc = _doc()
        del doc["limits"][nombre]
        _con(doc, nombre)


def test_relacion_con_forma_invalida() -> None:
    for relacion in (
        "fragment_overlap_turns",
        ["fragment_overlap_turns", "<"],
        ["fragment_overlap_turns", ">", "fragment_window_turns"],
        ["fragment_overlap_turns", "<", 60],
        [1, "<", "fragment_window_turns"],
        ["no_existe", "<", "fragment_window_turns"],
        ["fragment_overlap_turns", "<", "no_existe"],
    ):
        doc = _doc()
        doc["relations"].append(relacion)
        _con(doc, "relations")


def test_relacion_obligatoria_ausente() -> None:
    doc = _doc()
    doc["relations"] = [
        r for r in doc["relations"] if r[:1] != ["import_file_max_bytes"] or r[2] != "import_body_max_bytes"
    ]
    _con(doc, "import_file_max_bytes", "import_body_max_bytes", "obligatoria")


def test_cada_relacion_de_security_design_esta_declarada() -> None:
    declaradas = {tuple(r) for r in _doc()["relations"]}
    assert declaradas >= {
        ("fragment_overlap_turns", "<", "fragment_window_turns"),
        ("retention_min_days", "<=", "retention_max_days"),
        ("heartbeat_write_min_s", "<", "heartbeat_timeout_s"),
        ("poll_interval_active_s", "<=", "poll_interval_s"),
        ("voice_deadline_base_s", "<=", "voice_deadline_max_s"),
        ("run_deadline_incremental_s", "<=", "run_deadline_final_s"),
        ("import_file_max_bytes", "<=", "run_message_max_bytes"),
        ("import_file_max_bytes", "<", "import_body_max_bytes"),
    }


# ---- tipos ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "valor"),
    [
        ("turn_max_chars", 1.5),
        ("turn_max_chars", 0),
        ("turn_max_chars", -1),
        ("turn_max_chars", "20000"),
        ("turn_max_chars", True),
        ("turn_max_chars", float("inf")),
        ("claim_idle_ms", 60000.5),
        ("anonymizer_masking_budget_ratio", 0),
        ("anonymizer_masking_budget_ratio", 1.5),
        ("anonymizer_masking_budget_ratio", True),
        ("anonymizer_masking_budget_ratio", "0.15"),
        ("anonymizer_masking_budget_ratio", float("nan")),
        ("poll_interval_s", 0),
        ("poll_interval_s", -2.5),
        ("poll_interval_s", "15"),
        ("poll_interval_s", float("inf")),
    ],
)
def test_tipo_de_valor_invalido_para_su_unidad(nombre: str, valor: Any) -> None:
    doc = _doc()
    doc["limits"][nombre]["value"] = valor
    _con(doc, nombre, "valor")


def test_ratio_y_s_admiten_decimales_y_el_resto_solo_enteros() -> None:
    doc = _doc()
    doc["limits"]["anonymizer_masking_budget_ratio"]["value"] = 1
    doc["limits"]["poll_interval_s"]["value"] = 15.5
    doc["limits"]["poll_interval_active_s"]["value"] = 1.5
    assert _problemas(doc) == []


# ---- derivadas -----------------------------------------------------------------------------


def test_audio_base64_es_4_por_el_techo_de_audio_entre_3() -> None:
    doc = _doc()
    assert doc["limits"]["audio_base64_max_chars"]["derived_from"] == "audio_max_bytes"
    doc["limits"]["audio_base64_max_chars"]["value"] = 8_000_001
    _con(doc, "audio_base64_max_chars", "8000000")


@pytest.mark.parametrize(
    "nombre",
    [
        "audio_base64_max_chars",
        "transcript_body_max_bytes",
        "import_body_max_bytes",
        "voice_body_max_bytes",
    ],
)
def test_una_derivada_sin_derived_from_no_pasa(nombre: str) -> None:
    doc = _doc()
    del doc["limits"][nombre]["derived_from"]
    _con(doc, nombre, "derived_from")


def test_una_derivada_con_otro_origen_no_pasa() -> None:
    doc = _doc()
    doc["limits"]["import_body_max_bytes"]["derived_from"] = "audio_max_bytes"
    _con(doc, "import_body_max_bytes", "derived_from")


@pytest.mark.parametrize(
    ("nombre", "valor"),
    [
        ("transcript_body_max_bytes", 1_004_097),
        ("import_body_max_bytes", 2_113_537),
        ("voice_body_max_bytes", 6_016_385),
    ],
)
def test_una_derivada_con_otro_valor_no_pasa(nombre: str, valor: int) -> None:
    doc = _doc()
    doc["limits"][nombre]["value"] = valor
    _con(doc, nombre, str(valor))


def test_cambiar_el_origen_obliga_a_cambiar_la_derivada() -> None:
    doc = _doc()
    doc["limits"]["audio_max_bytes"]["value"] = 6_000_003
    _con(doc, "audio_base64_max_chars", "voice_body_max_bytes")


def test_derived_from_sin_formula_conocida() -> None:
    doc = _doc()
    doc["limits"]["cursor_max_chars"]["derived_from"] = "turn_max_chars"
    _con(doc, "cursor_max_chars", "fórmula")


# ---- relaciones ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "valor"),
    [
        ("fragment_overlap_turns", 60),
        ("retention_min_days", 91),
        ("heartbeat_write_min_s", 180),
        ("poll_interval_active_s", 16),
        ("voice_deadline_base_s", 1_801),
        ("run_deadline_incremental_s", 43_201),
        ("import_file_max_bytes", 2_097_153 + 2_000_000),
    ],
)
def test_una_relacion_rota_en_el_catalogo_se_reporta(nombre: str, valor: int) -> None:
    doc = _doc()
    doc["limits"][nombre]["value"] = valor
    problemas = _problemas(doc)
    assert any(nombre in p and "relación" in p for p in problemas), problemas


def test_e33_e37_el_catalogo_alterado_tambien_lo_ve_la_guardia(tmp_path: Path) -> None:
    ruta = tmp_path / "limits.yaml"
    texto = (CONTRACTS_ROOT / CATALOGO).read_text(encoding="utf-8")
    ruta.write_text(texto.replace("value: 20000,", "value: 20000.5,", 1), encoding="utf-8")
    assert _guardia().comprobar(ruta)
