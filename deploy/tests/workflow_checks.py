"""Reglas estáticas de los workflows de deploy (pasos 8 y 9, DP-07, DP-08).

Los workflows se leen como texto y como YAML; nunca se ejecutan. Cada regla devuelve su motivo y
cada una tiene un control negativo en `deploy/tests/fixtures/workflows/`. Los nombres de las
herramientas del clúster se arman con fragmentos, igual que en `autonomia.py`, para que este archivo
no se dispare a sí mismo cuando la comprobación de AUTONOMIA-01 recorre el repositorio.
"""

import re
import shlex
from typing import Any

import yaml

# Las dos únicas acciones que el repositorio permite, con el SHA que ya usan sus workflows.
ALLOWED_ACTIONS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "astral-sh/setup-uv": "37802adc94f370d6bfd71619e3f0bf239e1f3b78",
}

# Herramientas que la CI descarga con curl: asset y suma SHA-256 de la release (tabla de la tarea).
TOOLS: dict[str, tuple[str, str]] = {
    "kustomize": (
        "kustomize_v5.8.3_linux_amd64.tar.gz",
        "cb9e31198d3f63b44848bd0afc4c8efc56e6cfef9c93a4a39a211940e6decd61",
    ),
    "kubeconform": (
        "kubeconform-linux-amd64.tar.gz",
        "9bc2bffbf71f261128533edaf912153948b7ff238f9a531ae6d34466ec287883",
    ),
    "kyverno": (
        # 1.19.2 y no 1.20: Kyverno 1.20 quitó la ejecución de ClusterPolicy (kyverno.io/v1). K-107.
        "kyverno-cli_v1.19.2_linux_x86_64.tar.gz",
        "357eaf1df8bc24ddd5a73979fadeaae6a032e8710f11af264229756e4956bf4a",
    ),
    "hadolint": (
        "hadolint-linux-x86_64",
        "c7187db94eeeeca956519a6af171adc31453941a1e777961f6e680f697c8c507",
    ),
    "shellcheck": (
        "shellcheck-v0.11.0.linux.x86_64.tar.xz",
        "8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198",
    ),
    "trivy": (
        "trivy_0.76.2_Linux-64bit.tar.gz",
        "bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf",
    ),
}
TOOL_SUMS = frozenset(sha for _, sha in TOOLS.values())

