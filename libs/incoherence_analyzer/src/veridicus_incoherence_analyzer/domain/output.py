"""Armado de la salida C6 (BR8).

Estado: `build_finding` es *stub* del paso 1 (U11-T01); lo implementa U11-T03.

Costura de las pruebas (BR8.1): `application.analyze` arma cada hallazgo llamando a
`output.build_finding(...)` por el nombre del módulo, para que una prueba lo sustituya con
`monkeypatch` por un armador que deje fuera `observaciones` («un hallazgo armado a propósito sin
observaciones») y compruebe que la salida sustituta es `salida_invalida`, conserva
`registro.llamadas` (BR7.1) y valida contra C6.
"""

from collections.abc import Mapping
from typing import Any


def build_finding(
    finding_id: str, candidate: Mapping[str, Any], turns: Mapping[int, Mapping[str, Any]]
) -> dict[str, Any]:
    """El `hallazgo` de C6 de un candidato que sobrevivió: `id`, los campos del juez y, en cada
    cita, `pagina` y `avisos` tomados de su turno (BR5.7). `turns` va por número `n`."""
    raise NotImplementedError("build_finding: lo implementa U11-T03 (paso 7)")
