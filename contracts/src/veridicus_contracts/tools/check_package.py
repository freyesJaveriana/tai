"""Paso del paquete en entorno limpio (security-design §4.16, functional-spec F9, BR12.1, BR12.3).

Uso: `python -m veridicus_contracts.tools.check_package [ruta-de-contracts]`. Hace, en este orden, y
para en el primer fallo con un mensaje que nombra el paso y la ruta:

1. construye con `uv build` la rueda y el `sdist` en un directorio temporal (D15);
2. compara la lista de la rueda con la tabla de rutas de functional-spec §1 (falla si falta un
   esquema o catálogo, o si aparece `fixtures/`, `tests/`, `.env*`, `*.pem` o `*.key`);
3. crea un entorno nuevo con `uv venv` e instala la rueda (aquí hay red, solo para las dependencias);
4. ejecuta en ese entorno, con `python -I` y `socket.socket` sustituido por una función que falla,
   un guion que importa `veridicus_contracts`, lee cada dato de la tabla con `importlib.resources`,
   valida sin red los *fixtures* de C7, C1 y C19 (que recibe por ruta: no van en la rueda) contra su
   `expectation` y comprueba que la forma antigua de referencia no se resuelve (BR12.3, E36).

La tabla de rutas no se escribe dos veces: se deriva de la configuración de la rueda en
`pyproject.toml` (`sources` y `force-include`), que `tests/test_package_map.py` fija contra el árbol.
`subprocess` se admite solo aquí (E-19, §4.2), con listas de argumentos fijas y sin `shell`.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, NamedTuple

PAQUETE = "veridicus_contracts"
CODIGO_CORRECTO = 0
CODIGO_PASO_FALLIDO = 1
CODIGO_USO = 2

DIRECTORIOS_PROHIBIDOS = frozenset({"fixtures", "tests"})
SUFIJOS_PROHIBIDOS = (".pem", ".key")
PREFIJO_PROHIBIDO = ".env"

PLAZO_CONSTRUCCION_S = 90
PLAZO_ENTORNO_S = 30
PLAZO_INSTALACION_S = 90
PLAZO_GUION_S = 30

MENSAJE_SOCKET = "socket bloqueado por check_package: este paso no usa la red"

# Se antepone a todo guion: `ssl` se importa antes porque hereda de `socket.socket` al cargarse.
PREAMBULO = f"""\
import socket
import ssl

def _socket_bloqueado(*args, **kwargs):
    raise RuntimeError({MENSAJE_SOCKET!r})

socket.socket = _socket_bloqueado
"""

# Guion del paso 4. argv[1]: la tabla de rutas en JSON; argv[2]: la carpeta contracts/ del
# repositorio, solo para leer los fixtures. Termina con SystemExit y un mensaje si algo no cuadra.
GUION = """\
import importlib.resources
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT202012

import veridicus_contracts
from veridicus_contracts.loaders import load_file
from veridicus_contracts.registry import BASE_URI, build_registry, validator_for

tabla = json.loads(sys.argv[1])
raiz_fixtures = Path(sys.argv[2])
raiz = importlib.resources.files("veridicus_contracts")
print("importa veridicus_contracts sin Redis, Kubernetes ni base de datos")


def archivos_de(carpeta):
    for entrada in sorted(carpeta.iterdir(), key=lambda e: e.name):
        if entrada.is_dir():
            yield from archivos_de(entrada)
        else:
            yield entrada


for directorio in tabla["directorios"]:
    # transcript/ es un directorio reservado que solo trae su .gitkeep (vacio): se lee igual.
    leidos = [a.read_bytes() for a in archivos_de(raiz / directorio)]
    if not leidos:
        raise SystemExit(f"importlib.resources: sin archivos en veridicus_contracts/{directorio}")
for archivo in tabla["archivos"]:
    if not (raiz / archivo).read_bytes():
        raise SystemExit(f"importlib.resources: vacio veridicus_contracts/{archivo}")
print(f"lee cada dato de la tabla: {len(tabla['directorios'])} directorios y "
      f"{len(tabla['archivos'])} archivos")


def fixtures(carpeta, patron):
    archivos = sorted((raiz_fixtures / carpeta).glob(patron))
    if not archivos:
        raise SystemExit(f"sin fixtures en {raiz_fixtures / carpeta}")
    return [load_file(a) for a in archivos]


def comparar(contrato, validador, lista):
    for f in lista:
        aceptado = not list(validador.iter_errors(f["payload"]))
        if aceptado != (f["expectation"] == "accept"):
            raise SystemExit(
                f"{contrato}: {f['fixture_id']} tiene expectation {f['expectation']} y "
                f"{'se acepto' if aceptado else 'se rechazo'}"
            )
    print(f"{contrato}: {len(lista)} fixtures coinciden con su expectation")


registro = build_registry()
sugerencias = fixtures("integrity/fixtures/review-suggestion", "*.yaml")
comparar("C7", validator_for(registro, BASE_URI + "veridicus/contracts/integrity/review-suggestion/v2"),
         sugerencias)
