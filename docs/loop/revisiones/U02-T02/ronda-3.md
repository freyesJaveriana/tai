# Ronda 3: U02-T02

VEREDICTO: VERDE

Corrí CA-1 a CA-5 y todos pasan. Ya no queda ningún xfail. Los cuatro cierres encargados (F-10 a F-13) y el digest de curl están hechos. Con cada arreglo neutralizado en memoria, sus controles fallan. No queda ningún ROJO ni NARANJA; quedan cuatro AMARILLO que no bloquean. El worktree quedó limpio antes y después, en la cabeza `65ed804`. La fusión la decides tú.

## Criterios de aceptación, verificados por mí
| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 a CA-4 | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T02/deploy pytest tests/test_manifests.py tests/test_autonomia_01.py tests/test_policies_layout.py tests/test_scripts_humano.py tests/test_check_no_cluster_apply.py -q -rxXs` | 407 passed, sin xfail ni skip |
| CA-4 | `bash -n` sobre `demo-analyzer.sh`, `crear-secret-anthropic.sh` y `crear-pull-secret-ghcr.sh` | 0 en los tres |
| CA-5 | `… pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q -rxXs` | 503 passed, 100 % de líneas y ramas |
| CA-5 | `… mypy --strict src tests`, `… ruff check .`, `… ruff format --check .` | sin problemas en los tres |
| CA-5 | `bash /workspace/.worktrees/U02-T02/scripts/check-no-{cluster-apply,cluster-ids,datos-personales,insumos}.sh /workspace/.worktrees/U02-T02` | 0 apariciones en los cuatro |
| CA-5 | `git -C /workspace/.worktrees/U02-T02 diff --stat 297ab33...65ed804 -- libs contracts` | vacío |

**Rojo primero:** `e5e1dd2` trae solo `test_autonomia_01.py` y `test_scripts_humano.py`. El único cambio que quita algo es el xfail, que pasa a ser una comprobación real; ninguna prueba se aflojó.

**Mutantes en memoria** (con `python -c`, sin tocar archivos):
- Con `_container_hits` neutralizado, el cierre `[,\])]` de la lista devuelto a `[,\]]` y la ruta quitada de la regla de bloque, fallan 14 pruebas `test_f10_*`.
- Con `strip_comment` como identidad y `_kustomization_problem` devolviendo `None`, fallan 6 pruebas `test_f13_*`.
- F-11 lo razoné en lugar de mutarlo: `test_f11_*` exige que la comprobación vaya antes del apply y que el bloque lleve `delete secret … --namespace` y `exit 2`.

## Cierres y los cuatro puntos que pediste
- **F-10, cerrado.** La sonda la hice escribiendo archivos en el scratchpad y recorriéndolos con `autonomia.scan`. Ahora se detectan:
  - `command` y `args` separados, en flujo y en bloque;
  - un CronJob con `initContainers` y la ruta absoluta;
  - `helm` repartido en `command` y `args`;
  - `sh -c` con la orden en `args`;
  - `lifecycle.exec`, el ancla `*b`, el segundo documento de un archivo, el bloque con ruta y la tupla de dos elementos.

  `kubectl get` en `command` y `args` no da falso positivo, ni una variable de entorno que nombra `kubectl`.
- **F-13, cerrado.** Se detectan `apply -f - # --server-side` y `#--server-side`. Un `#` entre comillas no se toma por comentario. Las cinco formas de `-k` y `--kustomize` (incluidas `$raiz`, `./` y `/` final) fallan si la kustomization tiene `secretGenerator`.
- **F-11, cerrado.** Los dos scripts terminan con 2 y piden `kubectl delete secret … --namespace …` si encuentran la anotación. La cabecera ya no habla de conflicto.
- **F-12, cerrado.** El hueco consta en las dos políticas y su `match` no cambió.
- **Digest de curl, cerrado.** `curlimages/curl:8.11.1@sha256:c1fe…9a69` cumple la expresión de imagen de Kyverno y de pytest, y el pod de la sonda lleva `resources` y el contexto restricted. No puedo verificar sin red que el digest sea el real. Si fuera falso, el pod no arrancaría, `codigo_red` no sería ni 6, ni 7, ni 28, y el script terminaría en 1, es decir, fallaría cerrado.

