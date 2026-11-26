"""Validación previa de la entrada, antes de cualquier llamada (BR1.1 a BR1.4, AUTONOMIA-04).

`check` lanza una de las clases de `InputRejected` en el primer fallo, con un mensaje en español que
nombra el campo y nunca el texto del testimonio. Orden (F1): esquema C6 y límites de C25 (BR1.1),
consentimiento según el origen (BR1.2), transferencia autorizada si el perfil tiene un destino
externo (BR1.3) y perfil aprobado (BR1.4). Quien llama no hace ninguna llamada a un modelo si algo
de esto falla.

Dos comprobaciones más, de B11a, que cierran lo que el esquema deja abierto:

- el número `n` de cada turno es único, porque la verificación de citas busca el turno por su `n`;
- el modo incremental (BR1.5) se difiere a B11b: se rechaza con `import.invalid_transcript` en vez de
  analizar toda la transcripción como si fuera el modo final.
"""

from collections.abc import Mapping
from typing import Any

from jsonschema.exceptions import ValidationError
from veridicus_contracts import limits
from veridicus_errors import (
    ImportInvalidTranscriptError,
    ProfileNotApprovedError,
    ProfileTransferNotAuthorizedError,
    SessionConsentMissingError,
)
from veridicus_execution_profiles.loader import EffectiveConfig

from veridicus_incoherence_analyzer.application.contract import entrada_validator


def _is_missing_consent(error: ValidationError) -> bool:
    """El error del esquema que exige `consentimiento` cuando el origen es corpus o guiada."""
    return error.validator == "required" and error.validator_value == ["consentimiento"]


def _where(error: ValidationError) -> str:
    """La ruta del error en la entrada, sin valores: solo claves del esquema e índices."""
    return "/" + "/".join(str(part) for part in error.absolute_path)


def _check_schema(entrada: Any) -> None:
    """BR1.1 (esquema) y BR1.2: sin el bloque de consentimiento, el código propio de la ausencia."""
    errors = sorted(entrada_validator().iter_errors(entrada), key=_where)
    others = [error for error in errors if not _is_missing_consent(error)]
    if others:
        raise ImportInvalidTranscriptError(
            f"la entrada no cumple el esquema C6 de entrada en {_where(others[0])}"
        )
    if errors:
        raise SessionConsentMissingError(
            "la transcripción de origen corpus o guiada no trae el bloque de consentimiento"
        )


def _check_limits(turns: list[Mapping[str, Any]]) -> None:
    """BR1.1 (límites): cifras de C25, el catálogo sin bajar (el entorno solo las baja)."""
    catalog = limits.load({})
    if len(turns) > catalog["transcript_max_turns"]:
        raise ImportInvalidTranscriptError("la transcripción supera el máximo de turnos")
    if any(len(turn["texto"]) > catalog["turn_max_chars"] for turn in turns):
        raise ImportInvalidTranscriptError("un turno supera el máximo de caracteres")
    if sum(len(turn["texto"]) for turn in turns) > catalog["transcript_max_chars"]:
        raise ImportInvalidTranscriptError("la transcripción supera el máximo de caracteres")


def _has_external_destination(config: EffectiveConfig) -> bool:
    profile = config.profile
    destinations = list(profile["roles"].values())
    if "fallback_provider" in profile:
        destinations.append(profile["fallback_provider"])
    return any(destination["scope"] == "external" for destination in destinations)


def check(entrada: Any, config: EffectiveConfig) -> None:
    """Valida `entrada` frente a `config`; lanza `InputRejected` (BR1.1 a BR1.4) y no llama a nadie."""
    _check_schema(entrada)
    transcription = entrada["transcripcion"]
    turns: list[Mapping[str, Any]] = transcription["turnos"]
    _check_limits(turns)
    if len({turn["n"] for turn in turns}) != len(turns):
        raise ImportInvalidTranscriptError("el número de un turno se repite en la transcripción")
    consent = transcription.get("consentimiento")
    if (
        consent is not None
        and not consent["autoriza_transferencia"]
        and _has_external_destination(config)
    ):
        raise ProfileTransferNotAuthorizedError(
            "el consentimiento no autoriza la transferencia y el perfil tiene un destino externo"
        )
    if entrada["perfil"] != config.profile_name:
        raise ProfileNotApprovedError(
            "el perfil de la entrada no es el de la configuración efectiva"
        )
    if entrada["modo"] != "final":
        raise ImportInvalidTranscriptError(
            "el modo incremental no está disponible en esta versión: se difiere a B11b"
        )
