"""Módulo guardia de soberanía de datos: `servers` internos en todo contrato (NFR1.1, §4.9).

Los controles negativos trabajan sobre copias en `tmp_path` o sobre documentos en memoria; nunca
se toca un archivo versionado. Cada constante, cada patrón y cada regla tiene un control positivo y
uno negativo, y ningún mensaje de la guardia copia un valor del documento (se prueba con un *canary*).
"""

import copy
import shutil
from pathlib import Path
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT

from veridicus_contracts.checks import servers as guardia

C21 = "api/anonymizer-proxy.v1.yaml"
# Los contratos que ya existen en esta tarea; `api/console.v2.yaml` (C1) llega en el paso 16.
EXISTENTES = tuple(ruta for ruta in guardia.CONTRATOS if ruta != "api/console.v2.yaml")
CANARY = "canary-7f3a"
SUFIJO = "(NFR1.1, §4.9)"

INTERNAS = [
    "/",
    "/api/v1",
    "/a.b_c~d-e/F9",
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
    "/\\evil.com",
    "/\\/evil.com",
    "/\t/evil.com",
    "/ /evil.com",
    "/%2F/evil.com",
    "/%2f%2fevil.com",
    "/a@b",
    "/a:b",
    "/a?b",
    "/a#b",
    "/a b",
    "/{p}",
    "/a\n",
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
    "http://veridicus-x:80/a\\b",
    "http://veridicus-x:80/a?b",
    "http://veridicus-x.evil.example:80",
    "http://a.svc.cluster.local.evil.example",
    "http://svc.cluster.local",
    "http://.svc.cluster.local",
    "http://a.svc.cluster.localx",
    "http://a_b.svc.cluster.local",
    "http://a.svc.cluster.local:",
    "http://a.svc.cluster.local:x",
    "http://a.svc.cluster.local\n",
    "http://a.svc.cluster.local/a b",
    "http://evil-svc-cluster-local",
    "http://evilxsvcxclusterxlocal",
    "http://a.svcxclusterxlocal",
    "http://a.svc-cluster.local",
    "http://a.svc.cluster-local",
    "http://a.svc.clusterxlocal",
    "http://a.svcxcluster.local",
    "http://a-svc.cluster.local",
    "ftp://veridicus-x:80",
    "http://veridicus-x:{port}",
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


def _oas(**extra: Any) -> dict[str, Any]:
    """Un OpenAPI mínimo con un servidor global interno, más lo que se le añada."""
    documento: dict[str, Any] = {"servers": [{"url": "/"}], "paths": {"/x": {"get": {}}}}
    documento.update(extra)
    return documento


def _problemas(documento: Any) -> list[str]:
    return guardia.comprobar_documento("c.yaml", documento)


def _externo(puntero: str, regla: str = "dirección no interna") -> str:
    return f"c.yaml: {puntero}: {regla} {SUFIJO}"


def test_un_documento_limpio_y_el_servidor_global_se_reportan_con_su_puntero() -> None:
    assert _problemas(_oas()) == []
    sucio = _oas(servers=[{"url": "/"}, {"url": "https://api.openai.com"}])
    assert _problemas(sucio) == [_externo("/servers/1")]


def test_servers_por_ruta_por_operacion_y_en_enlaces_se_revisan() -> None:
    malo = {"url": "https://api.openai.com"}
    por_ruta = _oas()
    por_ruta["paths"]["/x"]["servers"] = [malo]
    assert _problemas(por_ruta) == [_externo("/paths/~1x/servers/0")]
    por_operacion = _oas()
    por_operacion["paths"]["/x"]["get"]["servers"] = [malo]
    assert _problemas(por_operacion) == [_externo("/paths/~1x/get/servers/0")]
    en_respuesta = _oas()
    en_respuesta["paths"]["/x"]["get"]["responses"] = {"200": {"links": {"l": {"server": malo}}}}
    assert _problemas(en_respuesta) == [_externo("/paths/~1x/get/responses/200/links/l/server")]
    en_componentes = _oas(components={"links": {"l": {"server": malo}}})
    assert _problemas(en_componentes) == [_externo("/components/links/l/server")]
    en_callback = _oas()
    en_callback["paths"]["/x"]["get"]["callbacks"] = {"cb": {"expr": {"servers": [malo]}}}
    assert _problemas(en_callback) == [_externo("/paths/~1x/get/callbacks/cb/expr/servers/0")]
    en_callback_con_operacion = _oas()
    en_callback_con_operacion["paths"]["/x"]["get"]["callbacks"] = {
        "cb": {"expr": {"post": {"servers": [malo]}}}
    }
    assert _problemas(en_callback_con_operacion) == [
        _externo("/paths/~1x/get/callbacks/cb/expr/post/servers/0")
    ]
    en_webhook = _oas(webhooks={"w": {"servers": [malo], "put": {"servers": [malo]}}})
    assert _problemas(en_webhook) == [
        _externo("/webhooks/w/servers/0"),
        _externo("/webhooks/w/put/servers/0"),
    ]
    en_servidores_de_componentes = _oas(components={"servers": {"s": {"host": "api.openai.com"}}})
    assert _problemas(en_servidores_de_componentes) == [_externo("/components/servers/s")]
    en_respuestas_de_componentes = _oas(
        components={"responses": {"r": {"links": {"l": {"server": malo}}}}}
    )
    assert _problemas(en_respuestas_de_componentes) == [
        _externo("/components/responses/r/links/l/server")
    ]
    en_pathitems = _oas(components={"pathItems": {"p": {"get": {"servers": [malo]}}}})
    assert _problemas(en_pathitems) == [_externo("/components/pathItems/p/get/servers/0")]


def test_los_nombres_que_coinciden_con_palabras_de_esquema_o_ejemplo_no_ocultan_servers() -> None:
    """F-09: `schema`, `example`, `examples`, `schemas` y `properties` son nombres válidos de claves."""
    malo = {"url": "https://api.openai.com"}
    en_callback = _oas()
    en_callback["paths"]["/x"]["get"]["callbacks"] = {"schema": {"expr": {"servers": [malo]}}}
    assert _problemas(en_callback) == [_externo("/paths/~1x/get/callbacks/schema/expr/servers/0")]
    en_enlace = _oas()
    en_enlace["paths"]["/x"]["get"]["responses"] = {"200": {"links": {"example": {"server": malo}}}}
    assert _problemas(en_enlace) == [_externo("/paths/~1x/get/responses/200/links/example/server")]
    en_webhook = _oas(webhooks={"examples": {"servers": [malo]}})
    assert _problemas(en_webhook) == [_externo("/webhooks/examples/servers/0")]
    en_pathitems = _oas(components={"pathItems": {"schemas": {"servers": [malo]}}})
    assert _problemas(en_pathitems) == [_externo("/components/pathItems/schemas/servers/0")]
    en_enlaces = _oas(components={"links": {"example": {"server": malo}}})
    assert _problemas(en_enlaces) == [_externo("/components/links/example/server")]
    en_callbacks = _oas(components={"callbacks": {"properties": {"expr": {"servers": [malo]}}}})
    assert _problemas(en_callbacks) == [_externo("/components/callbacks/properties/expr/servers/0")]


def test_un_servers_global_con_un_nombre_parecido_no_cuenta() -> None:
    assert _problemas({"serversX": [{"url": "/"}]}) == [
        f"c.yaml: no declara ningún servidor en servers {SUFIJO}"
    ]
    assert _problemas({"x-servers": [{"url": "/"}]}) == [
        f"c.yaml: no declara ningún servidor en servers {SUFIJO}"
    ]


def test_las_estructuras_que_no_son_objetos_se_recorren_sin_error() -> None:
    documento = _oas(
        paths={"/x": "texto", "/y": {"get": "texto", "put": {"callbacks": "x", "responses": "x"}}},
        webhooks=["x"],
        components="x",
    )
    assert _problemas(documento) == []
    documento = _oas(
        paths="x",
        components={
            "pathItems": "x",
            "callbacks": {"c": "x", "d": {"e": "x"}},
            "links": "x",
            "responses": {"r": "x", "s": {"links": "x"}, "t": {"links": {"l": "x"}}},
            "servers": "x",
        },
    )
    assert _problemas(documento) == [_externo("/components/servers", "servidor mal formado")]
    documento = _oas()
    documento["paths"]["/x"]["get"]["responses"] = {"200": {"links": {"l": {}}}}
    documento["paths"]["/x"]["get"]["callbacks"] = {"cb": "x"}
    assert _problemas(documento) == []


def test_servers_internos_por_ruta_y_enlaces_no_dan_problemas() -> None:
    bueno = {"url": "http://veridicus-x:80"}
    documento = _oas()
    documento["paths"]["/x"]["servers"] = [bueno]
    documento["paths"]["/x"]["get"]["servers"] = [bueno]
    documento["paths"]["/x"]["get"]["responses"] = {"200": {"links": {"l": {"server": bueno}}}}
    assert _problemas(documento) == []


def test_los_esquemas_y_los_ejemplos_no_son_estructura() -> None:
    falso = {"servers": [{"url": "https://api.openai.com"}], "server": "x"}
    documento = _oas(
        components={
            "schemas": {"S": falso},
            "examples": {"E": falso},
        }
    )
    documento["paths"]["/x"]["get"]["responses"] = {
        "200": {"content": {"a/b": {"schema": falso, "example": falso, "examples": {"e": falso}}}}
    }
    documento["paths"]["/x"]["get"]["x-props"] = {"properties": falso}
    assert _problemas(documento) == []


def test_un_puntero_escapa_la_barra_y_la_tilde_del_nombre() -> None:
    documento = _oas()
    documento["paths"] = {"/a~b/c": {"servers": [{"url": "//evil.example"}]}}
    assert _problemas(documento) == [_externo("/paths/~1a~0b~1c/servers/0")]


@pytest.mark.parametrize("valor", ["texto", 7, True])
def test_servers_que_no_es_lista_ni_mapa_es_mal_formado(valor: Any) -> None:
    assert _problemas({"servers": valor}) == [_externo("/servers", "servidor mal formado")]
    por_ruta = _oas(paths={"/x": {"servers": valor}})
    assert _problemas(por_ruta) == [_externo("/paths/~1x/servers", "servidor mal formado")]


def test_un_servidor_que_no_es_un_objeto_es_mal_formado() -> None:
    assert _problemas({"servers": ["texto", {"url": "/"}]}) == [
        _externo("/servers/0", "servidor mal formado")
    ]
    assert _problemas({"servers": {"a": "texto"}}) == [
        _externo("/servers/a", "servidor mal formado")
    ]
    enlace = _oas()
    enlace["paths"]["/x"]["get"]["responses"] = {"200": {"links": {"l": {"server": "x"}}}}
    assert _problemas(enlace) == [
        _externo("/paths/~1x/get/responses/200/links/l/server", "servidor mal formado")
    ]


@pytest.mark.parametrize("documento", [None, [], {}, "texto", 7, {"servers": []}, {"servers": {}}])
def test_sin_servidores_globales_no_pasa_en_vacio(documento: Any) -> None:
    assert _problemas(documento) == [f"c.yaml: no declara ningún servidor en servers {SUFIJO}"]


def test_solo_servers_por_ruta_no_cuenta_como_servidor_global() -> None:
    documento = {"paths": {"/x": {"servers": [{"url": "/"}]}}}
    assert _problemas(documento) == [f"c.yaml: no declara ningún servidor en servers {SUFIJO}"]


def test_el_problema_de_sin_servidores_va_primero() -> None:
    documento = {"paths": {"/x": {"servers": [{"url": "https://a.example"}]}}}
    assert _problemas(documento) == [
        f"c.yaml: no declara ningún servidor en servers {SUFIJO}",
        _externo("/paths/~1x/servers/0"),
    ]


def test_variable_con_url_de_ruta_y_default_externo_se_detecta() -> None:
    servidor = {"url": "/{p}", "variables": {"p": {"default": "/evil.com"}}}
    assert _problemas(_oas(servers=[servidor])) == [_externo("/servers/0")]


def test_variable_con_un_valor_de_enum_externo_se_detecta() -> None:
    servidor = {
        "url": "http://veridicus-x:{port}",
        "variables": {"port": {"default": "8080", "enum": ["8080", "80@evil.example"]}},
    }
    assert _problemas(_oas(servers=[servidor])) == [_externo("/servers/0")]


def test_variable_de_puerto_interna_no_da_falso_positivo() -> None:
    servidor = {
        "url": "http://veridicus-x:{port}",
        "variables": {"port": {"default": "8080", "enum": ["8080", "9090"]}},
    }
    assert _problemas(_oas(servers=[servidor])) == []
    numerico = {"url": "http://veridicus-x:{port}", "variables": {"port": {"default": 8080}}}
    assert _problemas(_oas(servers=[numerico])) == []


def test_variable_con_host_externo_por_omision_se_detecta() -> None:
    servidor = {"url": "http://{host}:80", "variables": {"host": {"default": "api.openai.com"}}}
    assert _problemas(_oas(servers=[servidor])) == [_externo("/servers/0")]


def test_se_combinan_las_variables_y_basta_una_combinacion_externa() -> None:
    servidor = {
        "url": "http://{a}-{b}:80",
        "variables": {
            "a": {"default": "veridicus", "enum": ["veridicus", "evil"]},
            "b": {"default": "x"},
        },
    }
    assert _problemas(_oas(servers=[servidor])) == [_externo("/servers/0")]
    interno = {
        "url": "http://veridicus-{b}:80{c}",
        "variables": {"b": {"default": "x", "enum": ["y"]}, "c": {"default": "/v1"}},
    }
    assert _problemas(_oas(servers=[interno])) == []


def test_variable_sin_default_o_sin_declarar_deja_la_llave_y_se_detecta() -> None:
    sin_default = {"url": "http://veridicus-x:{port}", "variables": {"port": {"enum": ["80"]}}}
    assert _problemas(_oas(servers=[sin_default])) == [_externo("/servers/0")]
    sin_declarar = {"url": "/{p}"}
    assert _problemas(_oas(servers=[sin_declarar])) == [_externo("/servers/0")]


MAL_FORMADA = "variable de servidor mal formada"


@pytest.mark.parametrize("variable", ["texto", 7, None, [], ["p"], True])
def test_una_variable_que_no_es_un_objeto_es_mal_formada_y_no_falla_con_typeerror(
    variable: Any,
) -> None:
    usada = {"url": "/{p}", "variables": {"p": variable}}
    assert _problemas(_oas(servers=[usada])) == [
        _externo("/servers/0", MAL_FORMADA),
        _externo("/servers/0"),
    ]
    sin_uso = {"url": "/", "variables": {"p": variable}}
    assert _problemas(_oas(servers=[sin_uso])) == [_externo("/servers/0", MAL_FORMADA)]


@pytest.mark.parametrize("variables", ["texto", 7, None, [], ["p"], True])
def test_variables_que_no_es_un_objeto_es_mal_formada(variables: Any) -> None:
    assert _problemas(_oas(servers=[{"url": "/", "variables": variables}])) == [
        _externo("/servers/0", MAL_FORMADA)
    ]


@pytest.mark.parametrize("valor", [None, 7, [], ["x"], "x", True])
def test_un_server_de_enlace_o_de_lista_que_no_es_un_objeto_es_mal_formado(valor: Any) -> None:
    enlace = _oas()
    enlace["paths"]["/x"]["get"]["responses"] = {"200": {"links": {"l": {"server": valor}}}}
    assert _problemas(enlace) == [
        _externo("/paths/~1x/get/responses/200/links/l/server", "servidor mal formado")
    ]
    assert _problemas(_oas(servers=[valor])) == [_externo("/servers/0", "servidor mal formado")]
    assert _problemas({"servers": {"a": valor}}) == [_externo("/servers/a", "servidor mal formado")]


def _version(documento: Any) -> list[str]:
    return guardia.comprobar_version("c.yaml", documento)


@pytest.mark.parametrize("version", ["3.1.0", "3.1.9", "3.1.0-rc1"])
def test_las_versiones_3_1_de_openapi_pasan(version: str) -> None:
    assert _version({"openapi": version}) == []


@pytest.mark.parametrize("version", ["3.0.0", "3.0.9", "3.0.0-rc1"])
def test_las_versiones_3_0_de_asyncapi_pasan(version: str) -> None:
    assert _version({"asyncapi": version}) == []


@pytest.mark.parametrize(
    "version", ["3.2.0", "3.0.3", "3.10.0", "3.1", "4.1.0", "v3.1.0", "", None, 3.1, 7]
)
def test_otras_versiones_de_openapi_no_se_admiten_porque_no_se_recorren_sus_nodos(
    version: Any,
) -> None:
    assert _version({"openapi": version}) == [
        _externo("/openapi", "versión de OpenAPI no admitida")
    ]


@pytest.mark.parametrize("version", ["3.1.0", "2.6.0", "3.0", "3.00.0", "v3.0.0", "", None, 3.0, 7])
def test_otras_versiones_de_asyncapi_no_se_admiten(version: Any) -> None:
    assert _version({"asyncapi": version}) == [
        _externo("/asyncapi", "versión de AsyncAPI no admitida")
    ]


SIN_VERSION = f"c.yaml: /: versión no admitida {SUFIJO}"


@pytest.mark.parametrize(
    "documento",
    [
        {},
        None,
        [],
        "texto",
        {"servers": [{"url": "/"}]},
        {"swagger": "2.0", "host": "api.openai.com"},
        {"swagger": "2.0", "openapi": "3.1.0"},
        {"swagger": "2.0", "asyncapi": "3.0.0"},
        {"openapi": "3.1.0", "asyncapi": "3.0.0"},
    ],
    ids=[
        "vacio",
        "none",
        "lista",
        "texto",
        "sin-clave",
        "swagger",
        "swagger-y-openapi",
        "swagger-y-asyncapi",
        "ambos",
    ],
)
def test_un_documento_sin_openapi_ni_asyncapi_o_con_swagger_o_con_ambos_no_se_admite(
    documento: Any,
) -> None:
    assert _version(documento) == [SIN_VERSION]


@pytest.mark.parametrize(
    "metodo", ["get", "put", "post", "delete", "options", "head", "patch", "trace"]
)
def test_servers_por_operacion_en_cada_uno_de_los_ocho_metodos(metodo: str) -> None:
    malo = {"url": "https://api.openai.com"}
    documento = _oas(paths={"/x": {metodo: {"servers": [malo]}}})
    assert _problemas(documento) == [_externo(f"/paths/~1x/{metodo}/servers/0")]
    en_webhook = _oas(webhooks={"w": {metodo: {"servers": [malo]}}})
    assert _problemas(en_webhook) == [_externo(f"/webhooks/w/{metodo}/servers/0")]


def test_los_metodos_que_recorre_son_exactamente_los_ocho_de_openapi_3_1() -> None:
    assert guardia.METODOS == ("get", "put", "post", "delete", "options", "head", "patch", "trace")


FUERA = "referencia fuera de la estructura"
DESTINOS_MALOS = [
    "#/x-evil",
    "otro.yaml#/p",
    "#/components/schemas/S",
    "#/components/pathItems",
    "#/components/pathItems/p%2Fx",
    "#/components/pathItems/a/b",
    "#/components/pathItems/a#b",
    "#/components/pathItems/inexistente",
    "#/x/components/pathItems/p",
    "",
    7,
    None,
]


@pytest.mark.parametrize("destino", DESTINOS_MALOS)
def test_un_ref_estructural_fuera_de_components_se_detecta_en_cada_tipo_de_nodo(
    destino: Any,
) -> None:
    ref = {"$ref": destino}
    elemento = _oas(paths={"/x": ref})
    assert _problemas(elemento) == [_externo("/paths/~1x", FUERA)]
    webhook = _oas(webhooks={"w": ref})
    assert _problemas(webhook) == [_externo("/webhooks/w", FUERA)]
    en_componentes = _oas(components={"pathItems": {"p": ref}})
    assert _problemas(en_componentes) == [_externo("/components/pathItems/p", FUERA)]
    respuesta = _oas(paths={"/x": {"get": {"responses": {"200": ref}}}})
    assert _problemas(respuesta) == [_externo("/paths/~1x/get/responses/200", FUERA)]
    respuesta_de_componentes = _oas(components={"responses": {"r": ref}})
    assert _problemas(respuesta_de_componentes) == [_externo("/components/responses/r", FUERA)]
    enlace = _oas(paths={"/x": {"get": {"responses": {"200": {"links": {"l": ref}}}}}})
    assert _problemas(enlace) == [_externo("/paths/~1x/get/responses/200/links/l", FUERA)]
    enlace_de_componentes = _oas(components={"links": {"l": ref}})
    assert _problemas(enlace_de_componentes) == [_externo("/components/links/l", FUERA)]
    callback = _oas(paths={"/x": {"get": {"callbacks": {"cb": ref}}}})
    assert _problemas(callback) == [_externo("/paths/~1x/get/callbacks/cb", FUERA)]
    callback_de_componentes = _oas(components={"callbacks": {"cb": ref}})
    assert _problemas(callback_de_componentes) == [_externo("/components/callbacks/cb", FUERA)]
    en_callback = _oas(paths={"/x": {"get": {"callbacks": {"cb": {"expr": ref}}}}})
    assert _problemas(en_callback) == [_externo("/paths/~1x/get/callbacks/cb/expr", FUERA)]


@pytest.mark.parametrize(
    "destino",
    DESTINOS_MALOS
    + [
        "#/servers",
        "#/components/servers",
        "#/servers/a/b",
        "#/x/servers/a",
        "#/x/components/servers/a",
        "#/servers/a%2Fx",
        "#/servers/a#b",
        "#/servers/inexistente",
        "#/components/servers/inexistente",
        "#/components/links/a",
    ],
)
def test_un_servidor_de_canal_de_asyncapi_con_ref_fuera_de_servers_se_detecta(destino: Any) -> None:
    documento = {
        "servers": {"a": {"host": "veridicus-x:80"}},
        "channels": {"c": {"servers": [{"$ref": destino}]}},
    }
    assert _problemas(documento) == [_externo("/channels/c/servers/0", FUERA)]
    sin_ref = {
        "servers": {"a": {"host": "veridicus-x:80"}},
        "channels": {"c": {"servers": [{"host": "x"}, "x"]}},
    }
    assert _problemas(sin_ref) == [
        _externo("/channels/c/servers/0", FUERA),
        _externo("/channels/c/servers/1", FUERA),
    ]


NOMBRES_RAROS = ("p%2Fx", "a/b", "a#b", "a b")
"""Claves que existen pero cuyo nombre no puede nombrarse en un `$ref` (F-14)."""
COMPONENTES = {
    # `x` existe en los cuatro tipos: así un `$ref` de tipo cruzado solo falla por el tipo.
    "pathItems": {"p": {}, "x": {}, "p/q": {}, "a.b_c~d-E9": {}, **{n: {} for n in NOMBRES_RAROS}},
    "responses": {"r": {}, "x": {}, **{n: {} for n in NOMBRES_RAROS}},
    "links": {"l": {}, "x": {}, **{n: {} for n in NOMBRES_RAROS}},
    "callbacks": {"c": {}, "x": {}, **{n: {} for n in NOMBRES_RAROS}},
    "servers": {"b": {"host": "veridicus-x:80"}},
}


def test_los_ref_estructurales_a_components_y_los_de_canal_a_servers_pasan() -> None:
    documento = _oas(
        paths={
            "/x": {
                "$ref": "#/components/pathItems/p",
                "get": {
                    "responses": {
                        "200": {
                            "$ref": "#/components/responses/r",
                            "links": {"l": {"$ref": "#/components/links/l"}},
                        }
                    },
                    "callbacks": {
                        "cb": {"$ref": "#/components/callbacks/c"},
                        "d": {"expr": {"$ref": "#/components/pathItems/p"}},
                    },
                },
            }
        },
        webhooks={
            "w": {"$ref": "#/components/pathItems/p~1q"},
            "v": {"$ref": "#/components/pathItems/a.b_c~0d-E9"},
        },
        components=copy.deepcopy(COMPONENTES),
    )
    assert _problemas(documento) == []
    asyncapi = {
        "servers": {"a": {"host": "veridicus-x:80"}},
        "components": {"servers": {"b": {"host": "veridicus-x:80"}}},
        "channels": {
            "c": {"servers": [{"$ref": "#/servers/a"}, {"$ref": "#/components/servers/b"}]},
            "sin_servers": {},
            "no_canal": "x",
        },
    }
    assert _problemas(asyncapi) == []


def _nodos_con_ref(ref: dict[str, Any]) -> dict[str, tuple[dict[str, Any], str]]:
    """Un documento por tipo de nodo estructural, con `ref` en él, y el puntero del nodo."""
    base = copy.deepcopy(COMPONENTES)
    return {
        "pathItem": (_oas(paths={"/x": ref}, components=base), "/paths/~1x"),
        "respuesta": (
            _oas(paths={"/x": {"get": {"responses": {"200": ref}}}}, components=base),
            "/paths/~1x/get/responses/200",
        ),
        "link": (
            _oas(
                paths={"/x": {"get": {"responses": {"200": {"links": {"l": ref}}}}}},
                components=base,
            ),
            "/paths/~1x/get/responses/200/links/l",
        ),
        "callback": (
            _oas(paths={"/x": {"get": {"callbacks": {"cb": ref}}}}, components=base),
            "/paths/~1x/get/callbacks/cb",
        ),
        "callback-elemento": (
            _oas(paths={"/x": {"get": {"callbacks": {"cb": {"e": ref}}}}}, components=base),
            "/paths/~1x/get/callbacks/cb/e",
        ),
    }


@pytest.mark.parametrize("nodo", ["pathItem", "respuesta", "link", "callback"])
def test_un_ref_con_nombre_codificado_o_con_barra_o_almohadilla_no_pasa_en_cada_tipo(
    nodo: str,
) -> None:
    """F-14: `%2F` se decodifica antes de leerse como puntero JSON y llegaría a un `servers` oculto."""
    tipo = {
        "pathItem": "pathItems",
        "respuesta": "responses",
        "link": "links",
        "callback": "callbacks",
    }[nodo]
    for nombre in ("p%2Fx", "p%2fx", "a/b", "a#b", "a%23b", "", "a b", "a\n"):
        assert nombre in ("p%2fx", "a%23b", "", "a\n") or nombre in COMPONENTES[tipo]
        documento, puntero = _nodos_con_ref({"$ref": f"#/components/{tipo}/{nombre}"})[nodo]
        assert _problemas(documento) == [_externo(puntero, FUERA)], (nodo, nombre)


def test_un_ref_con_nombre_codificado_no_pasa_en_el_elemento_de_un_callback() -> None:
    for nombre in NOMBRES_RAROS:
        documento, puntero = _nodos_con_ref({"$ref": f"#/components/pathItems/{nombre}"})[
            "callback-elemento"
        ]
        assert _problemas(documento) == [_externo(puntero, FUERA)], nombre


@pytest.mark.parametrize("nombre", NOMBRES_RAROS)
def test_un_servidor_de_canal_con_nombre_raro_que_existe_no_pasa(nombre: str) -> None:
    documento = {
        "servers": {nombre: {"host": "veridicus-x:80"}},
        "components": {"servers": {nombre: {"host": "veridicus-x:80"}}},
        "channels": {
            "c": {
                "servers": [
                    {"$ref": f"#/servers/{nombre}"},
                    {"$ref": f"#/components/servers/{nombre}"},
                ]
            }
        },
    }
    assert _problemas(documento) == [
        _externo("/channels/c/servers/0", FUERA),
        _externo("/channels/c/servers/1", FUERA),
    ]


@pytest.mark.parametrize("nodo", ["pathItem", "respuesta", "link", "callback", "callback-elemento"])
def test_un_ref_a_un_componente_que_existe_del_tipo_correcto_pasa_y_a_uno_inexistente_no(
    nodo: str,
) -> None:
    tipo = {
        "pathItem": "pathItems",
        "respuesta": "responses",
        "link": "links",
        "callback": "callbacks",
        "callback-elemento": "pathItems",
    }[nodo]
    existente = {"pathItems": "p", "responses": "r", "links": "l", "callbacks": "c"}[tipo]
    documento, _ = _nodos_con_ref({"$ref": f"#/components/{tipo}/{existente}"})[nodo]
    assert _problemas(documento) == []
    documento, puntero = _nodos_con_ref({"$ref": f"#/components/{tipo}/inexistente"})[nodo]
    assert _problemas(documento) == [_externo(puntero, FUERA)]


CRUZADOS = [
    ("respuesta", "links", "x"),
    ("respuesta", "pathItems", "x"),
    ("respuesta", "callbacks", "x"),
    ("callback", "pathItems", "x"),
    ("callback", "responses", "x"),
    ("callback", "links", "x"),
    ("link", "responses", "x"),
    ("link", "callbacks", "x"),
    ("link", "pathItems", "x"),
    ("pathItem", "callbacks", "x"),
    ("pathItem", "responses", "x"),
    ("pathItem", "links", "x"),
    ("callback-elemento", "callbacks", "x"),
    ("callback-elemento", "links", "x"),
    ("callback-elemento", "responses", "x"),
]


@pytest.mark.parametrize("nodo", ["pathItem", "respuesta", "link", "callback", "callback-elemento"])
def test_un_ref_a_x_del_tipo_correcto_pasa_y_demuestra_que_los_cruzados_fallan_solo_por_el_tipo(
    nodo: str,
) -> None:
    tipo = {
        "pathItem": "pathItems",
        "respuesta": "responses",
        "link": "links",
        "callback": "callbacks",
        "callback-elemento": "pathItems",
    }[nodo]
    documento, _ = _nodos_con_ref({"$ref": f"#/components/{tipo}/x"})[nodo]
    assert _problemas(documento) == []


@pytest.mark.parametrize(("nodo", "tipo", "nombre"), CRUZADOS)
def test_un_ref_de_tipo_cruzado_a_un_componente_que_existe_no_pasa(
    nodo: str, tipo: str, nombre: str
) -> None:
    documento, puntero = _nodos_con_ref({"$ref": f"#/components/{tipo}/{nombre}"})[nodo]
    assert _problemas(documento) == [_externo(puntero, FUERA)]


def test_un_ref_con_un_prefijo_antes_de_components_no_pasa() -> None:
    for nodo in ("pathItem", "respuesta", "link", "callback"):
        documento, puntero = _nodos_con_ref({"$ref": "#/x/components/pathItems/p"})[nodo]
        assert _problemas(documento) == [_externo(puntero, FUERA)]
        documento, puntero = _nodos_con_ref({"$ref": "#/a/b/components/links/l"})[nodo]
        assert _problemas(documento) == [_externo(puntero, FUERA)]


def test_los_ref_cuyo_destino_es_otro_ref_o_forman_un_ciclo_no_cuelgan_la_guardia() -> None:
    componentes = {
        "pathItems": {
            "a": {"$ref": "#/components/pathItems/b"},
            "b": {"$ref": "#/components/pathItems/a"},
            "c": {"$ref": "#/components/pathItems/c"},
        },
        "responses": {"r": {"$ref": "#/components/responses/r"}},
        "callbacks": {"k": {"$ref": "#/components/callbacks/k"}},
        "links": {"l": {"$ref": "#/components/links/l"}},
    }
    documento = _oas(paths={"/x": {"$ref": "#/components/pathItems/a"}}, components=componentes)
    assert _problemas(documento) == []


def test_un_ciclo_con_un_destino_externo_en_el_medio_se_detecta() -> None:
    componentes = {
        "pathItems": {
            "a": {"$ref": "#/components/pathItems/b"},
            "b": {"$ref": "#/components/pathItems/a", "servers": [{"url": "//evil.com"}]},
        }
    }
    documento = _oas(components=componentes)
    assert _problemas(documento) == [_externo("/components/pathItems/b/servers/0")]


def test_canales_con_servers_que_no_es_lista_son_mal_formados_y_los_demas_se_revisan() -> None:
    documento = {
        "servers": {"a": {"host": "veridicus-x:80"}},
        "channels": {
            "primero": {"servers": "x"},
            "segundo": {"servers": [{"$ref": "#/x/servers/e"}]},
            "tercero": {"servers": {"$ref": "#/servers/a"}},
            "cuarto": {"servers": [{"$ref": "#/servers/a"}, {"$ref": "#/servers/e"}]},
            "quinto": {},
            "sexto": "x",
        },
    }
    assert _problemas(documento) == [
        _externo("/channels/primero/servers", "servidor mal formado"),
        _externo("/channels/segundo/servers/0", FUERA),
        _externo("/channels/tercero/servers", "servidor mal formado"),
        _externo("/channels/cuarto/servers/1", FUERA),
    ]


def test_un_canal_sin_clave_servers_no_detiene_el_recorrido_de_los_siguientes() -> None:
    documento = {
        "servers": {"a": {"host": "veridicus-x:80"}},
        "channels": {"vacio": {}, "no_canal": 7, "malo": {"servers": [{"$ref": "#/x/servers/e"}]}},
    }
    assert _problemas(documento) == [_externo("/channels/malo/servers/0", FUERA)]


def test_un_ref_estructural_valido_no_oculta_un_servers_hermano_externo() -> None:
    documento = _oas(
        paths={"/x": {"$ref": "#/components/pathItems/p", "servers": [{"url": "//evil.com"}]}},
        components={"pathItems": {"p": {}}},
    )
    assert _problemas(documento) == [_externo("/paths/~1x/servers/0")]


def test_una_variable_que_la_url_no_usa_no_cuenta() -> None:
    sin_uso = {"url": "/", "variables": {"p": {"default": "https://api.openai.com"}}}
    assert _problemas(_oas(servers=[sin_uso])) == []


@pytest.mark.parametrize("enum", ["evil", [], {}, 7, None])
def test_un_enum_que_no_es_una_lista_con_valores_es_una_variable_mal_formada(enum: Any) -> None:
    mal = {"url": "/{p}", "variables": {"p": {"default": "a", "enum": enum}}}
    assert _problemas(_oas(servers=[mal])) == [
        _externo("/servers/0", "variable de servidor mal formada")
    ]
    sin_uso = {"url": "/", "variables": {"p": {"default": "a", "enum": enum}}}
    assert _problemas(_oas(servers=[sin_uso])) == [
        _externo("/servers/0", "variable de servidor mal formada")
    ]


def test_un_enum_con_valores_internos_y_un_enum_ausente_no_dan_problemas() -> None:
    bueno = {"url": "/{p}", "variables": {"p": {"default": "a", "enum": ["a", "b"]}}}
    assert _problemas(_oas(servers=[bueno])) == []


def test_una_url_ausente_o_que_no_es_texto_es_externa() -> None:
    assert _problemas(_oas(servers=[{}])) == [_externo("/servers/0")]
    assert _problemas(_oas(servers=[{"url": 5}])) == [_externo("/servers/0")]
    assert _problemas(_oas(servers=[{"url": None}])) == [_externo("/servers/0")]


def _asyncapi(**servidor: Any) -> dict[str, Any]:
    return {"servers": {"redis": {"host": "veridicus-redis:6379", **servidor}}}


def test_asyncapi_con_host_interno_pasa_con_protocolo_redis_http_o_ausente() -> None:
    assert _problemas(_asyncapi()) == []
    assert _problemas(_asyncapi(protocol="redis", description="x")) == []
    assert _problemas(_asyncapi(protocol="http", pathname="/v1")) == []
    assert _problemas({"servers": {"a": {"host": "a.svc.cluster.local"}}}) == []


def test_asyncapi_con_host_externo_o_ausente_se_detecta() -> None:
    assert _problemas({"servers": {"redis": {"host": "api.openai.com:443"}}}) == [
        _externo("/servers/redis")
    ]
    assert _problemas({"servers": {"redis": {}}}) == [_externo("/servers/redis")]
    assert _problemas({"servers": {"redis": {"host": 5}}}) == [_externo("/servers/redis")]
    assert _problemas({"servers": {"redis": {"host": "veridicus-x:80", "pathname": 7}}}) == [
        _externo("/servers/redis", "pathname no interno")
    ]


def test_asyncapi_con_url_y_host_a_la_vez_o_con_claves_extra_se_detecta() -> None:
    con_url = _asyncapi(url="https://api.openai.com")
    assert _problemas(con_url) == [
        _externo("/servers/redis", "campo no admitido en un servidor de AsyncAPI")
    ]
    con_extra = _asyncapi(variables={"a": {}})
    assert _problemas(con_extra) == [
        _externo("/servers/redis", "campo no admitido en un servidor de AsyncAPI")
    ]
    solo_url = {"servers": {"redis": {"url": "http://veridicus-redis:6379"}}}
    assert _problemas(solo_url) == [
        _externo("/servers/redis", "campo no admitido en un servidor de AsyncAPI"),
        _externo("/servers/redis"),
    ]


@pytest.mark.parametrize("protocolo", ["https", "rediss", "amqps", "HTTP", 7])
def test_asyncapi_con_protocolo_que_no_es_http_ni_redis_se_detecta(protocolo: Any) -> None:
    assert _problemas(_asyncapi(protocol=protocolo)) == [
        _externo("/servers/redis", "protocolo no admitido")
    ]


@pytest.mark.parametrize("ruta", ["//evil.com", "/\\evil.com", "v1", "/a b", ""])
def test_asyncapi_con_pathname_no_interno_se_detecta(ruta: str) -> None:
    assert _problemas(_asyncapi(pathname=ruta)) == [
        _externo("/servers/redis", "pathname no interno")
    ]


def test_el_arbol_versionado_cumple_todo() -> None:
    assert guardia.comprobar(CONTRACTS_ROOT, EXISTENTES) == []


def test_la_entrada_principal_recorre_los_siete_y_c1_ausente_es_un_problema() -> None:
    """Hasta el paso 16, C1 no existe: es el único problema y no se pasa en vacío."""
    esperado = (
        []
        if (CONTRACTS_ROOT / "api" / "console.v2.yaml").is_file()
        else [f"api/console.v2.yaml: contrato ausente {SUFIJO}"]
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
        f"api/anonymizer-proxy.v1.yaml: /servers/0: dirección no interna {SUFIJO}"
    ]


@pytest.mark.parametrize(
    "url",
    [
        "http://203.0.113.7:8080",
        "https://veridicus-anonymizer-proxy:8080",
        "http://anonymizer-proxy:8080",
        "//veridicus-x:80",
        "/\\\\evil.com",
    ],
    ids=["ip-literal", "https-en-el-cluster", "sin-prefijo", "relativa-de-red", "barra-invertida"],
)
def test_cada_regla_tiene_su_control_negativo_en_c21(tmp_path: Path, url: str) -> None:
    raiz = _con_servers(tmp_path, C21, f"servers:\n  - url: '{url}'\n")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"api/anonymizer-proxy.v1.yaml: /servers/0: dirección no interna {SUFIJO}"
    ]


