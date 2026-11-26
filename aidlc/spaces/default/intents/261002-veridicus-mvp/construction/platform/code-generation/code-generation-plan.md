# Plan de Code Generation de U2 platform: B4-demo

**Unidad:** U2 platform (packaging). **Bolt:** B4-demo, un corte de B4 que se adelanta.
**Decisión del humano (2026-11-26):** «Necesito algo que funcione en Kubernetes para mostrarlo corriendo en Kubernetes: puede ser el demo de la CLI, pero corriendo en Kubernetes». Eligió la opción «Job de la CLI». La demo es el sábado 2026-11-28.
**Modo:** liviano (DT31): 15 pasos como máximo (DP-03), tareas del loop con 3 a 6 pasos cada una, y revisor `opus` en las tareas de riesgo alto.
**Estado:** propuesto. Falta `Approve Plan` del humano.

## Qué se va a mostrar

1. La CLI del analizador (B11a, `analyzer-v0.1.0`) corre como **Job de Kubernetes** en Minikube, dentro de una VM Ubuntu de 32 GB con Calico.
2. Lee dos transcripciones **sintéticas** de un ConfigMap: una con una contradicción sembrada y un relato coherente. Llama a Anthropic con el anonimizador en el mismo proceso y escribe en los logs del pod la salida C6. La contradicción sembrada debe dar al menos un hallazgo con sus dos citas verificadas, y el relato coherente, cero hallazgos.
3. La `NetworkPolicy` niega toda salida del namespace. La única excepción es ese Job, y solo hacia el puerto 443 y el DNS. Un pod de prueba en el mismo namespace no llega a internet.
4. La clave de Anthropic vive en un `Secret` que crea el humano. Solo la monta el Job.

## Precisiones al diseño aprobado (no se edita el original)

| ID | Documento aprobado | Precisión | Por qué |
|---|---|---|---|
| DP-04 | `bolt-plan.md` B4 y DP-03; `team.md` Deployment («la NetworkPolicy la niega a todos los pods salvo al anonimizador»); AC11.6.4 (mitad U2: Secret solo en `anonymizer-proxy`) | En B4-demo, el único pod con salida a internet y el único que monta el Secret es el Job de la CLI. Ese Job lleva el anonimizador dentro del proceso (P16 = A) y falla cerrado: la CLI no arranca con un destino externo sin anonimizador (código 3) y no sale ninguna llamada si este falla. `anonymizer-proxy` (C21) sigue en B10b, y la política «solo el proxy sale» se aplica cuando exista. | No existe ningún servicio todavía. Es la forma más corta de correr en Kubernetes sin rebajar AUTONOMIA-04: el anonimizador sigue delante de toda llamada externa. |
| DP-05 | `bolt-plan.md` (orden B10b → B11b → B2–B9) | B4-demo se adelanta a B10b, B11b, B2 y B3. El resto de B4 (charts de los servicios, Kyverno completo, Argo CD, prueba de humo de `scripts/smoke.sh` con la consola) queda en B4 tal cual. | La demo del sábado necesita mostrar algo en Kubernetes. |
| DP-06 | Infrastructure Design de U2 (IDS-U2-01: Minikube de 50 GiB y 16 CPU en el equipo de 64 GB) | Para la demo: VM Ubuntu de 32 GB con Minikube y la CNI Calico (`--cni=calico`), 8 GiB y 4 CPU para Minikube. No hay modelos locales en este corte. | El Job solo necesita la CLI y Anthropic. Calico hace que la `NetworkPolicy` se cumpla. |
| DP-07 | `team.md` Testing Posture (`helm template` → `kubeconform` → Kyverno CLI) | Los manifiestos de la demo son YAML planos con `kustomization.yaml`, sin chart de Helm: el humano aplica con `kubectl apply -k`. Las políticas se comprueban en dos capas. En local y en la CI, pruebas `pytest` sobre el YAML, con un control negativo por política. Solo en la CI, `kustomize build` → `kubeconform` → Kyverno CLI, todo fijado por versión y suma SHA-256. | El contenedor de trabajo no tiene `helm`, `kubeconform` ni Kyverno, y un chart no aporta nada para un solo Job. |
| DP-08 | Mapa AUTONOMIA-01 de `team.md` («ningún workflow ni script aplica cambios al clúster») | La comprobación estática prohíbe `kubectl apply\|create\|delete\|patch`, `helm install\|upgrade` y `sbatch` en `.github/` y en todo script, salvo los de `scripts/humano/`. Esos scripts los corre solo el humano, empiezan con la marca `# Lo ejecuta el humano (AUTONOMIA-01)` y ningún workflow los invoca. | El Secret lo crea el humano con un script revisable (team.md, Secrets), y ese script tiene que tocar el clúster. |

## Pasos

Cada paso nombra su verificación (AUTONOMIA-02). El riesgo alto se revisa con `opus` (ML-4).

