"""Validación de un perfil de ejecución (BR2.1 a BR2.5, BR2.11).

Estado: *stub* del paso 1 (U11-T01). Lo implementa U11-T02.
"""

from collections.abc import Mapping
from typing import Any


def validate_profile(
    document: Mapping[str, Any], name: str, env: Mapping[str, str]
) -> tuple[str, ...]:
    """Valida el perfil `name` del archivo `document` y devuelve sus avisos (por ejemplo `same_family`).

    `document` es el archivo ya cargado (`schema_version` y `profiles`). Valida con
    `profiles.validate(..., key_prefix="VERIDICUS_", kind="analyzer")` de U1 y con las reglas de
    BR2: misma familia solo con `purpose: demonstration` y `same_family_declared` (BR2.5) y la
    variable de `api_key_ref` presente en `env` (BR2.2). Lanza `ConfigInvalidProfileError`
    (`config.invalid_profile`) con el perfil, el papel y el ajuste que fallan, nunca un valor.
    """
    raise NotImplementedError("validate_profile: lo implementa U11-T02 (paso 4)")