def test_c21_con_un_servers_por_operacion_externo_se_detecta(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    ruta = raiz / C21
    texto = ruta.read_text(encoding="utf-8")
    marca = "      operationId: generate\n"
    assert marca in texto
    nuevo = texto.replace(marca, marca + "      servers:\n        - url: https://api.openai.com\n")
    ruta.write_text(nuevo, encoding="utf-8")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"api/anonymizer-proxy.v1.yaml: /paths/~1v1~1generate/post/servers/0: dirección no interna {SUFIJO}"
    ]


def test_un_asyncapi_con_host_externo_se_detecta(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    ruta = raiz / "queues" / "runs.v2.yaml"
    texto = ruta.read_text(encoding="utf-8")
    assert "host: 'veridicus-redis:6379'" in texto
    ruta.write_text(texto.replace("host: 'veridicus-redis:6379'", "host: 'api.openai.com:443'"))
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"queues/runs.v2.yaml: /servers/redis: dirección no interna {SUFIJO}"
    ]


def test_un_asyncapi_con_protocolo_https_se_detecta(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    ruta = raiz / "queues" / "results.v2.yaml"
    texto = ruta.read_text(encoding="utf-8")
    assert "protocol: redis" in texto
    ruta.write_text(texto.replace("protocol: redis", "protocol: https"), encoding="utf-8")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"queues/results.v2.yaml: /servers/redis: protocolo no admitido {SUFIJO}"
    ]


