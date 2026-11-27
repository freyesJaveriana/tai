# Ronda 1 — U02-T04

VEREDICTO: NO-VERDE

Hay dos hallazgos NARANJA y ningún ROJO. CA-1 y CA-2 pasan, el rojo primero se cumple, todos los mutantes mueren y el diff no se sale del alcance. Los dos NARANJA son errores de la guía que el humano va a seguir en la demo de mañana.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Prueba de la guía | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T04/deploy pytest tests/test_readme.py -q` | 33 passed in 0.03s (sin estado externo: son reglas sobre texto) |
| CA-2a | Suite, cobertura 100 % de ramas | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T04/deploy pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q` | 880 passed in 10.68s, 100,00 % |
| CA-2b | mypy | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T04/deploy mypy --strict src tests` | sin errores, 19 archivos |
| CA-2c | ruff check | `uv run … ruff check .` | All checks passed |
| CA-2d | ruff format | `uv run … ruff format --check .` | 28 files already formatted |
| CA-2e | Los cuatro `check-no-*.sh` | `bash /workspace/.worktrees/U02-T04/scripts/check-no-{datos-personales,insumos,cluster-ids,cluster-apply}.sh /workspace/.worktrees/U02-T04` (una llamada por script) | los cuatro dan `0 apariciones` |
| CA-2f | Alcance | `git -C /workspace/.worktrees/U02-T04 diff --stat origin/bolt/b4-demo -- libs contracts .github deploy/demo-analyzer/{job,kustomization,namespace,networkpolicy,serviceaccount}.yaml deploy/demo-analyzer/entrada scripts deploy/images deploy/src deploy/pyproject.toml deploy/uv.lock` | vacío |
| Rojo | Commit del rojo | `git -C … show --stat 8b6cfef` y `git -C … diff --stat 8b6cfef de13e0c` | el rojo trae solo la prueba y los *fixtures*; el verde trae solo el README y la bitácora; las pruebas no cambian entre los dos |
| Worktree | Limpio | `git -C … status --short --ignored deploy` | solo archivos ignorados (cachés, `.venv`, `.coverage`) |

## Mutantes (en memoria, `mock.patch.object` dentro de `python -c` con `uv run … --directory deploy`)
| Mutante en `readme_checks` | Resultado |
|---|---|
| Sin mutante (control) | 33 passed |
| `_PATH` no detecta nada | 2 fallan, muerto |
| `_BARE_SCRIPT` no detecta nada | 1 falla, muerto |
| `_LATEST` no detecta nada | 1 falla, muerto |
| `_KUBECONFIG` no detecta nada | 1 falla, muerto |
| `_SECRET_SHAPES = ()` | 4 fallan, muerto |
| `REQUIRED_SCRIPTS` sin `crear-pull-secret-ghcr.sh` | 3 fallan, muerto |
| `_HEADING` no detecta nada | 25 fallan, muerto |

No hice un mutante de la regla `minikube start`, porque está escrita en línea dentro de `violations`. La cubren de forma exacta `sin-calico.md` y otros dos controles.

Sondas de evasión sobre `violations(ok.md + línea)`: ver F-03.

## Hallazgos

### F-01 · NARANJA · deploy/demo-analyzer/README.md:27 y :94-95 · La forma admitida del usuario de GHCR está mal, y el plan B depende de ella
- La guía dice que el usuario y el token admiten «letras, cifras, guion y guion bajo».
- El script no admite guion bajo en el usuario: `crear-pull-secret-ghcr.sh:33` usa `^[A-Za-z0-9-]+$`. Solo el token lo admite (`:37`, `^[A-Za-z0-9_-]+$`).
- El plan B le pide al humano crear `veridicus-ghcr` «usando valores de relleno con la forma admitida», sin dar ningún ejemplo. Un relleno natural como `relleno_usuario` hace que el script salga con 2.
- **Arreglo:** separar las dos formas (usuario: letras, cifras y guion; token: además guion bajo). En el plan B, dar el relleno literal para el `.env`: `VERIDICUS_GHCR_USER=relleno` y `VERIDICUS_GHCR_TOKEN=relleno`. Decir también que se corre antes de `demo-analyzer.sh`.

### F-02 · NARANJA · deploy/demo-analyzer/README.md:75-76 · La frontera de datos promete más de lo que hacen sus controles (AUTONOMIA-04)
- **«Ningún otro pod tiene salida (`veridicus-deny-all`)».** Esa política está en el namespace (`networkpolicy.yaml:6-11`, `podSelector: {}`) y solo cubre `veridicus-demo`. Además solo se cumple con Calico activo. Los pods de `kube-system` y de cualquier otro namespace siguen teniendo salida.
- **«Hacia fuera solo cruza … hacia Anthropic, por el puerto 443».** La `NetworkPolicy` deja salir por 443 a **cualquier** IP pública: `0.0.0.0/0` menos los rangos privados (`networkpolicy.yaml:26-36`). El límite a Anthropic, y la seudonimización, los pone el anonimizador dentro del proceso; así lo dice el comentario de `networkpolicy.yaml:14`. La guía no dice qué control hace cumplir cada cosa.
- **Arreglo propuesto:**
  - «Ningún otro pod **del namespace `veridicus-demo`** tiene salida (`veridicus-deny-all`, que exige Calico)».
  - «La `NetworkPolicy` deja al Job HTTPS (443) hacia IP públicas y DNS hacia `kube-dns`. El destino Anthropic y la seudonimización los impone el anonimizador dentro del proceso».
  - Opcional: «solo el Job **declara** el Secret; en el clúster no hay una política de admisión que lo impida (Kyverno corre solo en la CI)».

### F-03 · AMARILLO · deploy/tests/readme_checks.py:27-35 · La prueba deja huecos fáciles de explotar
Lo comprobé con sondas en memoria; en cada caso `violations` devolvió `[]` aunque la regla debía fallar:
- `bash scripts/otra/nada.sh`: una ruta de script fuera de `scripts/humano` no se comprueba.
- `.github/workflows/no-existe.yml`: las rutas de `.github/` no se comprueban, y el README sí cita `.github/workflows/analyzer-image.yml`.
- `redeploy/demo-analyzer/job.yaml`: `_PATH` no tiene límite a la izquierda.
- `ghs_…`: los tokens de Actions y los OAuth (`ghs_`, `gho_`, `ghu_`) no están en `_SECRET_SHAPES`.
- Una línea `minikube start \` con `--cni=calico` en la línea siguiente da un falso positivo. No pasa en el README actual.
- La regla de secciones solo busca la palabra en un encabezado: un único encabezado que contenga las siete palabras clave basta.

**Arreglo:** `_PATH = (?<![\w.\-])(?:\.github|scripts|deploy|libs|contracts)/…`, ampliar `_SECRET_SHAPES` a `gh[pousr]_` y añadir un control negativo para cada caso.

### F-04 · AMARILLO · deploy/demo-analyzer/README.md:84-96 · Faltan precisiones en el plan A y el plan B
- Plan A: decir que el token de GHCR es un PAT clásico con `read:packages`.
- Plan B: decir que se construye **antes** del script 3, y en la reversión borrar la imagen local con `minikube image rm <imagen:etiqueta>`.

## Plan B: lo que comprobé (pregunta 2)
- **`imagePullPolicy`:** `job.yaml` no la fija, y kustomize pone la etiqueta `sha-pendiente`, que no es `latest`. El API server la deja entonces en `IfNotPresent`: si la imagen ya está en el runtime del nodo de Minikube, el kubelet no la descarga. Es correcto, por la regla de valores por omisión de Kubernetes.
- **`imagePullSecret` con relleno:** el kubelet solo usa el Secret cuando descarga. Con la imagen presente no se consulta, y un Secret con credenciales inválidas no impide crear el pod. No rompe nada, siempre que el relleno pase la regex del script (ver F-01).
- **`-f` y contexto:** el contexto es la raíz del repositorio y `-f` es relativo a ella. Da igual si minikube lee `-f` respecto al contexto o al directorio actual. Es el mismo Dockerfile y el mismo contexto que `analyzer-image.yml:57/94`.
- **Constructor:** el Dockerfile no usa sintaxis exclusiva de BuildKit (`COPY --from=<imagen>` funciona también con el constructor clásico).

## No verificado
- Cómo se comporta `minikube image build` en la práctica: si respeta `.dockerignore` al empaquetar el contexto y cómo resuelve `-f`. No hay VM, y la documentación por MCP cubre solo la API de Claude, no minikube. Lo razoné leyendo el código del repositorio.
- La etiqueta `k8s-app=calico-node`, que `kubectl delete -k` borre el namespace con sus Secrets, y la forma real de los logs (solo la contrasté con el código de `entrypoint.py`).
- Los mutantes de la regla `minikube start`, que no se pueden aislar.

## Fidelidad del README (pregunta 1), contrastada con el código
Coinciden con el código:
- **Usos y salidas de los scripts:** los usos con `<.env>`, las salidas con 2 de los tres scripts (salvo F-01), el borrado previo del Job, la espera de 900 s, el código del Job y el 1 de la sonda.
- **Mensajes:** los mensajes `La red está cerrada…` y `La NetworkPolicy NO bloquea…`, con los códigos de curl 6, 7 y 28.
- **Logs:** los formatos de `entrypoint.py` (`<nombre>: estado=…, N hallazgo(s)`, `cita A (turno Tn): «…»`), el orden alfabético, los códigos 4 y 5 y el mensaje de la CLI.
- **Imagen:** el nombre de la imagen y la etiqueta provisional.
- La CLI devuelve 0 aunque algún archivo quede en `error` (`cli/main.py:274`), así que «Job sale con 4» es correcto.

## Tareas candidatas (fuera de alcance)
- `demo-analyzer.sh` sigue exigiendo `veridicus-ghcr` aunque se use el plan B. Ya lo propone la bitácora.
- `demo-analyzer.sh:50` lee `.items[0]` del selector `job-name`. Como `kubectl delete job` borra en segundo plano, un pod de la corrida anterior todavía vivo podría dar un código de salida equivocado.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/demo-analyzer/README.md:27|La forma admitida del usuario de GHCR está mal (sin guion bajo) y el relleno del plan B no trae ejemplo
NARANJA|deploy/demo-analyzer/README.md:75|La frontera de datos promete más que la NetworkPolicy: el deny-all es solo del namespace y el 443 va a cualquier IP pública
AMARILLO|deploy/tests/readme_checks.py:27|Rutas de .github y scripts/otra sin comprobar, _PATH sin límite a la izquierda, faltan ghs_/gho_
AMARILLO|deploy/demo-analyzer/README.md:84|Plan A y B: PAT clásico read:packages, orden del build y minikube image rm en la reversión
INFORME: docs/loop/revisiones/U02-T04/ronda-1.md
```
