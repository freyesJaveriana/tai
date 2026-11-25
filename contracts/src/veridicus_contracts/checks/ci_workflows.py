"""La CI no aplica cambios, no tiene credenciales del clúster y va fijada (security-design §4.11 y §4.13, AUTONOMIA-01).

Módulo guardia (100 % de ramas). Falla si un *workflow* de `.github/workflows/`:

- contiene `--write` (la CI nunca regenera la huella de seguridad), `kubectl apply`, `helm install`,
  `helm upgrade` o credenciales del clúster (`kubeconfig`, `KUBECONFIG`, `KUBE_CONFIG`), también con opciones
  globales entre la herramienta y el verbo (`kubectl -n x apply`). Mira cada línea, también los comentarios: lo
  que un *workflow* nombra, un cambio posterior lo puede activar;
- usa una acción de otro repositorio (`dueño/repo@ref`, `dueño/repo/ruta@ref`) cuyo `ref` no sea un SHA de 40
  caracteres hexadecimales en minúscula, o una `docker://` sin `@sha256:` de 64 caracteres. Una acción local
  (`./…`) no lleva `ref` y pasa (K-70, `team.md`, Deployment);
- no declara `permissions: contents: read` en la raíz, declara en la raíz cualquier valor `write` (P-T22b-2:
  `packages: write` solo va en un *job*), o usa `contents: write` o `write-all` en cualquier otro nivel. Los
  permisos de escritura de otros alcances dentro de un *job* (`packages: write`) no se marcan.

Los permisos se leen con el cargador YAML del paquete; un *workflow* que no carga es un problema, no un salto.
Los mensajes nombran el archivo, la línea cuando se conoce y el término.
"""

import re
from collections.abc import Iterable, Iterator
from pathlib import Path

from veridicus_contracts.loaders import LoadError, load_yaml_text

REGLA = "(AUTONOMIA-01, §4.11, team.md, Deployment)"
# Límites declarados (P-T18-12 y P-T18-16): el análisis es de texto, no de shell.
LIMITACIONES = (
    "una herramienta invocada por una variable o un alias (`$K apply`) no se detecta",
    'un valor de opción entre comillas con espacios (`--namespace "a b"`) no se detecta',
    "que el SHA corresponda de verdad a la versión del comentario necesita red y no se comprueba (K-70)",
)
_ACCION_FIJADA = re.compile(r"[^@\s]+@[0-9a-f]{40}")
_DOCKER_FIJADA = re.compile(r"docker://\S+@sha256:[0-9a-f]{64}")
# Entre la herramienta y el verbo pueden ir opciones globales (`-n x`, `--context=x`, `--namespace x`,
# `--dry-run`, `--`). Cada opción es uno o dos guiones, un nombre cuyo primer carácter no es un guion, y a lo
# sumo un valor tras `=` o un valor tras un espacio que no empieza por guion; o el `--` solo.
#
# Sin solapamiento, para que el motor no retroceda de forma exponencial (F-02 de las rondas 2 y 3):
# - el nombre empieza por `[\w.]` y no por guion, así que `--a` solo se lee como `--` más `a` (antes, `-` más
#   `-a` o `--` más `a`);
# - un valor no puede empezar por guion, así que un `-a` que sigue a una opción solo puede ser una opción;
# - `--` solo no es el prefijo de ninguna otra forma: un nombre exige un carácter tras los guiones y un valor
#   exige `=` o un espacio.
# Cada texto tiene así una sola lectura y la búsqueda es lineal.
_OPCIONES = r"(?:\s+(?:--?[\w.][\w.-]*(?:=\S+|\s+[^\s-]\S*)?|--))*"
PROHIBIDOS = (
    ("--write", re.compile(r"--write\b")),
    ("kubectl apply", re.compile(rf"kubectl{_OPCIONES}\s+apply\b", re.IGNORECASE)),
    ("helm install", re.compile(rf"helm{_OPCIONES}\s+install\b", re.IGNORECASE)),
    ("helm upgrade", re.compile(rf"helm{_OPCIONES}\s+upgrade\b", re.IGNORECASE)),
    ("kubeconfig", re.compile(r"kube_?config", re.IGNORECASE)),
)


def _fijada(valor: str) -> bool:
    if valor.startswith("./"):
        return True
    patron = _DOCKER_FIJADA if valor.startswith("docker://") else _ACCION_FIJADA
    return patron.fullmatch(valor) is not None