_K = "kube" + "ctl"
_KUBECONFIG = re.compile(r"kube_?config", re.IGNORECASE)
_CLUSTER_CLI = re.compile(rf"(?<![\w-]){_K}(?![\w-])", re.IGNORECASE)
# `latest` como etiqueta de imagen: tras dos puntos, o en cualquier línea de docker que lo nombre.
_LATEST_TAG = re.compile(r":latest\b", re.IGNORECASE)
_DOCKER_LATEST = re.compile(r"\bdocker\b[^\n]*\blatest\b", re.IGNORECASE)
_SHA40 = re.compile(r"[0-9a-f]{40}")
_SUM = re.compile(r"\b[0-9a-f]{64}\b")
_FETCH = re.compile(r"(?<![\w./-])(?:curl|wget)\s")
_VERIFY = re.compile(r"sha256sum\s+(?:--check|-c)\b")
# Lo que ejecuta o desempaqueta lo descargado, al inicio de un comando.
_USE = re.compile(
    r"(?:^|\n|;|&&|\|\|?)\s*(?:sudo\s+)?(?:tar|unzip|chmod|install|bash|sh|python3?|\./\S+)(?:\s|$)"
)
# F-01: la condición de un job con packages: write es esta y ninguna otra. Una condición que solo la
# contiene (`… || always()`, `!cancelled() && …`) puede dejar correr el job en un pull_request.
MAIN_CONDITION = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
# F-01: lo que anula el código de salida de sha256sum -c si va tras él en su línea (o empieza la
# siguiente): un `||`, un `;` o un pipe.
_MASKS_EXIT = re.compile(r"\|\||;|\|")
_NEXT_LINE_MASKS = re.compile(r"\s*(?:\|\||;)")
# F-02: una expresión de Actions se expande antes de que corra el shell, así que dentro de un run
# deja inyectar comandos con un título de pull request o una rama.
_EXPRESSION = re.compile(r"\$\{\{")
# F-06: también `docker buildx build` y `docker image build|push|tag`.
_DOCKER = re.compile(
    r"(?:^|[\s;&|(])docker\s+(buildx\s+build|image\s+(?:build|push|tag)|build|tag|push)\b"
    r"([^\n;&|]*)"
)
# F-05: la verificación de una descarga tiene una forma fija, como línea propia, y no se acepta nada
# distinto (ni `&&`, ni `&`, ni un `if`): con set -e, cualquiera de esas formas deja pasar una suma mala.
_VERIFY_LINE = re.compile(r'echo "\$\{[A-Za-z_][A-Za-z0-9_]*\}  [^"\n]+" \| sha256sum -c -')
_SHA_WORD = re.compile(r"\bsha256sum\b")
_PROLOGUE = "set -euo pipefail"
_RELAXES_SET = re.compile(r"(?:^|[;&|(])\s*set\s+\+")
_OPENS = re.compile(r"\b(?:if|while|until|case|for|select)\b")
_CLOSES = re.compile(r"\b(?:fi|done|esac)\b")
_CHAINED = ("\\", "&&", "||", "|")
# F-07: la plantilla del script de un paso que descarga, línea lógica por línea lógica. Las rutas solo
# admiten letras, cifras y `_ $ / . { } -`: ni comillas, ni paréntesis, ni `;`, `&`, `|`.
# F-10: lo que hace de un paso un paso que descarga, con o sin URL (comentarios aparte).
_DOWNLOADERS = re.compile(
    r"https?://|\bcurl\b|\bwget\b|\bgh\s+release\s+download\b|\burllib\b|\bpip3?\s+download\b"
)
# F-09 y F-10: la variable de la suma, las variables que usa la plantilla y las tres rutas.
_VERIFY_VARIABLE = re.compile(r'echo "\$\{(\w+)\}  ')
_USED_VARIABLE = re.compile(r"\$\{?([A-Za-z_]\w*)")
_BUILTIN_VARIABLES = frozenset({"RUNNER_TEMP", "GITHUB_PATH"})
_CURL_OUT = re.compile(r'curl .*?-o "([^"]+)"')
_VERIFY_PATH = re.compile(r'echo "\$\{\w+\}  ([^"]+)"')
_EXTRACT_SOURCE = re.compile(r'(?:tar -x[zJ]f|mv) "([^"]+)"')
_P = r"[A-Za-z0-9_$/.{}\-]+"
_CURL_LINE = re.compile(rf'curl -fsSL(?: --retry \d+)? -o "{_P}" "https://[A-Za-z0-9._%/$\-]+"')
_TEMPLATE_SET = re.compile(r"set -euo pipefail")
_TEMPLATE_MKDIR = re.compile(rf'mkdir -p "{_P}"')
_TEMPLATE_TAR = re.compile(rf'tar -x[zJ]f "{_P}" -C "{_P}"(?: --strip-components=\d)?')
_TEMPLATE_MV = re.compile(rf'mv "{_P}" "{_P}"')
_TEMPLATE_CHMOD = re.compile(rf'chmod \+x "{_P}"')
_TEMPLATE_PATH = re.compile(rf'echo "{_P}" >> "\$GITHUB_PATH"')
_SEQUENCES = (
    (
        _TEMPLATE_SET,
        _TEMPLATE_MKDIR,
        _CURL_LINE,
        _VERIFY_LINE,
        _TEMPLATE_TAR,
        _TEMPLATE_PATH,
    ),
    (
        _TEMPLATE_SET,
        _TEMPLATE_MKDIR,
        _CURL_LINE,
        _VERIFY_LINE,
        _TEMPLATE_MV,
        _TEMPLATE_CHMOD,
        _TEMPLATE_PATH,
    ),
)
_WHOLE_VAR = re.compile(r"^\$(?:\{(\w+)\}|(\w+))$")
_SHA_EXPRESSION = "${{ github.sha }}"
_SHA_VARIABLE = "GITHUB_SHA"


