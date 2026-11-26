"""Mensajes al juez y al verificador, *prompt* y esquemas de respuesta (BR3.1, BR3.3, BR3.4, PD-6, PD-11).

Esta es la **única** función que arma mensajes (`build_messages`): `system` es siempre el texto fijo
del *prompt* para el papel y no lleva ningún carácter de la entrada (K-84); el testimonio va solo en
el mensaje `user`, como JSON (`ensure_ascii=False`, separadores compactos). Así el testimonio no
puede cerrar un bloque ni cambiar las reglas.

El *prompt* es un solo archivo, `data/prompt.v1.md`, con una sección por papel. Su SHA-256 es
`prompt_sha256` y `data/prompt.v1.sha256` guarda la referencia versionada (PD-13): `analyze` compara
la huella de los bytes leídos con la de la configuración y con esa referencia, y si no coinciden la
corrida termina en `salida_invalida` sin llamar. Quien arma la configuración obtiene la referencia
con `load_prompt_reference()` (K-88).
"""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from importlib.resources import files
from typing import Any, Final, Literal

from veridicus_contracts.loaders import load_json_text
from veridicus_contracts.model_calls import Message

Role = Literal["judge", "verifier"]
SchemaKind = Literal["wire", "local"]

_DATA: Final = "data"
_PROMPT_FILE: Final = "prompt.v1.md"
_REFERENCE_FILE: Final = "prompt.v1.sha256"
# Los encabezados de sección del archivo del prompt, por papel.
_SECTION_TITLES: Final = {"juez": "judge", "verificador": "verifier"}
_SECTION: Final = re.compile(r"^# (juez|verificador)$", re.MULTILINE)


def _resource(*parts: str) -> Any:
    return files("veridicus_incoherence_analyzer").joinpath(_DATA, *parts)


def prompt_bytes() -> bytes:
    """Los bytes del archivo del *prompt*; su SHA-256 es `prompt_sha256` (BR3.1)."""
    data: bytes = _resource(_PROMPT_FILE).read_bytes()
    return data


def prompt_sha256() -> str:
    """El SHA-256 en hexadecimal de los bytes del *prompt* leídos ahora."""
    return hashlib.sha256(prompt_bytes()).hexdigest()


def load_prompt_reference() -> str:
    """La referencia versionada del *prompt* (`data/prompt.v1.sha256`), para `load_config` (K-88).

    Devuelve el texto tal cual está en el archivo, sin espacios en los extremos: una referencia
    dañada no se corrige aquí, simplemente no coincidirá con la huella de los bytes.
    """
    text: str = _resource(_REFERENCE_FILE).read_text(encoding="utf-8")
    return text.strip()


def _sections() -> dict[str, str]:
    text = prompt_bytes().decode("utf-8")
    found = list(_SECTION.finditer(text))
    ends = [match.start() for match in found[1:]] + [len(text)]
    return {
        _SECTION_TITLES[match.group(1)]: text[match.end() : end].strip()
        for match, end in zip(found, ends, strict=True)
    }


def load_system_prompt(role: Role) -> str:
    """El texto fijo del mensaje `system` de un papel, sección de `data/prompt.v1.md` (PD-6, BR3.1).

    Es lo único que viaja en `system`: no lleva ningún carácter de la entrada. El verificador y el
    verificador permutado usan el del papel `verifier`.
    """
    return _sections()[role]


def load_response_schema(role: Role, kind: SchemaKind) -> dict[str, Any]:
    """Esquema de la respuesta de un papel, de `data/schemas/` (PD-11).

    `wire` es el que viaja en `GenerateRequest.schema` hacia el proveedor, sin las palabras clave que
    Anthropic no admite; `local` es el estricto con el que se valida la respuesta (cerrado, 7 tipos,
    `minLength: 1`). Cada llamada lee una copia nueva.
    """
    suffix = ".wire" if kind == "wire" else ""
    text = _resource("schemas", f"{role}{suffix}.v1.json").read_text(encoding="utf-8")
    schema: dict[str, Any] = load_json_text(text)
    return schema


def judge_payload(turns: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """El documento JSON del juez: los turnos con `n`, `hablante`, `estado` (si lo tienen) y `texto`
    (BR3.1). No lleva la página ni nada más de la entrada."""
    sent: list[dict[str, Any]] = []
    for turn in turns:
        item: dict[str, Any] = {"n": turn["n"], "hablante": turn["hablante"]}
        if "estado" in turn:
            item["estado"] = turn["estado"]
        item["texto"] = turn["texto"]
        sent.append(item)
    return {"turnos": sent}


def verifier_payload(candidate: Mapping[str, Any], *, permuted: bool) -> dict[str, Any]:
    """El documento JSON del verificador: solo `hecho`, `tipo` y las dos citas con su turno, en ese
    orden (BR3.3); nunca las observaciones del juez. Con `permuted`, las citas van intercambiadas."""
    quotes = [
        {"cita": candidate[name]["cita"], "turno": candidate[name]["turno"]}
        for name in ("cita_a", "cita_b")
    ]
    if permuted:
        quotes.reverse()
    return {
        "hecho": candidate["hecho"],
        "tipo": candidate["tipo"],
        "cita_a": quotes[0],
        "cita_b": quotes[1],
    }


def build_messages(role: Role, payload: Mapping[str, Any]) -> list[Message]:
    """`system` fijo del papel y `user` con el JSON del documento (PD-6).

    Es la única función que arma mensajes: el testimonio nunca entra en `system`.
    """
    user = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return [Message("system", load_system_prompt(role)), Message("user", user)]
