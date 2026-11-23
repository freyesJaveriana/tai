"""Módulo guardia de soberanía de datos: `servers` internos en todo contrato (NFR1.1, §4.9).

Los controles negativos trabajan sobre copias en `tmp_path`; nunca se toca un archivo versionado.
Cada constante, cada patrón y cada regla tiene un control positivo y uno negativo.
"""

import shutil
from pathlib import Path
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT

from veridicus_contracts.checks import servers as guardia

C21 = "api/anonymizer-proxy.v1.yaml"
# Los contratos que ya existen en esta tarea; `api/console.v2.yaml` (C1) llega en el paso 16.
EXISTENTES = tuple(ruta for ruta in guardia.CONTRATOS if ruta != "api/console.v2.yaml")

INTERNAS = [
    "/",
    "/api/v1",
    "http://veridicus-anonymizer-proxy:8080",
    "http://veridicus-a:1",
    "http://veridicus-a1-b2:65535/v1",
    "http://veridicus-x:12345/",
    "http://session-api.veridicus.svc.cluster.local",
    "http://session-api.veridicus.svc.cluster.local:8080",
    "http://a.svc.cluster.local:80/v1",
    "http://a-1.b-2.c.svc.cluster.local",
]
EXTERNAS = [
    "",
    "api/v1",
    "//api.openai.com",
    "//veridicus-x:80",
    "https://api.openai.com",
    "http://api.openai.com",
    "http://10.0.0.1:8080",
    "http://127.0.0.1",
    "http://localhost:8080",
    "https://veridicus-anonymizer-proxy:8080",
    "https://a.svc.cluster.local",
    "http://veridicus-x",
    "http://veridicus-:80",
    "http://veridicus:80",
    "http://anonymizer-proxy:8080",
    "http://Veridicus-x:80",
    "http://veridicus-X:80",
    "http://veridicus-x:123456",
    "http://veridicus-x:80@evil.example",
    "http://veridicus-x:80\n",
    "http://veridicus-x.evil.example:80",
    "http://a.svc.cluster.local.evil.example",
    "http://svc.cluster.local",
    "http://.svc.cluster.local",
    "http://a.svc.cluster.localx",
    "http://a_b.svc.cluster.local",
    "http://a.svc.cluster.local:",
    "http://a.svc.cluster.local:x",
    "http://a.svc.cluster.local\n",
    "ftp://veridicus-x:80",
]


@pytest.mark.parametrize("url", INTERNAS)
def test_es_interna_acepta_las_formas_declaradas(url: str) -> None:
    assert guardia.es_interna(url) is True


@pytest.mark.parametrize("url", EXTERNAS)
def test_es_interna_rechaza_todo_lo_demas(url: str) -> None:
    assert guardia.es_interna(url) is False


def test_el_tope_de_puerto_es_de_cinco_cifras_y_el_prefijo_es_veridicus() -> None:
    assert guardia.es_interna("http://veridicus-x:99999") is True
    assert guardia.es_interna("http://veridicus-x:100000") is False
    assert guardia.PREFIJO == "veridicus-"
    assert guardia.SUFIJO_DEL_CLUSTER == ".svc.cluster.local"


def test_los_contratos_que_recorre_son_exactamente_los_siete_de_4_9() -> None:
    assert guardia.CONTRATOS == (
        "api/console.v2.yaml",
        "health/health.v2.yaml",
        "api/anonymizer-proxy.v1.yaml",
        "api/speech-internal.v1.yaml",
        "queues/runs.v2.yaml",
        "queues/results.v2.yaml",
        "queues/speech.v2.yaml",
    )


def test_direcciones_de_openapi_incluyen_url_y_valores_por_omision() -> None:
    documento = {
        "servers": [
            {"url": "/api"},
            {"url": "http://{host}:80", "variables": {"host": {"default": "h1"}, "p": {"default": "8"}}},
            {"url": "/sin-variables", "variables": None},
        ]
    }
    assert guardia.direcciones(documento) == ["/api", "http://{host}:80", "h1", "8", "/sin-variables"]


def test_direcciones_de_asyncapi_anteponen_http_al_host() -> None:
    documento = {"servers": {"redis": {"host": "veridicus-redis:6379"}, "otro": {}}}
    assert guardia.direcciones(documento) == ["http://veridicus-redis:6379", "http://"]


@pytest.mark.parametrize("servidores", [None, [], {}, "texto", 7])
def test_direcciones_sin_servidores_utilizables_es_una_lista_vacia(servidores: Any) -> None:
    assert guardia.direcciones({"servers": servidores}) == []
    assert guardia.direcciones({}) == []


def test_direcciones_tolera_servidores_que_no_son_objetos() -> None:
    assert guardia.direcciones({"servers": ["texto", {"url": "/x"}]}) == ["", "/x"]
    assert guardia.direcciones({"servers": {"a": "texto"}}) == ["http://"]
    assert guardia.direcciones({"servers": [{"url": "/x", "variables": {"v": "texto"}}]}) == [
        "/x",
        "",
    ]
    assert guardia.direcciones({"servers": [{"url": "/x", "variables": ["texto"]}]}) == ["/x"]
    assert guardia.direcciones({"servers": [{"url": "/x", "variables": {"v": {}}}]}) == ["/x", ""]


def test_direcciones_toma_url_y_host_como_texto() -> None:
    assert guardia.direcciones({"servers": [{"url": 5}]}) == ["5"]
    assert guardia.direcciones({"servers": {"a": {"host": 5}}}) == ["http://5"]


def test_el_arbol_versionado_cumple_todo() -> None:
    assert guardia.comprobar(CONTRACTS_ROOT, EXISTENTES) == []


