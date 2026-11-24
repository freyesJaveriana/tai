"""Cobertura de fixtures por regla de nivel 0 (security-design §4.10, NFR12.1, BR1.6).

`checks/fixture_coverage.py` exige un fixture `accept` y uno `reject` por cada regla de U1 que se prueba con
fixtures, y falla si un `reject` no falla o falla por otra regla (otra palabra clave del validador que las
que la regla declara). Quedan fuera BR5.2 a BR5.6 (solo la forma, BR5.8), BR1.5, BR1.8 y BR12.2 (revisión
del PR).
"""

import copy
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

BASE = "analyzer/v1/fixtures/"
REGLA = {"BR3.5": frozenset({"required"})}


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.fixture_coverage", "T18, paso 19")


def _poner(raiz: Path, nombre: str, documento: Any) -> None:
    ruta = raiz / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(documento, ensure_ascii=False), encoding="utf-8")


def _aceptado() -> dict[str, Any]:
    return copy.deepcopy(load_contract(BASE + "entrada.valid.yaml"))


def _rechazado() -> dict[str, Any]:
    return copy.deepcopy(load_contract(BASE + "entrada.corpus-sin-consentimiento.yaml"))


def _arbol(raiz: Path) -> Path:
    _poner(raiz, BASE + "a.json", _aceptado())
    _poner(raiz, BASE + "r.json", _rechazado())
    return raiz


def test_cada_regla_de_fixtures_tiene_su_accept_y_su_reject_en_el_repositorio(guardia: ModuleType) -> None:
    assert guardia.comprobar(CONTRACTS_ROOT) == []
    # No pasa en vacío: cada regla exigida tiene al menos un reject real, y los accept existen.
    rechazos = {f["reject_reason"] for _, f in guardia.fixtures(CONTRACTS_ROOT) if f["expectation"] == "reject"}
    assert set(guardia.REGLAS) <= rechazos
    assert len(guardia.REGLAS) >= 15
    assert sum(1 for _, f in guardia.fixtures(CONTRACTS_ROOT) if f["expectation"] == "accept") >= 10


def test_las_exclusiones_son_las_de_4_10_y_no_se_exigen(guardia: ModuleType) -> None:
    assert set(guardia.EXCLUIDAS) == {"BR5.2", "BR5.3", "BR5.4", "BR5.5", "BR5.6", "BR1.5", "BR1.8", "BR12.2"}
    assert not set(guardia.EXCLUIDAS) & set(guardia.REGLAS)
    assert all(re.fullmatch(r"(BR|NFR|NFRD-U)[0-9.\-]+", regla) for regla in guardia.REGLAS)
    assert all(causas for causas in guardia.REGLAS.values())


def test_un_arbol_con_su_accept_y_su_reject_pasa(guardia: ModuleType, tmp_path: Path) -> None:
    assert guardia.comprobar(_arbol(tmp_path), reglas=REGLA) == []


def test_un_accept_de_otro_contrato_de_la_misma_familia_basta(guardia: ModuleType, tmp_path: Path) -> None:
    raiz = tmp_path
    _poner(raiz, BASE + "r.json", _rechazado())
    salida = copy.deepcopy(load_contract(BASE + "salida.valid.yaml"))
    _poner(raiz, BASE + "s.json", salida)
    assert guardia.comprobar(raiz, reglas=REGLA) == []
    # Una familia distinta no sirve.
    ajeno = copy.deepcopy(load_contract("model_calls/fixtures/model-call.valid.yaml"))
    (raiz / BASE / "s.json").unlink()
    _poner(raiz, "model_calls/fixtures/m.json", ajeno)
    assert guardia.comprobar(raiz, reglas=REGLA) == ["BR3.5: falta un fixture accept (NFR12.1, §4.10)"]


def test_falta_el_accept_o_el_reject_se_dice_por_regla(guardia: ModuleType, tmp_path: Path) -> None:
    _poner(tmp_path, BASE + "r.json", _rechazado())
    assert guardia.comprobar(tmp_path, reglas=REGLA) == ["BR3.5: falta un fixture accept (NFR12.1, §4.10)"]
    otro = tmp_path / "otro"
    _poner(otro, BASE + "a.json", _aceptado())
    assert guardia.comprobar(otro, reglas=REGLA) == ["BR3.5: falta un fixture reject (NFR12.1, §4.10)"]
    assert guardia.comprobar(tmp_path / "vacio", reglas={"BR3.5": frozenset({"required"}), "BR3.1": frozenset({"required"})}) == [
        "BR3.1: falta un fixture accept (NFR12.1, §4.10)",
        "BR3.1: falta un fixture reject (NFR12.1, §4.10)",
        "BR3.5: falta un fixture accept (NFR12.1, §4.10)",
        "BR3.5: falta un fixture reject (NFR12.1, §4.10)",
    ]