### Tarea A: imagen de la CLI (pasos 1 a 3). Riesgo alto: lleva el anonimizador y la clave.

1. **Entrada sintética.** `deploy/demo-analyzer/entrada/contradiccion.json` y `coherente.json` en formato C6 de entrada, sintéticos, sin nada del piloto. Se reutilizan las entrevistas sintéticas de `libs/incoherence_analyzer/tests/support.py` o de la prueba manual, si sirven.
   *Verificación:* una prueba `deploy/tests/test_entrada.py` valida los dos archivos contra el esquema C6 de entrada y pasa el escáner de datos del piloto que ya usa `repo-level0`.
2. **Punto de entrada de la demo.** `deploy/images/analyzer-cli/demo_entrypoint.py` llama a `veridicus analyze /entrada --perfil demo-anthropic --salida /salida` y escribe en stdout, por cada archivo, el estado, el número de hallazgos y, de cada hallazgo, `hecho`, `tipo` y las dos citas con su turno. No imprime la transcripción completa ni la clave. El código de salida es el de la CLI.
   *Verificación:* pruebas con el doble del proveedor de B11a. Con la contradicción salen 1 o más hallazgos; con el relato coherente, 0. Sin la clave sale el código 3 y ninguna llamada. Con el anonimizador caído no sale ninguna llamada. Ni la clave ni una cadena canario de la transcripción aparecen en stdout ni en stderr.
3. **Dockerfile.** `deploy/images/analyzer-cli/Dockerfile` en varias etapas, con `python:3.12-slim` fijada por digest. Instala la CLI con `uv sync --frozen --no-dev --extra cli` sin modo editable, corre con el usuario 10001 sin shell de login y deja `ENTRYPOINT` en el punto de entrada. No copia `.env`, `resultados-locales/` ni pruebas, y usa `.dockerignore`.
   *Verificación:* `deploy/tests/test_dockerfile.py` exige un digest en cada `FROM`, `USER` numérico distinto de 0, ningún `latest` y ningún `COPY` de `.env`. En la CI, `hadolint` en 0 y el *build* de la imagen.

### Tarea B: manifiestos y políticas (pasos 4 a 7). Riesgo alto: AUTONOMIA-01 y AUTONOMIA-04.

4. **Namespace y Job.** `deploy/demo-analyzer/` con `kustomization.yaml`, el `Namespace` `veridicus-demo` con las etiquetas de Pod Security `restricted` y el `Job` `veridicus-analyzer-demo`. El Job lleva:
   - `backoffLimit: 0`, `activeDeadlineSeconds: 900` y `ttlSecondsAfterFinished: 3600`;
   - `automountServiceAccountToken: false`;
   - `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]` y `seccompProfile: RuntimeDefault`;
   - `requests` y `limits` de CPU y memoria;
   - un `emptyDir` en `/salida` y en `/tmp`, y la entrada desde un ConfigMap generado con `configMapGenerator`;
   - `VERIDICUS_ANTHROPIC_API_KEY` por `secretKeyRef` (`veridicus-anthropic`, opcional: no) y `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300`;
   - la imagen `ghcr.io/<dueño>/veridicus-analyzer-cli` con la etiqueta del SHA del commit y un `imagePullSecrets` que crea el humano.

   *Verificación:* `deploy/tests/test_manifests.py` lo comprueba campo por campo.
5. **`NetworkPolicy`.** `deny-all` para la entrada y la salida de todo el namespace. Además, `allow-analyzer-egress`, solo para el selector del Job: TCP 443 hacia `0.0.0.0/0` salvo `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` y `169.254.0.0/16`, y UDP y TCP 53 hacia `kube-dns` en `kube-system`. La lista de dominios la impone el propio anonimizador; CoreDNS queda para B4 completo.
   *Verificación:* las pruebas exigen que exista `deny-all` con `policyTypes` de entrada y salida, y que ninguna otra política dé salida a otro selector. Control negativo: un manifiesto con una segunda política de salida para otro pod hace fallar la prueba.
6. **Políticas estáticas, con su control negativo.**
   - **(a)** Solo el Job referencia el Secret `veridicus-anthropic` (AC11.6.4, con la lectura de DP-04). Control: un Deployment de prueba que lo monta.
   - **(b)** Toda imagen lleva un digest o un SHA, nunca `latest`.
   - **(c)** El `securityContext` es `restricted`.
   - **(d)** Hay `resources` en todo contenedor.
   - **(e)** AUTONOMIA-01 se cumple como dice DP-08. Controles: un workflow con `kubectl apply` y un script fuera de `scripts/humano/` con `kubectl apply`.

   Las mismas reglas van como políticas de Kyverno en `deploy/policies/`, con casos de paso y de fallo.
   *Verificación:* `uv run --frozen --offline --directory deploy pytest -q`, con cada control negativo en rojo. En la CI, `kyverno test deploy/policies`.
