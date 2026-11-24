"""Cobertura de fixtures por regla de nivel 0 (security-design §4.10, NFR12.1, BR1.6).

Módulo guardia (100 % de ramas). Exige, por cada regla de `REGLAS`, un fixture `accept` y uno `reject`, y
falla si:

- un `accept` no se acepta o un `reject` no falla al validarlo contra su contrato;
- un `reject` falla solo por palabras clave del validador que su regla no declara (falla por otra regla).

Un `accept` cubre una regla si es de la misma familia de contrato que alguno de sus `reject` (`C6.entrada`
y `C6.salida` son de la familia `C6`). Quedan fuera (`EXCLUIDAS`) BR5.2 a BR5.6 (solo la forma, BR5.8),
BR1.5, BR1.8 y BR12.2 (revisión del PR). Las reglas de nivel 0 que se prueban con código y no con fixtures
no están en `REGLAS`: cada una tiene su prueba propia (P-T18-3).

Los mensajes nombran el archivo y la regla, nunca el contenido del fixture.
"""

import importlib.resources
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from referencing import Resource
from referencing.jsonschema import DRAFT202012

from veridicus_contracts.checks._recorrido import DIRECTORIOS_SALTADOS, documentos
from veridicus_contracts.loaders import load_file
from veridicus_contracts.registry import BASE_URI, build_registry
from veridicus_contracts.validators import extract_message_payloads

REGLA = "NFR12.1"
ESTRUCTURA = frozenset({"required", "additionalProperties"})
EXCLUIDAS = ("BR5.2", "BR5.3", "BR5.4", "BR5.5", "BR5.6", "BR1.5", "BR1.8", "BR12.2")

# Regla -> palabras clave del validador por las que su `reject` puede fallar.
REGLAS: dict[str, frozenset[str]] = {
    "BR1.2": frozenset({"pattern"}),
    "BR2.1": frozenset({"required"}),
    "BR2.3": frozenset({"required"}),
    "BR3.1": ESTRUCTURA,
    "BR3.2": frozenset({"enum"}),
    "BR3.5": frozenset({"required"}),
    "BR3.6": frozenset({"maxItems"}),
    "BR4.1": frozenset({"required", "minLength", "enum"}),
    "BR4.2": frozenset({"additionalProperties"}),
    "BR4.4": frozenset({"required", "minLength", "not"}),
    "BR9.1": frozenset({"pattern"}),
    "BR9.3": frozenset({"additionalProperties"}),
    "BR10.1": frozenset({"pattern"}),
    "BR10.2": frozenset({"enum"}),
    "NFR1.3": frozenset({"additionalProperties"}),
    "NFR10.2": frozenset({"required"}),
    "NFRD-U1-07": frozenset({"additionalProperties"}),
}

# Contrato del fixture -> (archivo del paquete, puntero dentro de él).
ESQUEMAS: dict[str, tuple[str, str]] = {
    "C6.entrada": ("analyzer/v1/entrada.schema.json", ""),
    "C6.salida": ("analyzer/v1/salida.schema.json", ""),
    "C7": ("integrity/review-suggestion.v2.json", ""),
    "C18.effective-config": ("profiles/effective-config.v1.yaml", ""),
    "C18.profile-base": ("profiles/profile-base.schema.v1.yaml", ""),
    "C18.profiles": ("profiles/profiles.schema.v1.yaml", ""),
    "C19": ("cli/report.schema.v2.yaml", ""),
    "model-call": ("model_calls/model-call.v1.yaml", ""),
    "C21.request": (
        "api/anonymizer-proxy.v1.yaml",
        "#/paths/~1v1~1generate/post/requestBody/content/application~1json/schema",
    ),
}
# Familia de mensajes de cola -> AsyncAPI que los declara.
COLAS = {"C2": "queues/runs.v2.yaml", "C3": "queues/results.v2.yaml", "C5": "queues/speech.v2.yaml"}
AJENOS = DIRECTORIOS_SALTADOS - {"fixtures", "tests"}


def _familia(contrato: str) -> str:
    return contrato.split(".")[0]


def _puntero_de_cola(documento: Any, mensaje: str) -> str | None:
    cargas = extract_message_payloads(documento)
    return next((f"#/{ruta}/payload" for ruta in cargas if ruta.endswith("/" + mensaje)), None)


