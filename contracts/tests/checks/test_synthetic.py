"""Guardia de datos sintéticos (security-design §4.10, NFR12.1, NFR12.2, BR1.6; cierra K-04).

`checks/synthetic.py` exige que cada fixture declare `synthetic: true`, `expectation`, `reject_reason` si es
`reject` y `mentions`; que cada mención esté en `fixtures/synthetic-names.yaml` y aparezca en el texto, y
rechaza secuencias de 6 a 10 dígitos y de 23 dígitos, con o sin separadores, en todo campo de texto y en
todo `example`. Se eximen los campos uuid y las huellas de 64 caracteres hexadecimales (K-04). Los mensajes
nombran el archivo y el puntero, nunca el valor.
"""

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar

CATALOGO = CONTRACTS_ROOT / "fixtures" / "synthetic-names.yaml"
UUID = "123e4567-e89b-12d3-a456-426614174000"
HUELLA = "0123456789abcdef" * 4


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.synthetic", "T18, paso 19")


def _fixture(**cambios: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "fixture_id": "x-valid",
        "contract": "C6.entrada",
        "synthetic": True,
        "expectation": "accept",
        "mentions": ["Villa Rocamora"],
        "payload": {"texto": "Esa noche dormí en Villa Rocamora, en la casa de mi hermana."},
    }
    base.update(cambios)
    return {clave: valor for clave, valor in base.items() if valor is not ...}


def _escribir(raiz: Path, nombre: str, documento: Any) -> Path:
    ruta = raiz / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(documento, ensure_ascii=False), encoding="utf-8")
    return ruta


def _problemas(guardia: ModuleType, raiz: Path, documento: Any, nombre: str = "f/x.json") -> list[str]:
    archivo = _escribir(raiz, nombre, documento)
    problemas: list[str] = guardia.scan([archivo], catalogo=CATALOGO)
    for problema in problemas:
        assert problema.startswith(archivo.as_posix()), problema
        assert problema.endswith("(NFR12.1)"), problema
    return problemas


def test_los_archivos_reales_de_contracts_son_sinteticos_y_sin_numeros_largos(guardia: ModuleType) -> None:
    archivos = guardia.archivos([CONTRACTS_ROOT])
    assert len(archivos) > 50, "la guardia no pasa en vacío"
    nombres = {a.name for a in archivos}
    assert {"scan-cases.v1.yaml", "testimony-warning-cases.v1.yaml", "run.valid.yaml"} <= nombres
    assert guardia.scan([CONTRACTS_ROOT]) == []
    # El catálogo por defecto es el del repositorio.
    assert guardia.scan([CONTRACTS_ROOT], catalogo=CATALOGO) == []


def test_un_fixture_valido_pasa(guardia: ModuleType, tmp_path: Path) -> None:
    assert _problemas(guardia, tmp_path, _fixture()) == []
    rechazo = _fixture(expectation="reject", reject_reason="BR3.1")
    assert _problemas(guardia, tmp_path, rechazo) == []
    assert _problemas(guardia, tmp_path, _fixture(mentions=[], payload={"texto": "sin nombres"})) == []


@pytest.mark.parametrize(
    ("cambios", "texto"),
    [
        ({"synthetic": ...}, "faltan campos"),
        ({"mentions": ...}, "faltan campos"),
        ({"synthetic": False}, "synthetic debe ser true"),
        ({"synthetic": "true"}, "synthetic debe ser true"),
        ({"expectation": "maybe"}, "expectation debe ser accept o reject"),
        ({"expectation": "reject"}, "reject exige reject_reason"),
        ({"expectation": "reject", "reject_reason": ""}, "reject exige reject_reason"),
        ({"reject_reason": "BR3.1"}, "accept no lleva reject_reason"),
        ({"mentions": "Villa Rocamora"}, "mentions debe ser una lista"),
        ({"mentions": ["Villa Inventada"]}, "mención que no está en el catálogo"),
        ({"mentions": ["Puerto Altamira"]}, "mención que no aparece en el texto"),
    ],
)
def test_formato_de_fixture_de_4_10(guardia: ModuleType, tmp_path: Path, cambios: dict[str, Any], texto: str) -> None:
    problemas = _problemas(guardia, tmp_path, _fixture(**cambios))
    assert len(problemas) == 1 and texto in problemas[0], problemas
    assert "Inventada" not in problemas[0] and "Altamira" not in problemas[0], "no repite la mención"


