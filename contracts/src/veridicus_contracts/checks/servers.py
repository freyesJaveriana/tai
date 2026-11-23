"""Soberanía de datos: `servers` internos en todo contrato (NFR1.1, §4.9 de NFR Design).

Módulo guardia (100 % de ramas). Recorre todo objeto `servers` y `server` del documento (el global,
los de cada ruta y operación, y los de `links`) de los OpenAPI (C1, C16, C21 y la ruta interna de
voz) y los `servers` de los AsyncAPI (C2, C3 y C5). Acepta solo:

- una ruta relativa (`/api/v1`) de caracteres `[A-Za-z0-9._~/-]` que no empieza por `//`;
- el nombre corto `http://veridicus-<nombre>:<puerto>` (NFR-U1-06);
- un *host* que termina en `.svc.cluster.local`, con puerto opcional.

Siempre con el esquema `http`: dentro del clúster no hay `https` y cualquier otro destino (un
nombre de internet, una IP literal, un nombre sin el prefijo `veridicus-`) es externo. En OpenAPI se
sustituyen las variables de la URL por su `default` y por cada valor de su `enum`, y se comprueba
cada URL resultante. En AsyncAPI el servidor lleva `host` (y, si acaso, `protocol` y `pathname`).

Los mensajes dicen dónde falla (un puntero JSON) y qué regla; nunca copian una URL ni el texto de
un error de carga, que pueden arrastrar credenciales o fragmentos del documento. Todas las funciones
reciben rutas o documentos y devuelven la lista de problemas (vacía si todo está bien); nunca
escriben.
"""

import itertools
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from veridicus_contracts.loaders import LoadError, load_file

PREFIJO = "veridicus-"
SUFIJO_DEL_CLUSTER = ".svc.cluster.local"
ETIQUETA = "[a-z0-9-]+"
PUERTO = "[0-9]{1,5}"
RUTA = "[A-Za-z0-9._~/-]*"
# `fullmatch` y no `match` con `$`: un salto de línea final no puede colarse.
RELATIVA = re.compile(rf"/(?!/){RUTA}")
NOMBRE_CORTO = re.compile(rf"http://{re.escape(PREFIJO)}{ETIQUETA}:{PUERTO}(/{RUTA})?")
DENTRO_DEL_CLUSTER = re.compile(
    rf"http://{ETIQUETA}(\.{ETIQUETA})*{re.escape(SUFIJO_DEL_CLUSTER)}(:{PUERTO})?(/{RUTA})?"
)
# Contratos con `servers` (§4.9). C14 y C22 no se copian a `contracts/`.
CONTRATOS = (
    "api/console.v2.yaml",
    "health/health.v2.yaml",
    "api/anonymizer-proxy.v1.yaml",
    "api/speech-internal.v1.yaml",
    "queues/runs.v2.yaml",
    "queues/results.v2.yaml",
    "queues/speech.v2.yaml",
)
METODOS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
CAMPOS_DE_SERVIDOR_ASYNCAPI = frozenset({"host", "protocol", "pathname", "description"})
PROTOCOLOS_ASYNCAPI = frozenset({"http", "redis"})
REGLA = "NFR1.1, §4.9"

LISTA = "lista"  # `servers` de OpenAPI: lista de objetos con `url`
MAPA = "mapa"  # `servers` de AsyncAPI: nombre -> servidor con `host`
ENLACE = "enlace"  # `server` de un `link` de OpenAPI
MAL_FORMADO = "mal formado"  # `servers` que no es ni lista ni mapa


def es_interna(url: str) -> bool:
    """La dirección es una ruta relativa, un nombre corto `veridicus-*` o `*.svc.cluster.local`."""
    return (
        RELATIVA.fullmatch(url) is not None
        or NOMBRE_CORTO.fullmatch(url) is not None
        or DENTRO_DEL_CLUSTER.fullmatch(url) is not None
    )


def _texto(valor: Any) -> str:
    return "" if valor is None else str(valor)


def _escapar(clave: Any) -> str:
    return str(clave).replace("~", "~0").replace("/", "~1")