1. **`humano_checks.py`, línea por línea** (`git diff -U0` de `72126ca...65ed804`). Los únicos cambios son el encargo:
   - el `import Path`;
   - la regla del apply, que sale de `LINE_RULES` y pasa a `_APPLY_LINE`, con `-k[\s=]`;
   - `strip_comment` y `_kustomization_problem`;
   - el parámetro `root` de `violations`;
   - `PINNED` y `REAL_DIGEST` con `(?::[\w.-]+)?`.

   No hay cambios ajenos. El salto de las líneas que son comentarios sigue antes de todas las reglas.
2. **La anotación no se filtra:**
   - por argv solo pasa la expresión jsonpath;
   - stderr va a `/dev/null`;
   - stdout va solo al pipe de `grep -q`, que no imprime nada;
   - no hay variables ni archivos, y los `echo` solo llevan `$namespace`.
3. **PyYAML** se usa con `yaml.safe_load_all` y atrapa `YAMLError`. Un YAML roto no tumba la suite: la sonda `broken.yaml` sigue cayendo por la regla de texto. Ver F-14.
4. **`PINNED` y `REAL_DIGEST`** solo los usa `test_scripts_humano.py` para curl. `policy_checks.IMAGE_PINNED` no cambió en esta ronda, así que la regla de imágenes de los manifiestos no se afloja. Ver F-16.

## Hallazgos
### F-14 · AMARILLO · deploy/tests/autonomia.py:120-125 · Una etiqueta YAML desconocida apaga la regla de `command` + `args` en todo el archivo
La sonda `x: !Ref y` seguida de `command: ["kubectl"]` y `args: ["apply"]` da 0 infracciones, porque `ConstructorError` es un `YAMLError` y el archivo entero se salta. Hoy los YAML del repositorio son de Kubernetes y de GitHub y no usan etiquetas. Propuesta: un `SafeLoader` derivado con `add_multi_constructor("!", …)` que ignore las etiquetas desconocidas.

### F-15 · AMARILLO · deploy/tests/humano_checks.py:69-91 · `apply -k` solo mira el `kustomization.yaml` de primer nivel
Estos casos dan 0 infracciones (sonda en memoria):
- una base con `secretGenerator` que se trae por `resources: [../x]`;
- un `kind: Secret` puesto en `resources`;
- un `kustomization.yml`.

La kustomization real no tiene ninguno de los tres casos, y pytest (a) frena el Secret `veridicus-anthropic` en lo renderizado.

### F-16 · AMARILLO · deploy/tests/humano_checks.py:119-122 · `PINNED` acepta `curlimages/curl:latest@sha256:…`
Los manifiestos y Kyverno rechazan `latest` aunque lleve digest. Para que sean coherentes, conviene excluir `latest` también aquí.

### F-17 · AMARILLO · scripts/humano/crear-secret-anthropic.sh:49 y crear-pull-secret-ghcr.sh:58 · `| grep -q .` con `pipefail` podría fallar abierto (lo razoné, no lo verifiqué)
Si `grep -q` sale antes de que kubectl termine de escribir, kubectl recibe SIGPIPE (141). Con `pipefail`, el `if` sale falso y el script aplica igual. Con una sola salida de jsonpath es improbable.

La alternativa sin carrera y sin que el valor pase por el pipe es una plantilla `-o go-template='{{if index .metadata.annotations "kubectl.kubernetes.io/last-applied-configuration"}}si{{end}}'` y comparar su salida con `si`. Para no romper el analizador de permisos, no la escribí entre acentos graves.

## Tareas candidatas (defectos reales fuera de alcance)
- F-06/K-99, el falso positivo en prosa (también lo repite la regla de `command` + `args`, como `echo "kubectl … create"`), `procMount`/`hostPort`/`sysctls` y `100.64.0.0/10`: sin cambios, como se encargó.

```
VEREDICTO: VERDE
AMARILLO|deploy/tests/autonomia.py:120-125|Una etiqueta YAML desconocida apaga la regla de command + args en todo el archivo
AMARILLO|deploy/tests/humano_checks.py:69-91|apply -k solo mira el kustomization.yaml de primer nivel (bases, Secret en resources, .yml)
AMARILLO|deploy/tests/humano_checks.py:119-122|PINNED acepta curl:latest@sha256
AMARILLO|scripts/humano/crear-secret-anthropic.sh:49|grep -q con pipefail podría fallar abierto por SIGPIPE (razonado)
INFORME: docs/loop/revisiones/U02-T02/ronda-3.md
```
