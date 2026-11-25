"""Guardia de patrones sin retroceso catastrófico (security-design §4.5, NFR10.6, K-24).

`checks/redos.py` hace el recorrido completo del árbol con `re._parser`, comprueba el subconjunto portátil
(el mismo patrón corre en JavaScript), exige entrada acotada y deja a Hypothesis medir con un techo de 1 s
una entrada adversaria de 10 000 caracteres. Depende de una API privada de Python 3.12: la prueba de
versión es obligatoria.
"""

import re
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract
from hypothesis import given, settings
from hypothesis import strategies as st

TECHO_DE_SEGUNDOS = 1.0
LARGO_ADVERSARIO = 10_000


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.redos", "T18, paso 19")


def test_la_api_privada_exige_python_3_12_y_detecta_los_controles_conocidos(
    guardia: ModuleType,
) -> None:
    # Si cambia la versión de Python, la suite falla aquí antes de dar un falso verde (§4.5).
    assert sys.version_info[:2] == (3, 12)
    assert guardia.violaciones_del_arbol("^(a+)+$") == [guardia.ANIDADA]
    assert guardia.violaciones_del_arbol("^[a-z]+$") == []


CONTROLES_NEGATIVOS = [
    ("^(a+)+$", {"ANIDADA"}),
    ("^(a|aa)*$", {"RAMA"}),
    ("^(x|(a+)+)$", {"ANIDADA"}),
    ("^(?:a|(?:b+)+)*$", {"ANIDADA", "RAMA"}),
    ("^(\\w+)\\1$", {"REFERENCIA"}),
    # K-24: la rama idéntica la rechaza la regla de BRANCH.
    ("^(a|a)+$", {"RAMA"}),
    # Otras formas de repetición ilimitada dentro de otra.
    ("^(?:a{2,})+$", {"ANIDADA"}),
    ("^(a+?)*$", {"ANIDADA"}),
    ("^(?:a*+b)*$", {"ANIDADA"}),
    ("^(?>(a+)+)$", {"ANIDADA"}),
    ("^(?=(a+)+)a$", {"ANIDADA"}),
    ("^(?!(a+)+)a$", {"ANIDADA"}),
    ("^(?<=(?:ab|cd)+)c$", {"RAMA"}),
    ("^(a)?(?(1)(b+)+|c)$", {"ANIDADA"}),
    ("^(a)?(?(1)b|(c+)+)$", {"ANIDADA"}),
    ("^(a)?(?(1)b)$", {"REFERENCIA"}),
    ("^(?:ab)+$", set()),
]


@pytest.mark.parametrize(("patron", "esperadas"), CONTROLES_NEGATIVOS)
def test_recorrido_completo_del_arbol(
    guardia: ModuleType, patron: str, esperadas: set[str]
) -> None:
    codigos = {getattr(guardia, nombre) for nombre in esperadas}
    encontradas = set(guardia.violaciones_del_arbol(patron))
    # Las reglas de grupos y repeticiones no se pierden por estar dentro de un contenedor.
    assert codigos <= encontradas
    if not esperadas:
        assert encontradas == set()


def test_la_referencia_condicional_tambien_es_hacia_atras(guardia: ModuleType) -> None:
    assert guardia.violaciones_del_arbol("^(a)?(?(1)b|c)$") == [guardia.REFERENCIA]
    assert guardia.violaciones_del_arbol("^(a)\\1$") == [guardia.REFERENCIA]


def test_un_patron_sin_defectos_no_da_hallazgos(guardia: ModuleType) -> None:
    for patron in (
        "^[a-z0-9]{1,64}$",
        "^(?:ab)+$",
        "^(?:ab){2,5}$",
        "^[A-Z]{2}-[0-9]{4}$",
        "^(?=a)a$",
    ):
        assert guardia.comprobar_patron(patron) == []


