"""Guardia de las condiciones de C7 (functional-spec FD-U1-13, E35; security-design §4.8, NFR11.5).

C7 debe declarar las cuatro condiciones `if/then` de BR4.4, exigir que `note` y `reformulation`
no estén vacías (`minLength`), y llevar un *fixture* negativo por cada una de las seis. Quitar una condición del esquema, o su *fixture*, deja la suite en rojo. Solo lee.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

from veridicus_contracts.loaders import LoadError, load_file

C7 = "integrity/review-suggestion.v2.json"
DIRECTORIO_DE_FIXTURES = "integrity/fixtures/review-suggestion"
REGLA = "BR4.4"


class Condicion(NamedTuple):
    """Una condición de BR4.4 y el *fixture* negativo que la ejerce."""

    nombre: str
    estado: str
    fixture: str
    campo: str
    presente: bool  # el fixture negativo trae el campo (pending) o le falta (resto)
    vacio: bool = False  # la condición es «no vacío»: el fixture trae el campo con "" (BR4.4)

    def exigencia(self) -> str:
        """Lo que el fixture negativo debe hacer con su campo."""
        if self.vacio:
            return f"traer {self.campo} vacío"
        return f"{'traer' if self.presente else 'no traer'} {self.campo}"

    def cumple(self, carga: Mapping[str, Any]) -> bool:
        """La carga del fixture negativo ejerce la condición."""
        if self.vacio:
            return carga.get(self.campo) == ""
        return (self.campo in carga) == self.presente


CONDICIONES = (
    Condicion("pending_sin_decision", "pending", "pending-con-decided-at.yaml", "decided_at", True),
    Condicion("decidida_con_quien", "accepted", "accepted-sin-decided-by.yaml", "decided_by", False),
    Condicion("dismissed_con_nota", "dismissed", "dismissed-sin-note.yaml", "note", False),
    Condicion("edited_con_reformulacion", "edited", "edited-sin-reformulation.yaml", "reformulation", False),
    Condicion("note_no_vacia", "dismissed", "dismissed-note-vacia.yaml", "note", True, True),
    Condicion(
        "reformulation_no_vacia", "edited", "edited-reformulation-vacia.yaml", "reformulation", True, True
    ),
)


def _bloque(esquema: Mapping[str, Any], estado: str) -> Mapping[str, Any]:
    """El `if/then/else` de `allOf` cuyo `if` es `state == estado`; vacío si no está."""
    for bloque in esquema.get("allOf", []):
        const = bloque.get("if", {}).get("properties", {}).get("state", {}).get("const")
        if const == estado:
            return dict(bloque)
    return {}


def _requeridos(nodo: Any) -> set[str]:
    return set(nodo.get("required", [])) if isinstance(nodo, Mapping) else set()


def _prohibidos(nodo: Any) -> set[str]:
    """Campos que `not: {anyOf: [{required: [x]}, ...]}` prohíbe."""
    if not isinstance(nodo, Mapping):
        return set()
    ramas = nodo.get("not", {}).get("anyOf", [])
    return {campo for rama in ramas for campo in _requeridos(rama)}


def _declara(esquema: Mapping[str, Any], condicion: Condicion) -> bool:
    if condicion.nombre == "pending_sin_decision":
        return _prohibidos(_bloque(esquema, "pending").get("then")) == {"decided_by", "decided_at"}
    if condicion.nombre == "decidida_con_quien":
        return _requeridos(_bloque(esquema, "pending").get("else")) == {"decided_by", "decided_at"}
    if condicion.vacio:
        propiedad = esquema.get("properties", {}).get(condicion.campo, {})
        return bool(propiedad.get("minLength", 0) >= 1)
    return condicion.campo in _requeridos(_bloque(esquema, condicion.estado).get("then"))


def _problemas_del_fixture(condicion: Condicion, fixture: Any) -> list[str]:
    nombre = condicion.nombre
    if not isinstance(fixture, Mapping) or not isinstance(fixture.get("payload"), Mapping):
        return [f"{nombre}: el fixture {condicion.fixture} no es un fixture con payload"]
    problemas: list[str] = []
    if fixture.get("expectation") != "reject" or fixture.get("reject_reason") != REGLA:
        problemas.append(f"{nombre}: {condicion.fixture} debe rechazarse con reject_reason {REGLA}")
    carga = fixture["payload"]
    if carga.get("state") != condicion.estado:
        problemas.append(f"{nombre}: {condicion.fixture} debe tener state {condicion.estado}")
    if not condicion.cumple(carga):
        problemas.append(f"{nombre}: {condicion.fixture} debe {condicion.exigencia()}")
    return problemas


def comprobar_documentos(
    esquema: Mapping[str, Any], fixtures: Mapping[str, Any]
) -> list[str]:
    """Problemas de C7 y de sus *fixtures* negativos (por nombre de archivo); vacío si todo está."""
    problemas: list[str] = []
    for condicion in CONDICIONES:
        if not _declara(esquema, condicion):
            problemas.append(f"{condicion.nombre}: C7 no declara la condición de {REGLA}")
        if condicion.fixture not in fixtures:
            problemas.append(f"{condicion.nombre}: falta el fixture negativo {condicion.fixture}")
        else:
            problemas.extend(_problemas_del_fixture(condicion, fixtures[condicion.fixture]))
    return problemas


def comprobar(raiz: Path) -> list[str]:
    """Lee C7 y los fixtures negativos bajo `raiz` (la carpeta `contracts/`) y los comprueba."""
    try:
        esquema = load_file(raiz / C7)
    except (LoadError, OSError) as error:
        return [f"C7 ilegible o ausente: {error}"]
    if not isinstance(esquema, Mapping):
        return ["C7 no es un objeto JSON"]
    fixtures: dict[str, Any] = {}
    for condicion in CONDICIONES:
        ruta = raiz / DIRECTORIO_DE_FIXTURES / condicion.fixture
        if ruta.is_file():
            try:
                fixtures[condicion.fixture] = load_file(ruta)
            except LoadError as error:
                fixtures[condicion.fixture] = f"ilegible: {error}"
    return comprobar_documentos(esquema, fixtures)