def test_un_documento_con_payload_pero_sin_los_demas_campos_es_un_fixture_incompleto(
    guardia: ModuleType, tmp_path: Path
) -> None:
    problemas = _problemas(guardia, tmp_path, {"payload": {"a": "b"}})
    assert len(problemas) == 1 and "faltan campos" in problemas[0]


@pytest.mark.parametrize(
    ("texto", "marcado"),
    [
        ("12345678", True),  # el control de §4.10: un número de 8 dígitos
        ("123456", True),
        ("1234567890", True),
        ("12345", False),
        ("12345678901", False),
        ("1234567890123456789012", False),
        ("12345678901234567890123", True),
        ("123456789012345678901234", False),
        ("1234-5678", True),
        ("1234 5678", True),
        ("12.345.678", True),
        ("12/34/5678", True),
        ("1-2-3-4-5-6", True),
        ("1234-5678-9012-3456-7890-123", True),
        ("1 de 2 y 3 de 4", False),
        ("abc 12 def 34 ghi 56", False),
        ("SINT-0002", False),
        ("versión 1.0.0", False),
    ],
)
def test_secuencias_de_digitos(guardia: ModuleType, tmp_path: Path, texto: str, marcado: bool) -> None:
    problemas = _problemas(guardia, tmp_path, _fixture(mentions=[], payload={"texto": texto}))
    assert bool(problemas) is marcado, (texto, problemas)
    if marcado:
        assert problemas[0].startswith(f"{tmp_path.as_posix()}/f/x.json#/payload/texto: ")
        assert "secuencia numérica" in problemas[0]
        sin_regla = problemas[0].removesuffix(" (NFR12.1)")
        assert not any(c.isdigit() for c in sin_regla.split("#", 1)[1]), "no repite el valor"


def test_la_secuencia_se_busca_en_cada_campo_de_texto_anidado(guardia: ModuleType, tmp_path: Path) -> None:
    carga = {"turnos": [{"n": 1, "texto": "sin números"}, {"n": 2, "texto": "llame al 12345678"}], "n": 12345678}
    problemas = _problemas(guardia, tmp_path, _fixture(mentions=[], payload=carga))
    assert len(problemas) == 1 and "#/payload/turnos/1/texto" in problemas[0]


def test_k04_se_eximen_uuid_huellas_y_fechas_completas(guardia: ModuleType, tmp_path: Path) -> None:
    carga = {
        "id": UUID,
        "huella": HUELLA,
        "registrado_en": "2026-11-20T10:00:00Z",
        "fecha": "2026-11-20",
        "version_de_precios": "2026-11",
        "con_milis": "2026-11-20T10:00:00.123456+05:00",
    }
    assert _problemas(guardia, tmp_path, _fixture(mentions=[], payload=carga)) == []
    # La exención es por forma completa: una frase con la fecha, o una huella con un carácter de más, no.
    for malo in ("nació el 2026-11-20", HUELLA + "0", UUID.replace("123e", "1234567e"), "2026-11-20T10:00:00Zx"):
        problemas = _problemas(guardia, tmp_path, _fixture(mentions=[], payload={"v": malo}))
        assert len(problemas) == 1, malo


@pytest.mark.parametrize(
    "texto",
    [
        "1234-56-78",  # tiene la forma de una fecha y no lo es (8 dígitos)
        "2026-13-45",  # mes y día imposibles
        "2026-02-30",  # día que no existe
        "1234-56",  # año-mes con un mes imposible (6 dígitos)
        "2026-00",
        "2026-11-24T25:00:00Z",  # hora imposible
        "2026-11-24T10:61:00Z",
        "2026-11-24T10:00:00+25:00",  # desplazamiento imposible
        "2026-11-24T10:00:00.1234567890123",  # fracción sin cota
        "2026-11-24T10:00:00.1234567Z",  # siete dígitos de fracción
    ],
)
def test_f03_una_fecha_imposible_o_una_fraccion_larga_no_se_exime(
    guardia: ModuleType, tmp_path: Path, texto: str
) -> None:
    problemas = _problemas(guardia, tmp_path, _fixture(mentions=[], payload={"v": texto}))
    assert len(problemas) == 1, texto


