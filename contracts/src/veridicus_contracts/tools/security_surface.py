"""Huella de seguridad versionada `contracts/security-surface.json` (§4.11 de NFR Design, DS3).

Proyección de lo que importa a la seguridad en siete secciones: `operations`, `schemas`, `cookie`,
`servers`, `limits`, `metrics` e `integrity`. Es reproducible en bytes entre WSL y la CI:

- cada huella de `integrity` es el SHA-256 de la forma JCS (`canonical.sha256_jcs`) del documento
  ya cargado con los cargadores del paquete, así que un comentario, un espacio o un final de línea
  del YAML no la cambia; la de C6 es la de los bytes de `analyzer/v1/SHA256SUMS` (BR1.7);
- las listas sin orden semántico se ordenan, y el archivo se escribe con
  `json.dumps(sort_keys=True, indent=2, ensure_ascii=False)` más un salto, en UTF-8 sin BOM.

Sin argumentos, o con `--check`, compara en memoria y sale con código 1 mostrando la diferencia.
Solo `--write` escribe el archivo (AUTONOMIA-01): la CI nunca lo ejecuta. Código 2: un contrato no
se pudo leer o los argumentos no son válidos.

Uso: `python -m veridicus_contracts.tools.security_surface [--check | --write]`.
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from veridicus_contracts.canonical import sha256_jcs
from veridicus_contracts.checks._openapi import cuerpos, es_tipo, objeto, operaciones, resolver
from veridicus_contracts.checks.auth_surface import ENCOLAN, _tiene_csrf
from veridicus_contracts.loaders import LoadError, load_file
from veridicus_contracts.tools._comparar import diferencia, leer_si_existe

CODIGO_VERDE = 0
CODIGO_DIFIERE = 1
CODIGO_ILEGIBLE = 2

SALIDA = "security-surface.json"
# BR1.1 (guardia E-28 de T18): todo contrato propio declara su versión arriba, y la huella es uno.
# Es una clave más, no una octava sección: la forma de las siete no cambia con ella.
VERSION = "1.0.0"
# Contratos OpenAPI de la sección `operations` (C1, C16, C21 y la ruta interna de voz).
OPENAPI = (
    ("C1", "api/console.v2.yaml"),
    ("C16", "health/health.v2.yaml"),
    ("C21", "api/anonymizer-proxy.v1.yaml"),
    ("voz_interna", "api/speech-internal.v1.yaml"),
)
C25 = "limits.v1.yaml"
INTEGRIDAD = (
    ("forbidden_vocabulary", "integrity/forbidden-vocabulary.v2.yaml"),
    ("result_labels", "ui/result-labels.v2.yaml"),
    ("error_codes", "errors/error-codes.v2.yaml"),
)
SHA256SUMS_C6 = "analyzer/v1/SHA256SUMS"
MARCAS = {"x-veridicus-limit": "limit", "x-veridicus-max-bytes": "max_bytes"}


def _ordenar(valor: Any) -> Any:
    """Una lista de textos sin orden semántico se ordena; cualquier otro valor queda igual."""
    if isinstance(valor, list) and all(isinstance(v, str) for v in valor):
        return sorted(valor)
    return valor


def _marcas(nodo: Any, encontradas: dict[str, set[str]]) -> None:
    """Reúne los nombres de C25 de `x-veridicus-limit` y `x-veridicus-max-bytes` bajo `nodo`."""
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            if clave in MARCAS and isinstance(valor, str):
                encontradas[MARCAS[clave]].add(valor)
            _marcas(valor, encontradas)
    elif isinstance(nodo, list):
        for valor in nodo:
            _marcas(valor, encontradas)


def _marcas_de(*nodos: Any) -> dict[str, list[str]]:
    encontradas: dict[str, set[str]] = {"limit": set(), "max_bytes": set()}
    for nodo in nodos:
        _marcas(nodo, encontradas)
    return {clave: sorted(valores) for clave, valores in encontradas.items()}


def _campos_de_texto(raiz: Any, esquema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Las propiedades de texto libre del esquema, con su marca de límite y su `maxLength`."""
    campos: dict[str, dict[str, Any]] = {}
    for nombre, propiedad in objeto(esquema.get("properties")).items():
        resuelta = objeto(resolver(raiz, propiedad))
        if es_tipo(resuelta, "string") and "enum" not in resuelta and "const" not in resuelta:
            campos[str(nombre)] = {
                "limit": resuelta.get("x-veridicus-limit"),
                "max_length": resuelta.get("maxLength"),
            }
    return campos


