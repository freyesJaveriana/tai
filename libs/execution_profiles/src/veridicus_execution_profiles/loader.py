"""Carga de `config/profiles.yaml` y resolución de la configuración efectiva (BR2.1, BR2.10).

Estado: *stubs* del paso 1 (U11-T01). Los implementa U11-T02. Las pruebas del rojo (paso 3) pasan por
estos símbolos y nunca leen el archivo directamente (R-07).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, kw_only=True)
class EffectiveConfig:
    """La configuración efectiva de una corrida (`effective-config.v1.yaml`, BR2.10).

    `profile` es la entrada del perfil tal como está en el archivo, sin resolver claves: nunca lleva
    el valor de una clave, solo su nombre (`api_key_ref`). `profile_sha256` es el SHA-256 de su
    forma canónica JCS y `config_sha256` el de todo el objeto. `limits` son las cifras de C25 que
    cambian el resultado, ya bajadas por el entorno.
    """

    schema_version: str
    analyzer_version: str
    profile_name: str
    profile: Mapping[str, Any]
    profile_sha256: str
    prompt_sha256: str
    limits: Mapping[str, float]
    config_sha256: str


def load_profiles(path: Path | None = None) -> dict[str, Any]:
    """Lee el archivo de perfiles aprobado y lo devuelve tal cual (`schema_version` y `profiles`).

    Sin `path`, lee el `config/profiles.yaml` versionado. Solo lee: ninguna ruta lo escribe (BR2.11).
    La validación es de `validate.validate_profile`.
    """
    raise NotImplementedError("load_profiles: lo implementa U11-T02 (paso 4)")


def load_config(profile_name: str, env: Mapping[str, str]) -> EffectiveConfig:
    """Resuelve la configuración efectiva del perfil `profile_name` con el entorno `env`.

    Valida con `validate.validate_profile`, carga los límites con `limits.load(env)` y calcula las
    dos huellas con `canonical.sha256_jcs`. El valor de ninguna clave entra en ellas (BR2.10).
    """
    raise NotImplementedError("load_config: lo implementa U11-T02 (paso 4)")