def test_un_reject_que_no_falla_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    disfrazado = _aceptado()
    disfrazado.update(expectation="reject", reject_reason="BR3.5")
    _poner(tmp_path, BASE + "disfrazado.json", disfrazado)
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/disfrazado.json: el reject no falla (BR3.5, NFR12.1)"
    ]


def test_un_reject_que_falla_por_otra_regla_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    # Un reject cuya única causa es una palabra clave que la regla no declara (`enum`, no `required`).
    solo_enum = _aceptado()
    solo_enum.update(expectation="reject", reject_reason="BR3.5")
    solo_enum["payload"]["modo"] = "otro"
    _poner(tmp_path, BASE + "solo_enum.json", solo_enum)
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/solo_enum.json: el reject falla por otra regla (BR3.5, NFR12.1)"
    ]
    # Si además falla por la causa de la regla, basta: el fixture ejercita la regla.
    ambos = _rechazado()
    ambos["payload"]["modo"] = "otro"
    _poner(tmp_path, BASE + "ambos.json", ambos)
    assert len(guardia.comprobar(tmp_path, reglas=REGLA)) == 1


def test_un_accept_que_no_se_acepta_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    roto = _aceptado()
    roto["payload"]["modo"] = "otro"
    _poner(tmp_path, BASE + "roto.json", roto)
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/roto.json: el accept no se acepta (NFR12.1)"
    ]


