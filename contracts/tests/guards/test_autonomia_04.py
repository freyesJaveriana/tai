"""AUTONOMIA-04: soberanía de los datos (NFR1.1–NFR1.4, BR9.9).

- `servers` internos en C1, C16, C21, la ruta interna de voz y los AsyncAPI, con control de C21
  con `https://api.openai.com` (NFR1.1, §4.9);
- `AnonymizingProvider`, la única puerta a un destino externo, con un solo `generate`
  (BR9.9, NFR1.2, §4.17);
- C21 estricto (NFR1.3) y reporte de C19 sin texto libre (NFR1.4, §4.18).

Rojo hasta T05 (AsyncAPI), T08 (C13), T12 (C19), T13 (C21, voz, C16) y T14 (C1).
"""

import ast
import copy
import re
from pathlib import Path
from typing import Any

import pytest
from helpers import importar_o_fallar, load_contract, recorrer

C21 = "api/anonymizer-proxy.v1.yaml"
MAXIMO_ENTERO = 2**53 - 1
INTERNA = re.compile(
    r"^http://(veridicus-[a-z0-9-]+|[a-z0-9-]+(\.[a-z0-9-]+)*\.svc\.cluster\.local)"
    r"(:[0-9]{1,5})?(/.*)?$"
)
IMPORTACIONES_PERMITIDAS = {"veridicus_contracts", "typing", "dataclasses", "enum", "datetime"}


def es_interna(url: str) -> bool:
    """Ruta relativa, nombre corto `http://veridicus-<nombre>:<puerto>` o `*.svc.cluster.local`."""
    return (url.startswith("/") and not url.startswith("//")) or INTERNA.match(url) is not None


def servidores_externos(documento: Any) -> list[str]:
    """URL de `servers` (OpenAPI) o `host` (AsyncAPI) y valores por omisión que no son internos."""
    externos: list[str] = []
    servidores = documento.get("servers") or []
    if isinstance(servidores, dict):  # AsyncAPI 3.0: mapa nombre -> servidor
        for servidor in servidores.values():
            direccion = "http://" + str(servidor.get("host", ""))
            if not es_interna(direccion):
                externos.append(str(servidor.get("host", "")))
        return externos
    for servidor in servidores:  # OpenAPI 3.1: lista con `url` y `variables`
        candidatas = [str(servidor.get("url", ""))]
        candidatas += [str(v.get("default", "")) for v in (servidor.get("variables") or {}).values()]
        externos += [url for url in candidatas if not es_interna(url)]
    return externos


SERVIDORES = [
    pytest.param("api/console.v2.yaml", marks=pytest.mark.c1, id="c1"),
    pytest.param("health/health.v2.yaml", marks=pytest.mark.c16, id="c16"),
    pytest.param(C21, marks=pytest.mark.c21, id="c21"),
    pytest.param("api/speech-internal.v1.yaml", marks=pytest.mark.speech, id="voz-interna"),
    pytest.param("queues/runs.v2.yaml", marks=pytest.mark.asyncapi, id="c2"),
    pytest.param("queues/results.v2.yaml", marks=pytest.mark.asyncapi, id="c3"),
    pytest.param("queues/speech.v2.yaml", marks=pytest.mark.asyncapi, id="c5"),
]


@pytest.mark.parametrize("ruta", SERVIDORES)
def test_los_servers_son_internos(ruta: str) -> None:
    assert servidores_externos(load_contract(ruta)) == []


@pytest.mark.c21
def test_control_c21_con_un_destino_externo_se_detecta() -> None:
    """NFR1.1: una copia de C21 con `https://api.openai.com` queda marcada como externa."""
    copia = copy.deepcopy(load_contract(C21))
    copia["servers"] = [{"url": "https://api.openai.com"}]
    assert servidores_externos(copia) == ["https://api.openai.com"]


@pytest.mark.c13
def test_anonymizing_provider_declara_solo_generate() -> None:
    """BR9.9, NFR1.2: el `Protocol` tiene un único método `generate(request: GenerateRequest)`."""
    modulo = importar_o_fallar("veridicus_contracts.model_calls", "T08")
    arbol = ast.parse(Path(str(modulo.__file__)).read_text(encoding="utf-8"))
    clases = [n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == "AnonymizingProvider"]
    assert clases, "AnonymizingProvider no está declarado en model_calls"
    clase = clases[0]
    assert any(isinstance(b, ast.Name) and b.id == "Protocol" for b in clase.bases)
    miembros = [
        n for n in clase.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))
    ]
    assert [type(n) for n in miembros] == [ast.FunctionDef], "solo un método, sin atributos"
    metodo = miembros[0]
    assert isinstance(metodo, ast.FunctionDef) and metodo.name == "generate"
    entradas = [a.annotation for a in metodo.args.args if a.arg != "self"]
    assert [getattr(a, "id", None) for a in entradas] == ["GenerateRequest"]
    assert getattr(metodo.returns, "id", None) == "GenerateResult"


