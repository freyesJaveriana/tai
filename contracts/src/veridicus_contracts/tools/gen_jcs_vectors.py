"""Vectores de la huella JCS `contracts/fixtures/jcs-vectors.json` (§4.14, NFR10.15).

Genera 200 objetos sintéticos con los números límite (`1e21`, `-0`, `5e-324`, `0.1`), claves Unicode
y anidamiento, cada uno con el SHA-256 esperado de `canonical.sha256_jcs`. Las dos mitades
(Python y TypeScript) recalculan cada huella; una sola diferencia pone las dos suites en rojo.

Los primeros vectores son fijos (los números límite y las claves Unicode) y el resto sale de un
`random.Random` con semilla fija, usando solo `random()` y `getrandbits()`, cuyas secuencias no
cambian entre versiones de Python. Así dos corridas dan los mismos bytes, en cualquier proceso
(P-T19-4: Hypothesis no daba los mismos 200 vectores desde `python -m` y desde `pytest`).

Sin argumentos escribe el archivo (y crea su carpeta); con `--check` compara sin escribir y sale con
código 1 si difiere o falta.

Uso: `python -m veridicus_contracts.tools.gen_jcs_vectors [--check]`.
"""

import argparse
import json
import math
import random
import struct
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from veridicus_contracts.canonical import canonical_bytes, sha256_jcs
from veridicus_contracts.tools._comparar import diferencia, leer_si_existe

CODIGO_VERDE = 0
CODIGO_DIFIERE = 1

SALIDA = "fixtures/jcs-vectors.json"
VERSION = "1.0.0"
SEMILLA = 20261124
CANTIDAD = 200
ENTERO_SEGURO = 2**53 - 1  # RFC 8785 solo admite enteros que un número IEEE 754 representa exacto
PROFUNDIDAD_MAXIMA = 3
INTENTOS_MAXIMOS = 20000

# Vectores fijos: los cuatro números límite, claves Unicode (también fuera del plano básico, cuyo
# orden JCS es por unidades UTF-16) y anidamiento.
FIJOS: tuple[dict[str, Any], ...] = (
    {"limite": 1e21},
    {"limite": -0.0},
    {"limite": 5e-324},
    {"limite": 0.1},
    {"números": [1e21, -0.0, 5e-324, 0.1, 1e-7, 123456789012345680000.0]},
    {"ñ": 1, "é": 2, "z": 3, "a": 4, "\U0001f600": 5, "€": 6},
    {"anidado": {"a": {"b": [1, {"c": [None, True, False, "é"]}]}}},
)
FLOTANTES_NOTABLES = (
    1e21,
    -0.0,
    5e-324,
    0.1,
    1e-7,
    1e-6,
    1e300,
    -1.7976931348623157e308,
    4.35,
    0.30000000000000004,
    9007199254740993.0,
    123456789012345680000.0,
)
# Rangos de puntos de código: controles, ASCII, Latín, griego, cirílico, símbolos, y planos altos.
RANGOS = (
    (0x00, 0x1F),
    (0x20, 0x7E),
    (0xA0, 0x24F),
    (0x370, 0x3FF),
    (0x400, 0x4FF),
    (0x2000, 0x20FF),
    (0x4E00, 0x4E7F),
    (0x1F300, 0x1F64F),
    (0x20000, 0x2002F),
)


def _entero(azar: random.Random, tope: int) -> int:
    """Un entero en `[0, tope)` desde `getrandbits`, con rechazo para no sesgarlo."""
    bits = max(1, (tope - 1).bit_length())
    while True:
        candidato = azar.getrandbits(bits)
        if candidato < tope:
            return candidato


def _texto(azar: random.Random, largo_maximo: int, minimo: int = 0) -> str:
    largo = minimo + _entero(azar, largo_maximo - minimo + 1)
    caracteres = []
    for _ in range(largo):
        desde, hasta = RANGOS[_entero(azar, len(RANGOS))]
        caracteres.append(chr(desde + _entero(azar, hasta - desde + 1)))
    return "".join(caracteres)


