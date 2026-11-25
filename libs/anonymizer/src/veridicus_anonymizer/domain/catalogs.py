"""Listas y tablas versionadas del módulo (BR1.2, BR1.5, BR3.1, BR5.2).

`load_catalogs` lee los cuatro archivos de `data/`, los valida contra los esquemas versionados de
`data/schemas/` y falla cerrado (`CatalogError`) ante cualquier archivo ausente, mal formado, con un
campo de más, con una expresión que `google-re2` no compila o con una entrada repetida. Nunca
repara ni completa: un catálogo dudoso impide construir el módulo (BR2.2).
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Literal, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from veridicus_contracts.loaders import LoadError, load_file

from veridicus_anonymizer.domain.regex import RegexError, compile_pattern

PROVIDERS = frozenset({"anthropic", "google", "openai"})

# Grupo del archivo de reglas -> categoría de marca (BR1.5).
_CATEGORY_BY_GROUP = {
    "person_patterns": "PERSONA",
    "place_patterns": "LUGAR",
    "case_number_patterns": "EXPEDIENTE",
    "identifier_patterns": "IDENTIFICADOR",
}


class CatalogError(ValueError):
    """Un archivo de `data/` es inválido: el módulo no se construye (falla cerrado, BR2.2)."""


@dataclass(frozen=True)
class RulePattern:
    """Un patrón de detección en `google-re2` con su categoría."""

    id: str
    category: str
    pattern: str


@dataclass(frozen=True)
class ProviderDomain:
    """Dominio fijo de un proveedor. El archivo versionado no trae puerto: siempre es 443."""

    domain: str
    port: int = 443


@dataclass(frozen=True)
class Capability:
    """Modo de salida estructurada y parámetro de esfuerzo de un modelo (BR5.2)."""

    provider: str
    model: str
    structured_mode: Literal["json_schema_native", "forced_tool"]
    effort_parameter: str


@dataclass(frozen=True)
class Catalogs:
    """Las cuatro listas del módulo, ya validadas contra `data/schemas/`."""

    rules: tuple[RulePattern, ...]
    allowed_words: frozenset[str]
    domains: Mapping[str, ProviderDomain]
    capabilities: Mapping[tuple[str, str], Capability]


def _package_data() -> Traversable:
    return files("veridicus_anonymizer") / "data"


def _read(root: Traversable | Path, stem: str) -> dict[str, Any]:
    """Un archivo de datos ya validado contra su esquema; lo que falle sale como `CatalogError`."""
    schema_text = (_package_data() / "schemas" / f"{stem}.schema.v1.json").read_text("utf-8")
    try:
        document = load_file(root / f"{stem}.v1.yaml")
        Draft202012Validator(json.loads(schema_text)).validate(document)
    except (OSError, LoadError, ValidationError) as exc:
        raise CatalogError(f"el archivo de datos «{stem}» es inválido") from exc
    return cast(dict[str, Any], document)


def _rules(document: Mapping[str, Any]) -> tuple[RulePattern, ...]:
    rules: list[RulePattern] = []
    for group, category in _CATEGORY_BY_GROUP.items():
        for entry in document[group]:
            try:
                compile_pattern(entry["pattern"])
            except RegexError as exc:
                raise CatalogError(f"la regla «{entry['id']}» no compila en re2") from exc
            rules.append(RulePattern(entry["id"], category, entry["pattern"]))
    if len({r.id for r in rules}) != len(rules):
        raise CatalogError("hay un identificador de regla repetido")
    return tuple(rules)


def _domains(document: Mapping[str, Any]) -> dict[str, ProviderDomain]:
    domains = {e["provider"]: ProviderDomain(domain=e["domain"]) for e in document["entries"]}
    if set(domains) != PROVIDERS:
        raise CatalogError("la lista de dominios debe tener un solo dominio por proveedor")
    return domains


def _capabilities(document: Mapping[str, Any]) -> dict[tuple[str, str], Capability]:
    capabilities = {
        (e["provider"], e["model"]): Capability(
            provider=e["provider"],
            model=e["model"],
            structured_mode=e["structured_mode"],
            effort_parameter=e["effort_parameter"],
        )
        for e in document["entries"]
    }
    if len(capabilities) != len(document["entries"]):
        raise CatalogError("la tabla de capacidades repite un modelo")
    return capabilities


def load_catalogs(data_dir: Path | None = None) -> Catalogs:
    """Carga y valida `data/` (o `data_dir`); un archivo inválido lanza `CatalogError`."""
    root: Traversable | Path = _package_data() if data_dir is None else data_dir
    return Catalogs(
        rules=_rules(_read(root, "detection-rules")),
        allowed_words=frozenset(_read(root, "allowed-words")["words"]),
        domains=_domains(_read(root, "allowed-domains")),
        capabilities=_capabilities(_read(root, "capabilities")),
    )
