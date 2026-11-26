"""Carga de `config/profiles.yaml` y resolución de la configuración efectiva (BR2.1, BR2.10, BR2.11).

Solo lee: ninguna ruta de este módulo abre un archivo para escribir (BR2.11). Las pruebas del rojo
(paso 3) pasan por estos símbolos y nunca leen el archivo directamente (R-07).
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from veridicus_contracts import limits
from veridicus_contracts.canonical import sha256_jcs
from veridicus_contracts.loaders import load_file
from veridicus_errors import ConfigInvalidLimitError, ConfigInvalidProfileError

from veridicus_execution_profiles.validate import validate_profile

SCHEMA_VERSION: Final = "1.0.0"
# La versión de la biblioteca del analizador; la entrega U11-T03 en `analyzer_version` cuando la fije.
ANALYZER_VERSION: Final = "0.1.0"
# Sin la referencia del prompt (la guarda `incoherence_analyzer`, PD-13) la huella es ceros: el
# analizador la compara con el hash de los bytes del prompt y una referencia ausente no coincide.
PROMPT_SHA256_UNSET: Final = "0" * 64
_SHA256: Final = re.compile(r"[0-9a-f]{64}")
# Las cifras de C25 que cambian el resultado del análisis (`effective-config.v1.yaml`, `limits`).
EFFECTIVE_LIMITS: Final = (
    "model_call_timeout_s",
    "run_deadline_incremental_s",
    "run_deadline_final_s",
    "fragment_window_turns",
    "fragment_overlap_turns",
)


@dataclass(frozen=True, kw_only=True)
class EffectiveConfig:
    """La configuración efectiva de una corrida (`effective-config.v1.yaml`, BR2.10).

    `profile` es la entrada del perfil tal como está en el archivo, sin resolver claves: nunca lleva
    el valor de una clave, solo su nombre (`api_key_ref`). `profile_sha256` es el SHA-256 de su
    forma canónica JCS y `config_sha256` el de todo el objeto. `limits` son las cifras de C25 que
    cambian el resultado, ya bajadas por el entorno. `warnings` son los avisos de la validación (por
    ejemplo `same_family`, BR2.5): no entran en ninguna huella, porque salen del perfil y del
    entorno que ya las determinan. `warnings` no existe en C18 (`additionalProperties: false`): quien
    serialice la configuración al objeto C18 debe excluirlo.
    """

    schema_version: str
    analyzer_version: str
    profile_name: str
    profile: Mapping[str, Any]
    profile_sha256: str
    prompt_sha256: str
    limits: Mapping[str, float]
    config_sha256: str
    warnings: tuple[str, ...] = ()


def _default_path() -> Path:
    """El `config/profiles.yaml` versionado: el del paquete instalado o el del árbol de fuentes."""
    packaged = Path(__file__).parent / "config" / "profiles.yaml"
    return (
        packaged if packaged.is_file() else Path(__file__).parents[2] / "config" / "profiles.yaml"
    )


def load_profiles(path: Path | None = None) -> dict[str, Any]:
    """Lee el archivo de perfiles aprobado y lo devuelve tal cual (`schema_version` y `profiles`).

    Sin `path`, lee el `config/profiles.yaml` versionado. Solo lee: ninguna ruta lo escribe (BR2.11).
    La validación es de `validate.validate_profile`.
    """
    document: dict[str, Any] = load_file(path if path is not None else _default_path())
    return document


def _freeze(value: Any) -> Any:
    """Copia inmutable: los objetos como `MappingProxyType` y las listas como tuplas."""
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def load_config(
    profile_name: str,
    env: Mapping[str, str],
    path: Path | None = None,
    *,
    prompt_sha256: str = PROMPT_SHA256_UNSET,
) -> EffectiveConfig:
    """Resuelve la configuración efectiva del perfil `profile_name` con el entorno `env`.

    Sin `path`, lee el `config/profiles.yaml` versionado; con `path`, ese archivo (las pruebas de
    huellas lo usan con otros formatos del mismo contenido, BR2.10).

    Valida con `validate.validate_profile`, carga los límites con `limits.load(env)` y calcula las
    dos huellas con `canonical.sha256_jcs`. El valor de ninguna clave entra en ellas (BR2.10).
    """
    if not _SHA256.fullmatch(prompt_sha256):
        raise ConfigInvalidProfileError(
            "configuración no válida: prompt_sha256 no tiene la forma de un SHA-256 en hexadecimal"
        )
    document = load_profiles(path)
    warnings = validate_profile(document, profile_name, env)
    profile = document["profiles"][profile_name]
    try:
        effective = limits.load(env)
    except limits.LimitsConfigError as error:
        raise ConfigInvalidLimitError(str(error)) from error
    chosen = {name: effective[name] for name in EFFECTIVE_LIMITS}
    profile_sha256 = sha256_jcs(profile)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "analyzer_version": ANALYZER_VERSION,
        "profile_name": profile_name,
        "profile": profile,
        "profile_sha256": profile_sha256,
        "prompt_sha256": prompt_sha256,
        "limits": chosen,
    }
    return EffectiveConfig(
        schema_version=SCHEMA_VERSION,
        analyzer_version=ANALYZER_VERSION,
        profile_name=profile_name,
        profile=_freeze(profile),
        profile_sha256=profile_sha256,
        prompt_sha256=prompt_sha256,
        limits=MappingProxyType(chosen),
        config_sha256=sha256_jcs(body),
        warnings=warnings,
    )