def _flotante(azar: random.Random) -> float:
    if _entero(azar, 3) == 0:
        return FLOTANTES_NOTABLES[_entero(azar, len(FLOTANTES_NOTABLES))]
    if _entero(azar, 2) == 0:
        # La escala sale de analizar un literal (redondeo exacto), no de una potencia de libm.
        return (azar.random() - 0.5) * float(f"1e{_entero(azar, 41) - 20}")
    while True:  # cualquier patrón de bits IEEE 754 que sea finito
        valor: float = struct.unpack("<d", azar.getrandbits(64).to_bytes(8, "little"))[0]
        if math.isfinite(valor):
            return valor


def _entero_json(azar: random.Random) -> int:
    clase = _entero(azar, 4)
    if clase == 0:
        return _entero(azar, 21) - 10
    if clase == 1:
        return ENTERO_SEGURO if _entero(azar, 2) else -ENTERO_SEGURO
    signo = 1 if _entero(azar, 2) else -1
    return signo * azar.getrandbits(1 + _entero(azar, 53))


def _valor(azar: random.Random, profundidad: int) -> Any:
    clases = 7 if profundidad < PROFUNDIDAD_MAXIMA else 5
    clase = _entero(azar, clases)
    if clase == 0:
        return None
    if clase == 1:
        return bool(_entero(azar, 2))
    if clase == 2:
        return _entero_json(azar)
    if clase == 3:
        return _flotante(azar)
    if clase == 4:
        return _texto(azar, 12)
    if clase == 5:
        return [_valor(azar, profundidad + 1) for _ in range(_entero(azar, 5))]
    return _objeto(azar, profundidad + 1, 0)


def _objeto(azar: random.Random, profundidad: int, minimo: int) -> dict[str, Any]:
    cantidad = minimo + _entero(azar, 5 - minimo)
    return {_texto(azar, 8, 1): _valor(azar, profundidad) for _ in range(cantidad)}


def generar() -> dict[str, Any]:
    """El documento de vectores: 200 objetos distintos con su SHA-256 esperado."""
    azar = random.Random(SEMILLA)  # noqa: S311  # motivo: vectores sintéticos reproducibles, no es criptografía
    vistos: set[bytes] = set()
    vectores: list[dict[str, Any]] = []
    candidatos = iter(FIJOS)
    for _ in range(INTENTOS_MAXIMOS):
        candidato = next(candidatos, None)
        if candidato is None:
            candidato = _objeto(azar, 0, 1)
        forma = canonical_bytes(candidato)
        if forma in vistos:
            continue
        vistos.add(forma)
        vectores.append(
            {"id": f"vec-{len(vectores) + 1:03d}", "value": candidato, "sha256": sha256_jcs(candidato)}
        )
        if len(vectores) == CANTIDAD:
            return {"schema_version": VERSION, "seed": SEMILLA, "vectors": vectores}
    raise RuntimeError(f"solo se obtuvieron {len(vectores)} vectores distintos de {CANTIDAD}")


def serializar(documento: Mapping[str, Any]) -> bytes:
    """Los bytes del archivo: JSON con claves ordenadas, sangría de 2, UTF-8 sin BOM y un salto final."""
    return (json.dumps(documento, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _raiz_de_contracts() -> Path:
    # tools/ -> veridicus_contracts/ -> src/ -> contracts/
    return Path(__file__).resolve().parents[3]


def main(argumentos: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida."""
    analizador = argparse.ArgumentParser(prog="gen_jcs_vectors", description=__doc__)
    analizador.add_argument("--check", action="store_true", help="compara sin escribir")
    analizador.add_argument("--output", type=Path, default=None, help="archivo de vectores")
    leidos = analizador.parse_args(list(sys.argv[1:] if argumentos is None else argumentos))
    destino: Path = leidos.output or _raiz_de_contracts() / SALIDA
    generado = serializar(generar())
    if not leidos.check:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(generado)
        print(f"gen_jcs_vectors: escrito {destino.name}")
        return CODIGO_VERDE
    problemas = diferencia(destino.name, generado, leer_si_existe(destino))
    if problemas:
        print("\n".join(problemas))
        return CODIGO_DIFIERE
    print(f"gen_jcs_vectors: {destino.name} está al día")
    return CODIGO_VERDE


if __name__ == "__main__":
    sys.exit(main())