def workflows(raiz: Path) -> list[Path]:
    """Los `.yml` y `.yaml` de `.github/workflows/` bajo `raiz`, ordenados."""
    carpeta = raiz / ".github" / "workflows"
    return sorted(carpeta.glob("*.yml")) + sorted(carpeta.glob("*.yaml"))


def scan(paths: Iterable[Path]) -> list[str]:
    """Los comandos prohibidos de cada workflow dado, por archivo y por línea."""
    problemas: list[str] = []
    for ruta in sorted(paths):
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
        for numero, linea in enumerate(lineas, start=1):
            problemas.extend(
                f"{ruta.as_posix()}:{numero}: {termino} no se permite en un workflow {REGLA}"
                for termino, patron in PROHIBIDOS
                if patron.search(linea)
            )
    return problemas


def _usos(nodo: object) -> Iterator[str]:
    """Cada valor de una clave `uses` del documento cargado, en el orden del archivo."""
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            if clave == "uses":
                yield str(valor)
            else:
                yield from _usos(valor)
    elif isinstance(nodo, list):
        for valor in nodo:
            yield from _usos(valor)


def scan_acciones(paths: Iterable[Path]) -> list[str]:
    """Las acciones sin fijar por SHA (o por digest, si son `docker://`) de cada workflow.

    Los `uses` se leen del YAML cargado, así que ninguna forma de escribirlos se escapa (valor en otra línea,
    clave entre comillas, espacio antes de los dos puntos, flujo `{uses: x}`). La línea se busca en el texto
    siguiendo el orden del documento; si no se encuentra, el mensaje va sin línea. Un workflow que no carga lo
    reporta `scan_permisos`.
    """
    problemas: list[str] = []
    for ruta in sorted(paths):
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        try:
            datos = load_yaml_text(texto)
        except LoadError:
            continue
        lineas = texto.splitlines()
        cursor = 0
        for valor in _usos(datos):
            posicion = next((i for i in range(cursor, len(lineas)) if valor in lineas[i]), None)
            if posicion is not None:
                cursor = posicion + 1
            if not _fijada(valor):
                lugar = ruta.as_posix() if posicion is None else f"{ruta.as_posix()}:{posicion + 1}"
                problemas.append(f"{lugar}: acción sin fijar por SHA: {valor} {REGLA}")
    return problemas


def _escritura_en_algun_nivel(nodo: object) -> bool:
    """Si en algún lugar del documento hay `permissions: write-all` o `permissions: {contents: write}`."""
    if isinstance(nodo, dict):
        permisos = nodo.get("permissions")
        if permisos == "write-all" or (
            isinstance(permisos, dict) and permisos.get("contents") == "write"
        ):
            return True
        return any(_escritura_en_algun_nivel(valor) for valor in nodo.values())
    if isinstance(nodo, list):
        return any(_escritura_en_algun_nivel(valor) for valor in nodo)
    return False


def scan_permisos(paths: Iterable[Path]) -> list[str]:
    """Los permisos de cada workflow: raíz `contents: read` y ninguna escritura de contenido en otro nivel."""
    problemas: list[str] = []
    for ruta in sorted(paths):
        try:
            datos = load_yaml_text(ruta.read_text(encoding="utf-8", errors="replace"))
        except LoadError as error:
            problemas.append(f"{ruta.as_posix()}: no se puede cargar: {error} {REGLA}")
            continue
        raiz = datos.get("permissions") if isinstance(datos, dict) else None
        if raiz is None:
            problemas.append(
                f"{ruta.as_posix()}: falta `permissions: contents: read` en la raíz {REGLA}"
            )
        elif not (isinstance(raiz, dict) and raiz.get("contents") == "read"):
            problemas.append(
                f"{ruta.as_posix()}: la raíz declara permisos distintos de `contents: read` {REGLA}"
            )
        elif "write" in raiz.values():
            escrituras = ", ".join(clave for clave, valor in raiz.items() if valor == "write")
            problemas.append(
                f"{ruta.as_posix()}: la raíz declara escritura ({escrituras}); solo un job puede tenerla {REGLA}"
            )
        resto = (
            {clave: valor for clave, valor in datos.items() if clave != "permissions"}
            if isinstance(datos, dict)
            else {}
        )
        if _escritura_en_algun_nivel(resto):
            problemas.append(
                f"{ruta.as_posix()}: `contents: write` o `write-all` no se permite en ningún nivel {REGLA}"
            )
    return problemas


def comprobar(raiz: Path) -> list[str]:
    """Escanea los workflows del repositorio cuya raíz es `raiz`: comandos, acciones y permisos."""
    rutas = workflows(raiz)
    return scan(rutas) + scan_acciones(rutas) + scan_permisos(rutas)