# K-24, limitación declarada: varios `[a-z]*` contiguos son polinomiales y el recorrido del árbol no los
# ve. Lo que los acota es la regla de entrada acotada (un patrón con repetición ilimitada exige maxLength).
def test_k24_varios_cuantificadores_contiguos_quedan_como_limitacion_declarada(
    guardia: ModuleType,
) -> None:
    patron = "^[a-z]*[a-z]*[a-z]*$"
    assert guardia.violaciones_del_arbol(patron) == []
    assert guardia.LIMITACION_K24 and "K-24" in guardia.LIMITACION_K24
    sin_cota = guardia.comprobar_esquema({"type": "string", "pattern": patron})
    assert len(sin_cota) == 1 and "maxLength" in sin_cota[0]
    acotado = {
        "type": "string",
        "pattern": patron,
        "maxLength": 64,
        "x-veridicus-limit": "turn_chars",
    }
    assert guardia.comprobar_esquema(acotado) == []


@pytest.mark.parametrize(
    ("patron", "etiqueta"),
    [
        ("^\\d{6}$", "CLASE"),
        ("^[\\d]{6}$", "CLASE"),
        ("^\\w{1,5}$", "CLASE"),
        ("^a\\sb$", "CLASE"),
        ("^\\ba$", "CLASE"),
        ("^a\\B$", "CLASE"),
        ("^(?P<x>a)$", "NOMBRADO"),
        ("(?i)^a$", "BANDERAS"),
        ("^(?i:a)$", "BANDERAS"),
        ("^(?<=a)b$", "ATRAS"),
        ("^(?<!a)b$", "ATRAS"),
        ("a+", "SIN_ANCLAR"),
        ("^a", "SIN_ANCLAR"),
        ("a$", "SIN_ANCLAR"),
        ("^a$|b", "SIN_ANCLAR"),
        ("", "SIN_ANCLAR"),
    ],
)
def test_subconjunto_portatil(guardia: ModuleType, patron: str, etiqueta: str) -> None:
    assert getattr(guardia, etiqueta) in guardia.violaciones_portables(patron)
    assert guardia.comprobar_patron(patron), patron


def test_los_hallazgos_de_un_patron_van_ordenados_y_sin_repetir(guardia: ModuleType) -> None:
    hallazgos = guardia.comprobar_patron("(\\d+)+\\1")
    assert hallazgos == sorted(set(hallazgos))
    assert len(hallazgos) == len(set(hallazgos)) >= 3


def test_un_patron_que_no_compila_es_un_problema(guardia: ModuleType) -> None:
    assert guardia.comprobar_patron("^(a$") == [guardia.NO_VALIDO]
    assert guardia.violaciones_del_arbol("^(a$") == [guardia.NO_VALIDO]
    assert guardia.violaciones_portables("^(a$") == [guardia.NO_VALIDO]


def test_entrada_acotada(guardia: ModuleType) -> None:
    # `^[a-z]+$` sin maxLength es rojo; con maxLength y su límite, verde.
    assert len(guardia.comprobar_esquema({"pattern": "^[a-z]+$"})) == 1
    con_cota = {"pattern": "^[a-z]+$", "maxLength": 64}
    problemas = guardia.comprobar_esquema(con_cota)
    assert len(problemas) == 1 and "x-veridicus-limit" in problemas[0]
    assert guardia.comprobar_esquema({**con_cota, "x-veridicus-limit": "turn_chars"}) == []
    for ilimitado in ("^a*$", "^a{2,}$", "^(?:ab)+$"):
        assert len(guardia.comprobar_esquema({"pattern": ilimitado})) == 1
    # Un patrón sin repetición ilimitada se acota solo.
    assert guardia.comprobar_esquema({"pattern": "^[a-z]{1,8}$"}) == []
    assert guardia.comprobar_esquema({"pattern": "^[a-z]?$"}) == []
    assert guardia.comprobar_esquema({"type": "string"}) == []
    assert guardia.comprobar_esquema({"pattern": 3}) == []
    # Un patrón que no compila no puede decidir si hay repetición: lo dice comprobar_patron.
    assert guardia.comprobar_esquema({"pattern": "^(a$"}) == []