def resumen_de_esquema(raiz: Any, esquema: Any) -> dict[str, Any]:
    """Estrictez, obligatorios y campos de texto con su marca de un esquema de objeto."""
    resuelto = objeto(resolver(raiz, esquema))
    obligatorios = resuelto.get("required")
    return {
        "strict": resuelto.get("additionalProperties") is False
        or resuelto.get("unevaluatedProperties") is False,
        "required": sorted(str(n) for n in obligatorios) if isinstance(obligatorios, list) else [],
        "text_fields": _campos_de_texto(raiz, resuelto),
    }


def _requisitos_de_seguridad(
    documento: Any, operacion: dict[str, Any]
) -> list[dict[str, list[str]]]:
    """Los requisitos de seguridad efectivos como lista de alternativas (los de la operación o los globales).

    Cada alternativa es `{esquema: [scopes]}` con los scopes ordenados: `{}` es la alternativa anónima
    (autenticación opcional) y varios esquemas en una alternativa son «todos a la vez», frente a varias
    alternativas, que son «cualquiera». Las alternativas se ordenan por su forma JSON canónica porque su
    orden no tiene significado.
    """
    requisitos = operacion.get("security", objeto(documento).get("security"))
    alternativas = [
        {
            str(esquema): sorted(str(s) for s in scopes) if isinstance(scopes, list) else []
            for esquema, scopes in objeto(requisito).items()
        }
        for requisito in (requisitos if isinstance(requisitos, list) else [])
    ]
    return sorted(alternativas, key=lambda a: json.dumps(a, sort_keys=True))


def _operacion(documento: Any, operacion: dict[str, Any]) -> dict[str, Any]:
    cuerpo_resuelto = resolver(documento, operacion.get("requestBody"))
    return {
        "operation_id": operacion.get("operationId"),
        "security": _requisitos_de_seguridad(documento, operacion),
        "csrf": _tiene_csrf(documento, operacion),
        "encola": operacion.get("operationId") in ENCOLAN,
        "extensions": {
            clave: _ordenar(valor)
            for clave, valor in operacion.items()
            if str(clave).startswith("x-veridicus-")
        },
        "responses": sorted(str(codigo) for codigo in objeto(operacion.get("responses"))),
        "limit_marks": _marcas_de(operacion, cuerpo_resuelto),
        "request_bodies": {
            str(medio): resumen_de_esquema(documento, esquema)
            for medio, _, esquema in cuerpos(documento, operacion)
        },
    }


def _operaciones(documento: Any) -> dict[str, Any]:
    return {
        f"{metodo.upper()} {ruta}": _operacion(documento, operacion)
        for ruta, metodo, operacion in operaciones(documento)
    }


def _esquemas(etiqueta: str, documento: Any) -> Iterator[tuple[str, dict[str, Any]]]:
    componentes = objeto(objeto(documento).get("components"))
    for nombre, esquema in objeto(componentes.get("schemas")).items():
        yield f"{etiqueta}.{nombre}", resumen_de_esquema(documento, esquema)


def _cookie(documento: Any) -> dict[str, Any]:
    esquemas = objeto(objeto(objeto(documento).get("components")).get("securitySchemes"))
    return {
        str(nombre): {
            "in": esquema.get("in"),
            "name": esquema.get("name"),
            "x-veridicus-cookie": esquema["x-veridicus-cookie"],
        }
        for nombre, esquema in esquemas.items()
        if isinstance(esquema, dict) and "x-veridicus-cookie" in esquema
    }


def _servidores(documento: Any) -> list[dict[str, Any]]:
    lista = objeto(documento).get("servers")
    servidores = (
        [
            {
                "url": servidor.get("url"),
                "variables": {
                    str(nombre): objeto(variable).get("default")
                    for nombre, variable in objeto(servidor.get("variables")).items()
                },
            }
            for servidor in lista
            if isinstance(servidor, dict)
        ]
        if isinstance(lista, list)
        else []
    )
    return sorted(servidores, key=lambda s: str(s["url"]))


def _limites(catalogo: Any) -> dict[str, Any]:
    limites = objeto(objeto(catalogo).get("limits"))
    relaciones = objeto(catalogo).get("relations")
    return {
        "schema_version": objeto(catalogo).get("schema_version"),
        "limits": {
            str(nombre): {
                **{clave: valor for clave, valor in objeto(entrada).items() if clave != "used_in"},
                "used_in": sorted(str(u) for u in objeto(entrada).get("used_in", [])),
            }
            for nombre, entrada in limites.items()
        },
        "relations": sorted(
            (list(r) for r in relaciones if isinstance(r, list))
            if isinstance(relaciones, list)
            else [],
            key=lambda r: [str(x) for x in r],
        ),
    }


