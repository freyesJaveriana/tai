"""Tipos del contrato común del analizador (C6, contrato 1.0.0) que usan las interfaces en proceso.

`Hallazgo` y `Cita` repiten las propiedades de `$defs/hallazgo` y `$defs/cita` de
`analyzer/v1/salida.schema.json`, con sus nombres en español y sin alias (CD-05, FD-U1-04). El
esquema manda: una prueba exige que las claves sean exactamente las del esquema. Este módulo
convive con el directorio de datos `analyzer/v1/` bajo el mismo nombre, igual que `model_calls.py`
con `model_calls/` (K-12); no lleva `__init__.py` en `analyzer/` para no tapar los datos.
"""

from typing import Literal, NotRequired, TypedDict

HallazgoTipo = Literal["fecha", "numero", "lugar", "persona", "negacion", "secuencia", "otro"]
CitaAviso = Literal["turno_entrevistador", "turno_plegado"]


class Cita(TypedDict):
    """Una cita literal con su turno; la página falta si el turno no la tiene."""

    cita: str
    turno: str
    pagina: NotRequired[int]
    avisos: NotRequired[list[CitaAviso]]


class Hallazgo(TypedDict):
    """Una contradicción con sus dos citas verificadas; sin ellas no sale (AUTONOMIA-05)."""

    id: str
    hecho: str
    tipo: HallazgoTipo
    actos: NotRequired[list[str]]
    cita_a: Cita
    cita_b: Cita
    observaciones: str