def test_comprobar_documento_recorre_todo_el_arbol_con_puntero(guardia: ModuleType) -> None:
    documento = {
        "properties": {
            "a": {"pattern": "^(a+)+$", "maxLength": 8, "x-veridicus-limit": "x"},
            "b": [{"pattern": "^[a-z]+$"}],
            "c": {"pattern": "^[a-z]{1,3}$"},
        }
    }
    problemas = guardia.comprobar_documento(documento, "c.json")
    assert [p.split(": ", 1)[0] for p in problemas] == [
        "c.json#/properties/a",
        "c.json#/properties/b/0",
    ]
    assert all("(NFR10.6)" in p for p in problemas)
    assert all("^" not in p for p in problemas), "el mensaje no repite el patrón"


C6 = "analyzer/v1/salida.schema.json"
PUNTEROS_DE_C6 = [
    "/$defs/cita/properties/turno",
    "/$defs/hallazgo/properties/id",
    "/$defs/registro/properties/descartes/items/properties/turno_a",
    "/$defs/registro/properties/descartes/items/properties/turno_b",
    "/properties/observaciones_conductor/items/properties/turnos/items",
]


def test_e23_la_lista_de_excepciones_de_c6_es_cerrada_y_exacta(guardia: ModuleType) -> None:
    assert isinstance(guardia.EXCEPCIONES, tuple)
    assert [(e.ruta, e.puntero) for e in guardia.EXCEPCIONES] == [(C6, p) for p in PUNTEROS_DE_C6]
    assert all("BR1.7" in e.motivo for e in guardia.EXCEPCIONES)


def test_e23_la_copia_de_c6_pasa_solo_por_sus_cinco_punteros(guardia: ModuleType) -> None:
    documento = load_contract(C6)
    # Sin la lista no pasaría: las cinco son repeticiones ilimitadas sin maxLength.
    sin_lista = guardia.comprobar_documento(documento, "otro/propio.schema.json")
    assert sorted(m.split(": ", 1)[0].split("#", 1)[1] for m in sin_lista) == sorted(PUNTEROS_DE_C6)
    assert guardia.comprobar_documento(documento, C6) == []


def test_e23_el_mismo_patron_en_un_contrato_propio_sigue_en_rojo(guardia: ModuleType) -> None:
    nodo = {"properties": {"turno": {"type": "string", "pattern": "^T[0-9]+$"}}}
    assert guardia.comprobar_documento(nodo, "queues/runs.v2.yaml") == [
        "queues/runs.v2.yaml#/properties/turno: repetición ilimitada sin maxLength (NFR10.6)"
    ]
    cita = {
        "$defs": {"cita": {"properties": {"turno": {"type": "string", "pattern": "^T[0-9]+$"}}}}
    }
    assert guardia.comprobar_documento(cita, C6) == []
    # Con el mismo contenido pero en otro archivo de analyzer/v1/ la excepción no vale.
    assert len(guardia.comprobar_documento(cita, "analyzer/v1/entrada.schema.json")) == 1


def test_e23_la_excepcion_no_cubre_otro_puntero_de_c6_ni_otra_regla(guardia: ModuleType) -> None:
    otro = {
        "$defs": {"cita": {"properties": {"texto": {"type": "string", "pattern": "^T[0-9]+$"}}}}
    }
    problemas = guardia.comprobar_documento(otro, C6)
    assert [p.split(": ", 1)[0] for p in problemas] == [f"{C6}#/$defs/cita/properties/texto"]
    # En un puntero exceptuado, la repetición anidada y lo no portátil siguen en rojo.
    anidada = {"$defs": {"cita": {"properties": {"turno": {"pattern": "^(a+)+$"}}}}}
    problemas = guardia.comprobar_documento(anidada, C6)
    assert len(problemas) == 1 and "dentro de otra repetición" in problemas[0]
    no_portatil = {"$defs": {"cita": {"properties": {"turno": {"pattern": "^T\\d+$"}}}}}
    problemas = guardia.comprobar_documento(no_portatil, C6)
    assert len(problemas) == 1 and "no portátil" in problemas[0]


