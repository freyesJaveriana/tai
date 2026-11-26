"""Máquina de estados de la corrida y fallo cerrado (BR7.1, BR7.6).

Una corrida recorre `judging` → `filtering` → `verifying` → `finalizing`, sin saltos ni retrocesos,
y puede fallar desde cualquiera de ellas. `fail` guarda el código del error con una sola regla de
precedencia (BR7.6): `incidente_anonimizacion` gana sobre cualquier otro código, porque con un
destino externo que volvió sin anonimizar la sesión debe bloquearse; entre los demás gana el
primero. Un fallo es terminal: nada avanza después.

`error_code_for` es la correspondencia de BR7.1 entre los errores tipados de `model_calls` y los
códigos de C6. Un error que no es de `model_calls` no se convierte en estado error: se propaga
(CLI 5), y aquí un `ModelCallError` sin subclase conocida es un defecto del código, no un código.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    InvalidOutput,
    ModelCall,
    ModelCallError,
    ProviderError,
    Timeout,
)

INCIDENT: Final = "incidente_anonimizacion"

_CODES: Final[dict[type[ModelCallError], str]] = {
    InvalidOutput: "salida_invalida",
    ContentBlocked: "bloqueo_contenido",
    Timeout: "tiempo_agotado",
    ProviderError: "proveedor",
    AnonymizerUnavailable: "anonimizador_no_disponible",
}


class Phase(StrEnum):
    JUDGING = "judging"
    FILTERING = "filtering"
    VERIFYING = "verifying"
    FINALIZING = "finalizing"
    ERROR = "error"


_NEXT: Final[dict[Phase, Phase]] = {
    Phase.JUDGING: Phase.FILTERING,
    Phase.FILTERING: Phase.VERIFYING,
    Phase.VERIFYING: Phase.FINALIZING,
}


@dataclass(frozen=True)
class RunState:
    """Estado inmutable de la corrida; cada transición devuelve uno nuevo."""

    phase: Phase = Phase.JUDGING
    error_code: str | None = None

    @property
    def failed(self) -> bool:
        return self.phase is Phase.ERROR

    def advance(self, target: Phase) -> "RunState":
        """Pasa a la fase siguiente; cualquier otra transición es un defecto del código."""
        if _NEXT.get(self.phase) is not target:
            raise ValueError(f"transición no válida de {self.phase} a {target}")
        return RunState(target, self.error_code)

    def fail(self, code: str) -> "RunState":
        """Falla cerrado con `code`; el incidente de anonimización tiene precedencia (BR7.6)."""
        if self.error_code == INCIDENT or (self.error_code is not None and code != INCIDENT):
            return self
        return RunState(Phase.ERROR, code)


def error_code_for(error: ModelCallError) -> str:
    """El código de C6 de un error tipado de `model_calls` (BR7.1)."""
    for cls, code in _CODES.items():
        if isinstance(error, cls):
            return code
    raise TypeError(f"{type(error).__name__} no tiene código de salida")


def is_incident(scope: str, call: ModelCall | None) -> bool:
    """Un destino externo cuya llamada volvió con `anonymized` falso es un incidente (BR7.6)."""
    return call is not None and scope == "external" and not call.anonymized