def test_un_contrato_ausente_no_pasa_en_vacio(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    (raiz / C21).unlink()
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"api/anonymizer-proxy.v1.yaml: contrato ausente {SUFIJO}"
    ]


def test_un_directorio_con_el_nombre_del_contrato_no_es_un_archivo(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    (raiz / C21).unlink()
    (raiz / C21).mkdir()
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"api/anonymizer-proxy.v1.yaml: no es un archivo {SUFIJO}"
    ]


def test_un_contrato_ilegible_es_un_problema_sin_el_texto_del_error(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    (raiz / C21).write_text(f"a: {CANARY}-uno\na: {CANARY}-dos\n", encoding="utf-8")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"api/anonymizer-proxy.v1.yaml: contrato ilegible, no se pudo interpretar {SUFIJO}"
    ]


def test_un_documento_que_no_es_un_objeto_no_declara_servidores(tmp_path: Path) -> None:
    raiz = _copia(tmp_path)
    (raiz / C21).write_text("- uno\n- dos\n", encoding="utf-8")
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"api/anonymizer-proxy.v1.yaml: /: versión no admitida {SUFIJO}",
        f"api/anonymizer-proxy.v1.yaml: no declara ningún servidor en servers {SUFIJO}",
    ]


@pytest.mark.parametrize(
    ("ruta", "texto"),
    [
        ("health/health.v2.yaml", "openapi: 3.1.0\n"),
        ("api/anonymizer-proxy.v1.yaml", "openapi: 3.1.0\n"),
        ("api/speech-internal.v1.yaml", "openapi: 3.1.0\n"),
        ("queues/runs.v2.yaml", "asyncapi: 3.0.0\n"),
        ("queues/results.v2.yaml", "asyncapi: 3.0.0\n"),
        ("queues/speech.v2.yaml", "asyncapi: 3.0.0\n"),
    ],
)
def test_cada_contrato_declara_su_version_y_sin_ella_o_con_swagger_no_pasa(
    tmp_path: Path, ruta: str, texto: str
) -> None:
    raiz = _copia(tmp_path)
    original = (raiz / ruta).read_text(encoding="utf-8")
    assert original.startswith(texto)
    assert guardia.comprobar(raiz, EXISTENTES) == []
    (raiz / ruta).write_text(original.removeprefix(texto), encoding="utf-8")
    assert guardia.comprobar(raiz, EXISTENTES) == [f"{ruta}: /: versión no admitida {SUFIJO}"]
    (raiz / ruta).write_text("swagger: '2.0'\n" + original, encoding="utf-8")
    assert guardia.comprobar(raiz, EXISTENTES) == [f"{ruta}: /: versión no admitida {SUFIJO}"]