def _triggers(document: dict[Any, Any]) -> list[str]:
    """Los eventos del workflow. PyYAML lee la clave `on` como el booleano `True`."""
    raw = document.get("on", document.get(True))
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, dict):
        return [str(item) for item in raw]
    return []


def _steps(document: dict[Any, Any]) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    for job_name, job in (document.get("jobs") or {}).items():
        for index, step in enumerate((job or {}).get("steps") or []):
            if isinstance(step, dict):
                found.append((f"{job_name}[{index}]", step))
    return found


def _packages_write(permissions: object) -> bool:
    return isinstance(permissions, dict) and permissions.get("packages") == "write"


def _permission_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    found: list[str] = []
    root = document.get("permissions")
    if not (isinstance(root, dict) and root.get("contents") == "read"):
        found.append(f"{rel}: falta «permissions: contents: read» en el nivel del workflow")
    elif "write" in root.values():
        found.append(f"{rel}: el nivel del workflow declara una escritura; solo un job puede")
    writers = 0
    for name, job in (document.get("jobs") or {}).items():
        permissions = (job or {}).get("permissions")
        if permissions == "write-all" or (
            isinstance(permissions, dict) and permissions.get("contents") == "write"
        ):
            found.append(f"{rel}: el job {name} escribe el contenido del repositorio")
        if not _packages_write(permissions):
            continue
        writers += 1
        condition = str((job or {}).get("if") or "").strip()
        if condition != MAIN_CONDITION:
            found.append(
                f"{rel}: el job {name} tiene packages: write y su if no es exactamente la "
                "condición de push a main (puede correr en un pull_request)"
            )
    if writers > 1:
        found.append(f"{rel}: packages: write en {writers} jobs; solo el que publica puede")
    return found


def _action_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    found: list[str] = []
    for where, step in _steps(document):
        used = step.get("uses")
        if used is None:
            continue
        name, _, ref = str(used).partition("@")
        if not _SHA40.fullmatch(ref):
            found.append(f"{rel}: {where} usa {used}, que no está fijada por un SHA de 40 hex")
        elif name not in ALLOWED_ACTIONS:
            found.append(f"{rel}: {where} usa {name}, que no es una de las dos acciones permitidas")
        elif ALLOWED_ACTIONS[name] != ref:
            found.append(f"{rel}: {where} usa {name} con un SHA distinto del del repositorio")
    return found


def _code(run: str) -> str:
    """El script sin comentarios y con las continuaciones de línea unidas."""
    lines = [line for line in run.splitlines() if not line.lstrip().startswith("#")]
    return re.sub(r"\\\n", " ", "\n".join(lines))


def _code_lines(run: str) -> list[str]:
    return [line.strip() for line in run.splitlines() if line.strip() and not _is_comment(line)]


def _is_comment(line: str) -> bool:
    return line.lstrip().startswith("#")


def _prologue_violations(rel: str, where: str, run: str) -> list[str]:
    """Todo run que descarga empieza por `set -euo pipefail` y nunca lo relaja."""
    lines = _code_lines(run)
    found: list[str] = []
    if not lines or lines[0] != _PROLOGUE:
        found.append(f"{rel}: {where} descarga y su script no empieza por {_PROLOGUE}")
    if any(_RELAXES_SET.search(line) for line in lines):
        found.append(f"{rel}: {where} relaja {_PROLOGUE} con set +")
    return found


