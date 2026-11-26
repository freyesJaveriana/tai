"""Entrada de la CLI (PD-12): `main()` llama a `run(sys.argv[1:], os.environ)`.

Estado: `run` es *stub* del paso 1 (U11-T01); lo implementa U11-T05.
"""

import os
import sys
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


def run(
    argv: Sequence[str],
    env: Mapping[str, str],
    *,
    transport: "httpx.BaseTransport | None" = None,
) -> int:
    """Única entrada que usan las pruebas; devuelve el código de salida (BR11.3).

    `transport` solo llega a `build_anonymizer(env, transport)`: ningún argumento ni variable de
    entorno lo activa (PD-12). Escribe el aviso de VE-01 y los identificadores de los avisos del
    perfil (por ejemplo `same_family`) en stderr y en `AVISO.txt`, y termina con 3 sin ninguna
    llamada si el aviso, el perfil o el anonimizador no están bien (BR9.5, BR10.1). Llama al aviso
    como `notice.load_notice()` y construye el módulo como `api.build_anonymizer(env, transport)`.
    """
    raise NotImplementedError("run: lo implementa U11-T05 (paso 10)")


def main() -> None:
    """Punto de entrada del script `veridicus`."""
    raise SystemExit(run(sys.argv[1:], os.environ))
