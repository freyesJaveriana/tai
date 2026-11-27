# Ronda 4 — U02-T03

VEREDICTO: NO-VERDE

La plantilla cierra F-07: los cinco mutantes M4, M5, M5b, M13 y M14 quedan atrapados. Los criterios CA-1 a CA-4 pasan, los arreglos de SC2034 no cambian el comportamiento y las tres pruebas cambiadas no aflojan nada.

El bloqueo es nuevo para esta ronda, aunque el defecto existe desde la ronda 1 y no lo vi entonces. La suma que realmente se usa al verificar puede venir del `env:` del job o del workflow, que el comprobador no lee. Con una suma de la tabla de señuelo en el `env:` del paso, cualquier suma pasa la regla y toda la suite.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Prueba de los workflows | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T03/deploy pytest tests/test_workflows.py -q` | 250 passed |
| CA-2 | AUTONOMIA-01 (DP-08) | `uv run … pytest tests/test_autonomia_01.py tests/test_check_no_cluster_apply.py -q` | 170 passed |
| CA-3 | K-97, K-102, K-103, K-104 | `uv run … pytest tests/test_dockerfile.py tests/test_manifests.py tests/test_scripts_humano.py -q`, más `bash -n` de los dos scripts (rutas absolutas) | 283 passed; los dos `bash -n` en 0 |
| CA-4 | Nada retrocede | `uv run … pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q`, más `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | 808 passed, 100 % de líneas y ramas; mypy, ruff y formato en 0 |
| CA-4 | Los cuatro check-no-*.sh | `bash /workspace/.worktrees/U02-T03/scripts/check-no-<x>.sh /workspace/.worktrees/U02-T03`, uno por script | los cuatro dan `0 apariciones` |
| CA-4 | Sin cambios en libs/ ni contracts/ | `git -C /workspace/.worktrees/U02-T03 diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |
| SC2034 | Las guardias siguen igual | `bash /workspace/.worktrees/U02-T03/scripts/tests/autoprueba-guardias.sh` | `sondas: 17 de 17 detectadas`, `controles: 10 de 10 limpios` |
| CA-5 | En la CI (#62) | no corresponde aquí | pendiente del orquestador |

- **Ningún workflow ni el Dockerfile cambiaron:** `git -C … diff --stat 7e4c1c6 4ad4024 -- .github deploy/images` sale vacío.
- **Estado del worktree:** `git status --short` sale limpio.
- **Los arreglos de SC2034 son equivalentes:** `read -r archivo numero _` guarda el resto de la línea en `_`, igual que antes en `texto`, que no se usaba.

## Mutantes en memoria
Apliqué cada uno con `python -c` sobre el paso de Trivy de `analyzer-image.yml` (`workflow_checks.violations` tras un `replace`).

**Atrapados:**
- M4 (función), M5 (subshell), M5b (llaves) y M13 (`trap 'exit 0' ERR`): «no sigue la plantilla».
- M14 (`continue-on-error`): «no puede llevar continue-on-error».
- B6 (un `\` que une `&& echo hola` a `mkdir`): «plantilla».
- B7 (`wget -q -O` en lugar de `curl`) y B7b (una línea extra con `python3 -c` y `urllib`): «plantilla».

**Pasan el comprobador, pero fallan cerrado en ejecución** (comprobador `[]`):
- B1, un `curl -o` hacia otra ruta: `sha256sum` verifica un archivo que no existe.
- B2, `sha256sum` sobre otra ruta: lo mismo.
- B3, `${OTRA}` sin definir: `set -u` lo rechaza.
- B4, un `tar` de otro archivo: no existe.
- B5, el PATH hacia otro directorio: no ejecuta nada sin verificar.

**Pasan el comprobador y no fallan en ejecución:**
- **B8 y B8c:** la suma está en el `env:` del job o del workflow, y el `env:` del paso trae la suma real de la tabla con otro nombre (`SUMA_TABLA`): `[]`.
- B9: un `gh release download … && ./x` en un `run` sin URL ni curl: `[]`.

## Hallazgos

### F-09 · NARANJA · deploy/tests/workflow_checks.py, `_download_step_violations` (`sums = set(_SUM.findall(code + " " + str(step.get("env"))))`) · La suma que se usa al verificar puede no ser la de la tabla
La comprobación de la tabla busca cualquier suma de 64 hex en el script o en el `env:` del paso. No mira qué variable usa la línea fija ni de dónde sale su valor.

Mutante B8:
- se añade `env: SHA256: "eeee…"` (64 caracteres) al job `build-scan`;
- la suma del paso se renombra a `SUMA_TABLA: "bc0fc726…"`;
- la línea fija sigue con `echo "${SHA256}  …"`.

En ejecución, `${SHA256}` toma la suma del job: un binario cualquiera con esa suma se verifica y se ejecuta.

- **Comprobador:** `[]`. Con la suma en el `env:` del workflow (B8c) da lo mismo, `[]`.
- **Pruebas de forma:** `test_trivy_is_downloaded…` y `test_deploy_level0_downloads_each_tool…` solo comprueban que la suma de la tabla aparezca en el texto del paso. Lo cumple el señuelo, así que **el mutante sobrevive a toda la suite**.
- **Regla rota:** la de la tarea, «su suma no es una de las de la tabla».
- **Edad:** el defecto existe desde la ronda 1. No lo detecté entonces.

Arreglo propuesto:
- leer el nombre de la variable de la línea fija (`${VAR}`);
- exigir que `VAR` esté definida en el `env:` del paso con exactamente la suma de la tabla de la herramienta cuyo asset aparece en `ASSET` o en la URL;
- rechazar que `VAR` o `ASSET` se definan también en el `env:` del job o del workflow;
- añadir los controles negativos B8 y B8c.

### F-10 · AMARILLO · deploy/tests/workflow_checks.py, `_SEQUENCES` · La plantilla no ata las rutas entre sí ni ve descargas sin URL
- **Rutas sueltas:** la plantilla no exige que la ruta de `curl -o`, la de la verificación y la de `tar` o `mv` sean la misma. Con un solo `curl`, cualquier desajuste falla cerrado (B1 a B4). El único caso que sobreviviría necesita un archivo versionado con la suma de la tabla: verificar ese archivo y extraer el descargado. Es rebuscado, pero se cierra exigiendo la misma cadena en las tres líneas.
- **Descargas sin URL:** `gh release download` y otras formas sin `http(s)://` ni curl/wget no activan la plantilla (B9). Hoy ningún workflow lo hace.