def test_contrato_desconocido_y_fixture_ilegible_son_problemas(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    raro = _aceptado()
    raro["contract"] = "C99.nada"
    _poner(tmp_path, BASE + "raro.json", raro)
    (tmp_path / BASE / "roto.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/raro.json: contrato desconocido (NFR12.1)",
        "analyzer/v1/fixtures/roto.yaml: fixture ilegible (NFR12.1)",
    ]


def test_un_mensaje_de_cola_desconocido_y_una_expectativa_ajena(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    for nombre, contrato in (("cola.json", "C2.NoExiste"), ("sola.json", "C2")):
        desconocido = _aceptado()
        desconocido["contract"] = contrato
        _poner(tmp_path, BASE + nombre, desconocido)
    # Una expectativa que no es accept ni reject la reporta synthetic.py, no esta guardia.
    rara = _aceptado()
    rara["expectation"] = "maybe"
    _poner(tmp_path, BASE + "rara.json", rara)
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/cola.json: contrato desconocido (NFR12.1)",
        "analyzer/v1/fixtures/sola.json: contrato desconocido (NFR12.1)",
    ]


def test_lo_que_no_es_un_fixture_o_no_declara_su_regla_se_ignora(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    _poner(tmp_path, BASE + "lista.json", [1, 2])
    _poner(tmp_path, BASE + "suelto.json", {"a": 1})
    sin_razon = _rechazado()
    del sin_razon["reject_reason"]
    _poner(tmp_path, BASE + "sin_razon.json", sin_razon)
    ajena = _rechazado()
    ajena["reject_reason"] = "BR1.5"
    _poner(tmp_path, BASE + "ajena.json", ajena)
    (tmp_path / BASE / "huella.sha256").write_text("abc\n", encoding="utf-8")
    # Los directorios ajenos no se recorren.
    _poner(tmp_path, "vendor/fixtures/x.json", _aceptado())
    assert guardia.comprobar(tmp_path, reglas=REGLA) == []


def test_las_reglas_por_omision_son_las_de_regla(guardia: ModuleType, tmp_path: Path) -> None:
    assert guardia.comprobar(tmp_path / "vacio") != []
    assert len(guardia.comprobar(tmp_path / "vacio")) == 2 * len(guardia.REGLAS)


# E-24: las reglas de nivel 0 que se prueban con código y no con documentos, cada una con la prueba que la
# cubre (archivo bajo contracts/ y nombre de la prueba). Añadir una entrada requiere una precisión.
_UNA_PRUEBA = {
    "BR1.3": ("tests/contracts/test_queue_messages.py", "test_cada_fixture_de_cola_se_acepta_o_se_rechaza_por_su_regla"),
    "BR1.6": ("tests/checks/test_synthetic.py", "test_los_archivos_reales_de_contracts_son_sinteticos_y_sin_numeros_largos"),
    "BR1.7": ("tests/contracts/test_analyzer_copy.py", "test_sha256sums_tiene_dos_lineas_y_coincide_con_los_bytes"),
    "BR1.9": ("tests/test_validators.py", "test_una_palabra_clave_desconocida_se_rechaza"),
    "BR3.3": ("tests/guards/test_autonomia_03.py", "test_ningun_nombre_ni_enum_declara_veracidad"),
    "BR3.4": ("tests/checks/test_error_codes.py", "test_tabla_c6_del_arbol_real_completa"),
    "BR4.3": ("tests/contracts/test_review_suggestion.py", "test_las_citas_referencian_la_definicion_de_c6_por_id_canonico"),
    "BR5.1": ("tests/guards/test_autonomia_03.py", "test_c8_tiene_exactamente_los_terminos_aprobados"),
    "BR5.7": ("tests/checks/test_veracity.py", "test_el_aviso_versionado_trae_version_y_frase_base"),
    "BR5.8": ("tests/checks/test_scan_cases.py", "test_el_conjunto_versionado_cubre_cada_termino_y_cada_frase"),
    "BR6.1": ("tests/guards/test_autonomia_03.py", "test_hay_exactamente_nueve_rotulos_y_uno_por_tipo"),
    "BR6.2": ("tests/checks/test_veracity.py", "test_rotulos_con_una_fila_type_que_no_es_de_c6"),
    "BR6.3": ("tests/guards/test_autonomia_03.py", "test_los_rotulos_no_contienen_vocabulario_prohibido"),
    "BR7.1": ("tests/checks/test_config_write.py", "test_e15_put_profiles_nombra_perfil_en_la_ruta"),
    "BR7.2": ("tests/checks/test_error_codes.py", "test_toda_4xx_y_5xx_de_c1_es_una_referencia_a_problem"),
    "BR7.3": ("tests/contracts/test_console.py", "test_los_cuerpos_json_de_c1_son_estrictos"),
    "BR7.4": ("tests/checks/test_error_codes.py", "test_e31_code_sin_clase"),
    "BR9.2": ("tests/test_profiles.py", "test_e23_un_alias_a_un_papel_que_no_existe_se_rechaza"),
    "BR9.4": ("tests/test_profiles.py", "test_e24_otro_clave_se_rechaza_con_un_prefijo_y_se_acepta_con_otro"),
    "BR9.5": ("tests/test_profiles.py", "test_e26_un_papel_con_su_propio_fallback_se_rechaza"),
    "BR9.6": ("tests/typing/test_role_translation.py", "test_la_tabla_traduce_solo_los_tres_papeles_del_analizador_y_coincide_con_c6"),
    "BR9.7": ("tests/contracts/test_profiles_contract.py", "test_la_huella_jcs_de_la_configuracion_efectiva_es_la_del_fixture"),
    "BR9.8": ("tests/test_profiles.py", "test_validate_no_hace_entrada_salida_ni_lee_el_entorno"),
    "BR9.9": ("tests/typing/test_anonymizing_provider.py", "test_un_doble_con_solo_generate_pasa_mypy_estricto"),
    "BR11.1": ("tests/test_limits.py", "test_e33_una_variable_que_sube_la_cifra_se_rechaza"),
    "BR12.1": ("tests/test_package_map.py", "test_la_rueda_trae_el_mapa_completo_y_sin_fixtures"),
    "BR12.3": ("tests/test_registry.py", "test_la_forma_antigua_del_ref_no_se_resuelve_e36"),
}

# Cada regla cita una prueba o más: la primera es la positiva y las siguientes, sus controles negativos.
CON_CODIGO = {regla: (prueba,) for regla, prueba in _UNA_PRUEBA.items()}
CON_CODIGO.update(
    {
        # P-T18-10: BR1.1 y BR8.1 pasan a la lista con las pruebas que ya están en el árbol.
        "BR1.1": (
            ("tests/contracts/test_queue_messages.py", "test_cada_fixture_de_cola_se_acepta_o_se_rechaza_por_su_regla"),
        ),
        "BR8.1": (
            ("tests/contracts/test_console.py", "test_toda_fecha_tiene_el_formato_unico_con_el_mismo_patron"),
            ("tests/contracts/test_console.py", "test_las_fechas_reales_pasan_y_las_imposibles_o_con_otra_forma_no"),
        ),
        # F-05: BR3.4 y BR5.1 se citan con su control negativo.
        "BR3.4": (
            ("tests/checks/test_error_codes.py", "test_tabla_c6_del_arbol_real_completa"),
            ("tests/checks/test_error_codes.py", "test_e34_codigo_de_c6_sin_code"),
        ),
        "BR5.1": (
            ("tests/guards/test_autonomia_03.py", "test_c8_tiene_exactamente_los_terminos_aprobados"),
            ("tests/checks/test_veracity.py", "test_c8_con_un_termino_nuevo_o_repetido_da_br51"),
        ),
    }
)
REGLAS_DE_RULES_MD = (
    "aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md"
)


def _reglas_vigentes() -> set[str]:
    """Los ID de `rules.md` cuyo estado no es `Retirado`."""
    texto = (CONTRACTS_ROOT.parent / REGLAS_DE_RULES_MD).read_text(encoding="utf-8")
    vigentes: set[str] = set()
    for bloque in re.split(r"(?m)^  - id: ", texto)[1:]:
        identificador = bloque.split("\n", 1)[0].strip()
        estado = re.search(r"(?m)^    status: (.+)$", bloque)
        assert estado is not None, identificador
        if estado.group(1).strip() != "Retirado":
            vigentes.add(identificador)
    return vigentes


def test_e24_la_lista_de_reglas_con_codigo_es_cerrada_y_exacta(guardia: ModuleType) -> None:
    assert guardia.REGLAS_CON_CODIGO == CON_CODIGO
    assert len(guardia.REGLAS_CON_CODIGO) == 29
    # Ninguna regla está a la vez en dos listas.
    assert not set(guardia.REGLAS_CON_CODIGO) & set(guardia.REGLAS)
    assert not set(guardia.REGLAS_CON_CODIGO) & set(guardia.EXCLUIDAS)
    assert not set(guardia.REGLAS) & set(guardia.EXCLUIDAS)


def test_p_t18_10_no_hay_una_tercera_lista(guardia: ModuleType) -> None:
    # Toda regla de §4.10 tiene sus fixtures o una prueba en REGLAS_CON_CODIGO; SIN_PRUEBA desaparece.
    assert not hasattr(guardia, "SIN_PRUEBA")


def test_p_t18_10_las_listas_juntas_suman_todas_las_reglas_vigentes_de_rules_md(guardia: ModuleType) -> None:
    vigentes = _reglas_vigentes()
    assert len(vigentes) == 53, "rules.md: 56 reglas menos 3 retiradas"
    listadas = {r for r in (*guardia.REGLAS, *guardia.REGLAS_CON_CODIGO, *guardia.EXCLUIDAS) if r.startswith("BR")}
    assert sorted(vigentes - listadas) == [], "reglas vigentes que ninguna lista cubre"
    assert sorted(listadas - vigentes) == [], "reglas listadas que rules.md no tiene vigentes"


def test_p_t18_10_el_control_de_la_union_detecta_una_regla_que_falta(guardia: ModuleType) -> None:
    vigentes = _reglas_vigentes()
    listadas = {r for r in (*guardia.REGLAS, *guardia.REGLAS_CON_CODIGO, *guardia.EXCLUIDAS) if r.startswith("BR")}
    # Control negativo de la propia prueba: quitar una regla de la unión deja una vigente sin cubrir.
    assert vigentes - (listadas - {"BR1.1"}) == {"BR1.1"}
    assert (listadas | {"BR99.9"}) - vigentes == {"BR99.9"}


def test_e24_cada_prueba_de_la_lista_existe(guardia: ModuleType) -> None:
    assert guardia.comprobar_pruebas(CONTRACTS_ROOT) == []
    # No pasa en vacío: BR3.4 y BR5.1 llevan su control negativo.
    assert len(guardia.REGLAS_CON_CODIGO["BR3.4"]) == 2 and len(guardia.REGLAS_CON_CODIGO["BR5.1"]) == 2


def test_e24_una_prueba_inexistente_o_un_archivo_ausente_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_existe() -> None:\n    pass\n\n\nclass TestX:\n    def test_en_clase(self) -> None:\n        pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_roto.py").write_text("def (:\n", encoding="utf-8")
    reglas = {
        "BR1.3": (("tests/test_a.py", "test_existe"),),
        "BR1.6": (("tests/test_a.py", "test_en_clase"),),
        "BR1.7": (("tests/test_a.py", "test_no_existe"),),
        "BR1.9": (("tests/test_ausente.py", "test_existe"),),
        "BR3.3": (("tests/test_roto.py", "test_existe"),),
        # El control negativo que falta también se informa.
        "BR3.4": (("tests/test_a.py", "test_existe"), ("tests/test_a.py", "test_control_ausente")),
    }
    assert guardia.comprobar_pruebas(tmp_path, reglas=reglas) == [
        "BR1.7: la prueba test_no_existe no existe en tests/test_a.py (NFR12.1, §4.10)",
        "BR1.9: la prueba test_existe no existe en tests/test_ausente.py (NFR12.1, §4.10)",
        "BR3.3: la prueba test_existe no existe en tests/test_roto.py (NFR12.1, §4.10)",
        "BR3.4: la prueba test_control_ausente no existe en tests/test_a.py (NFR12.1, §4.10)",
    ]
