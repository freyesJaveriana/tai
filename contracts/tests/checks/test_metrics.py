"""Módulo guardia de métricas: prefijo, unicidad, etiquetas cerradas y sin texto libre (§4.12, BR8.2).

Los controles negativos trabajan sobre copias en memoria o en `tmp_path`; los positivos, sobre el
árbol versionado. Un mensaje nombra el archivo, el puntero y la regla, nunca el valor.
"""

import copy
from pathlib import Path
from typing import Any

from helpers import CONTRACTS_ROOT, load_contract

from veridicus_contracts.checks import metrics as guardia

ARCHIVOS = {
    "anonymizer.v1.yaml",
    "assistant-extras.v1.yaml",
    "review.v2.yaml",
    "session-lifecycle.v1.yaml",
    "text-flow.v1.yaml",
    "voice.v1.yaml",
}
CODIGOS = frozenset({"analysis.system", "analysis.timeout", "limits.exceeded"})
UUID = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


def _metrica(
    nombre: str = "veridicus_x_total",
    etiquetas: list[Any] | None = None,
    **resto: Any,
) -> dict[str, Any]:
    return {
        "name": nombre,
        "type": "counter",
        "labels": [] if etiquetas is None else etiquetas,
        "description": "Cuenta algo.",
        **resto,
    }


def _doc(*metricas: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "1.0.0", "endpoint": "GET /metrics", "metrics": list(metricas)}


def _etiqueta(nombre: str, *valores: str) -> dict[str, Any]:
    return {"name": nombre, "values": list(valores)}


def _problemas(documentos: dict[str, Any]) -> list[str]:
    return guardia.comprobar_documentos(documentos, CODIGOS)


def _con(etiqueta: Any) -> list[str]:
    return _problemas({"a.yaml": _doc(_metrica(etiquetas=[etiqueta]))})


def test_el_arbol_versionado_cumple_todo_y_trae_los_seis_archivos() -> None:
    carpeta = CONTRACTS_ROOT / "metrics"
    assert {ruta.name for ruta in carpeta.glob("*.yaml")} == ARCHIVOS
    assert guardia.comprobar(CONTRACTS_ROOT) == []
    nombres = [
        metrica["name"]
        for archivo in sorted(ARCHIVOS)
        for metrica in load_contract(f"metrics/{archivo}")["metrics"]
    ]
    assert len(nombres) == len(set(nombres)) >= 30
    assert {"veridicus_review_decisions_total", "veridicus_anonymizer_ready"} <= set(nombres)
    c15 = load_contract("metrics/review.v2.yaml")
    ratio = next(m for m in c15["metrics"] if m["name"] == "veridicus_session_dismissal_ratio")
    assert "AC10.8.2" in ratio["description"]
    assert ratio["labels"] == [{"name": "session_id", "pattern": UUID}]


def test_una_metrica_sin_prefijo_o_con_forma_rota_es_rojo() -> None:
    assert _problemas({"a.yaml": _doc(_metrica())}) == []
    sin_prefijo = _problemas({"a.yaml": _doc(_metrica("x_total"))})
    assert sin_prefijo == ["a.yaml: /metrics/0/name: el nombre no empieza por veridicus_ (BR8.2)"]
    rota = _metrica()
    rota["type"] = "summary"
    rota["description"] = " "
    rota["labels"] = "state"
    assert _problemas({"a.yaml": _doc(rota)}) == [
        "a.yaml: /metrics/0/type: el tipo no es counter, gauge ni histogram (C15)",
        "a.yaml: /metrics/0/description: falta la descripción (C15)",
        "a.yaml: /metrics/0/labels: las etiquetas deben ser una lista (C15)",
    ]
    sin_nombre = {"type": "counter", "labels": [], "description": "d"}
    assert any("/metrics/0/name" in p for p in _problemas({"a.yaml": _doc(sin_nombre)}))
    assert _problemas({"a.yaml": _doc("no es un objeto")}) == [  # type: ignore[arg-type]
        "a.yaml: /metrics/0: la métrica debe ser un objeto (C15)"
    ]
    for malo in ("texto", {"schema_version": "1.0.0", "endpoint": "GET /metrics", "metrics": []}):
        assert _problemas({"a.yaml": malo}) == [
            "a.yaml: /: la forma no es la de C15 (schema_version, endpoint y metrics con elementos)"
        ]
    sin_endpoint = _doc(_metrica())
    del sin_endpoint["endpoint"]
    assert len(_problemas({"a.yaml": sin_endpoint})) == 1


