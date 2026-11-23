"""Tipos de las llamadas a modelos (C13, revisión 4) y la puerta única al exterior (BR9.9).

Este módulo es neutral: lo importan U10 (anonimizador) y U11 (ModelGateway) y no importa a
ninguno. Solo puede importar de `veridicus_contracts`, `typing`, `dataclasses`, `enum` y
`datetime`; la guardia `checks/protocol_surface.py` lo comprueba con `ast` (§4.17, E43).

Los datos de `model_calls/` (el esquema `model-call.v1.yaml` y la tabla de papeles) conviven con
este módulo bajo el mismo nombre de paquete: se leen como recursos de la raíz,
`files("veridicus_contracts") / "model_calls" / "..."`.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Final, Literal, Protocol

# Revisión 4 (FD-U1-01, BR9.1): el papel es un texto con patrón y no una lista cerrada. El
# analizador lo restringe a judge, verifier y verifier_permuted (C18, C19).
ROLE_PATTERN: Final = "^[a-z][a-z0-9_]{0,31}$"
Role = str

# primary: el destino del papel; fallback: el `fallback_provider` del perfil.
DestinationSlot = Literal["primary", "fallback"]
Provider = Literal["anthropic", "google", "openai", "local"]
Scope = Literal["local", "external"]
MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True, kw_only=True)
class Destination:
    """Un destino ya resuelto de C18. Nunca lleva el valor de una clave, solo su nombre."""

    provider: Provider
    model: str
    scope: Scope
    version: str | None = None
    family: str | None = None
    base_url: str | None = None  # solo local
    api_key_ref: str | None = None  # nombre de la variable o del Secret
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Message:
    """Un mensaje de la conversación; el testimonio va como JSON dentro del mensaje `user`."""

    role: MessageRole
    content: str


@dataclass(frozen=True, kw_only=True)
class GenerateRequest:
    """La petición de una llamada a un modelo."""

    role: Role
    destination_slot: DestinationSlot
    profile_name: str
    profile_sha256: str  # huella de la entrada del perfil (C18); el proxy la comprueba (C21)
    destination: Destination
    messages: list[Message]
    schema: dict[str, Any]  # JSON Schema de la respuesta; salida JSON forzada
    timeout_s: float  # explícito siempre (C25)
    seed: int | None = None


@dataclass(frozen=True, kw_only=True)
class ModelCall:
    """El registro de una llamada; misma forma que `model_calls/model-call.v1.yaml`."""

    role: Role
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    fallback_provider: bool
    anonymized: bool
    at: datetime
    version: str | None = None
    effort_or_quantization: str | None = None
    engine: str | None = None
    seed: int | None = None


@dataclass(frozen=True, kw_only=True)
class GenerateResult:
    """La respuesta de una llamada, ya parseada; quien llama la valida contra su esquema."""

    content: dict[str, Any]
    altered_markers: list[str]  # punteros JSON (RFC 6901), sin repetidos y en orden de recorrido
    call: ModelCall


class ModelCallError(Exception):
    """Raíz de los errores tipados de una llamada a un modelo (FR15.2)."""


class ContentBlocked(ModelCallError):
    """El proveedor bloqueó el contenido (451)."""

    call: ModelCall

    def __init__(self, message: str, call: ModelCall) -> None:
        super().__init__(message)
        self.call = call


class Timeout(ModelCallError):
    """La llamada pasó de su plazo."""

    call: ModelCall

    def __init__(self, message: str, call: ModelCall) -> None:
        super().__init__(message)
        self.call = call


class ProviderError(ModelCallError):
    """El proveedor respondió con un fallo; la llamada ya salió y no se repite sola."""

    call: ModelCall

    def __init__(self, message: str, call: ModelCall) -> None:
        super().__init__(message)
        self.call = call


class InvalidOutput(ModelCallError):
    """La salida del modelo no cumple el esquema pedido."""

    call: ModelCall

    def __init__(self, message: str, call: ModelCall) -> None:
        super().__init__(message)
        self.call = call


class AnonymizerUnavailable(ModelCallError):
    """Fallo cerrado: no salió ninguna llamada fuera del clúster o de la máquina."""


class AnonymizingProvider(Protocol):
    """Única puerta a un destino externo (BR9.9, NFR1.2).

    La implementan el módulo en proceso de C20 (U10) y el cliente HTTP de C21 (U11). La
    disponibilidad del proxy no es parte del `Protocol`: solo hay `generate`.
    """

    def generate(self, request: GenerateRequest) -> GenerateResult: ...
