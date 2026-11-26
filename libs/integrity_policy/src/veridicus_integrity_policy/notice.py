"""Aviso de propósito limitado de VE-01 (BR9.5).

Estado: *stub* del paso 1 (U11-T01). Lo implementa U11-T02.

Costura de las pruebas: `cli.composition` lo llama como `notice.load_notice()`, por el nombre del
módulo, para que una prueba lo sustituya con `monkeypatch` (igual que `api.load_catalogs` en U10).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Notice:
    """El aviso con su versión, tal como están en `contracts/integrity/notice.v1.yaml`."""

    version: str
    text: str


def load_notice() -> Notice:
    """Lee el aviso del archivo versionado de C8, sin cambiarlo.

    Si el archivo falta o no trae versión, lanza `ConfigInvalidProfileError` (CLI, código 3).
    """
    raise NotImplementedError("load_notice: lo implementa U11-T02 (paso 5)")