@cache
def _validador(contrato: str) -> Draft202012Validator | None:
    """El validador del contrato de un fixture, desde los datos del paquete; `None` si no se conoce."""
    puntero: str | None
    if contrato in ESQUEMAS:
        archivo, puntero = ESQUEMAS[contrato]
    elif _familia(contrato) in COLAS and "." in contrato:
        archivo, puntero = COLAS[_familia(contrato)], None
    else:
        return None
    documento = load_file(importlib.resources.files("veridicus_contracts") / archivo)
    if puntero is None:
        puntero = _puntero_de_cola(documento, contrato.split(".", 1)[1])
        if puntero is None:
            return None
    identificador = documento.get("$id") if isinstance(documento, dict) else None
    uri = urljoin(BASE_URI, identificador) if isinstance(identificador, str) else f"{BASE_URI}_documentos/{archivo}"
    recurso = Resource.from_contents(documento, default_specification=DRAFT202012)
    return Draft202012Validator(
        {"$ref": uri + puntero},
        registry=_registro().with_resource(uri, recurso),
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


@cache
def _registro() -> Any:
    return build_registry()


def _palabras(errores: Any) -> set[str]:
    palabras: set[str] = set()
    for error in errores:
        palabras.add(str(error.validator))
        palabras |= _palabras(error.context or ())
    return palabras


def _leidos(raiz: Path) -> Iterator[tuple[str, Any, bool]]:
    """Cada archivo de una carpeta `fixtures/` bajo `raiz`: ruta relativa, contenido y si se leyó."""
    for relativa, documento, legible in documentos(raiz, AJENOS):
        if "fixtures" in relativa.split("/")[:-1]:
            yield relativa, documento, legible


def _es_fixture(documento: Any) -> bool:
    return isinstance(documento, dict) and "contract" in documento and "expectation" in documento


def fixtures(raiz: Path) -> list[tuple[str, dict[str, Any]]]:
    """Los fixtures legibles bajo `raiz` (los archivos de `fixtures/` con `contract` y `expectation`)."""
    return [(r, d) for r, d, legible in _leidos(raiz) if legible and _es_fixture(d)]


def _problemas_del_fixture(relativa: str, fixture: dict[str, Any], reglas: dict[str, frozenset[str]]) -> list[str]:
    esperado = fixture["expectation"]
    if esperado not in ("accept", "reject"):
        return []
    validador = _validador(str(fixture["contract"]))
    if validador is None:
        return [f"{relativa}: contrato desconocido ({REGLA})"]
    errores = list(validador.iter_errors(fixture.get("payload")))
    if esperado == "accept":
        return [] if not errores else [f"{relativa}: el accept no se acepta ({REGLA})"]
    razon = str(fixture.get("reject_reason", "sin regla"))
    if not errores:
        return [f"{relativa}: el reject no falla ({razon}, {REGLA})"]
    if razon in reglas and not _palabras(errores) & reglas[razon]:
        return [f"{relativa}: el reject falla por otra regla ({razon}, {REGLA})"]
    return []


def comprobar(raiz: Path, reglas: dict[str, frozenset[str]] | None = None) -> list[str]:
    """Los problemas de cobertura y de causa de los fixtures bajo `raiz` (la carpeta `contracts/`)."""
    reglas = REGLAS if reglas is None else reglas
    problemas: list[str] = []
    rechazados: dict[str, set[str]] = {}
    aceptados: set[str] = set()
    for relativa, documento, legible in _leidos(raiz):
        if not legible:
            problemas.append(f"{relativa}: fixture ilegible ({REGLA})")
        elif _es_fixture(documento):
            problemas.extend(_problemas_del_fixture(relativa, documento, reglas))
            familia = _familia(str(documento["contract"]))
            if documento["expectation"] == "accept":
                aceptados.add(familia)
            elif documento["expectation"] == "reject":
                rechazados.setdefault(str(documento.get("reject_reason")), set()).add(familia)
    for regla in sorted(reglas):
        contratos = rechazados.get(regla, set())
        if not (contratos & aceptados if contratos else aceptados):
            problemas.append(f"{regla}: falta un fixture accept ({REGLA}, §4.10)")
        if not contratos:
            problemas.append(f"{regla}: falta un fixture reject ({REGLA}, §4.10)")
    return problemas
