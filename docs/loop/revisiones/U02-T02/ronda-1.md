# Ronda 1 — U02-T02

VEREDICTO: NO-VERDE

Todos los criterios pasan con mi propia ejecución. El veredicto es NO-VERDE por tres hallazgos NARANJA: los tres son huecos de las guardias estáticas que la CI usará como compuerta. Los manifiestos reales están bien.

## Criterios de aceptación, verificados por mí (worktree en df99160, limpio antes y después)

| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T02/deploy pytest tests/test_manifests.py -q` | 89 passed |
| CA-2 | `… pytest tests/test_autonomia_01.py -q` | 85 passed |
| CA-3 | `… pytest tests/test_policies_layout.py -q` | 31 passed |
| CA-4 | `… pytest tests/test_scripts_humano.py -q -rxX` | 38 passed, 1 xfailed (`REEMPLAZAR_DIGEST_CURL`, ya conocido) |
| CA-4 | `bash -n` sobre los tres scripts de `scripts/humano/` | 0 en los tres |
| CA-5 | `… pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100` | 339 passed, 1 xfailed, 100 % |
| CA-5 | `mypy --strict src tests`; `ruff check .`; `ruff format --check .` | sin problemas en los tres |
| CA-5 | `bash …/scripts/check-no-{cluster-apply,cluster-ids,datos-personales,insumos}.sh /workspace/.worktrees/U02-T02` | 0 apariciones en los cuatro |
| CA-5 | `git -C … diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |

**Rojo primero:** el commit `e72d743` trae solo pruebas y *fixtures*, 28 archivos sin ningún manifiesto ni script. No lo volví a correr, porque habría tenido que cambiar de commit en el worktree. Su contenido es coherente con el «50 failed, 85 errors» que anota la bitácora.

**Las 5 sondas**, que probé en memoria con `policy_checks` y `autonomia`:
1. Un Deployment con `envFrom` o con un volumen del Secret: los dos fallan. Pasa.
2. Una política con `podSelector: {}` hacia `0.0.0.0/0`, y un `ipBlock` sin `except` para el Job: las dos fallan. Pasa.
3. El puerto 53 sin selector: falla. Pasa.
4. `kubectl   apply`, `kubectl -n x apply` y `helm upgrade --install`: los tres fallan. Pasa, pero ver F-02.
5. `--from-literal`, también con espacio o con `$(…)`: falla. Pasa.

**Manifiestos:**
- `veridicus-deny-all` niega toda entrada y toda salida.
- `veridicus-allow-analyzer-egress` selecciona solo al Job. Abre TCP 443 sin los rangos privados, y DNS solo a `k8s-app: kube-dns` de `kube-system`, con el selector de namespace y el de pod en el mismo elemento, así que se exigen los dos.
- El rango `192.168.0.0/16` cubre la red del nodo `192.168.49.0/24`, con la anfitriona en `.1` y la API en `.2`.
- `10.0.0.0/8` cubre los rangos de pods (`10.244.0.0/16`) y de servicios (`10.96.0.0/12`) que Minikube usa por defecto con Calico, `kubernetes.default` incluido. Es un supuesto: sin `kubectl` no puedo confirmar los rangos del clúster real.
- El Job cumple Pod Security restricted y solo él referencia el Secret.

**Scripts del humano:**
- La clave nunca pasa por argv, `echo` ni `set -x`. El archivo temporal se crea con `umask 077` y se borra con `trap … EXIT`, y `tr` quita el salto de línea final.
- `demo-analyzer.sh` termina en 1 si curl devuelve 0, es decir, si la sonda llegó a internet. Con 6, 7 o 28 da la red por cerrada, y con cualquier otro código también termina en 1, así que falla cerrado.
- Supuesto sin verificar, porque no ejecuto `kubectl`: que `kubectl run --rm --stdin` devuelve el código de salida del contenedor.
- Las `overrides` hacen que la sonda cumpla Pod Security restricted.

**Los dos desvíos declarados:**
- (a) `--exclude-dir=humano` es aceptable: sin él, `kubectl apply -k` de `demo-analyzer.sh` haría fallar la guardia. El hueco que deja está en F-07.
- (b) `autonomia.EXCEPTIONS`: busqué con grep en cada archivo eximido y ninguno contiene un uso real; todos nombran los verbos como datos o como texto, y cada excepción exime solo su regla (`test_an_exception_exempts_only_the_rules_it_names`). La que se puede ajustar está en F-08.

## Hallazgos

### F-01 · NARANJA · deploy/tests/policy_checks.py:186 y 214 · La regla de la NetworkPolicy ignora `endPort`
Los dos conjuntos de puertos se arman como `(protocol, port)` y nunca leen `endPort`. Probé en memoria:
- `endPort: 65535` en la regla del 443 da `endPort443 []`: abre del 443 al 65535 hacia internet y la guardia no lo ve.
- Lo mismo en la regla del 53 (`endPort53 []`).

Es la guardia estática de AUTONOMIA-04. La solución es rechazar `endPort`, o exigir que sea igual al puerto, y añadir un control negativo por regla.

### F-02 · NARANJA · deploy/tests/autonomia.py:27-28 · AUTONOMIA-01 no ve los verbos escritos como lista de argumentos
DP-08 prohíbe esos verbos «en todo script», y la comprobación lee `.py` y `.yaml`. Estas formas pasan sin detectarse (sonda en memoria):
- `subprocess.run(["kubectl", "apply", …])`;
- `command: ["kubectl", "apply", …]`;
- un bloque YAML `- kubectl` / `- apply`;
- `(which kubectl) apply`.

Son las formas naturales en Python y en YAML. Falta una regla para las comillas, comas y listas YAML entre la herramienta y el verbo, con sus controles negativos.