def _verify_line_violations(rel: str, where: str, run: str) -> list[str]:
    """Cada línea con sha256sum es exactamente la forma fija y nada la encadena a la anterior."""
    found: list[str] = []
    lines = run.splitlines()
    for number, raw in enumerate(lines):
        line = raw.strip()
        if _is_comment(raw) or not _SHA_WORD.search(line):
            continue
        if not _VERIFY_LINE.fullmatch(line):
            found.append(
                f"{rel}: {where} la verificación no tiene la forma fija "
                'echo "${VAR}  ruta" | sha256sum -c - sola en su línea'
            )
            continue
        previous = _code_lines("\n".join(lines[:number]))[-1:]
        if previous and previous[0].endswith(_CHAINED):
            found.append(
                f"{rel}: {where} la forma fija de la verificación va encadenada a la anterior"
            )
    return found


def _nesting_violations(rel: str, where: str, run: str) -> list[str]:
    """La verificación no va dentro de un if, while, until, case ni for: con set -e no detendría nada."""
    depth = 0
    for line in _code_lines(run):
        if _SHA_WORD.search(line):
            if depth > 0:
                return [f"{rel}: {where} la verificación va dentro de un if, while o until"]
            continue
        depth = max(depth + len(_OPENS.findall(line)) - len(_CLOSES.findall(line)), 0)
    return []


def _logical_lines(run: str) -> tuple[list[str], list[str]]:
    """Las líneas lógicas del script (continuaciones unidas, sin vacías ni comentarios) y los problemas.

    Un comentario que sigue a una continuación con barra la oculta: se informa como problema.
    """
    lines: list[str] = []
    problems: list[str] = []
    pending: str | None = None
    for raw in run.splitlines():
        piece = raw.strip()
        if pending is None and (not piece or piece.startswith("#")):
            continue
        if pending is not None and piece.startswith("#"):
            problems.append("un comentario sigue a una continuación con barra")
        joined = piece if pending is None else f"{pending} {piece}"
        if piece.endswith("\\"):
            pending = joined[:-1].rstrip()
        else:
            lines.append(joined)
            pending = None
    if pending is not None:
        problems.append("el script termina con una continuación con barra")
    return lines, problems


def _template_violations(
    rel: str, where: str, step: dict[str, Any], job: dict[str, Any], run: str
) -> list[str]:
    """F-07: el script de un paso que descarga es exactamente la plantilla y el paso no se salta."""
    found: list[str] = []
    if "continue-on-error" in step or "if" in step or "continue-on-error" in job:
        found.append(f"{rel}: {where} el paso que descarga no puede llevar continue-on-error ni if")
    lines, problems = _logical_lines(run)
    found.extend(f"{rel}: {where} fuera de la plantilla: {problem}" for problem in problems)
    if any("$(" in line or "`" in line for line in lines):
        found.append(f"{rel}: {where} fuera de la plantilla: una sustitución de comandos")
    fits = any(
        len(sequence) == len(lines)
        and all(shape.fullmatch(line) for shape, line in zip(sequence, lines, strict=True))
        for sequence in _SEQUENCES
    )
    if not fits:
        found.append(
            f"{rel}: {where} el script que descarga no sigue la plantilla: set -euo pipefail, "
            "mkdir, curl, la verificación, la extracción y el PATH, en ese orden y sin otras líneas"
        )
    return found


def _download_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    found: list[str] = []
    for job_name, job in (document.get("jobs") or {}).items():
        for index, step in enumerate((job or {}).get("steps") or []):
            if isinstance(step, dict):
                found.extend(
                    _download_step_violations(rel, f"{job_name}[{index}]", step, job, document)
                )
    return found


def _env_keys(source: dict[str, Any]) -> set[str]:
    env = source.get("env")
    return {str(key) for key in env} if isinstance(env, dict) else set()