No bloquea.

## Juicio sobre las tres pruebas cambiadas
- **`ok.yml`:** suma la línea de `mkdir` y la del PATH para ajustarse a la plantilla. Es necesario y no afloja nada: el fixture base es ahora exactamente la plantilla, y `test_f07_the_base_fixture_is_exactly_the_template` lo fija.
- **`test_f05_a_closed_structure…`:** **endurece.** Antes exigía `== []`, es decir, aceptaba la línea extra `if true; then true; fi`. Ahora esa línea la rechaza la plantilla, y la prueba solo comprueba que no se informe como anidamiento.
- **`test_negative_f07_a_missing_template_line_fails`:** se estrechó en el verde afbaa5d, de todos los índices a `[0, 1, 3, 4, 5]`. Quita el caso «sin la línea de curl». No afloja la seguridad: sin curl tampoco queda URL, así que el paso ya no descarga nada, y su `tar` de un archivo inexistente falla en ejecución. Debió quedar así desde el rojo d036fd0, pero el cambio está declarado en la bitácora. Lo doy por aceptable.

## Lo demás
- **Nota de F-08:** está en la bitácora («Ronda 4»).
- **Lo que más probablemente rompa la CI** no cambia: hadolint sobre el `RUN` de libzstd1, que esa versión exista hoy en el espejo, Kyverno 1.19.2 con `userinfo` y el render de kustomize en pytest. Los tres SC2034 deberían cerrar el fallo de shellcheck que ya se vio.

## Tareas candidatas (defectos reales fuera de alcance)
- K-106 y K-107, sin cambios.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/tests/workflow_checks.py:_download_step_violations|la suma que usa la verificación puede venir del env del job o del workflow; con un señuelo de la tabla en el env del paso pasa la regla y toda la suite
AMARILLO|deploy/tests/workflow_checks.py:_SEQUENCES|la plantilla no ata la ruta del curl, la de la verificación y la de la extracción, y no ve descargas sin URL (gh release)
INFORME: docs/loop/revisiones/U02-T03/ronda-4.md
```
