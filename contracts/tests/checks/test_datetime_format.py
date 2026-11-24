"""Módulo guardia de fechas: el patrón único de BR8.1 y E16 (§4.12).

Los controles negativos trabajan sobre copias en memoria o en `tmp_path`; los positivos, sobre el
árbol versionado. La copia de C6 (`analyzer/v1/`) queda fuera: no se toca (BR1.8).
"""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, load_contract

from veridicus_contracts.checks import datetime_format as guardia
from veridicus_contracts.validators import ValidationFailure, validate_instance

PATRON = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
FORMATO = "format/datetime.v1.yaml"
E16 = ("2026-10-02T21:40:00.123Z", "2026-10-02T16:40:00-05:00")


def _fecha(**resto: Any) -> dict[str, Any]:
    return {"type": "string", "format": "date-time", **resto}


def test_el_arbol_versionado_cumple_y_el_patron_es_el_de_c1() -> None:
    documento = load_contract(FORMATO)
    assert documento["pattern"] == PATRON
    assert documento["format"] == "date-time"
    assert guardia.comprobar_formato(documento) == []
    assert guardia.comprobar(CONTRACTS_ROOT) == []
    c1 = load_contract("api/console.v2.yaml")
    assert c1["components"]["schemas"]["DateTime"]["pattern"] == documento["pattern"]


def test_e16_rechaza_fracciones_y_desfases_y_acepta_la_forma_unica() -> None:
    assert guardia.fecha_valida("2026-10-02T21:40:00Z", PATRON)
    for texto in E16:
        assert not guardia.fecha_valida(texto, PATRON), texto
    esquema = load_contract("api/console.v2.yaml")["components"]["schemas"]["DateTime"]
    validate_instance(esquema, "2026-10-02T21:40:00Z")
    for texto in E16:
        with pytest.raises(ValidationFailure, match="does not match"):
            validate_instance(esquema, texto)


def test_una_fecha_imposible_es_rojo_aunque_tenga_la_forma() -> None:
    for texto in (
        "2026-02-30T10:00:00Z",
        "2026-13-01T10:00:00Z",
        "2026-10-02T25:00:00Z",
        "2026-10-02T10:61:00Z",
        "2026-10-02T10:00:61Z",
        "2026-10-02T21:40:00Z\n",
    ):
        assert not guardia.fecha_valida(texto, PATRON), repr(texto)
    esquema = load_contract("api/console.v2.yaml")["components"]["schemas"]["DateTime"]
    with pytest.raises(ValidationFailure, match="date-time"):
        validate_instance(esquema, "2026-02-30T10:00:00Z")
    assert guardia.fecha_valida("2028-02-29T00:00:00Z", PATRON)
    assert not guardia.fecha_valida("2027-02-29T00:00:00Z", PATRON)


def test_un_date_time_sin_el_patron_o_con_otro_es_rojo() -> None:
    sano = {"properties": {"at": _fecha(pattern=PATRON)}}
    assert guardia.comprobar_documento("queues/x.yaml", sano, PATRON) == []
    sin = {"properties": {"at": _fecha()}}
    assert guardia.comprobar_documento("queues/x.yaml", sin, PATRON) == [
        "queues/x.yaml: /properties/at: date-time sin el pattern de format/datetime.v1.yaml "
        "(BR8.1, E16)"
    ]
    otro = {"a": [{"b": _fecha(pattern="^.*$")}], "c": {"format": "uuid"}, "d": [1, "date-time"]}
    assert guardia.comprobar_documento("queues/x.yaml", otro, PATRON) == [
        "queues/x.yaml: /a/0/b: date-time sin el pattern de format/datetime.v1.yaml (BR8.1, E16)"
    ]
    permisivo = {"at": _fecha(pattern=PATRON.replace("Z$", "(Z|[+-][0-9]{2}:[0-9]{2})$"))}
    assert len(guardia.comprobar_documento("cli/x.yaml", permisivo, PATRON)) == 1


def test_un_formato_con_patron_debil_o_forma_rota_es_rojo() -> None:
    base = load_contract(FORMATO)
    debil = copy.deepcopy(base)
    debil["pattern"] = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]+)?Z$"
    assert guardia.comprobar_formato(debil) == [
        f"{FORMATO}: /pattern: el patrón admite una forma que E16 rechaza (BR8.1)"
    ]
    estrecho = {**base, "pattern": "^$"}
    assert guardia.comprobar_formato(estrecho) == [
        f"{FORMATO}: /pattern: el patrón no acepta la forma única AAAA-MM-DDTHH:MM:SSZ (BR8.1)"
    ]
    roto = {**base, "pattern": "(sin cerrar"}
    assert guardia.comprobar_formato(roto) == [f"{FORMATO}: /pattern: no es una expresión regular (BR8.1)"]
    sin_patron = {k: v for k, v in base.items() if k != "pattern"}
    assert guardia.comprobar_formato(sin_patron) == [f"{FORMATO}: /pattern: falta el patrón (BR8.1)"]
    otro_tipo = {**base, "format": "date", "type": "integer"}
    assert guardia.comprobar_formato(otro_tipo) == [
        f"{FORMATO}: /: debe ser type string y format date-time (BR8.1)"
    ]
    assert guardia.comprobar_formato("texto") == [
        f"{FORMATO}: /: debe ser type string y format date-time (BR8.1)"
    ]


def test_comprobar_recorre_los_contratos_propios_y_deja_fuera_c6_y_fixtures(tmp_path: Path) -> None:
    raiz = tmp_path / "contracts"
    for directorio in ("format", "queues", "analyzer/v1", "queues/fixtures", "vendor", ".venv"):
        (raiz / directorio).mkdir(parents=True)
    (raiz / FORMATO).write_text(
        json.dumps({"schema_version": "1.0.0", "type": "string", "format": "date-time", "pattern": PATRON}),
        encoding="utf-8",
    )
    suelta = json.dumps({"properties": {"at": _fecha()}})
    for ajeno in ("analyzer/v1/salida.schema.json", "queues/fixtures/x.json", "vendor/y.json"):
        (raiz / ajeno).write_text(suelta, encoding="utf-8")
    (raiz / ".venv" / "z.json").write_text(suelta, encoding="utf-8")
    (raiz / "queues" / "notas.txt").write_text("date-time", encoding="utf-8")
    assert guardia.comprobar(raiz) == []
    (raiz / "queues" / "run.json").write_text(suelta, encoding="utf-8")
    assert guardia.comprobar(raiz) == [
        "queues/run.json: /properties/at: date-time sin el pattern de format/datetime.v1.yaml "
        "(BR8.1, E16)"
    ]
    (raiz / FORMATO).write_text(json.dumps({"format": "date-time"}), encoding="utf-8")
    assert guardia.comprobar(raiz) == [
        f"{FORMATO}: /: debe ser type string y format date-time (BR8.1)"
    ]