@pytest.mark.c13
def test_model_calls_solo_importa_el_paquete_de_contratos() -> None:
    """E43: el módulo no importa nada fuera de `veridicus_contracts` y la biblioteca estándar citada."""
    modulo = importar_o_fallar("veridicus_contracts.model_calls", "T08")
    arbol = ast.parse(Path(str(modulo.__file__)).read_text(encoding="utf-8"))
    importados: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module.split(".")[0])
    assert importados <= IMPORTACIONES_PERMITIDAS, sorted(importados - IMPORTACIONES_PERMITIDAS)


def _objetos_abiertos(nodo: Any, ruta: str) -> list[str]:
    """Rutas de esquemas de objeto con `properties` que no cierran `additionalProperties`."""
    return [
        sitio
        for sitio, _, valor in recorrer(nodo, ruta)
        if isinstance(valor, dict)
        and isinstance(valor.get("properties"), dict)
        and valor.get("additionalProperties") is not False
    ]


@pytest.mark.c21
def test_c21_peticion_y_respuesta_son_estrictas() -> None:
    """NFR1.3: `additionalProperties: false` en todos los niveles; `role` y `profile_sha256` con patrón."""
    operacion = load_contract(C21)["paths"]["/v1/generate"]["post"]
    cuerpo = operacion["requestBody"]["content"]["application/json"]["schema"]
    respuesta = operacion["responses"]["200"]["content"]["application/json"]["schema"]
    assert _objetos_abiertos(cuerpo, "peticion") == []
    assert _objetos_abiertos(respuesta, "respuesta") == []
    assert cuerpo["properties"]["role"]["pattern"] == "^[a-z][a-z0-9_]{0,31}$"
    assert cuerpo["properties"]["profile_sha256"]["pattern"] == "^[0-9a-f]{64}$"


@pytest.mark.c21
def test_c21_declara_el_tamano_maximo_de_peticion_y_respuesta() -> None:
    """NFRD-U1-04: marcas `x-veridicus-max-bytes` contra C25 (el valor se compara en T14)."""
    operacion = load_contract(C21)["paths"]["/v1/generate"]["post"]
    en_peticion = {v for _, c, v in recorrer(operacion["requestBody"]) if c == "x-veridicus-max-bytes"}
    en_respuesta = {v for _, c, v in recorrer(operacion["responses"]["200"]) if c == "x-veridicus-max-bytes"}
    assert en_peticion == {"anonymizer_request_max_bytes"}
    assert en_respuesta == {"anonymizer_response_max_bytes"}


def _cadenas_abiertas(documento: Any) -> list[str]:
    """Cadenas que no son enum, const, formato cerrado ni patrón sin espacios con tope de 128."""
    abiertas = []
    for sitio, _, valor in recorrer(documento):
        if not isinstance(valor, dict) or valor.get("type") != "string":
            continue
        cerrada = (
            "enum" in valor
            or "const" in valor
            or valor.get("format") in {"date-time", "uuid"}
            or (
                isinstance(valor.get("pattern"), str)
                and not re.search(r"\s|\\s| ", valor["pattern"])
                and valor.get("maxLength", MAXIMO_ENTERO) <= 128
            )
        )
        if not cerrada:
            abiertas.append(sitio)
    return abiertas


def _enteros_sin_tope(documento: Any) -> list[str]:
    sin_tope = []
    for sitio, _, valor in recorrer(documento):
        if isinstance(valor, dict) and valor.get("type") == "integer":
            maximo = valor.get("maximum")
            if "minimum" not in valor or not isinstance(maximo, int) or maximo > MAXIMO_ENTERO:
                sin_tope.append(sitio)
    return sin_tope


@pytest.mark.parametrize(
    "ruta",
    [
        pytest.param("cli/report.schema.v2.yaml", marks=pytest.mark.c19, id="report"),
        pytest.param("model_calls/model-call.v1.yaml", marks=pytest.mark.c19, id="model-call"),
    ],
)
def test_c19_no_tiene_campos_de_texto_libre(ruta: str) -> None:
    """NFR1.4, BR10.1: toda cadena es cerrada y todo entero lleva `minimum` y `maximum` acotados."""
    documento = load_contract(ruta)
    assert _cadenas_abiertas(documento) == []
    assert _enteros_sin_tope(documento) == []