def _etiqueta(etiqueta: Any) -> tuple[str, dict[str, Any]]:
    declarada = objeto(etiqueta)
    nombre = str(declarada.get("name"))
    if isinstance(declarada.get("values"), list):
        return nombre, {"values": sorted(str(v) for v in declarada["values"])}
    return nombre, {"pattern": declarada.get("pattern")}


def _metricas(documentos: Mapping[str, Any]) -> dict[str, Any]:
    metricas: dict[str, Any] = {}
    for archivo in sorted(documentos):
        for metrica in objeto(documentos[archivo]).get("metrics", []):
            declarada = objeto(metrica)
            etiquetas = objeto(declarada).get("labels")
            metricas[str(declarada.get("name"))] = {
                "file": archivo,
                "type": declarada.get("type"),
                "labels": dict(
                    _etiqueta(e) for e in (etiquetas if isinstance(etiquetas, list) else [])
                ),
            }
    return metricas


def _leer(raiz: Path, relativa: str, sustituciones: Mapping[str, Any]) -> Any:
    """El documento ya cargado de `relativa`; una sustitución en memoria manda sobre el disco."""
    if relativa in sustituciones:
        return sustituciones[relativa]
    return load_file(raiz / relativa)


def construir(raiz: Path, sustituciones: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """La huella como objeto. `sustituciones` cambia en memoria documentos ya cargados (pruebas).

    Las claves de `sustituciones` son rutas relativas a `raiz` (la carpeta `contracts/`). Lanza
    `LoadError` u `OSError` si un contrato no se puede leer.
    """
    cambios = sustituciones or {}
    openapi = {etiqueta: _leer(raiz, ruta, cambios) for etiqueta, ruta in OPENAPI}
    catalogo = _leer(raiz, C25, cambios)
    carpeta_metricas = raiz / "metrics"
    metricas = {
        f"metrics/{archivo.name}": _leer(raiz, f"metrics/{archivo.name}", cambios)
        for archivo in sorted(carpeta_metricas.glob("*.yaml"))
    }
    integridad = {nombre: sha256_jcs(_leer(raiz, ruta, cambios)) for nombre, ruta in INTEGRIDAD}
    integridad["limits"] = sha256_jcs(catalogo)
    integridad["analyzer_v1_sha256sums"] = hashlib.sha256(
        (raiz / SHA256SUMS_C6).read_bytes()
    ).hexdigest()
    esquemas: dict[str, Any] = {}
    for etiqueta, documento in openapi.items():
        esquemas.update(_esquemas(etiqueta, documento))
    return {
        "schema_version": VERSION,
        "operations": {etiqueta: _operaciones(doc) for etiqueta, doc in openapi.items()},
        "schemas": esquemas,
        "cookie": _cookie(openapi["C1"]),
        "servers": {etiqueta: _servidores(doc) for etiqueta, doc in openapi.items()},
        "limits": _limites(catalogo),
        "metrics": _metricas(metricas),
        "integrity": integridad,
    }


def serializar(huella: Mapping[str, Any]) -> bytes:
    """Los bytes del archivo: JSON con claves ordenadas, sangría de 2, UTF-8 sin BOM y un salto final."""
    texto = json.dumps(huella, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return texto.encode("utf-8")


def _raiz_de_contracts() -> Path:
    # tools/ -> veridicus_contracts/ -> src/ -> contracts/
    return Path(__file__).resolve().parents[3]


def main(argumentos: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida."""
    analizador = argparse.ArgumentParser(prog="security_surface", description=__doc__)
    modo = analizador.add_mutually_exclusive_group()
    modo.add_argument("--check", action="store_true", help="compara sin escribir (por omisión)")
    modo.add_argument("--write", action="store_true", help="escribe el archivo; la CI nunca lo usa")
    analizador.add_argument("--root", type=Path, default=None, help="carpeta contracts/")
    analizador.add_argument("--output", type=Path, default=None, help="archivo de la huella")
    argumentos_leidos = analizador.parse_args(
        list(sys.argv[1:] if argumentos is None else argumentos)
    )
    raiz = argumentos_leidos.root or _raiz_de_contracts()
    destino: Path = argumentos_leidos.output or raiz / SALIDA
    try:
        generado = serializar(construir(raiz))
    except (LoadError, OSError) as error:
        print(f"security_surface: no se pudo leer un contrato: {error}", file=sys.stderr)
        return CODIGO_ILEGIBLE
    if argumentos_leidos.write:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(generado)
        print(f"security_surface: escrito {destino.name}")
        return CODIGO_VERDE
    problemas = diferencia(destino.name, generado, leer_si_existe(destino))
    if problemas:
        print("\n".join(problemas))
        return CODIGO_DIFIERE
    print(f"security_surface: {destino.name} está al día")
    return CODIGO_VERDE


if __name__ == "__main__":
    sys.exit(main())