Servidor = tuple[str, str, Any]  # (puntero JSON, forma, objeto)


def _objeto(valor: Any) -> dict[str, Any]:
    return valor if isinstance(valor, dict) else {}


def _declarados(contenedor: dict[str, Any], puntero: str) -> Iterator[Servidor]:
    """Los servidores de la clave `servers` de un objeto (raíz, elemento de ruta u operación)."""
    if "servers" not in contenedor:
        return
    valor = contenedor["servers"]
    hijo = f"{puntero}/servers"
    if isinstance(valor, list):
        yield from ((f"{hijo}/{i}", LISTA, s) for i, s in enumerate(valor))
    elif isinstance(valor, dict):
        yield from ((f"{hijo}/{_escapar(n)}", MAPA, s) for n, s in valor.items())
    else:
        yield hijo, MAL_FORMADO, valor


def _enlaces(contenedor: dict[str, Any], puntero: str) -> Iterator[Servidor]:
    """El `server` de cada `link` de una respuesta o de `components`."""
    for nombre, enlace in _objeto(contenedor.get("links")).items():
        if isinstance(enlace, dict) and "server" in enlace:
            yield f"{puntero}/links/{_escapar(nombre)}/server", ENLACE, enlace["server"]


def _de_respuestas(respuestas: dict[str, Any], puntero: str) -> Iterator[Servidor]:
    for estado, respuesta in respuestas.items():
        yield from _enlaces(_objeto(respuesta), f"{puntero}/{_escapar(estado)}")


def _de_callbacks(callbacks: Any, puntero: str) -> Iterator[Servidor]:
    for nombre, callback in _objeto(callbacks).items():
        for expresion, elemento in _objeto(callback).items():
            yield from _de_elemento(elemento, f"{puntero}/{_escapar(nombre)}/{_escapar(expresion)}")


def _de_operacion(operacion: dict[str, Any], puntero: str) -> Iterator[Servidor]:
    yield from _declarados(operacion, puntero)
    yield from _de_respuestas(_objeto(operacion.get("responses")), f"{puntero}/responses")
    yield from _de_callbacks(operacion.get("callbacks"), f"{puntero}/callbacks")


def _de_elemento(elemento: Any, puntero: str) -> Iterator[Servidor]:
    """Un elemento de ruta: sus `servers` y los de cada operación."""
    contenido = _objeto(elemento)
    yield from _declarados(contenido, puntero)
    for metodo in METODOS:
        if isinstance(contenido.get(metodo), dict):
            yield from _de_operacion(contenido[metodo], f"{puntero}/{metodo}")


def servidores(documento: Any) -> Iterator[Servidor]:
    """Cada servidor que la estructura de OpenAPI o AsyncAPI deja declarar, con su puntero JSON.

    Se sigue la estructura (raíz, `paths`, `webhooks`, operaciones, `callbacks`, `links` y
    `components`) y no se salta ninguna clave por su nombre: un callback, un enlace o un elemento de
    ruta pueden llamarse `schema`, `example` o `properties`.
    """
    raiz = _objeto(documento)
    yield from _declarados(raiz, "")
    for ruta, elemento in _objeto(raiz.get("paths")).items():
        yield from _de_elemento(elemento, f"/paths/{_escapar(ruta)}")
    for nombre, elemento in _objeto(raiz.get("webhooks")).items():
        yield from _de_elemento(elemento, f"/webhooks/{_escapar(nombre)}")
    componentes = _objeto(raiz.get("components"))
    for nombre, elemento in _objeto(componentes.get("pathItems")).items():
        yield from _de_elemento(elemento, f"/components/pathItems/{_escapar(nombre)}")
    yield from _de_callbacks(componentes.get("callbacks"), "/components/callbacks")
    yield from _enlaces(componentes, "/components")
    yield from _de_respuestas(_objeto(componentes.get("responses")), "/components/responses")
    yield from _declarados(componentes, "/components")


