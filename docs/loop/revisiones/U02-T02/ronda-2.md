# Ronda 2: U02-T02

VEREDICTO: NO-VERDE

Corrí los cinco criterios y todos pasan. Ocho de los nueve hallazgos de la ronda 1 y la candidata del Secret quedaron cerrados. Probé cada uno con un mutante en memoria, y con el arreglo neutralizado sus controles fallan. Queda un NARANJA, F-10: la guardia de AUTONOMIA-01 todavía no ve la forma natural de un contenedor de Kubernetes que separa la orden en `command:` y `args:`. El worktree quedó limpio antes y después, en la cabeza `72126ca`.

## Criterios de aceptación, verificados por mí
| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 a CA-4 | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T02/deploy pytest tests/test_manifests.py tests/test_autonomia_01.py tests/test_policies_layout.py tests/test_scripts_humano.py tests/test_check_no_cluster_apply.py -q` | 356 passed, 1 xfailed (`REEMPLAZAR_DIGEST_CURL`, fuera de alcance) |
| CA-4 | `bash -n` sobre `demo-analyzer.sh`, `crear-secret-anthropic.sh` y `crear-pull-secret-ghcr.sh` | 0 en los tres |
| CA-5 | `… pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q -rxX` | 452 passed, 1 xfailed, 100 % de líneas y ramas |
| CA-5 | `… mypy --strict src tests`, `… ruff check .`, `… ruff format --check .` | sin problemas en los tres |
| CA-5 | `bash /workspace/.worktrees/U02-T02/scripts/check-no-{cluster-apply,cluster-ids,datos-personales,insumos}.sh /workspace/.worktrees/U02-T02` | 0 apariciones en los cuatro |
| CA-5 | `git -C /workspace/.worktrees/U02-T02 diff --stat 297ab33...72126ca -- libs contracts` | vacío |

**Rojo primero:** `76c30bc` trae solo pruebas, *fixtures* y recursos de Kyverno (27 archivos, ningún arreglo). No lo volví a correr, porque habría tenido que cambiar de commit. En su lugar apliqué mutantes en memoria con `python -c`, sin tocar archivos. Con cada arreglo neutralizado fallan sus controles:
- F-01 y F-03: `_end_port_violations` devolviendo vacío y `_container_security_violations` sin sus reglas nuevas hacen fallar 13 pruebas de `test_manifests.py`.
- F-02 y F-08: `LIST_RULES = {}` y la excepción de carpeta `docs/validacion-zine/` restaurada hacen fallar 37 pruebas de `test_autonomia_01.py`.
- F-09 y la candidata: sin `SHEBANG_X` ni las reglas `export…` y `apply sin --server-side` fallan 5 pruebas; con `_KEY_NAMES` reducido fallan 3 más.

## Cierre de la ronda 1 (sondas en memoria)
- **F-01, cerrado.** `endPort` en la regla del 443 y en la del 53, sea 65535 o igual al puerto, da 1 infracción en cada caso.
- **F-02, cerrado para las cuatro formas que se pidieron:**
  - `subprocess.run(["kubectl","apply",…])`;
  - `command: ["kubectl","apply"]`;
  - el bloque `- kubectl` / `- apply`;
  - `(which kubectl) apply`.

  También detecta `*flags`, `--namespace=x`, la lista en varias líneas, la ruta absoluta en una lista entre corchetes y `helm` en lista o en bloque. Lo que sigue sin verse está en F-10.
- **F-03, cerrado.** En el contenedor se detectan `runAsUser: 0`, `runAsNonRoot: false`, seccomp `Unconfined`, `capabilities.add` (también vacío) y `privileged`. En el pod se detectan `hostPath`, `hostPID` y `runAsUser: 0`.
- **F-04, cerrado en cuanto a datos.** Las cuatro políticas cubren los tres tipos de contenedor, y las expresiones de la imagen son idénticas a las de pytest (hay una prueba que lo exige). `registry:5000/img` y `x:latest@sha256:…` fallan.
- **F-05, cerrado.** La política exige a la vez la `ownerReference` del Job y `request.userInfo.username == system:serviceaccount:kube-system:job-controller`, con `background: false`, que es obligatorio cuando una regla usa `userInfo`. El ensayo con otro usuario está en `otro-usuario/`.
- **F-07, cerrado.** El guardián salta solo la ruta `scripts/humano`, y `test_check_no_cluster_apply.py` prueba `scripts/otro/humano/` y `.github/humano/`.
- **F-08, cerrado.** `_exempt('docs/validacion-zine/nuevo.sh')` devuelve vacío y `comun.sh` devuelve `{'slurm'}`.
- **F-09, cerrado.** Se detectan:
  - los *shebang* con `-x` o `-ex`;
  - `export` de `$(grep … | xargs)`, de `$(cat .env)` y de `$(< .env)`;
  - `echo` de `$secreto`, de `${key}` y de `$API_KEY`.

  `echo $nombre` no da falso positivo.
- **Candidata del Secret, cerrada.** Los dos scripts usan `kubectl apply --server-side -f -`, y la regla nueva rechaza `kubectl apply -f -` y el pipe sin `--server-side`.

## Puntos dudosos que me pediste juzgar
- **Sintaxis de Kyverno.** No tengo context7 entre mis herramientas, así que no pude consultar la documentación y la juzgo de memoria, sin verificar. Todas las formas coinciden con las políticas de ejemplo oficiales que recuerdo:
  - `X(hostPath): "null"` dentro de `=(volumes)` y `X(add): "null"` (el ancla de negación exige que la clave no exista);
  - `=(privileged): "false"`, `=(runAsUser): ">0"` y `=(type): "RuntimeDefault | Localhost"`;
  - la lista `request.object.spec.[ephemeralContainers, initContainers, containers][]` (el aplanado de JMESPath descarta los nulos);
  - `regex_match('…', '{{ element.image }}')` anidado, sin llaves ni barras invertidas en la expresión;
  - `deny.conditions` con `all` y `any` juntos, que se evalúan como un Y entre los dos bloques;
  - en el Test, el campo `userinfo:` que apunta a un archivo `cli.kyverno.io/v1alpha1` de tipo `UserInfo`.

  Lo menos seguro es que `kyverno test` descubra el Test de la subcarpeta `otro-usuario/` y resuelva sus rutas `../`. Todo esto lo confirma U02-T03.
- **«Fijada por digest».** Aceptarla como «etiqueta o digest bien formado» es coherente con la regla (b) de la tarea («ni latest ni sin etiqueta»). El digest de la base que pide team.md es cosa del Dockerfile, no de esta regla.
- **El hueco de `pods/ephemeralcontainers`:** queda en AMARILLO, ver F-12.
- **El conflicto de propietario de `--server-side`:** no veo ese conflicto, pero sí otro riesgo, ver F-11.
- **El límite declarado de F-02 (`$K apply`):** es aceptable. Una orden armada con variables no se puede decidir en estático, y el guardián de shell tiene el mismo límite. Ese límite no cubre F-10.

## Hallazgos
### F-10 · NARANJA · deploy/tests/autonomia.py:44-70 · AUTONOMIA-01 no ve la orden separada en `command:` y `args:` ni otras formas de lista
La sonda la hice en memoria: escribí archivos con `python -c` en el scratchpad y los recorrí con `autonomia.scan`. Estas formas dan 0 infracciones:
- `command: ["kubectl"]` seguido de `args: ["apply", "-f", "x"]`, en flujo y en bloque. Es la forma canónica de un contenedor de Kubernetes. Un Job o un CronJob así en `deploy/`, que Argo CD sincronizará solo, aplicaría cambios desde el clúster.
- El bloque `- /usr/bin/kubectl` seguido de `- apply`. La regla de bloque exige que el nombre vaya justo después del guion.
- La tupla de dos elementos `subprocess.run(("kubectl", "apply"))`. Después del verbo, la regla espera una coma o un corchete, no un paréntesis.

La bitácora declara el primer caso («claves distintas de un YAML»), pero declararlo no lo cierra: es la misma clase que pedía F-02. Propuesta:
- en los `.yaml`, cargar los documentos con PyYAML y unir el `command` y los `args` de cada contenedor antes de aplicar la regla de línea;
- admitir una ruta antes del nombre de la herramienta en la regla de bloque;
- aceptar `)` después del verbo;
- añadir un control negativo por cada forma.

### F-11 · AMARILLO · scripts/humano/crear-secret-anthropic.sh:10-13 y crear-pull-secret-ghcr.sh:13-16 · El aviso sobre un Secret anterior no corresponde a lo que pasa (sin verificar)
Cuando un objeto viene de un apply del lado del cliente, Kubernetes documenta que `--server-side` transfiere la gestión de sus campos sin conflictos. Así que el aviso «si kubectl avisa de un conflicto, borre el Secret» no se dispararía nunca. Además, según recuerdo (KEP-555), el servidor mantiene actualizada la anotación `last-applied-configuration` cuando ya existe. Si es así, un Secret creado antes con el script de la ronda 1 seguiría guardando el valor en esa anotación.

Propuesta: que el script detecte la anotación y pida borrar el Secret, o que la quite con `kubectl annotate … last-applied-configuration-`. No pude verificarlo contra la documentación.

### F-12 · AMARILLO · deploy/policies/veridicus-secret-solo-job/policy.yaml y veridicus-imagen-con-etiqueta/policy.yaml · El hueco de `pods/ephemeralcontainers` también afecta a las reglas (a) y (b), y solo está declarado en la (c)
`kubectl debug` puede añadir un contenedor efímero con `envFrom: secretRef veridicus-anthropic` a otro pod del namespace. La etiqueta restricted de Pod Security frena el `securityContext`, pero no el uso del Secret ni la imagen. pytest sí cubre los efímeros en los manifiestos.

Propuesta: añadir `Pod/ephemeralcontainers` al `match`, o al menos declarar el hueco también en estas dos políticas.

### F-13 · AMARILLO · deploy/tests/humano_checks.py:41-43 · La regla `apply sin --server-side` se esquiva fácilmente
La prueba es la sonda en memoria `kubectl apply -f - # --server-side`, que da 0 infracciones: la búsqueda hacia adelante lee también el comentario del final de la línea. La excepción `-k` también dejaría pasar una kustomization con `secretGenerator`. Ninguno de los tres scripts reales tiene este problema.