def _binding_violations(
    rel: str,
    where: str,
    step: dict[str, Any],
    job: dict[str, Any],
    document: dict[Any, Any],
    run: str,
) -> list[str]:
    """F-09 y F-10: la suma, las variables y las rutas de la plantilla están atadas entre sí."""
    lines, _ = _logical_lines(run)
    verify = next((line for line in lines if _VERIFY_LINE.fullmatch(line)), None)
    if verify is None:
        return []  # la plantilla ya lo informa
    found: list[str] = []
    env = step.get("env")
    step_env = {str(key): str(value) for key, value in env.items()} if isinstance(env, dict) else {}
    variable = _VERIFY_VARIABLE.match(verify)
    haystack = run + " " + " ".join(step_env.values())
    tools = [name for name, (asset, _) in TOOLS.items() if asset in haystack]
    if not tools:
        found.append(
            f"{rel}: {where} no identifica la herramienta de la tabla por su asset ni su URL"
        )
    elif len(tools) > 1:
        found.append(
            f"{rel}: {where} nombra más de una herramienta de la tabla: {', '.join(tools)}"
        )
    elif variable is not None and step_env.get(variable.group(1)) != TOOLS[tools[0]][1]:
        found.append(
            f"{rel}: {where} la variable {variable.group(1)} no se define en el env del paso "
            f"con la suma de la tabla de {tools[0]}"
        )
    superior = _env_keys(job) | _env_keys(document)
    used = {name for line in lines for name in _USED_VARIABLE.findall(line)}
    for name in sorted(used):
        if name in superior:
            found.append(
                f"{rel}: {where} la variable {name} se define también en el env del job o del workflow"
            )
        elif name not in step_env and name not in _BUILTIN_VARIABLES:
            found.append(f"{rel}: {where} la variable {name} no está definida en el env del paso")
    paths: set[str] = set()
    for line in lines:
        for pattern in (_CURL_OUT, _VERIFY_PATH, _EXTRACT_SOURCE):
            match = pattern.match(line)
            if match:
                paths.add(match.group(1))
    if len(paths) > 1:
        found.append(
            f"{rel}: {where} la ruta del curl, la de la verificación y la de la extracción "
            "no son la misma cadena"
        )
    return found


def _download_step_violations(
    rel: str, where: str, step: dict[str, Any], job: dict[str, Any], document: dict[Any, Any]
) -> list[str]:
    run = str(step.get("run") or "")
    code = _code(run)
    fetches = [match.start() for match in _FETCH.finditer(code)]
    if not fetches and not _DOWNLOADERS.search(code):
        return []
    found = _template_violations(rel, where, step, job, run)
    found.extend(_binding_violations(rel, where, step, job, document, run))
    if not fetches:
        return found
    found.extend(_prologue_violations(rel, where, run))
    found.extend(_verify_line_violations(rel, where, run))
    found.extend(_nesting_violations(rel, where, run))
    sums = set(_SUM.findall(code + " " + str(step.get("env") or "")))
    if not sums:
        found.append(f"{rel}: {where} descarga con curl y no lleva ninguna suma SHA-256")
    for unknown in sorted(sums - TOOL_SUMS):
        found.append(f"{rel}: {where} usa la suma {unknown[:12]}…, que no es la de la tabla")
    bounds = [*fetches, len(code)]
    for number, start in enumerate(fetches):
        segment = code[start : bounds[number + 1]]
        first_line = segment.split("\n", 1)[0]
        if "|" in first_line:
            found.append(f"{rel}: {where} canaliza la descarga a otro comando")
        verify = _VERIFY.search(segment)
        if verify is None:
            found.append(f"{rel}: {where} no verifica la descarga con sha256sum -c")
        elif _USE.search(segment[: verify.start()]):
            found.append(f"{rel}: {where} usa lo descargado antes de verificarlo")
        else:
            line, _, following = segment[verify.end() :].partition("\n")
            if _MASKS_EXIT.search(line) or _NEXT_LINE_MASKS.match(following):
                found.append(f"{rel}: {where} anula el código de salida de sha256sum")
    return found


