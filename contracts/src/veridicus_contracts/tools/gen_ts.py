"""Constantes TypeScript `as const` generadas desde los contratos (D9, §4.14 de NFR Design).

Escribe en `contracts/ts/generated/` los catálogos que la consola importa como paquete local en
lugar de copiarlos: el catálogo de `code` de errores, los rótulos de resultado, el vocabulario
prohibido (C8) y las listas de §4.6 de `checks/auth_surface.py` (roles, rutas públicas, operaciones
que encolan y extensiones cerradas). No genera los tipos de C1: eso es `openapi-typescript` (T20).

La salida es determinista en bytes: UTF-8 sin BOM y finales de línea LF. Sin argumentos escribe los
archivos (y crea la carpeta si falta); con `--check` compara sin escribir y sale con código 1 si
algo difiere o falta. Los archivos ajenos de la carpeta (los de `openapi-typescript`) no se tocan.
Código 2: un contrato no se pudo leer.

Uso: `python -m veridicus_contracts.tools.gen_ts [--check]`.
"""

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from veridicus_contracts.checks import auth_surface
from veridicus_contracts.loaders import LoadError, load_file
from veridicus_contracts.tools._comparar import diferencia, leer_si_existe

CODIGO_VERDE = 0
CODIGO_DIFIERE = 1
CODIGO_ILEGIBLE = 2

CARPETA = "ts/generated"
ERRORES = "errors/error-codes.v2.yaml"
ROTULOS = "ui/result-labels.v2.yaml"
VOCABULARIO = "integrity/forbidden-vocabulary.v2.yaml"


def _literal(valor: Any) -> str:
    """Un valor JSON como literal de TypeScript (UTF-8, sin escapar los acentos)."""
    return json.dumps(valor, ensure_ascii=False)


def _cabecera(fuente: str) -> str:
    return (
        f"// Generado por veridicus_contracts.tools.gen_ts; no editar a mano. Fuente: {fuente}.\n"
        "// Regenerar: uv run --frozen --directory contracts python -m veridicus_contracts.tools.gen_ts\n"
    )


def _lista(nombre: str, tipo: str | None, valores: Iterable[Any]) -> str:
    cuerpo = "".join(f"  {_literal(v)},\n" for v in valores)
    texto = f"\nexport const {nombre} = [\n{cuerpo}] as const;\n"
    if tipo is not None:
        texto += f"\nexport type {tipo} = (typeof {nombre})[number];\n"
    return texto


def _objeto(nombre: str, pares: Iterable[tuple[str, Any]]) -> str:
    cuerpo = "".join(f"  {_literal(k)}: {_literal(v)},\n" for k, v in pares)
    return f"\nexport const {nombre} = {{\n{cuerpo}}} as const;\n"


def _errores(catalogo: Mapping[str, Any]) -> str:
    codigos = catalogo["codes"]
    http = sorted((c, e["status"]) for c, e in codigos.items() if e.get("http") is True)
    return (
        _cabecera(ERRORES)
        + _lista("ERROR_CODES", "ErrorCode", sorted(codigos))
        + _objeto("ERROR_STATUS", http)
    )


def _rotulos(catalogo: Mapping[str, Any]) -> str:
    return (
        _cabecera(ROTULOS)
        + _lista("RESULT_LABEL_KEYS", "ResultLabelKey", sorted(catalogo["labels"]))
        + _objeto("RESULT_LABELS", sorted(catalogo["labels"].items()))
    )


def _vocabulario(catalogo: Mapping[str, Any]) -> str:
    return (
        _cabecera(VOCABULARIO)
        + _lista("FORBIDDEN_TERMS", None, catalogo["terms"])
        + _lista("FORBIDDEN_SCHEMA_CATEGORIES", None, catalogo["categories_forbidden_in_schemas"])
        + _lista("QUOTE_DELIMITERS", None, catalogo["match"]["quote_delimiters"])
        + _plegado(catalogo["match"]["fold"])
    )


