"""Detección de entidades (BR1.2, BR1.5, BR1.7).

STUB de U10-T02: lo implementa U10-T03 (paso 7). `masking` llama a estas funciones por atributo de
módulo (`detection.apply_rules(...)`), no con `from ... import`, para que las pruebas rojas
puedan sustituirlas con `monkeypatch`.
"""

from dataclasses import dataclass

from veridicus_anonymizer.domain.catalogs import Catalogs


@dataclass(frozen=True)
class DetectedSpan:
    """Tramo `[start, end)` de un valor de texto que un detector marcó."""

    start: int
    end: int
    category: str
    source: str


def apply_rules(text: str, catalogs: Catalogs) -> list[DetectedSpan]:
    """Tramos que marcan las reglas de `DetectionRuleSet`."""
    raise NotImplementedError("apply_rules lo implementa U10-T03")


def safety_net(text: str, catalogs: Catalogs) -> list[DetectedSpan]:
    """Red de seguridad `ENTIDAD` (PD-2): se aplica a `user` y `assistant`, nunca a `system`."""
    raise NotImplementedError("safety_net lo implementa U10-T03")