@pytest.mark.parametrize(
    "texto",
    ["2026-11", "2026-12", "2026-11-24", "2024-02-29", "2026-11-24T10:00:00Z", "2026-11-24 10:00", "2026-11-24T10:00:00.123456+05:30"],
)
def test_f03_las_fechas_validas_con_fraccion_acotada_se_eximen(
    guardia: ModuleType, tmp_path: Path, texto: str
) -> None:
    assert _problemas(guardia, tmp_path, _fixture(mentions=[], payload={"v": texto})) == []


def test_en_un_esquema_solo_se_revisan_los_example_y_no_la_prosa(guardia: ModuleType, tmp_path: Path) -> None:
    esquema = {
        "$id": "/veridicus/contracts/x/v1",
        "description": "Se acepta hasta 12345678 y 1234567 por RFC.",
        "properties": {
            "a": {"type": "string", "example": "12345678"},
            "b": {"type": "string", "examples": ["ok", "87654321"]},
            "c": {"type": "string", "example": {"k": ["1234567"]}},
            "d": {"type": "string", "example": UUID},
        },
    }
    problemas = _problemas(guardia, tmp_path, esquema, "x/esquema.json")
    assert [p.split("#", 1)[1].split(":", 1)[0] for p in problemas] == [
        "/properties/a/example",
        "/properties/b/examples/1",
        "/properties/c/example/k/0",
    ]


def test_las_literal_sources_y_los_casos_de_aviso_estan_en_el_alcance(guardia: ModuleType, tmp_path: Path) -> None:
    casos = {"cases": [{"id": "c", "text": "limpio", "literal_sources": ["Mi cédula es 12345678."]}]}
    problemas = _problemas(guardia, tmp_path, casos, "integrity/scan-cases.v1.yaml")
    assert len(problemas) == 1 and "#/cases/0/literal_sources/0" in problemas[0]
    aviso = {"cases": [{"id": "c", "note": "ok", "turns": ["no hay nada", "tel 123456"]}]}
    problemas = _problemas(guardia, tmp_path, aviso, "integrity/testimony-warning-cases.v1.yaml")
    assert len(problemas) == 1 and "#/cases/0/turns/1" in problemas[0]
    # Los archivos reales, con una copia sembrada con un número, dejan de pasar.
    real = (CONTRACTS_ROOT / "integrity" / "scan-cases.v1.yaml").read_text(encoding="utf-8")
    sembrado = tmp_path / "integrity" / "scan-cases.v1.yaml"
    sembrado.parent.mkdir(parents=True, exist_ok=True)
    sembrado.write_text(real.replace("literal_sources: []", 'literal_sources: ["clave 12345678"]', 1), encoding="utf-8")
    assert len(guardia.scan([sembrado], catalogo=CATALOGO)) == 1


def test_el_catalogo_ausente_o_ilegible_es_un_problema_unico(guardia: ModuleType, tmp_path: Path) -> None:
    archivo = _escribir(tmp_path, "f/x.json", _fixture())
    ausente = guardia.scan([archivo], catalogo=tmp_path / "no-existe.yaml")
    assert len(ausente) == 2
    assert any("catálogo de nombres sintéticos" in p for p in ausente)
    roto = tmp_path / "roto.yaml"
    roto.write_text("a: 1\na: 2\n", encoding="utf-8")
    assert any("catálogo de nombres sintéticos" in p for p in guardia.scan([archivo], catalogo=roto))
    # Sin catálogo en la llamada, se usa el del repositorio.
    assert guardia.scan([archivo]) == []


def test_archivos_ilegibles_directorios_y_sufijos(guardia: ModuleType, tmp_path: Path) -> None:
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "roto.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    (tmp_path / "d" / "huella.sha256").write_text("12345678\n", encoding="utf-8")
    (tmp_path / "d" / "lista.json").write_text("[12345678, \"no es objeto\"]", encoding="utf-8")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "ajeno.json").write_text('{"example": "12345678"}', encoding="utf-8")
    problemas = guardia.scan([tmp_path], catalogo=CATALOGO)
    assert len(problemas) == 1 and problemas[0].startswith(f"{tmp_path.as_posix()}/d/roto.yaml: ")
    assert "ilegible" in problemas[0] and problemas[0].endswith("(NFR12.1)")
    assert sorted(a.name for a in guardia.archivos([tmp_path])) == ["lista.json", "roto.yaml"]
    # Un archivo dado de forma directa se mira solo si es YAML o JSON.
    assert guardia.archivos([tmp_path / "d" / "huella.sha256", str(tmp_path / "d" / "lista.json")]) == [
        tmp_path / "d" / "lista.json"
    ]
