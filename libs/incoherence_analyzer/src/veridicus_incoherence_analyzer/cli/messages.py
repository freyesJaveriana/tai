"""Catálogo cerrado de mensajes de la CLI, en español (BR11.7).

stderr y `AVISO.txt` nunca llevan texto de testimonio: solo estos textos fijos, con rutas, números,
nombres de ajustes y el texto del aviso de VE-01. Cada mensaje de este catálogo declara sus campos
(`FIELDS`) y `render` rechaza un campo que el mensaje no declara; una prueba con un *canary* sembrado
en un turno comprueba que no aparece en nada de lo que escribe la CLI.

Los detalles de los errores tipados de las bibliotecas (por ejemplo, «falta la variable de entorno
VERIDICUS_ANTHROPIC_API_KEY» o «la entrada no cumple el esquema C6 de entrada en /turnos/0/n»)
nombran el ajuste o la ruta del campo y nunca un valor ni el texto: así los definen sus módulos. Se
acotan en `detail` por si algún día uno no lo cumple.
"""

from collections.abc import Mapping
from typing import Final

# Códigos de salida (BR11.3). El 1 es de argparse al fallar un argumento y aquí no se usa: un
# argumento inválido es 2. El 6 es de `evaluate` y no existe en B11a.
EXIT_OK: Final = 0
EXIT_INPUT: Final = 2
EXIT_CONFIG: Final = 3
EXIT_INCIDENT: Final = 4
EXIT_UNEXPECTED: Final = 5

MAX_DETAIL: Final = 240

MESSAGES: Final[Mapping[str, str]] = {
    "notice": "Aviso de propósito limitado (versión {version}):\n{text}",
    "warning.same_family": (
        "Aviso same_family: el juez y el verificador de este perfil son de la misma familia de "
        "modelos; es un perfil de demostración y no sirve para medir."
    ),
    "warning.other": "Aviso del perfil: {id}.",
    "arguments": "Argumentos no válidos: {detail}",
    "input.missing": "No existe la entrada: {path}",
    "input.empty_directory": "El directorio de entrada no tiene archivos .json: {path}",
    "input.unreadable": "No se pudo leer el archivo de entrada: {path}",
    "input.not_json": "El archivo de entrada no es un JSON válido: {path}",
    "input.not_object": "El archivo de entrada no es un objeto JSON: {path}",
    "input.rejected": "La entrada no se puede analizar ({path}): {detail}",
    "input.limit": "La entrada supera un límite configurado ({path}): {detail}",
    "config.rejected": "La configuración no permite arrancar: {detail}",
    "config.profile_input": "El perfil no admite esta entrada ({path}): {detail}",
    "output.not_writable": "No se puede escribir en el directorio de salida: {path}",
    "output.corpus_tracked": (
        "Una transcripción de origen corpus solo se analiza si Git no puede rastrear el "
        "directorio de salida: {path}"
    ),
    "output.write_failed": "No se pudo escribir un archivo de salida: {path}",
    "run.written": "Salida escrita: {path}",
    "run.incident": (
        "Incidente de anonimización: el lote se detuvo y solo se escribió la salida en error: {path}"
    ),
    "run.incident_interrupted": (
        "Incidente de anonimización durante una interrupción: el lote se detuvo y se escribió la "
        "salida en error del incidente: {path}"
    ),
    "run.interrupted": "Interrupción: la corrida en curso quedó sin salida.",
    "run.interrupted_after_output": (
        "Interrupción tras escribir la última salida: las salidas ya escritas se conservan."
    ),
    "run.unexpected": "Error inesperado ({kind}). No se escribió ninguna salida parcial.",
}

FIELDS: Final[Mapping[str, frozenset[str]]] = {
    "notice": frozenset({"version", "text"}),
    "warning.other": frozenset({"id"}),
    "arguments": frozenset({"detail"}),
    "input.missing": frozenset({"path"}),
    "input.empty_directory": frozenset({"path"}),
    "input.unreadable": frozenset({"path"}),
    "input.not_json": frozenset({"path"}),
    "input.not_object": frozenset({"path"}),
    "input.rejected": frozenset({"path", "detail"}),
    "input.limit": frozenset({"path", "detail"}),
    "config.rejected": frozenset({"detail"}),
    "config.profile_input": frozenset({"path", "detail"}),
    "output.not_writable": frozenset({"path"}),
    "output.corpus_tracked": frozenset({"path"}),
    "output.write_failed": frozenset({"path"}),
    "run.written": frozenset({"path"}),
    "run.incident": frozenset({"path"}),
    "run.incident_interrupted": frozenset({"path"}),
    "run.unexpected": frozenset({"kind"}),
}


def detail(error: BaseException) -> str:
    """El mensaje de un error tipado de las bibliotecas, en una línea y acotado."""
    flat = " ".join(str(error).split())
    return flat if len(flat) <= MAX_DETAIL else flat[: MAX_DETAIL - 1] + "…"


def render(key: str, **fields: object) -> str:
    """El mensaje `key` con sus campos; un campo no declarado o ausente es un error del código."""
    declared = FIELDS.get(key, frozenset())
    if set(fields) != declared:
        raise KeyError(f"campos del mensaje {key}: {sorted(fields)} en vez de {sorted(declared)}")
    return MESSAGES[key].format(**{name: str(value) for name, value in fields.items()})


def warning_text(identifier: str) -> str:
    """El texto de un aviso del perfil por su identificador (por ejemplo `same_family`)."""
    key = f"warning.{identifier}"
    if key in MESSAGES and not FIELDS.get(key):
        return render(key)
    return render("warning.other", id=identifier)
