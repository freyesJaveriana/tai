"""Compuerta de auditoría de `pip-audit` (§4.13 paso 3 de NFR Design, NFRD-U1-11).

`pip-audit` no filtra por severidad, así que la compuerta es más estricta que `HIGH`+: lee el JSON
que escribe `pip-audit --format json` y la lista de excepciones, y sale con código 0 solo si no
queda ninguna vulnerabilidad **con `fix_versions` no vacío** fuera de una excepción vigente.

`contracts/.pip-audit-ignore.yaml` tiene la forma `excepciones: [{id, motivo, caduca}]`, con `caduca`
una fecha `AAAA-MM-DD` entre comillas. Una excepción vencida es un fallo (aunque ya no haga falta),
igual que una mal formada o con una clave desconocida. Una excepción cubre una vulnerabilidad por
su `id` o por cualquiera de sus `aliases`. Los mensajes nombran el paquete y el ID, nunca la
descripción de la vulnerabilidad.

Códigos de salida: 0 verde; 1 hay vulnerabilidades sin excepción vigente o la lista de excepciones
no es válida o está vencida; 2 el informe o la lista no se pueden leer. Si la carpeta del informe se
llama `build` y no existe, se crea (paso 1 del plan).

Uso: `python -m veridicus_contracts.tools.audit_gate build/pip-audit.json --ignore .pip-audit-ignore.yaml`.
"""

import argparse
import re
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, NamedTuple

from veridicus_contracts.checks._openapi import objeto
from veridicus_contracts.loaders import LoadError, load_file

CODIGO_VERDE = 0
CODIGO_FALLA = 1
CODIGO_ILEGIBLE = 2

CLAVES_DE_EXCEPCION = frozenset({"id", "motivo", "caduca"})
# `schema_version` es la versión que BR1.1 (guardia E-28 de T18) exige a todo contrato propio.
CLAVES_DE_RAIZ = frozenset({"schema_version", "excepciones"})
VERSION_SEMANTICA = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class Excepcion(NamedTuple):
    """Una excepción vigente o vencida de `.pip-audit-ignore.yaml`."""

    id: str
    motivo: str
    caduca: date


class InsumoIlegible(ValueError):
    """El informe o la lista de excepciones no existe o no se puede interpretar."""


class ExcepcionesInvalidas(ValueError):
    """La lista de excepciones se leyó, pero no tiene la forma exigida."""

    def __init__(self, problemas: list[str]) -> None:
        super().__init__("; ".join(problemas))
        self.problemas = problemas


def _excepcion(posicion: int, elemento: Any) -> tuple[Excepcion | None, list[str]]:
    donde = f"excepción {posicion}"
    if not isinstance(elemento, dict):
        return None, [f"{donde}: debe ser un objeto con id, motivo y caduca"]
    problemas = [
        f"{donde}: clave desconocida {clave!r}"
        for clave in sorted(set(elemento) - CLAVES_DE_EXCEPCION)
    ]
    for clave in ("id", "motivo"):
        valor = elemento.get(clave)
        if not (isinstance(valor, str) and valor.strip()):
            problemas.append(f"{donde}: {clave} falta o no es un texto no vacío")
    caduca = elemento.get("caduca")
    fecha: date | None = None
    if isinstance(caduca, str) and FECHA.fullmatch(caduca):
        try:
            fecha = date.fromisoformat(caduca)
        except ValueError:
            fecha = None
    if fecha is None:
        problemas.append(f"{donde}: caduca falta o no es una fecha AAAA-MM-DD válida")
    if problemas or fecha is None:
        return None, problemas
    return Excepcion(str(elemento["id"]), str(elemento["motivo"]), fecha), []