def _expression_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    return [
        f"{rel}: {where} lleva una expresión de Actions dentro de un run; va por env"
        for where, step in _steps(document)
        if _EXPRESSION.search(str(step.get("run") or ""))
    ]


def _var_name(text: str) -> str | None:
    match = _WHOLE_VAR.match(text)
    return (match.group(1) or match.group(2)) if match else None


def _ref_problem(ref: str, env: dict[str, str], depth: int = 0) -> str | None:
    """Por qué una referencia de imagen no lleva una etiqueta aceptable; None si la lleva.

    Una referencia sin `:` etiqueta (ni `@sha256:`) es un `latest` implícito. Si es solo una variable
    se mira su definición, y una etiqueta que es una variable debe estar definida con el SHA del commit.
    """
    name = _var_name(ref)
    if name is not None:
        if name not in env or depth > 5:
            return f"{ref} sin etiqueta: la variable no está definida con una referencia"
        return _ref_problem(env[name].strip(), env, depth + 1)
    segment = ref.rsplit("/", 1)[-1]
    if "@sha256:" in segment:
        return None
    tag = segment.partition(":")[2]
    if not tag:
        return f"{ref} sin etiqueta: es un latest implícito"
    tag_name = _var_name(tag)
    if tag == _SHA_EXPRESSION or tag_name == _SHA_VARIABLE:
        return None
    if tag_name is not None and env.get(tag_name, "").strip() != _SHA_EXPRESSION:
        return f"{ref}: la etiqueta {tag} no es el SHA del commit"
    if tag_name is None and "$" in tag:
        # F-06: una etiqueta que contiene una variable junto con otra cosa no viene entera del SHA.
        return f"{ref}: la etiqueta {tag} no viene entera del SHA del commit"
    return None


def _docker_refs(command: str, arguments: str) -> list[str]:
    try:
        words = shlex.split(arguments)
    except ValueError:
        words = arguments.split()
    command = command.split()[-1]
    if command == "build":
        refs = [words[i + 1] for i, word in enumerate(words[:-1]) if word in {"--tag", "-t"}]
        return refs + [word.partition("=")[2] for word in words if word.startswith("--tag=")]
    positional = [word for word in words if not word.startswith("-")]
    return positional[:2] if command == "tag" else positional[:1]


def _image_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    found: list[str] = []
    for job_name, job in (document.get("jobs") or {}).items():
        for index, step in enumerate((job or {}).get("steps") or []):
            if not isinstance(step, dict):
                continue
            env = {
                str(key): str(value)
                for source in (document, job, step)
                for key, value in (source.get("env") or {}).items()
            }
            for match in _DOCKER.finditer(_code(str(step.get("run") or ""))):
                for ref in _docker_refs(match.group(1), match.group(2)):
                    problem = _ref_problem(ref, env)
                    if problem:
                        where = f"{job_name}[{index}]"
                        found.append(f"{rel}: {where} docker {match.group(1)}: {problem}")
    return found


def violations(rel: str, text: str) -> list[str]:
    """Infracciones de un workflow; vacío si cumple todas las reglas."""
    found: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if _KUBECONFIG.search(line):
            found.append(f"{rel}:{number}: nombra un kubeconfig")
        if _CLUSTER_CLI.search(line):
            found.append(f"{rel}:{number}: nombra la herramienta del clúster")
        if _LATEST_TAG.search(line) or _DOCKER_LATEST.search(line):
            found.append(f"{rel}:{number}: etiqueta de imagen latest")
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        return [*found, f"{rel}: no es un YAML válido"]
    if not isinstance(document, dict):
        return [*found, f"{rel}: no es un workflow"]
    found.extend(_permission_violations(rel, document))
    found.extend(_action_violations(rel, document))
    found.extend(_download_violations(rel, document))
    found.extend(_expression_violations(rel, document))
    found.extend(_image_violations(rel, document))
    return found