def test_un_nombre_repetido_entre_dos_archivos_o_dentro_de_uno_es_rojo() -> None:
    uno = _doc(_metrica("veridicus_a_total"), _metrica("veridicus_b_total"))
    otro = _doc(_metrica("veridicus_c_total"), _metrica("veridicus_a_total"))
    assert _problemas({"uno.yaml": uno, "otro.yaml": copy.deepcopy(otro)}) == [
        "otro.yaml: /metrics/1/name: el nombre ya está en uno.yaml /metrics/0/name (§4.12)"
    ]
    dentro = _doc(_metrica("veridicus_a_total"), _metrica("veridicus_a_total"))
    assert _problemas({"uno.yaml": dentro}) == [
        "uno.yaml: /metrics/1/name: el nombre ya está en uno.yaml /metrics/0/name (§4.12)"
    ]


def test_una_etiqueta_fuera_de_la_lista_cerrada_es_rojo() -> None:
    assert len(guardia.ETIQUETAS) == 10
    for nombre in guardia.ETIQUETAS - {"session_id", "error_code"}:
        assert _con(_etiqueta(nombre, "a")) == [], nombre
    assert _con(_etiqueta("run_id", "a")) == [
        "a.yaml: /metrics/0/labels/0: la etiqueta no es de la lista cerrada (§4.12)"
    ]
    assert _con({"values": ["a"]}) == [
        "a.yaml: /metrics/0/labels/0: la etiqueta debe ser un objeto con name (§4.12)"
    ]
    assert _con("state") == [
        "a.yaml: /metrics/0/labels/0: la etiqueta debe ser un objeto con name (§4.12)"
    ]


def test_una_etiqueta_sin_values_o_de_texto_libre_es_rojo() -> None:
    sin_values = {"name": "state"}
    assert _con(sin_values) == [
        "a.yaml: /metrics/0/labels/0: la etiqueta declara values sin elementos (§4.12)"
    ]
    assert _con(_etiqueta("state")) == [
        "a.yaml: /metrics/0/labels/0: la etiqueta declara values sin elementos (§4.12)"
    ]
    assert _con({"name": "state", "values": "abierta"}) == [
        "a.yaml: /metrics/0/labels/0: la etiqueta declara values sin elementos (§4.12)"
    ]
    libre = {"name": "state", "values": ["a"], "pattern": "^.*$"}
    assert _con(libre) == [
        "a.yaml: /metrics/0/labels/0: la etiqueta admite texto libre; declare values (§4.12)"
    ]
    for valores in (["a", "a"], ["a", ""], ["a", 3]):
        assert _con({"name": "state", "values": valores}) == [
            "a.yaml: /metrics/0/labels/0: los values deben ser textos no vacíos y distintos (§4.12)"
        ], valores


def test_error_code_toma_el_catalogo_mas_none_y_session_id_el_patron_de_un_uuid() -> None:
    assert _con(_etiqueta("error_code", "none", "analysis.system", "limits.exceeded")) == []
    fuera = _con(_etiqueta("error_code", "none", "inventado.code"))
    assert fuera == [
        "a.yaml: /metrics/0/labels/0: error_code con un valor fuera del catálogo y de none (E-20)"
    ]
    assert "inventado" not in fuera[0]
    for centinela in ("ok", ""):
        assert _con(_etiqueta("error_code", centinela))
    otra = _con(_etiqueta("state", "inventado.code"))
    assert otra == []
    # session_id: solo el patrón de un UUID, sin values.
    assert _con({"name": "session_id", "pattern": UUID}) == []
    aviso = "a.yaml: /metrics/0/labels/0: session_id declara solo el patrón de un UUID (§4.12)"
    assert _con({"name": "session_id", "pattern": "^.*$"}) == [aviso]
    assert _con({"name": "session_id"}) == [aviso]
    assert _con({"name": "session_id", "pattern": UUID, "values": ["x"]}) == [aviso]


def test_comprobar_lee_el_directorio_y_el_catalogo_de_una_copia(tmp_path: Path) -> None:
    raiz = tmp_path / "contracts"
    (raiz / "metrics").mkdir(parents=True)
    (raiz / "errors").mkdir()
    catalogo = (CONTRACTS_ROOT / "errors" / "error-codes.v2.yaml").read_text(encoding="utf-8")
    (raiz / "errors" / "error-codes.v2.yaml").write_text(catalogo, encoding="utf-8")
    assert guardia.comprobar(raiz) == ["metrics/: no hay archivos de métricas que comprobar (§4.12)"]
    texto = (
        "schema_version: 1.0.0\nendpoint: GET /metrics\nmetrics:\n"
        "  - name: veridicus_a_total\n    type: counter\n    description: d\n    labels:\n"
        "      - {name: error_code, values: [none, inventado.code]}\n"
    )
    (raiz / "metrics" / "a.v1.yaml").write_text(texto, encoding="utf-8")
    assert guardia.comprobar(raiz) == [
        (
            "metrics/a.v1.yaml: /metrics/0/labels/0: error_code con un valor fuera del catálogo "
            "y de none (E-20)"
        )
    ]
