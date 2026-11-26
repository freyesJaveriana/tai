# Ronda 1 — U02-T01

VEREDICTO: NO-VERDE

Corrí los cinco criterios yo mismo y todos pasan. Queda un NARANJA: `uv` no está fijado por digest en la imagen, como pide el paso 3. El veredicto es NO-VERDE solo por eso. Lo demás son mejoras que no bloquean.

## Criterios de aceptación, verificados por mí

Todos con `--directory /workspace/.worktrees/U02-T01/deploy` salvo donde se indica. El worktree quedó limpio al terminar (`git status --porcelain` vacío).

| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `uv run --frozen --offline --directory …/deploy pytest tests/test_entrada.py -q` | pasa: `10 passed in 0.43s` |
| CA-2 | `uv run … pytest tests/test_entrypoint.py --cov=veridicus_demo --cov-branch --cov-fail-under=100 --cov-report=term-missing` | pasa: `28 passed`, `entrypoint.py 114 stmts, 30 branches, 100%` |
| CA-3 | `uv run … pytest tests/test_dockerfile.py -q` | pasa: `16 passed in 0.02s`. Solo lee archivos, por eso tarda milisegundos |
| CA-4 | `mypy --strict src tests`, luego `ruff check .`, luego `ruff format --check .` | los tres en 0 |
| CA-5 | `uv run --frozen --offline --directory …/libs/incoherence_analyzer --extra cli pytest tests/e2e --no-cov -q` | pasa: `4 passed` |
| CA-5 | los tres scripts `check-no-*.sh` | `0 apariciones` en cada uno |
| CA-5 | `git -C /workspace/.worktrees/U02-T01 diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |
| CA-5 | `grep -rnoP "sk-[A-Za-z0-9_-]{6,}" …/deploy` | una sola aparición: la clave canario en `tests/support.py:17` |

**Prueba primero:** el rojo `f2f9780` traía las pruebas sin el módulo ni las entradas, así que era un rojo real. Comparé las pruebas entre `f2f9780` y `ff5e1cc`: solo hay cambios de formato y casos nuevos. Ninguna aserción se debilitó.

## Casos sonda

1. **La clave en un error:** el `except` de `entrypoint.py:180` imprime solo el nombre de la clase. Además, sustituí en memoria `pseudonymize` por una función que lanza un error con la clave canario en el mensaje (`mock.patch.object`, sockets apagados con `pytest_socket.disable_socket()`, entorno explícito). Resultado: código 4, 0 llamadas al proveedor, y la clave no aparece en stdout ni en stderr.
2. **Salida parcial:** con la CLI en 4, el punto de entrada solo lee `estado` y lista los archivos en `error` con 0 hallazgos. Con un archivo en `error`, los hallazgos se descartan también en la ruta de código 0 (`_read`, línea 111). Lo cubren `test_with_exit_4_…` y `test_with_exit_0_but_a_file_in_error_state_…`, con un hecho de prueba que no debe aparecer.
3. **Salida que falta o está dañada:** probé 6 variantes, más un directorio de entrada vacío y una de dos salidas ausente. Todas terminan en 5 con un mensaje fijo, y el canario puesto en un turno nunca aparece. Del directorio de entrada solo se leen los nombres de archivo, no el contenido.
4. **Cita que no está en la transcripción:** se imprime tal cual la dio la CLI; la prueba lo deja explícito.
5. **Vocabulario prohibido:** pasé `scan` sobre los 4 mensajes fijos y los 6 rótulos: 0 coincidencias, y el control negativo «miente» sí se detecta. La prueba del repositorio solo cubre los rótulos de la corrida feliz (ver F-03).

**Los tres puntos que aceptó el orquestador:** los revisé y están bien implementados.
- Con la CLI en 4 solo se lee `estado`.
- Con el anonimizador caído, la CLI da 0 con `anonimizador_no_disponible` y la demo sale con 4. Lo comprobé en mi sondeo.
- Las bibliotecas hermanas son editables en `deploy/pyproject.toml` y la imagen se construye con `--no-editable`.

**Lo demás que pediste revisar:**
- El usuario final es `10001:10001`, no root.
- La etapa final copia solo `/app/.venv`; en el Dockerfile no hay claves ni `ENV` o `ARG` con secretos.
- Las entradas son sintéticas. Busqué solo nombres de archivo en `/insumos`: «Aurelia», «Rosalba», «Montenegro», «San Isidro» y «crecida» no aparecen. «la ceiba» aparece una vez en un archivo del piloto, pero como el árbol, en minúscula. No se copió nada del piloto.

## Hallazgos

### F-01 · NARANJA · `deploy/images/analyzer-cli/Dockerfile:15` · `uv` no está fijado por digest
El paso 3 pide `uv` «fijado por versión y digest». La imagen hace `RUN pip install --no-cache-dir uv==0.13.9`, sin digest ni hashes. La prueba `test_the_build_stage_…_and_pins_uv` solo comprueba la versión (`uv==\d+\.\d+\.\d+`), así que pasa aunque falte el requisito. La bitácora lo declara como pendiente. Pero el humano ya trajo con `!` el digest de `python:3.12-slim`, y el de uv se puede traer igual.
**Arreglo:** usar `COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:<digest> /uv /usr/local/bin/uv`, con el digest que traiga el humano. La prueba debe exigir ese `@sha256:` y tener un control negativo.

### F-02 · AMARILLO · `.dockerignore` · Faltan patrones de secretos dentro de las carpetas que entran al build
Fuera de `contracts/`, `libs/` y `deploy/` todo queda excluido. Dentro de ellas solo se excluyen `.env` y `**/.env`. No se excluyen `.env.*`, `*.pem`, `*.key`, `kubeconfig*` ni `secrets*.yaml`, que el `.gitignore` sí cubre (líneas 103–107). Esos archivos no llegarían a la imagen final, porque esa etapa copia solo el entorno virtual. Pero entrarían a la etapa de construcción y a la caché local si el humano construye en local con el plan B (`minikube image build`, R-B4d-1).

### F-03 · AMARILLO · `deploy/tests/test_entrypoint.py:201` · El sondeo 5 no cubre los mensajes fijos
La prueba solo pasa el escáner sobre la salida de la corrida feliz. Los cuatro mensajes `ARGS`, `CLI_FAILED`, `NO_OUTPUT` y `UNEXPECTED` no se prueban. Hoy pasan, porque lo comprobé a mano, pero ninguna prueba lo protege.

### F-04 · AMARILLO · `deploy/tests/test_entrypoint.py:444` · Una prueba corre el módulo con el entorno real
`test_running_the_module_as_main_…` usa `os.environ` tal cual, y en este contenedor ahí está la clave real `VERIDICUS_ANTHROPIC_API_KEY`. Hoy no sale ninguna llamada: la CLI termina en 2 al no encontrar la entrada, y los sockets están apagados. Aun así, la prueba debería borrar esa variable con `monkeypatch.delenv(…, raising=False)` para no depender de eso.

### F-05 · AMARILLO · `entrypoint.py:120` · «1 hallazgos»
El rótulo no concuerda en singular, y es texto que el público ve en la demo.

## Incidente de proceso: no bloquea el diff
La bitácora declara que el codificador hizo una corrida real contra el proveedor, aunque la tarea prohíbe la red. Viajaron solo las dos transcripciones sintéticas, ya seudonimizadas, y el diff no lleva nada de esa corrida. Igual conviene que el humano lo sepa por el costo y por la regla incumplida.

## Tareas candidatas
- Lanzar a los codificadores sin `VERIDICUS_ANTHROPIC_API_KEY` en el entorno, o sin red, para que no se repita el incidente.

## No verificado
- El build real de la imagen, `hadolint` y Trivy: le tocan a la CI (U02-T03).
- Que el digest de `python:3.12-slim` corresponda de verdad a esa imagen: lo trajo el humano y yo no tengo red para comprobarlo.
- Los mutantes del punto de entrada los razoné leyendo el código y las aserciones, sin ejecutarlos.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/images/analyzer-cli/Dockerfile:15|uv no está fijado por digest
AMARILLO|.dockerignore|Faltan patrones de secretos dentro de las carpetas que entran al build
AMARILLO|deploy/tests/test_entrypoint.py:201|El sondeo 5 no cubre los mensajes fijos
AMARILLO|deploy/tests/test_entrypoint.py:444|Una prueba corre el módulo con el entorno real
AMARILLO|deploy/src/veridicus_demo/entrypoint.py:120|«1 hallazgos»
INFORME: docs/loop/revisiones/U02-T01/ronda-1.md
```