uri_c1 = BASE_URI + "_documentos/api/console.v2.yaml"
con_c1 = registro.with_resource(
    uri_c1,
    Resource.from_contents(
        load_file(raiz / "api" / "console.v2.yaml"), default_specification=DRAFT202012
    ),
)
comparar("C1", validator_for(con_c1, uri_c1 + "#/components/schemas/ReviewSuggestion"), sugerencias)
comparar("C19", validator_for(registro, BASE_URI + "veridicus/contracts/cli/report.schema.v2"),
         fixtures("cli/fixtures", "*.json"))

antigua = Draft202012Validator(
    {"$ref": "contracts/analyzer/v1/salida.schema.json#/$defs/cita"},
    registry=registro,
    format_checker=Draft202012Validator.FORMAT_CHECKER,
)
try:
    list(antigua.iter_errors({}))
except Unresolvable:
    print("forma antigua contracts/analyzer/v1/salida.schema.json#/$defs/cita: no se resuelve")
else:
    raise SystemExit("la forma antigua de referencia se resolvio (BR12.3)")

if socket.socket is not _socket_bloqueado:
    raise SystemExit("socket.socket dejo de estar bloqueado")
print("socket bloqueado hasta el final")
"""


class PasoFallido(Exception):
    """Un paso falló: nombra el paso, la ruta y el motivo."""

    def __init__(self, paso: str, ruta: str, motivo: str) -> None:
        super().__init__(f"{paso}: {ruta}: {motivo}")
        self.paso = paso
        self.ruta = ruta
        self.motivo = motivo


class TablaDeRutas(NamedTuple):
    """Datos que la rueda debe traer, con la ruta relativa a `veridicus_contracts/`."""

    directorios: tuple[str, ...]
    archivos: tuple[str, ...]


def tabla_de_rutas(configuracion: dict[str, Any]) -> TablaDeRutas:
    """Deriva la tabla de rutas de `[tool.hatch.build.targets.wheel]` de `pyproject.toml`."""
    try:
        rueda = configuracion["tool"]["hatch"]["build"]["targets"]["wheel"]
        fuentes: dict[str, str] = rueda["sources"]
        sueltos: dict[str, str] = rueda["force-include"]
    except (KeyError, TypeError) as error:
        raise PasoFallido(
            "derivar la tabla de rutas", "pyproject.toml", f"falta la configuración {error}"
        ) from error
    prefijo = f"{PAQUETE}/"
    directorios = tuple(
        destino.removeprefix(prefijo) for origen, destino in fuentes.items() if origen != "src"
    )
    archivos = tuple(destino.removeprefix(prefijo) for destino in sueltos.values())
    return TablaDeRutas(directorios, archivos)


def _es_prohibida(nombre: str) -> bool:
    partes = nombre.split("/")
    return (
        any(parte in DIRECTORIOS_PROHIBIDOS for parte in partes)
        or partes[-1].startswith(PREFIJO_PROHIBIDO)
        or partes[-1].endswith(SUFIJOS_PROHIBIDOS)
    )


def comparar_rueda(nombres: Iterable[str], tabla: TablaDeRutas) -> list[str]:
    """Problemas de la lista de la rueda frente a la tabla de rutas; vacía si es correcta."""
    lista = list(nombres)
    existentes = set(lista)
    problemas: list[str] = []
    for directorio in tabla.directorios:
        prefijo = f"{PAQUETE}/{directorio}/"
        # `transcript/` solo trae su `.gitkeep` (directorio reservado): cuenta como presente.
        if not any(n.startswith(prefijo) and not n.endswith("/") for n in lista):
            problemas.append(f"falta el dato {prefijo.rstrip('/')} en la rueda")
    for archivo in tabla.archivos:
        if f"{PAQUETE}/{archivo}" not in existentes:
            problemas.append(f"falta el dato {PAQUETE}/{archivo} en la rueda")
    problemas.extend(f"ruta prohibida en la rueda: {n}" for n in lista if _es_prohibida(n))
    return problemas


def nombres_de_rueda(rueda: Path) -> list[str]:
    """Rutas de los archivos que trae la rueda."""
    try:
        with zipfile.ZipFile(rueda) as archivo:
            return archivo.namelist()
    except (OSError, zipfile.BadZipFile) as error:
        raise PasoFallido("leer la rueda", str(rueda), str(error)) from error


def _uv() -> str:
    uv = shutil.which("uv")
    if uv is None:
        raise PasoFallido("buscar uv", "PATH", "uv no está en PATH")
    return uv


def _correr(
    paso: str, ruta: str, comando: Sequence[str], plazo_s: int
) -> subprocess.CompletedProcess[str]:
    """Corre un comando de argumentos fijos, sin shell; el plazo vencido es un paso fallido."""
    try:
        return subprocess.run(  # noqa: S603  # motivo: lista de argumentos fija, sin shell ni entrada externa (E-19, §4.2)
            list(comando), capture_output=True, text=True, check=False, timeout=plazo_s
        )
    except subprocess.TimeoutExpired as error:
        raise PasoFallido(paso, ruta, f"superó el plazo de {plazo_s} s") from error
    except OSError as error:
        raise PasoFallido(paso, ruta, str(error)) from error


def _exigir(
    paso: str, ruta: str, comando: Sequence[str], plazo_s: int
) -> subprocess.CompletedProcess[str]:
    resultado = _correr(paso, ruta, comando, plazo_s)
    if resultado.returncode != 0:
        raise PasoFallido(paso, ruta, (resultado.stdout + resultado.stderr).strip())
    return resultado


def construir(
    contracts: Path, salida: Path, *, offline: bool = False, solo_rueda: bool = False
) -> Path:
    """`uv build` de `contracts/` en `salida`; devuelve la ruta de la rueda (y deja el `sdist`)."""
    comando = [_uv(), "build"]
    if solo_rueda:
        comando.append("--wheel")
    if offline:
        comando.append("--offline")
    comando += ["--directory", str(contracts), "--out-dir", str(salida)]
    _exigir("uv build", str(contracts), comando, PLAZO_CONSTRUCCION_S)
    ruedas = sorted(salida.glob("*.whl"))
    if len(ruedas) != 1:
        raise PasoFallido("uv build", str(salida), f"se esperaba una rueda y hay {len(ruedas)}")
    if not solo_rueda and not list(salida.glob("*.tar.gz")):
        raise PasoFallido("uv build", str(salida), "no produjo el sdist")
    return ruedas[0]


def crear_entorno(directorio: Path) -> Path:
    """`uv venv` nuevo en `directorio`; devuelve su intérprete."""
    _exigir(
        "uv venv",
        str(directorio),
        [_uv(), "venv", "--python", sys.executable, str(directorio)],
        PLAZO_ENTORNO_S,
    )
    for relativa in ("bin/python", "Scripts/python.exe"):
        python = directorio / relativa
        if python.is_file():
            return python
    raise PasoFallido("uv venv", str(directorio), "el entorno no tiene intérprete")


def instalar(python: Path, rueda: Path) -> None:
    """Instala la rueda en el entorno (aquí hay red, solo para las dependencias)."""
    _exigir(
        "instalar la rueda",
        str(rueda),
        [_uv(), "pip", "install", "--python", str(python), str(rueda)],
        PLAZO_INSTALACION_S,
    )


def ejecutar_guion(
    python: str | Path, guion: str, argumentos: Sequence[str]
) -> subprocess.CompletedProcess[str]:
    """Corre `guion` con `python -I` y `socket.socket` bloqueado; no exige código 0."""
    comando = [str(python), "-I", "-c", PREAMBULO + guion, *argumentos]
    return _correr("guion del paquete instalado", str(python), comando, PLAZO_GUION_S)


def _leer_tabla(contracts: Path) -> TablaDeRutas:
    pyproject = contracts / "pyproject.toml"
    try:
        configuracion = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise PasoFallido("derivar la tabla de rutas", str(pyproject), str(error)) from error
    return tabla_de_rutas(configuracion)


def _paso(numero: int, texto: str) -> None:
    print(f"paso {numero}: {texto}", flush=True)


def verificar(contracts: Path) -> None:
    """Corre los cuatro pasos sobre `contracts/`; lanza `PasoFallido` en el primer fallo."""
    tabla = _leer_tabla(contracts)
    with tempfile.TemporaryDirectory(prefix="check_package_") as temporal:
        base = Path(temporal)
        _paso(1, "uv build de la rueda y el sdist")
        rueda = construir(contracts, base / "dist")
        _paso(2, f"lista de {rueda.name} contra la tabla de rutas")
        problemas = comparar_rueda(nombres_de_rueda(rueda), tabla)
        if problemas:
            raise PasoFallido("comparar la rueda", str(rueda), "; ".join(problemas))
        _paso(3, "entorno limpio con uv venv e instalación de la rueda")
        python = crear_entorno(base / "entorno")
        instalar(python, rueda)
        _paso(4, "guion con python -I y socket bloqueado")
        argumentos = [json.dumps(tabla._asdict()), str(contracts)]
        resultado = ejecutar_guion(python, GUION, argumentos)
        if resultado.returncode != 0:
            raise PasoFallido(
                "guion del paquete instalado",
                str(python),
                (resultado.stdout + resultado.stderr).strip(),
            )
        print(resultado.stdout, end="")


def main(argumentos: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida."""
    argv = list(sys.argv[1:] if argumentos is None else argumentos)
    if len(argv) > 1:
        print("uso: python -m veridicus_contracts.tools.check_package [contracts]", file=sys.stderr)
        return CODIGO_USO
    contracts = Path(argv[0]) if argv else Path(__file__).resolve().parents[3]
    inicio = time.monotonic()
    try:
        verificar(contracts)
    except PasoFallido as error:
        print(f"check_package: {error}", file=sys.stderr)
        return CODIGO_PASO_FALLIDO
    print(f"check_package: correcto en {time.monotonic() - inicio:.1f} s")
    return CODIGO_CORRECTO


if __name__ == "__main__":
    sys.exit(main())