def test_la_entrada_principal_recorre_los_siete_y_c1_ausente_es_un_problema() -> None:
    """Hasta el paso 16, C1 no existe: es el único problema y no se pasa en vacío."""
    esperado = (
        []
        if (CONTRACTS_ROOT / "api" / "console.v2.yaml").is_file()
        else ["api/console.v2.yaml: contrato ausente (NFR1.1, §4.9)"]
    )
    assert guardia.comprobar(CONTRACTS_ROOT) == esperado


def _copia(tmp_path: Path, rutas: tuple[str, ...] = EXISTENTES) -> Path:
    raiz = tmp_path / "contracts"
    for ruta in rutas:
        destino = raiz / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(CONTRACTS_ROOT / ruta, destino)
    return raiz


def _con_servers(tmp_path: Path, ruta: str, texto: str) -> Path:
    raiz = _copia(tmp_path)
    original = (raiz / ruta).read_text(encoding="utf-8")
    inicio = original.index("servers:")
    fin = original.index("\npaths:", inicio) + 1
    (raiz / ruta).write_text(original[:inicio] + texto + original[fin:], encoding="utf-8")
    return raiz


def test_la_copia_limpia_pasa_y_no_pasa_en_vacio(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    assert (raiz / C21).is_file()
    assert guardia.comprobar(raiz, EXISTENTES) == []


def test_control_c21_con_https_api_openai_com(tmp_path: Path) -> None:
    raiz = _con_servers(tmp_path, C21, "servers:\n  - url: https://api.openai.com\n")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        "api/anonymizer-proxy.v1.yaml: dirección no interna: https://api.openai.com (NFR1.1, §4.9)"
    ]


@pytest.mark.parametrize(
    "url",
    [
        "http://203.0.113.7:8080",
        "https://veridicus-anonymizer-proxy:8080",
        "http://anonymizer-proxy:8080",
        "//veridicus-x:80",
    ],
    ids=["ip-literal", "https-en-el-cluster", "sin-prefijo", "relativa-de-red"],
)
def test_cada_regla_tiene_su_control_negativo_en_c21(tmp_path: Path, url: str) -> None:
    raiz = _con_servers(tmp_path, C21, f"servers:\n  - url: {url}\n")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"api/anonymizer-proxy.v1.yaml: dirección no interna: {url} (NFR1.1, §4.9)"
    ]


def test_un_valor_por_omision_externo_se_detecta(tmp_path: Path) -> None:
    texto = (
        "servers:\n  - url: 'http://{host}:80'\n    variables:\n"
        "      host: {default: api.openai.com}\n"
    )
    raiz = _con_servers(tmp_path, C21, texto)
    problemas = guardia.comprobar(raiz, EXISTENTES)
    assert problemas == [
        "api/anonymizer-proxy.v1.yaml: dirección no interna: http://{host}:80 (NFR1.1, §4.9)",
        "api/anonymizer-proxy.v1.yaml: dirección no interna: api.openai.com (NFR1.1, §4.9)",
    ]


def test_server_ausente_o_vacio_es_un_problema(tmp_path: Path) -> None:
    raiz = _con_servers(tmp_path, C21, "servers: []\n")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        "api/anonymizer-proxy.v1.yaml: no declara ningún servidor en servers (NFR1.1, §4.9)"
    ]
    raiz = _con_servers(tmp_path / "otro", "health/health.v2.yaml", "x-otra: 1\n")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        "health/health.v2.yaml: no declara ningún servidor en servers (NFR1.1, §4.9)"
    ]


def test_un_asyncapi_con_host_externo_se_detecta(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    ruta = raiz / "queues" / "runs.v2.yaml"
    texto = ruta.read_text(encoding="utf-8")
    assert "host: 'veridicus-redis:6379'" in texto
    ruta.write_text(texto.replace("host: 'veridicus-redis:6379'", "host: 'api.openai.com:443'"))
    assert guardia.comprobar(raiz, EXISTENTES) == [
        "queues/runs.v2.yaml: dirección no interna: http://api.openai.com:443 (NFR1.1, §4.9)"
    ]


def test_un_contrato_ausente_no_pasa_en_vacio(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    (raiz / C21).unlink()
    assert guardia.comprobar(raiz, EXISTENTES) == [
        "api/anonymizer-proxy.v1.yaml: contrato ausente (NFR1.1, §4.9)"
    ]


def test_un_contrato_ilegible_es_un_problema(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    (raiz / C21).write_text("a: 1\na: 2\n", encoding="utf-8")
    problemas = guardia.comprobar(raiz, EXISTENTES)
    assert len(problemas) == 1
    assert problemas[0].startswith("api/anonymizer-proxy.v1.yaml: contrato ilegible: ")


def test_un_documento_que_no_es_un_objeto_no_declara_servidores(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    (raiz / C21).write_text("- uno\n- dos\n", encoding="utf-8")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        "api/anonymizer-proxy.v1.yaml: no declara ningún servidor en servers (NFR1.1, §4.9)"
    ]


def test_varios_defectos_se_listan_todos_en_orden(tmp_path: Path) -> None:
    raiz = _con_servers(tmp_path, C21, "servers:\n  - url: https://a.example\n  - url: /ok\n")
    ruta = raiz / "health" / "health.v2.yaml"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("servers:", "servers:\n  - url: http://b.example"))
    problemas = guardia.comprobar(raiz, EXISTENTES)
    assert problemas == [
        "health/health.v2.yaml: dirección no interna: http://b.example (NFR1.1, §4.9)",
        "api/anonymizer-proxy.v1.yaml: dirección no interna: https://a.example (NFR1.1, §4.9)",
    ]
