"""Comparación en bytes de un archivo generado con el que está en disco (U01-T19).

Ayuda común de las herramientas que generan archivos versionados (`security_surface`, `gen_ts`,
`gen_jcs_vectors`): solo compara y arma el texto de la diferencia; nunca escribe.
"""

import difflib
from pathlib import Path

LINEAS_DE_DIFERENCIA = 60


def diferencia(nombre: str, generado: bytes, en_disco: bytes | None) -> list[str]:
    """Las líneas de la diferencia entre lo versionado y lo regenerado; vacía si son iguales."""
    if en_disco is None:
        return [f"{nombre}: el archivo no existe; genérelo con la opción de escritura"]
    if en_disco == generado:
        return []
    lineas = list(
        difflib.unified_diff(
            en_disco.decode("utf-8", errors="replace").splitlines(),
            generado.decode("utf-8", errors="replace").splitlines(),
            fromfile=f"{nombre} (versionado)",
            tofile=f"{nombre} (regenerado)",
            lineterm="",
            n=1,
        )
    )
    if not lineas:  # misma lista de líneas: difiere solo en finales de línea o en el último salto
        return [f"{nombre}: difiere solo en finales de línea o en el salto final"]
    recortadas = lineas[:LINEAS_DE_DIFERENCIA]
    if len(lineas) > LINEAS_DE_DIFERENCIA:
        recortadas.append(f"... {len(lineas) - LINEAS_DE_DIFERENCIA} líneas más")
    return [f"{nombre}: difiere de lo regenerado", *recortadas]


def leer_si_existe(ruta: Path) -> bytes | None:
    """Los bytes del archivo, o `None` si no existe."""
    try:
        return ruta.read_bytes()
    except FileNotFoundError:
        return None