7. **Scripts del humano.** En `scripts/humano/`, con la marca de DP-08:
   - `crear-secret-anthropic.sh`, que lee `VERIDICUS_ANTHROPIC_API_KEY` de un `.env` no versionado y crea el Secret sin imprimir la clave;
   - `crear-pull-secret-ghcr.sh`;
   - `demo-analyzer.sh`, que aplica con `kubectl apply -k`, espera al Job, imprime los logs y comprueba la `NetworkPolicy` con un pod `curl` efímero que debe fallar.

   *Verificación:* `shellcheck`, solo en la CI, y una prueba que exige la marca, `set -euo pipefail` y que no haya ningún `echo` de la clave. El orquestador nunca ejecuta estos scripts.

### Tarea C: CI e imagen publicada (pasos 8 y 9). Riesgo bajo: andamiaje de la CI.

8. **`deploy-level0.yml`.** Corre las pruebas de `deploy/`, `kustomize build`, `kubeconform -strict` con los esquemas de Kubernetes 1.31 (descargados en el *job*, fijados por versión y suma SHA-256), `kyverno test`, `hadolint` y `shellcheck`. Usa `permissions: contents: read`, acciones fijadas por SHA y ningún `kubeconfig`.
   *Verificación:* el workflow queda en verde en el PR. Un commit de prueba con el control negativo queda en rojo y se revierte, y el enlace a ese rojo se guarda en la bitácora.
9. **`analyzer-image.yml`.** En un *push* a `main` que toca `libs/**`, `contracts/**` o `deploy/images/**`, construye la imagen, la etiqueta con el SHA y la publica en GHCR. Trivy bloquea `HIGH` y `CRITICAL` con corrección. Solo el *job* de *build* tiene `packages: write`. Escribe el digest en el resumen del *job*.
   *Verificación:* corrida verde tras la fusión y digest visible. Antes de fusionar, el *build* corre en el PR sin publicar.

### Tarea D: guía y demo (pasos 10 a 12). Riesgo bajo, con verificación manual del humano.

10. **Guía de la demo.** `deploy/demo-analyzer/README.md` lleva:
    - los requisitos de la VM: Ubuntu, Docker, `minikube start --cni=calico --memory=8g --cpus=4` y `kubectl`;
    - el orden de los scripts del humano;
    - qué se ve en los logs;
    - cómo comprobar la `NetworkPolicy`;
    - la reversión con `kubectl delete -k deploy/demo-analyzer`;
    - qué datos cruzan la frontera: solo texto sintético seudonimizado hacia Anthropic (AUTONOMIA-04, declaración por componente).

    *Verificación:* una prueba de enlaces y comandos comprueba que cada ruta citada exista.
11. **Imagen fijada en el manifiesto.** Tras la fusión y la corrida de `analyzer-image.yml`, un PR de una línea fija el SHA de la imagen en `kustomization.yaml` (`images:`).
    *Verificación:* las pruebas de `deploy/` pasan y la imagen ya no usa una etiqueta provisional.
12. **Demo en la VM, que hace el humano.** Corre `scripts/humano/demo-analyzer.sh`, y se registran como evidencia en `docs/loop/bitacoras/B4-demo.md` la salida de los logs y la comprobación de la `NetworkPolicy`.
    *Verificación:*
    - el Job termina con `Complete`;
    - la contradicción da 1 o más hallazgos con dos citas;
    - el relato coherente da 0;
    - el pod `curl` no llega a `https://example.com` (es la verificación manual de AUTONOMIA-04 del mapa de team.md).

## Mapa AUTONOMIA

| Regla | Prueba |
|---|---|
| 01 | paso 6 (e) y DP-08; el orquestador no aplica nada |
| 02 | cada paso lleva su verificación |
| 03 | sin cambios: el escáner de vocabulario de B11a ya corre en la salida; el paso 2 no añade texto propio |
| 04 | paso 2 (fallo cerrado y sin clave), paso 5 (`NetworkPolicy`), paso 6 (a) (Secret solo en el Job) y paso 12 (manual) |
| 05 | sin cambios: la CLI de B11a ya verifica las citas; el paso 2 solo imprime lo que salió |

## Fuera de este corte

`anonymizer-proxy`, los servicios de B2 y B3, Helm, Argo CD, CoreDNS con lista blanca, Prometheus y Grafana, KEDA, CloudNativePG y la prueba de humo `scripts/smoke.sh` completa. Todo queda en B4 y B10b como estaba.

## Riesgos

- **R-B4d-1:** GHCR privado exige el `imagePullSecret` en la VM. Si falla la publicación, el plan B es que el humano construya la imagen en la VM con `minikube image build`. Eso se anotaría como desviación de team.md (las imágenes salen de la CI) y solo valdría para la demo.
- **R-B4d-2:** si Calico no queda activo, la `NetworkPolicy` no bloquea. El paso 12 lo detecta con el pod `curl`.
- **R-B4d-3:** el plazo. Las tareas A y B son el camino crítico, y C y D pueden ir en paralelo con B.
