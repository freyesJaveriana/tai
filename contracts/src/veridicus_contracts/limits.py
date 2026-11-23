"""Carga de las cifras efectivas de C25: el entorno solo baja (BR11.1, §4.15, NFRD-U1-09).

Módulo guardia (100 % de ramas). `load(environ)` es una función pura: no lee `os.environ`, no
abre archivos y no escribe; recibe el mapa de variables. El catálogo empaquetado
(`limits.v1.yaml`) se lee una sola vez, al importar, y es siempre el techo: una variable
`VERIDICUS_LIMIT_<NOMBRE>` solo puede bajar una cifra, nunca subirla.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from importlib.resources import files
from typing import Any

from veridicus_contracts.loaders import load_file

PREFIJO = "VERIDICUS_LIMIT_"
UNIDADES_DECIMALES = frozenset({"ratio", "s"})

# Sin ceros a la izquierda, signo ni exponente; la longitud acotada evita el tope de dígitos de int.
_ENTERO = re.compile(r"[1-9][0-9]{0,18}")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,18})(?:\.[0-9]{1,18})?")


class LimitsConfigError(ValueError):
    """Una cifra de límite del entorno o del catálogo no es válida: el servicio no arranca."""

    code = "config.invalid_limit"


def _leer_catalogo() -> dict[str, Any]:
    catalogo: dict[str, Any] = load_file(files("veridicus_contracts") / "limits.v1.yaml")
    return catalogo


# Una sola lectura, al importar (§4.15).
_CATALOGO = _leer_catalogo()


def relaciones_rotas(
    valores: Mapping[str, float], relaciones: Iterable[Sequence[str]]
) -> list[str]:
    """Las relaciones `[a, op, b]` (`<` o `<=`) que no se cumplen con estos valores."""
    rotas: list[str] = []
    for izquierda, operador, derecha in relaciones:
        cumple = (
            valores[izquierda] < valores[derecha]
            if operador == "<"
            else valores[izquierda] <= valores[derecha]
        )
        if not cumple:
            rotas.append(
                f"relación rota: {izquierda} ({valores[izquierda]}) {operador} "
                f"{derecha} ({valores[derecha]})"
            )
    return rotas


def _convertir(variable: str, unidad: str, texto: str) -> int | float:
    """El valor de una variable según la unidad del límite; si no es válido, `LimitsConfigError`."""
    if unidad in UNIDADES_DECIMALES:
        if not _DECIMAL.fullmatch(texto) or float(texto) <= 0:
            raise LimitsConfigError(f"{variable}: debe ser un número decimal mayor que 0")
        numero = float(texto)
        return int(numero) if numero.is_integer() else numero
    if not _ENTERO.fullmatch(texto):
        raise LimitsConfigError(f"{variable}: debe ser un entero mayor o igual que 1")
    return int(texto)


def load(environ: Mapping[str, str]) -> dict[str, int | float]:
    """Las cifras efectivas: el catálogo con las variables `VERIDICUS_LIMIT_<NOMBRE>` aplicadas.

    Rechaza con `LimitsConfigError` (`config.invalid_limit`) una variable que sube la cifra,
    que nombra un límite inexistente (también un nombre mal escrito), con un valor inválido
    para su unidad, o que deja rota una relación del catálogo.
    """
    limites: dict[str, dict[str, Any]] = _CATALOGO["limits"]
    efectivos: dict[str, int | float] = {nombre: e["value"] for nombre, e in limites.items()}
    por_variable = {PREFIJO + nombre.upper(): nombre for nombre in limites}
    for variable in sorted(environ):
        if not variable.startswith(PREFIJO):
            continue
        nombre = por_variable.get(variable)
        if nombre is None:
            raise LimitsConfigError(f"{variable}: no es un límite del catálogo")
        valor = _convertir(variable, limites[nombre]["unit"], environ[variable])
        if valor > efectivos[nombre]:
            raise LimitsConfigError(
                f"{variable}: sube la cifra de {efectivos[nombre]} a {valor}; solo se puede bajar"
            )
        efectivos[nombre] = valor
    rotas = relaciones_rotas(efectivos, _CATALOGO["relations"])
    if rotas:
        raise LimitsConfigError("; ".join(rotas))
    return efectivos