def _urls_resultantes(servidor: dict[str, Any]) -> list[str]:
    """La `url` con sus variables sustituidas por el `default` y por cada valor del `enum`."""
    url = _texto(servidor.get("url"))
    variables = servidor.get("variables")
    if not isinstance(variables, dict):
        variables = {}
    usadas = [nombre for nombre in variables if "{" + str(nombre) + "}" in url]
    opciones: list[list[str]] = []
    for nombre in usadas:
        variable = variables[nombre]
        por_omision = "{" + str(nombre) + "}"
        valores = [por_omision]
        if isinstance(variable, dict):
            if "default" in variable:
                valores = [_texto(variable["default"])]
            enum = variable.get("enum")
            valores += [_texto(valor) for valor in enum] if isinstance(enum, list) else []
        opciones.append(valores)
    resultantes = []
    for combinacion in itertools.product(*opciones):
        resultante = url
        for nombre, valor in zip(usadas, combinacion, strict=True):
            resultante = resultante.replace("{" + str(nombre) + "}", valor)
        resultantes.append(resultante)
    return resultantes


def _problemas_de_asyncapi(servidor: dict[str, Any]) -> list[str]:
    problemas: list[str] = []
    if set(servidor) - CAMPOS_DE_SERVIDOR_ASYNCAPI:
        problemas.append("campo no admitido en un servidor de AsyncAPI")
    if not es_interna("http://" + _texto(servidor.get("host"))):
        problemas.append("dirección no interna")
    if servidor.get("protocol", "http") not in PROTOCOLOS_ASYNCAPI:
        problemas.append("protocolo no admitido")
    ruta = servidor.get("pathname", "/")
    if not isinstance(ruta, str) or RELATIVA.fullmatch(ruta) is None:
        problemas.append("pathname no interno")
    return problemas


def comprobar_servidor(forma: str, servidor: Any) -> list[str]:
    """Las reglas que incumple un servidor, sin copiar ningún valor del documento."""
    if forma == MAL_FORMADO or not isinstance(servidor, dict):
        return ["servidor mal formado"]
    if forma == MAPA:
        return _problemas_de_asyncapi(servidor)
    problemas: list[str] = []
    variables = _objeto(servidor.get("variables"))
    if any(not _enum_valido(variable) for variable in variables.values()):
        problemas.append("variable de servidor mal formada")
    if not all(es_interna(url) for url in _urls_resultantes(servidor)):
        problemas.append("dirección no interna")
    return problemas


def _enum_valido(variable: Any) -> bool:
    """Sin `enum`, o una lista con al menos un valor."""
    if not isinstance(variable, dict) or "enum" not in variable:
        return True
    return isinstance(variable["enum"], list) and bool(variable["enum"])


def comprobar_documento(nombre: str, documento: Any) -> list[str]:
    """Problemas de un contrato ya cargado: sin servidores, o con alguno que no es interno."""
    encontrados = list(servidores(documento))
    problemas = [
        f"{nombre}: {puntero}: {regla} ({REGLA})"
        for puntero, forma, servidor in encontrados
        for regla in comprobar_servidor(forma, servidor)
    ]
    if not list(_declarados(_objeto(documento), "")):
        problemas.insert(0, f"{nombre}: no declara ningún servidor en servers ({REGLA})")
    return problemas


def comprobar(contracts_root: Path, contratos: tuple[str, ...] = CONTRATOS) -> list[str]:
    """Todos los contratos de `contratos` bajo `contracts_root`; uno ausente es un problema."""
    problemas: list[str] = []
    for relativa in contratos:
        ruta = contracts_root / relativa
        if not ruta.exists():
            problemas.append(f"{relativa}: contrato ausente ({REGLA})")
            continue
        if not ruta.is_file():
            problemas.append(f"{relativa}: no es un archivo ({REGLA})")
            continue
        try:
            documento = load_file(ruta)
        except LoadError:
            problemas.append(f"{relativa}: contrato ilegible, no se pudo interpretar ({REGLA})")
            continue
        problemas.extend(comprobar_documento(relativa, documento))
    return problemas