def test_las_claves_de_pattern_properties_tambien_son_patrones(guardia: ModuleType) -> None:
    documento = {
        "properties": {"m": {"patternProperties": {"^(a+)+$": {}, "^[a-z]{1,8}$": {}, "a": {}}}}
    }
    problemas = guardia.comprobar_documento(documento, "c.json")
    assert problemas == [
        "c.json#/properties/m/patternProperties/^(a+)+$: repetición ilimitada dentro de otra repetición ilimitada (NFR10.6)",
        "c.json#/properties/m/patternProperties/a: patrón sin anclar con ^ y $ (NFR10.6)",
    ]
    assert guardia.patrones_de_nodo(documento["properties"]["m"]) == [
        "^(a+)+$",
        "^[a-z]{1,8}$",
        "a",
    ]
    assert guardia.patrones_de_nodo({"patternProperties": 3, "pattern": 4}) == []
    assert guardia.patrones_de_nodo({"pattern": "^a$"}) == ["^a$"]


# Lo que queda en rojo tras la excepción de C6 son los defectos de los contratos que corrige U01-T18b
# (C2, C3, C5, C18, C21 y la ruta de voz). Esta prueba pasa a verde cuando T18b se fusiona.
def test_los_patrones_de_los_contratos_versionados_son_seguros(guardia: ModuleType) -> None:
    patrones = guardia.patrones(CONTRACTS_ROOT)
    assert len(patrones) >= 10, "la guardia no pasa en vacío"
    assert guardia.comprobar(CONTRACTS_ROOT) == []


def test_comprobar_salta_directorios_ajenos_y_reporta_lo_ilegible(
    guardia: ModuleType, tmp_path: Path
) -> None:
    (tmp_path / "a").mkdir()
    acotado = "p:\n  pattern: '^(a+)+$'\n  maxLength: 4\n  x-veridicus-limit: turn_chars\n"
    (tmp_path / "a" / "malo.yaml").write_text(acotado, encoding="utf-8")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "ajeno.json").write_text('{"pattern": "^(a+)+$"}', encoding="utf-8")
    (tmp_path / "roto.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    problemas = guardia.comprobar(tmp_path)
    assert [p.split(":", 1)[0] for p in problemas] == ["a/malo.yaml#/p", "roto.yaml"]
    assert guardia.patrones(tmp_path) == ["^(a+)+$"]


def _medir(patron: str) -> None:
    """Hypothesis genera cadenas válidas del patrón y se las vuelve adversarias de 10 000 caracteres."""

    @settings(max_examples=12, deadline=None, database=None)
    @given(st.from_regex(patron, fullmatch=True))
    def propiedad(ejemplo: str) -> None:
        base = ejemplo or "a"
        repetida = (base * (LARGO_ADVERSARIO // len(base) + 1))[:LARGO_ADVERSARIO]
        for adversaria in (repetida, repetida[:-1] + "\x00", "a" * (LARGO_ADVERSARIO - 1) + "!"):
            assert len(adversaria) <= LARGO_ADVERSARIO
            assert _tiempo(patron, adversaria) < TECHO_DE_SEGUNDOS

    propiedad()


def _tiempo(patron: str, texto: str) -> float:
    inicio = time.perf_counter()
    re.fullmatch(patron, texto)
    return time.perf_counter() - inicio


def test_hypothesis_techo_de_1_s_sobre_una_entrada_adversaria_de_10000_caracteres(
    guardia: ModuleType,
) -> None:
    for patron in guardia.patrones(CONTRACTS_ROOT):
        _medir(patron)
