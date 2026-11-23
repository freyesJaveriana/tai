"""Validación pura de archivos de perfiles de ejecución (F8, BR9.2 a BR9.5, BR9.8, §4.15).

`validate(data, *, key_prefix, kind)` recibe el documento ya cargado (por los cargadores de
`loaders.py`), no lee archivos, ni el entorno, ni la red. Los esquemas se leen una sola vez, al
importar el módulo, del paquete con `importlib.resources`.

Comprueba, en este orden:

1. el sobre y la forma contra `profile-base.schema.v1.yaml` (`kind="base"`) o contra
   `profiles.schema.v1.yaml`, que además cierra la especialización del analizador
   (`kind="analyzer"`);
2. las referencias cruzadas de los alias, que el esquema no expresa (BR9.2);
3. que cada `api_key_ref` empiece por `key_prefix` (BR9.4).

Cualquier fallo es un `ProfileValidationError` (`config.invalid_profile`) que nombra el perfil, el
papel y el ajuste, y nunca el valor de un ajuste (AUTONOMIA-04, §4.15): los mensajes se arman solo
con nombres de ajustes y con textos fijos, y todo nombre que no tenga una forma segura se
reemplaza por `?`.
"""

import importlib.resources
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Literal
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from veridicus_contracts.loaders import load_file
from veridicus_contracts.registry import BASE_URI

CODE = "config.invalid_profile"

_ESQUEMAS = {
    "base": "profile-base.schema.v1.yaml",
    "analyzer": "profiles.schema.v1.yaml",
}
_NOMBRE_SEGURO = re.compile(r"[A-Za-z0-9_.\-]{1,64}")
_PREFIJO_VALIDO = re.compile(r"[A-Z][A-Z0-9_]*")

# Texto fijo por palabra clave del esquema; ninguno incluye el valor de la instancia.
_MOTIVOS = {
    "required": "falta el ajuste obligatorio",
    "additionalProperties": "ajuste no permitido",
    "unevaluatedProperties": "ajuste no permitido",
    "minProperties": "debe tener al menos un elemento",
    "pattern": "no cumple la forma exigida",
    "format": "formato no válido",
    "minimum": "valor por debajo del mínimo",
    "enum": "valor fuera de los permitidos",
    "const": "valor distinto del exigido",
    "type": "tipo incorrecto",
}


class ProfileValidationError(ValueError):
    """Un archivo de perfiles no es válido; el servicio no arranca y la CLI no llama (AC13.3.1)."""

    code = CODE

    def __init__(self, problems: tuple[str, ...]) -> None:
        super().__init__("perfil no válido: " + "; ".join(problems))
        self.problems = problems


def _recurso(nombre: str) -> tuple[str, Resource[Any]]:
    carpeta = importlib.resources.files("veridicus_contracts") / "profiles"
    documento = load_file(carpeta / nombre)
    uri = urljoin(BASE_URI, documento["$id"])
    return uri, Resource.from_contents(documento, default_specification=DRAFT202012)


def _construir() -> dict[str, Draft202012Validator]:
    recursos = {nombre: _recurso(nombre) for nombre in _ESQUEMAS.values()}
    registro: Registry[Any] = Registry().with_resources(list(recursos.values()))
    return {
        kind: Draft202012Validator(
            {"$ref": recursos[nombre][0]},
            registry=registro,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )
        for kind, nombre in _ESQUEMAS.items()
    }


_VALIDADORES = _construir()


def _seguro(nombre: object) -> str:
    """El nombre de un ajuste si tiene una forma segura; si no, `?` (nunca un valor)."""
    texto = str(nombre)
    return texto if _NOMBRE_SEGURO.fullmatch(texto) else "?"


def _problema(perfil: object, papel: object, ajuste: object, motivo: str) -> str:
    return (
        f"perfil {_seguro(perfil)}, papel {_seguro(papel)}, ajuste {_seguro(ajuste)}: {motivo}"
    )


