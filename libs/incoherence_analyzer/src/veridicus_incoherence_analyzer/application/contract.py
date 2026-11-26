"""Validadores de la entrada y de la salida de C6 (BR1.1, BR8.1), con el registro de U1.

Construir el registro lee todos los esquemas de `veridicus_contracts`; se hace una sola vez por
proceso. Los validadores no guardan estado entre llamadas.
"""

from functools import cache

from jsonschema import Draft202012Validator
from veridicus_contracts.registry import BASE_URI, build_registry, validator_for

ENTRADA_URI = BASE_URI + "veridicus/contracts/analyzer/v1/entrada"
SALIDA_URI = BASE_URI + "veridicus/contracts/analyzer/v1/salida"


@cache
def entrada_validator() -> Draft202012Validator:
    """El validador del esquema C6 de entrada (Draft 2020-12)."""
    return validator_for(build_registry(), ENTRADA_URI)


@cache
def salida_validator() -> Draft202012Validator:
    """El validador del esquema C6 de salida (Draft 2020-12)."""
    return validator_for(build_registry(), SALIDA_URI)
