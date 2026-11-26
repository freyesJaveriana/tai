"""Mensajes al juez y al verificador y esquemas de respuesta (BR3.1, BR3.3, BR3.4, PD-6, PD-11).

Estado: *stub* del paso 1 (U11-T01). Lo implementa U11-T03 (paso 8).
"""

from typing import Any, Literal

Role = Literal["judge", "verifier"]
SchemaKind = Literal["wire", "local"]


def load_response_schema(role: Role, kind: SchemaKind) -> dict[str, Any]:
    """Esquema de la respuesta de un papel, de `data/schemas/` (PD-11).

    `wire` es el que viaja en `GenerateRequest.schema` hacia el proveedor, sin las palabras clave que
    Anthropic no admite; `local` es el estricto con el que se valida la respuesta (cerrado, 7 tipos,
    `minLength: 1`). Las pruebas rojas pasan por esta función y nunca leen el archivo (R-07).
    """
    raise NotImplementedError("load_response_schema: lo implementa U11-T03 (paso 8)")