def test_ningun_mensaje_copia_valores_del_documento(tmp_path: Path) -> None:
    documento: dict[str, Any] = {
        "servers": [
            {"url": f"https://user:{CANARY}@{CANARY}.example/{CANARY}"},
            {"url": "/{p}", "variables": {"p": {"default": f"/{CANARY}.evil", "enum": [CANARY]}}},
            {"url": f"//{CANARY}", "variables": {CANARY: {"default": CANARY}}},
        ],
        "paths": {f"/{CANARY}": {"servers": [{"url": CANARY}]}},
    }
    mapa = {
        "servers": {CANARY: {"host": f"{CANARY}.example", "protocol": CANARY, "pathname": CANARY}}
    }
    mensajes = _problemas(documento) + _problemas(mapa) + _problemas({"servers": CANARY})
    assert len(mensajes) == 8
    assert not [
        m
        for m in mensajes
        if CANARY in m.replace(f"/paths/~1{CANARY}", "").replace(f"/servers/{CANARY}", "")
    ]
    raiz = _copia(tmp_path)
    (raiz / C21).write_text(f"a: {CANARY}\na: {CANARY}\n", encoding="utf-8")
    assert not [m for m in guardia.comprobar(raiz, EXISTENTES) if CANARY in m]


def test_varios_defectos_se_listan_todos_en_orden(tmp_path: Path) -> None:
    raiz = _con_servers(tmp_path, C21, "servers:\n  - url: https://a.example\n  - url: /ok\n")
    ruta = raiz / "health" / "health.v2.yaml"
    ruta.write_text(
        ruta.read_text(encoding="utf-8").replace("servers:", "servers:\n  - url: http://b.example")
    )
    assert guardia.comprobar(raiz, EXISTENTES) == [
        f"health/health.v2.yaml: /servers/0: dirección no interna {SUFIJO}",
        f"api/anonymizer-proxy.v1.yaml: /servers/0: dirección no interna {SUFIJO}",
    ]


def test_la_copia_profunda_del_documento_no_se_modifica() -> None:
    documento = _oas(servers=[{"url": "/{p}", "variables": {"p": {"default": "a"}}}])
    antes = copy.deepcopy(documento)
    assert _problemas(documento) == []
    assert documento == antes