def cargar_excepciones(ruta: Path) -> list[Excepcion]:
    """Las excepciones de la lista; `InsumoIlegible` si no se lee, `ExcepcionesInvalidas` si no es válida."""
    try:
        documento = load_file(ruta)
    except (LoadError, OSError) as error:
        raise InsumoIlegible(
            f"no se pudo leer la lista de excepciones {ruta.name}: {error}"
        ) from error
    if (
        not isinstance(documento, dict)
        or "excepciones" not in documento
        or not set(documento) <= CLAVES_DE_RAIZ
    ):
        raise ExcepcionesInvalidas(
            [f"{ruta.name}: la raíz debe ser un objeto con excepciones y, si acaso, schema_version"]
        )
    version = documento.get("schema_version", "1.0.0")
    if not (isinstance(version, str) and VERSION_SEMANTICA.fullmatch(version)):
        raise ExcepcionesInvalidas([f"{ruta.name}: schema_version debe ser MAYOR.MENOR.PARCHE"])
    lista = documento["excepciones"]
    if not isinstance(lista, list):
        raise ExcepcionesInvalidas([f"{ruta.name}: excepciones debe ser una lista"])
    excepciones: list[Excepcion] = []
    problemas: list[str] = []
    for posicion, elemento in enumerate(lista):
        excepcion, de_elemento = _excepcion(posicion, elemento)
        problemas.extend(de_elemento)
        if excepcion is not None:
            excepciones.append(excepcion)
    if problemas:
        raise ExcepcionesInvalidas([f"{ruta.name}: {problema}" for problema in problemas])
    return excepciones


def leer_informe(ruta: Path) -> list[dict[str, Any]]:
    """Las dependencias del JSON de `pip-audit`; `InsumoIlegible` si no se lee o no tiene su forma."""
    try:
        documento = load_file(ruta)
    except (LoadError, OSError) as error:
        raise InsumoIlegible(f"no se pudo leer el informe {ruta.name}: {error}") from error
    dependencias = objeto(documento).get("dependencies")
    if not isinstance(dependencias, list) or not all(isinstance(d, dict) for d in dependencias):
        raise InsumoIlegible(f"el informe {ruta.name} no trae la lista dependencies de pip-audit")
    for dependencia in dependencias:
        vulns = dependencia.get("vulns", [])
        if not isinstance(vulns, list) or not all(isinstance(v, dict) for v in vulns):
            raise InsumoIlegible(
                f"el informe {ruta.name} trae vulns que no es una lista de objetos"
            )
    return list(dependencias)


def evaluar(
    dependencias: Sequence[dict[str, Any]], excepciones: Sequence[Excepcion], hoy: date
) -> list[str]:
    """Los problemas de la compuerta con las excepciones y la fecha dadas (vacía si es verde)."""
    problemas = [
        f"excepción vencida: {e.id} caducó el {e.caduca.isoformat()}"
        for e in excepciones
        if e.caduca < hoy
    ]
    vigentes = {e.id for e in excepciones if e.caduca >= hoy}
    for dependencia in dependencias:
        paquete = str(dependencia.get("name"))
        for vulnerabilidad in dependencia.get("vulns", []):
            if not vulnerabilidad.get("fix_versions"):
                continue
            identificadores = {
                str(vulnerabilidad.get("id")),
                *map(str, vulnerabilidad.get("aliases") or []),
            }
            if not identificadores & vigentes:
                problemas.append(
                    f"{paquete}: {vulnerabilidad.get('id')} tiene versión corregida y ninguna excepción vigente"
                )
    return problemas


def main(argumentos: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida."""
    analizador = argparse.ArgumentParser(prog="audit_gate", description=__doc__)
    analizador.add_argument("informe", type=Path, help="JSON de pip-audit")
    analizador.add_argument(
        "--ignore", type=Path, required=True, help="lista de excepciones (YAML)"
    )
    leidos = analizador.parse_args(list(sys.argv[1:] if argumentos is None else argumentos))
    informe: Path = leidos.informe
    if informe.parent.name == "build" and not informe.parent.exists():
        informe.parent.mkdir(parents=True)
    try:
        dependencias = leer_informe(informe)
        excepciones = cargar_excepciones(leidos.ignore)
    except InsumoIlegible as error:
        print(f"audit_gate: {error}", file=sys.stderr)
        return CODIGO_ILEGIBLE
    except ExcepcionesInvalidas as error:
        print("\n".join(f"audit_gate: {problema}" for problema in error.problemas))
        return CODIGO_FALLA
    problemas = evaluar(dependencias, excepciones, datetime.now(UTC).date())
    if problemas:
        print("\n".join(f"audit_gate: {problema}" for problema in problemas))
        return CODIGO_FALLA
    print("audit_gate: ninguna vulnerabilidad con corrección fuera de una excepción vigente")
    return CODIGO_VERDE


if __name__ == "__main__":
    sys.exit(main())