### F-03 · NARANJA · deploy/tests/policy_checks.py:146-166 y deploy/policies/veridicus-pod-restricted/policy.yaml · La regla (c) no ve lo que se sobrescribe en el contenedor
Cambios que dan `ctr-root []`, `ctr-seccomp-caps []` y `hostPath []`:
- `runAsUser: 0` o `runAsNonRoot: false` en el `securityContext` del contenedor;
- `seccompProfile: Unconfined` en el contenedor;
- `capabilities.add: [SYS_ADMIN]`;
- un volumen `hostPath`.

La política de Kyverno tiene el mismo hueco. La etiqueta restricted del namespace lo frena al admitir el pod, pero la regla dice «todo pod cumple el securityContext del paso 4», y la compuerta de la CI hoy no lo comprueba.

### F-04 · NARANJA · deploy/policies/* frente a policy_checks.py · Kyverno no aplica «las mismas reglas» que pytest
Es razonado, porque aquí no se pueden correr. Diferencias:
- Las reglas (c) y (d) en Kyverno solo miran `containers`; pytest mira también `initContainers` y `ephemeralContainers`.
- La regla (b) no cubre `ephemeralContainers`.
- El patrón `*?:?*` acepta `registry:5000/img` sin etiqueta; pytest la rechaza.
- `!*:latest` admite `x:latest@sha256:…`; pytest lo rechaza.
- Kyverno no comprueba `hostNetwork`, `privileged` ni `runAsUser: 0`, que pytest sí comprueba.

`test_each_pass_and_fail_resource_…` solo contrasta los *fixtures* que existen, así que no ve estas diferencias. Hay que añadir recursos de fallo para cada una.

### F-05 · AMARILLO · deploy/policies/veridicus-secret-solo-job/policy.yaml:3-4 · Las `ownerReferences` se pueden copiar
Quien crea un Pod puede poner `ownerReferences` hacia `Job/veridicus-analyzer-demo`: la API no valida el uid al admitirlo. El comentario dice que la etiqueta se puede copiar y el dueño no, y eso no es exacto. Para cerrarlo, sumar una condición sobre `request.userInfo.username` (el controlador de Jobs).

### F-06 · AMARILLO · deploy/tests/autonomia.py:24-31 · La lista de verbos es más corta que la de team.md y la del guardián anterior
La guardia nueva no ve `terraform apply` (está en `## Forbidden`), `helm uninstall` o `helm rollback`, ni `kubectl run`, `exec`, `scale`, `rollout`, `label` o `set`. El guardián de shell solo vigila `.github/` y `scripts/`. La tarea solo pedía la lista corta, así que esto queda como tarea candidata.

### F-07 · AMARILLO · scripts/check-no-cluster-apply.sh:32 · `--exclude-dir=humano` excluye cualquier carpeta con ese nombre
Un archivo sin extensión en `scripts/<x>/humano/` no lo ve ninguna de las dos guardias. En `.github/actions/humano/` sí lo cubre pytest. El desvío se acepta; conviene excluir la ruta exacta y no el nombre.

### F-08 · AMARILLO · deploy/tests/autonomia.py:43 · La excepción `docs/validacion-zine/` vale para toda la carpeta
Solo `comun.sh` y `comprobar_reporte.py` la necesitan, y en los dos `sbatch` aparece solo como texto. Con el prefijo, cualquier archivo nuevo de esa carpeta queda eximido de la regla de SLURM; conviene nombrar los dos archivos.

### F-09 · AMARILLO · deploy/tests/humano_checks.py:14-31 · Formas no cubiertas en las reglas de los scripts del humano
- Un *shebang* `#!/usr/bin/env bash -x` se salta porque empieza con `#`.
- `export $(grep … .env | xargs)` no se detecta, y es un `source` disfrazado que además pone los valores en argv.
- Variables llamadas `$secreto` o `$key` no las ve `_KEY_VAR`.

Los tres scripts reales no tienen ninguno de estos problemas.

## Tareas candidatas (defectos reales fuera de alcance)
- La forma del comando que pide la tarea, `create --dry-run=client -o yaml | kubectl apply -f -`, copia el valor del Secret en la anotación `last-applied-configuration`. Con `kubectl apply --server-side` esa anotación no se escribe.
- Ampliar los verbos de AUTONOMIA-01 a todo `## Forbidden` (F-06).
- La regla de la NetworkPolicy no excluye `100.64.0.0/10`. No aplica a Minikube; queda como nota para cuando exista B10b.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/tests/policy_checks.py:186,214|La regla de la NetworkPolicy ignora endPort
NARANJA|deploy/tests/autonomia.py:27-28|AUTONOMIA-01 no ve los verbos escritos como lista de argumentos (py/yaml)
NARANJA|deploy/tests/policy_checks.py:146-166 y veridicus-pod-restricted|La regla (c) no ve lo que se sobrescribe en el contenedor
NARANJA|deploy/policies/*|Kyverno no aplica las mismas reglas que pytest
AMARILLO|deploy/policies/veridicus-secret-solo-job/policy.yaml:3|Las ownerReferences se pueden copiar
AMARILLO|deploy/tests/autonomia.py:24-31|La lista de verbos es más corta que la de team.md
AMARILLO|scripts/check-no-cluster-apply.sh:32|--exclude-dir=humano excluye cualquier carpeta con ese nombre
AMARILLO|deploy/tests/autonomia.py:43|La excepción docs/validacion-zine/ vale para toda la carpeta
AMARILLO|deploy/tests/humano_checks.py:14-31|Shebang con -x, export de $(grep .env) y nombres de variable no cubiertos
INFORME: docs/loop/revisiones/U02-T02/ronda-1.md
```