## Tareas candidatas (defectos reales fuera de alcance)
- F-06 sigue pendiente: ampliar los verbos de AUTONOMIA-01 a todo `## Forbidden`.
- La regla de línea de AUTONOMIA-01 da un falso positivo, que ya venía de la ronda 1: `# kubectl get pods, do not delete anything` en prosa de un `.py`.
- Las reglas (c) y Kyverno no miran `procMount`, `hostPort` ni `sysctls`, que sí revisa Pod Security restricted. Hoy los frena la etiqueta del namespace.
- `100.64.0.0/10` no está en los rangos excluidos de la `NetworkPolicy`. Es una nota para B10b, como en la ronda 1.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/tests/autonomia.py:44-70|AUTONOMIA-01 no ve command/args separados, el bloque con ruta absoluta ni la tupla de dos elementos
AMARILLO|scripts/humano/crear-secret-anthropic.sh:10|El aviso de conflicto con --server-side no corresponde y la anotación previa podría seguir viva (sin verificar)
AMARILLO|deploy/policies/veridicus-secret-solo-job/policy.yaml|El hueco de pods/ephemeralcontainers también afecta a las reglas (a) y (b)
AMARILLO|deploy/tests/humano_checks.py:41-43|La regla apply sin --server-side se esquiva con un comentario al final de la línea o con -k
INFORME: docs/loop/revisiones/U02-T02/ronda-2.md
```