def _plegado(fold: Mapping[str, Any]) -> str:
    """El plegado de C8 (`match.fold`): la consola (U8) escanea igual que U11 sin copiar la regla."""
    return (
        f"\nexport const FOLD_NORMALIZATION = {_literal(fold['normalization'])} as const;\n"
        f"\nexport const FOLD_COMPATIBILITY_SCOPE = {_literal(fold['compatibility_scope'])} as const;\n"
        f"\nexport const FOLD_CASE ={_literal(fold['case'])} as const;\n"
        + _lista("FOLD_DROPPED_CATEGORIES", None, fold["dropped_categories"])
        + _lista("FOLD_DROPPED_CODE_POINTS", None, fold["dropped_code_points"])
    )


def _superficie() -> str:
    publicas = sorted(auth_surface.PUBLICAS)
    cuerpo = "".join(f"  {{ method: {_literal(m)}, path: {_literal(r)} }},\n" for m, r in publicas)
    return (
        _cabecera("checks/auth_surface.py")
        + _lista("ROLES", "Role", auth_surface.ROLES)
        + f"\nexport const PUBLIC_OPERATIONS = [\n{cuerpo}] as const;\n"
        + _lista("ENQUEUING_OPERATION_IDS", None, sorted(auth_surface.ENCOLAN))
        + _lista("VERIDICUS_EXTENSIONS", None, sorted(auth_surface.EXTENSIONES))
        + f"\nexport const CSRF_HEADER = {_literal(auth_surface.PARAMETRO_CSRF)} as const;\n"
        + f"\nexport const CSRF_MIN_LENGTH = {auth_surface.LONGITUD_MINIMA_CSRF} as const;\n"
    )


def generar(raiz: Path) -> dict[str, bytes]:
    """Nombre de archivo -> bytes de cada constante generada. Lanza `LoadError` u `OSError`."""
    textos = {
        "auth-surface.ts": _superficie(),
        "error-codes.ts": _errores(load_file(raiz / ERRORES)),
        "forbidden-vocabulary.ts": _vocabulario(load_file(raiz / VOCABULARIO)),
        "result-labels.ts": _rotulos(load_file(raiz / ROTULOS)),
    }
    return {nombre: texto.encode("utf-8") for nombre, texto in textos.items()}


def _raiz_de_contracts() -> Path:
    # tools/ -> veridicus_contracts/ -> src/ -> contracts/
    return Path(__file__).resolve().parents[3]


def main(argumentos: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida."""
    analizador = argparse.ArgumentParser(prog="gen_ts", description=__doc__)
    analizador.add_argument("--check", action="store_true", help="compara sin escribir")
    analizador.add_argument("--root", type=Path, default=None, help="carpeta contracts/")
    analizador.add_argument("--output-dir", type=Path, default=None, help="carpeta de salida")
    leidos = analizador.parse_args(list(sys.argv[1:] if argumentos is None else argumentos))
    raiz = leidos.root or _raiz_de_contracts()
    carpeta: Path = leidos.output_dir or raiz / CARPETA
    try:
        generados = generar(raiz)
    except (LoadError, OSError) as error:
        print(f"gen_ts: no se pudo leer un contrato: {error}", file=sys.stderr)
        return CODIGO_ILEGIBLE
    if not leidos.check:
        carpeta.mkdir(parents=True, exist_ok=True)
        for nombre, contenido in generados.items():
            (carpeta / nombre).write_bytes(contenido)
        print(f"gen_ts: escritos {len(generados)} archivos")
        return CODIGO_VERDE
    problemas = [
        linea
        for nombre, contenido in generados.items()
        for linea in diferencia(nombre, contenido, leer_si_existe(carpeta / nombre))
    ]
    if problemas:
        print("\n".join(problemas))
        return CODIGO_DIFIERE
    print(f"gen_ts: {len(generados)} archivos al día")
    return CODIGO_VERDE


if __name__ == "__main__":
    sys.exit(main())