def _del_esquema(error: ValidationError) -> str:
    """Perfil, papel, ajuste y motivo de un error del esquema, sin el valor de la instancia."""
    ruta = list(error.absolute_path)
    perfil = ruta[1] if len(ruta) > 1 else "-"
    papel = ruta[3] if len(ruta) > 3 and ruta[2] == "roles" else "-"
    if len(ruta) > 2 and ruta[2] == "fallback_provider":
        papel = "fallback_provider"
    # Los nombres salen de las claves de la instancia y del esquema, nunca del texto del mensaje
    # de jsonschema, que puede citar una clave de forma engañosa (F-01).
    instancia: Any = error.instance
    if error.validator == "required":
        exigidos: Any = error.validator_value
        faltan = [nombre for nombre in exigidos if nombre not in instancia]
        ajuste = ", ".join(_seguro(nombre) for nombre in faltan)
    elif error.validator in ("additionalProperties", "unevaluatedProperties"):
        esquema: Any = error.schema
        declarados = esquema.get("properties", {})
        sobran = sorted((clave for clave in instancia if clave not in declarados), key=str)
        ajuste = ", ".join(_seguro(nombre) for nombre in sobran)
    else:
        ajuste = _seguro(ruta[-1] if ruta else "-")
    motivo = _MOTIVOS.get(str(error.validator), "no cumple el esquema")
    return f"perfil {_seguro(perfil)}, papel {_seguro(papel)}, ajuste {ajuste}: {motivo}"


def _referencias(nombre: str, perfil: Mapping[str, Any]) -> list[str]:
    """Referencias cruzadas de los alias (BR9.2)."""
    roles = perfil["roles"]
    alias = perfil.get("role_aliases", {})
    problemas: list[str] = []
    for nombre_alias, destino in alias.items():
        if nombre_alias in roles:
            problemas.append(
                _problema(nombre, nombre_alias, "role_aliases", "el alias tiene el nombre de un papel")
            )
        if destino in alias:
            problemas.append(
                _problema(nombre, nombre_alias, "role_aliases", "el alias apunta a otro alias")
            )
        elif destino not in roles:
            problemas.append(
                _problema(nombre, nombre_alias, "role_aliases", "el alias apunta a un papel que no existe")
            )
    return problemas


def _claves(nombre: str, perfil: Mapping[str, Any], prefijo: str) -> list[str]:
    """Cada `api_key_ref` empieza por el prefijo que recibe la función (BR9.4)."""
    destinos = list(perfil["roles"].items())
    alterno = perfil.get("fallback_provider")
    if alterno is not None:
        destinos.append(("fallback_provider", alterno))
    return [
        _problema(nombre, papel, "api_key_ref", "no cumple el prefijo exigido")
        for papel, destino in destinos
        if "api_key_ref" in destino and not destino["api_key_ref"].startswith(prefijo)
    ]


def _congelar(valor: Any) -> Any:
    """Copia inmutable: los objetos como `MappingProxyType` y las listas como tuplas."""
    if isinstance(valor, dict):
        return MappingProxyType({clave: _congelar(contenido) for clave, contenido in valor.items()})
    if isinstance(valor, list):
        return tuple(_congelar(contenido) for contenido in valor)
    return valor


def validate(
    data: Any,
    *,
    key_prefix: str,
    kind: Literal["base", "analyzer"],
) -> Mapping[str, Mapping[str, Any]]:
    """Valida un archivo de perfiles ya cargado y devuelve sus perfiles como valores inmutables.

    `key_prefix` es obligatorio y sin valor por omisión (BR9.4, BR9.8): Veridicus pasa
    `VERIDICUS_`. `kind` es `"base"` (perfil genérico, abierto) o `"analyzer"` (además, la
    especialización cerrada del analizador). Lanza `ProfileValidationError`
    (`config.invalid_profile`) con el perfil, el papel y el ajuste que fallan.
    """
    if not isinstance(key_prefix, str) or not _PREFIJO_VALIDO.fullmatch(key_prefix):
        raise ProfileValidationError(("key_prefix debe ser un texto como VERIDICUS_",))
    if kind not in _VALIDADORES:
        raise ProfileValidationError(("kind debe ser base o analyzer",))
    errores = sorted(_VALIDADORES[kind].iter_errors(data), key=lambda e: e.json_path)
    if errores:
        raise ProfileValidationError(tuple(dict.fromkeys(_del_esquema(e) for e in errores)))
    problemas: list[str] = []
    for nombre, perfil in data["profiles"].items():
        problemas.extend(_referencias(nombre, perfil))
        problemas.extend(_claves(nombre, perfil, key_prefix))
    if problemas:
        raise ProfileValidationError(tuple(problemas))
    return _congelar(data["profiles"])  # type: ignore[no-any-return]  # motivo: _congelar devuelve Any por ser recursiva
