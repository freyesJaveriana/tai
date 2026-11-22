# Requisitos de seguridad — U2 platform

**Revisión 2 (2026-11-22). Segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **IDs.** Los requisitos conservan su ID; ninguno se renumera. Lo nuevo toma el número siguiente de su
  grupo: NFR1.4–NFR1.7, NFR8.2–NFR8.3, NFR10.11–NFR10.19, NFR11.2, NFR12.2 y NFR15.2. Cada fila dice si
  **se mantiene**, **cambia** o es **nuevo**. Nada queda «Retirado» como fila, pero salen de los criterios
  `pgvector`, el servidor de *embeddings*, el rol `veridicus_judge_ro` (C9) y la propuesta de umbral de la
  regla AIR (US10.6).
- **Respuesta de esta pasada:** P5 = A (excepción declarada solo para `argocd-repo-server` hacia
  `github.com`; `github.com` entra en CoreDNS como dominio de infraestructura con su motivo).
- **Revisión 1:** se cierran sus hallazgos R-01 a R-07 (`reviews/review-01.md`); la tabla de §7 dice dónde.

**Insumos.**
- Definición de U2 en `inception/units-generation/unit-of-work.md` (revisión 3). U2 es de tipo `packaging`
  y no tiene Functional Design propio, así que no consume `functional-spec` ni `rules` de su unidad.
- FR12 y NFR1–NFR15 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3; NFR9
  «Retirado»), y VE-12 de `requirements-adenda-02.md`.
- AC9.1.1–AC9.1.4, AC9.4.1–AC9.4.2, AC9.5.1–AC9.5.2, AC10.7.1, AC10.8.1–AC10.8.2, AC11.5.1–AC11.5.2 y
  AC11.6.1–AC11.6.4 de `inception/user-stories/stories.md` (revisión 3).
- C14–C16, C21, C22, C25, CD-04, CD-06 y CD-07 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3).
- Lo que piden a U2 los Functional Design aprobados: U3 (F7, `create-admin` y usuarios de base), U4, U9 (D4,
  ruta interna de síntesis), U10 (F9 y FD-U10-06) y U13 (F7 y §11 pregunta 4).
- Respuestas P1–P5 de `nfr-requirements-questions.md`; prácticas `## Deployment`, `## Forbidden` y
  `## Mandated` de `team.md` y `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla (`NFR10.3` detalla NFR10). Las comprobaciones
automáticas son de **nivel 0**, sin red ni clúster: `helm template` → `kubeconform` → Kyverno CLI (políticas
en `deploy/policies/`) más los *scripts* de comprobación de `scripts/`, y cada una lleva su **control
negativo** (un manifiesto o archivo que debe fallar). Los comandos exactos están en
`tech-stack-decisions.md` §4. Ningún paso aplica cambios al clúster (AUTONOMIA-01).

## 1. Frontera (AUTONOMIA-04)

| Componente | Namespace | Dentro o fuera del clúster | Datos que cruzan la frontera |
|---|---|---|---|
| `session-api`, `semantic-agent`, `audio-worker`, `frontend` | `veridicus` | Dentro | Ninguno: el testimonio, la CoT y el audio no salen (C1–C5) |
| PostgreSQL (CloudNativePG) y Redis | `veridicus` | Dentro | Ninguno |
| Servidores locales: juez, verificador, Whisper y TTS | `veridicus` | Dentro | Ninguno (reciben el texto sin anonimizar, pero no tienen salida) |
| `anonymizer-proxy` | `veridicus` | Dentro; **única salida con datos** | Solo texto seudonimizado, por 443, hacia los tres dominios de C22; la tabla de correspondencia nunca sale ni se registra |
| `Job` de migraciones, de `create-admin` y de retención | `veridicus` | Dentro | Ninguno |
| `ingress-nginx` | `ingress-nginx` | Dentro (termina TLS, ve el testimonio) | Ninguno |
| Operador CloudNativePG, Prometheus y Grafana, KEDA | `cnpg-system`, `monitoring`, `keda` | Dentro | Ninguno |
| `argocd-repo-server` | `argocd` | Dentro; **segunda salida, sin datos** (P5 = A) | Solo la lectura del repositorio público en `github.com`; no alcanza `veridicus` |
| Proveedores comerciales (C22) | — | Fuera | Reciben solo texto seudonimizado |
| GitHub, CI y GHCR | — | Fuera | Solo código e imágenes |
| Archivos de modelo | Anfitriona | Fuera de los pods | Se descargan con un *script* revisable y llegan a un volumen de solo lectura |

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Un pod con testimonio envía datos a internet | Information disclosure | Alto | NFR1.1, NFR1.4, NFR1.6 |
| T2 | Un archivo de modelo alterado, o un modelo descargado en ejecución | Tampering | Alto | NFR1.2, NFR10.4, NFR10.11 |
| T3 | Una imagen sin fijar cambia entre la CI y el clúster | Tampering | Medio | NFR10.1 |
| T4 | Un contenedor con root o con privilegios escapa al nodo | Elevation of privilege | Medio | NFR10.2 |
| T5 | Un Secret con su valor en el repositorio | Information disclosure | Alto | NFR10.3 |
| T6 | Un *script* o *workflow* aplica cambios al clúster o lanza trabajos en ZINE sin PR | Tampering | Alto | NFR10.5 |
| T7 | Un pod sin límites agota la máquina | Denial of service | Medio | NFR8.1, NFR8.2 |
| T8 | Un pod alcanza Redis, PostgreSQL o un servidor de modelos sin necesitarlo | Spoofing, Information disclosure | Medio | NFR10.6–NFR10.8, NFR10.18 |
| T9 | Argo CD borra la base o sus volúmenes, o relanza un `Job` de borrado | Tampering, Repudiation | Alto | NFR11.1, NFR10.16 |
| T10 | Una vulnerabilidad conocida en una imagen | Elevation of privilege | Medio | NFR10.1 |
| T11 | `anonymizer-proxy` conecta con un dominio fuera de C22 o con una IP literal | Information disclosure | Medio | NFR1.4, NFR1.5 (riesgo residual en §6) |
| T12 | Un pod distinto del proxy lee las claves de los proveedores y llama sin anonimizar | Information disclosure | Alto | NFR10.12 |
| T13 | `argocd-repo-server` se usa como salida o como puerta hacia `veridicus` | Information disclosure, Elevation of privilege | Medio | NFR1.7 |
| T14 | Los perfiles montados difieren de los del commit (otro modelo, otro destino) | Tampering | Medio | NFR10.15 |
| T15 | Contraseña, cookie o testimonio en claro entre el navegador y el clúster | Information disclosure | Medio | NFR10.14 |
| T16 | El testimonio o un *canary* aparece en los logs | Information disclosure | Medio | NFR10.19 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | Cambia | Entrada y salida negadas por defecto en `veridicus`; solo `anonymizer-proxy` sale a internet (FR12.3, AC9.1.1). | `NetworkPolicy` `veridicus-default-deny` con `podSelector: {}` y `policyTypes: [Ingress, Egress]`. Las demás solo abren DNS (53 UDP/TCP hacia `kube-dns`) y las dependencias de `tech-stack-decisions.md` §3. Ninguna regla de salida usa un `ipBlock` fuera de los rangos del clúster, salvo la de `anonymizer-proxy` (NFR1.5). Política Kyverno con control negativo: un `Deployment` de `semantic-agent` con salida a `0.0.0.0/0` falla, y también el proxy con el puerto 80. Antes de la sustentación, la verificación manual de AC9.1.2: desde cada pod distinto del proxy y de `argocd-repo-server`, `curl -m 5 https://example.com` termina con código ≠ 0, y el mismo pod alcanza PostgreSQL o Redis si los usa (control positivo). Solo lectura, sin `apply`. | Nivel 0 y manual |
| NFR1.2 | Se mantiene | Ningún pod descarga modelos. | `scripts/fetch-models.sh` descarga los archivos en la anfitriona y verifica el `sha256` de cada uno contra `deploy/models.lock`. Los pods los montan en solo lectura (NFR10.11). Ningún contenedor ni `initContainer` ejecuta `curl`, `wget`, `huggingface-cli` ni equivalente (comprobación estática con control negativo). | Nivel 0 |
| NFR1.3 | Cambia | Los modelos locales tienen destinos internos. | Las URL de los servidores locales del render (`VERIDICUS_JUDGE_URL`, `VERIDICUS_VERIFIER_URL`, `VERIDICUS_WHISPER_URL`, `VERIDICUS_TTS_URL`) y los destinos locales de `config/profiles.yaml` terminan en `.svc.cluster.local` (C14). Un destino externo del perfil solo es alcanzable por la dirección de `anonymizer-proxy` (C21). Sale `VERIDICUS_EMBEDDINGS_URL`. Control negativo: una URL de juez con un dominio público falla. | Nivel 0 |
| NFR1.4 | Nuevo | La lista blanca de CoreDNS es la de C22 más una lista cerrada de infraestructura (AC11.5.2 precisada por P5 = A, NFR-U2-02). | `deploy/coredns/Corefile` resuelve hacia fuera solo los dominios de la unión de dos listas: los de `libs/anonymizer/data/allowed-domains.v1.yaml` (exactamente `api.anthropic.com`, `generativelanguage.googleapis.com` y `api.openai.com`) y los de `deploy/coredns/infra-domains.yaml` (hoy solo `github.com`, con su motivo «lectura de Argo CD, US10.7»). `scripts/check-coredns-domains.sh` quita del Corefile la lista de infraestructura, pasa el resto a la función F9 de U10, que exige igualdad exacta, y además comprueba que ningún dominio de infraestructura está en la lista del anonimizador. Controles negativos: un dominio de más en el Corefile, un dominio de infraestructura sin motivo y `github.com` en la lista del anonimizador fallan. | Nivel 0 |
| NFR1.5 | Nuevo | `anonymizer-proxy` solo recibe de `semantic-agent` y solo sale por 443 (C21, FR12.3). | Entrada: solo desde pods `app.kubernetes.io/name: semantic-agent` del mismo namespace. Salida: TCP 443 hacia `0.0.0.0/0` con `except` de los rangos privados (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) y de los del clúster, más DNS a `kube-dns`. El dominio lo impone el módulo y no sigue redirecciones (AC11.5.1, FD-U10-05). Control negativo: una regla con el puerto 80 o sin `except` falla. | Nivel 0 |
| NFR1.6 | Nuevo | Tampoco salen los pods de los demás namespaces que instala U2 (FR12.3, «todos los pods»). | `ingress-nginx`, `cnpg-system`, `monitoring`, `keda` y `argocd` llevan su propia `NetworkPolicy` de negar la salida por defecto. Solo abren DNS, el tráfico interno que nombra §3 de `tech-stack-decisions.md` y el API server. Grafana va con `check_for_updates: false`, sin instalación de *plugins* en ejecución y sin análisis de uso. Control negativo: un namespace sin su política falla. | Nivel 0 y manual (AC9.1.2) |
| NFR1.7 | Nuevo | Excepción declarada solo para Argo CD (P5 = A, NFR-U2-01). | Solo `argocd-repo-server` sale fuera del clúster: TCP 22 y 443 hacia `0.0.0.0/0` con el mismo `except` de NFR1.5. Resuelve `github.com` por la lista de infraestructura de NFR1.4. Ningún otro pod de `argocd` tiene salida externa. La entrada a `veridicus` no admite nada desde `argocd`, y la *deploy key* es de solo lectura (AC10.7.1). Política Kyverno con una lista cerrada de excepciones (`anonymizer-proxy`, `argocd-repo-server`); control negativo: `argocd-server` o `argocd-application-controller` con salida externa falla. Manual: desde `argocd-repo-server`, `git ls-remote` al repositorio responde y `curl -m 5 https://example.com` falla. | Nivel 0 y manual |

### NFR10 — Seguridad de la plataforma

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | Cambia | Toda imagen está fijada y escaneada (R-03). | Las imágenes propias de GHCR llevan `@sha256:` y nunca `latest`. Las de terceros llevan versión exacta de chart y digest cuando el chart lo admite. Cada excepción vive en `deploy/image-exceptions.yaml` con motivo y fecha de caducidad, y una excepción vencida falla. Trivy no admite vulnerabilidades `HIGH` ni `CRITICAL` con corrección en las imágenes propias. Control negativo: una imagen propia con etiqueta falla. | Nivel 0 (Kyverno) y CI (Trivy) |
| NFR10.2 | Se mantiene | Todo pod cumple el perfil `restricted` de Pod Security. | Los namespaces `veridicus` y `argocd` llevan `pod-security.kubernetes.io/enforce: restricted`. Cada contenedor declara `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault` y `readOnlyRootFilesystem: true`, con `emptyDir` donde haga falta escribir. Los namespaces de operadores llevan al menos `baseline`, y cada desvío se registra con su motivo. | Nivel 0 |
| NFR10.3 | Se mantiene | Los manifiestos solo referencian Secrets. | 0 objetos `kind: Secret` con `data` o `stringData` en `deploy/`. Los valores llegan por `secretKeyRef` o `envFrom`. `gitleaks` sin hallazgos. El humano crea los Secrets desde su `.env` con `scripts/create-secrets.sh`, que no contiene valores. | Nivel 0 y CI |
| NFR10.4 | Se mantiene | Los archivos de modelo se verifican también al arrancar. | Un `initContainer` de cada servidor local calcula el `sha256` del archivo montado y termina con error si no coincide con `models.lock`, y el servidor no arranca. Control negativo con un archivo alterado en una prueba de nivel 1 de U2 (contenedor local). | Nivel 0 (presencia) y nivel 1 |
| NFR10.5 | Cambia | Nada aplica cambios al clúster ni lanza trabajos en ZINE sin PR (AUTONOMIA-01, AC9.5.1, AC9.5.2, R-07). | `scripts/check-no-cluster-apply.sh` busca con expresiones regulares tolerantes a espacios y a líneas partidas en `.github/`, `scripts/` y `deploy/`: `kubectl` con `apply`, `create`, `replace`, `patch`, `delete`, `edit`, `scale`, `rollout`, `set` o `annotate`; `helm` con `install`, `upgrade`, `uninstall` o `rollback`; `terraform apply` o `destroy`; `alembic upgrade` contra el clúster; toda referencia a `kubeconfig` en un *workflow*; todo `kind: CronJob`; y `sbatch`, `ssh`, `scp` o `rsync` hacia ZINE en *workflows* y en los *scripts* que corre la CI. 0 apariciones. Controles negativos con un *workflow* por patrón. Los `.sbatch` solo existen como archivos que lanza el humano. | Nivel 0 |
| NFR10.6 | Cambia | Redis exige contraseña y solo lo alcanzan sus clientes. | `requirepass` desde un Secret y `protected-mode yes`. La `NetworkPolicy` de entrada a Redis solo admite `session-api`, `semantic-agent`, `audio-worker` y el `Job` de retención (escribe la clave de cancelación de CD-06). | Nivel 0 |
| NFR10.7 | Cambia | PostgreSQL sin superusuario expuesto y con usuarios separados. | `enableSuperuserAccess: false` en el `Cluster` de CloudNativePG, sin la extensión `pgvector` (AC9.4.1) y con TLS entre clientes y base. Hay tres usuarios: `veridicus_owner` (solo el `Job` de migraciones), `veridicus_app` (`session-api` y el `Job` de `create-admin`) y `veridicus_retention` (solo el `Job` de retención). Solo esos cuatro consumidores y el operador alcanzan el puerto 5432; **`semantic-agent` ya no lo alcanza** (C9 «Retirado», CD-06). Control negativo: una regla de `semantic-agent` hacia 5432 falla. | Nivel 0 |
| NFR10.8 | Cambia | Los servidores de modelos solo atienden a sus clientes. | Juez y verificador solo admiten `semantic-agent`; Whisper y TTS solo admiten `audio-worker`. `llama-server` exige `--api-key` leída de un Secret. Sale el servidor de *embeddings*. | Nivel 0 |
| NFR10.9 | Cambia | Los pods de la aplicación no reciben credenciales de Kubernetes (R-01). | `automountServiceAccountToken: false` en todos los pods de `veridicus` hechos por U2 (servicios, servidores de modelos, Redis y los tres `Job`), sin `Role` ni `ClusterRole`. Quedan exentos, con su motivo en el chart, los pods de instancia de CloudNativePG (hablan con el API server para su estado) y los operadores de terceros, cuyo RBAC viene del chart oficial con versión fijada. Control negativo: `session-api` con el token montado falla. | Nivel 0 |
| NFR10.10 | Se mantiene | Las migraciones solo corren como `Job` aparte (AC9.4.2). | Ningún `Deployment` ni `initContainer` ejecuta Alembic. El `Job` de migraciones está en su propio archivo y entra por su propio PR (`project.md`). Control negativo. | Nivel 0 |
| NFR10.11 | Nuevo | Los modelos se montan sin `hostPath` (R-02). | Los modelos están en un `PersistentVolume` estático de solo lectura con su PVC (`ReadOnlyMany`), que el humano puebla con `scripts/fetch-models.sh` en la ruta que fija Infrastructure Design. Kyverno rechaza cualquier volumen `hostPath` en el render, con control negativo. | Nivel 0 |
| NFR10.12 | Nuevo | Las claves de los proveedores solo llegan a `anonymizer-proxy` (AC11.6.4, parte de U2; CD-04). | En el render, solo el pod de `anonymizer-proxy` referencia el Secret `veridicus-provider-keys`, por `secretKeyRef` o `envFrom`. Control negativo: un manifiesto que lo monta en `semantic-agent` falla. La otra mitad de AC11.6.4 (import-linter sobre `semantic-agent`) es de U4. | Nivel 0 |
| NFR10.13 | Nuevo | Cada Secret de credenciales lo referencia solo su consumidor. | `veridicus-db-owner` solo en el `Job` de migraciones; `veridicus-db-app` solo en `session-api` y `create-admin`; `veridicus-db-retention` solo en el `Job` de retención; `veridicus-speech-token` (`VERIDICUS_SPEECH_TOKEN`, D4 de U9) solo en `session-api` y `audio-worker`; `veridicus-model-api-key` solo en los servidores locales y en sus clientes. La tabla vive en `deploy/policies/secret-consumers.yaml`, y Kyverno falla ante cualquier otra referencia. | Nivel 0 |
| NFR10.14 | Nuevo | TLS en el *ingress* (R-06). | Todo `Ingress` lleva `tls` con el Secret `veridicus-tls`, que crea el humano con un certificado local, y la redirección a HTTPS (`ssl-redirect: "true"`). Lo exigen la cookie `Secure` (C1) y la grabación de voz, que el navegador solo permite en un contexto seguro. Control negativo: un `Ingress` sin `tls` falla. | Nivel 0 |
| NFR10.15 | Nuevo | Los perfiles y precios montados son los del mismo commit (C21). | Un `ConfigMap` `veridicus-profiles` con la copia del chart de `config/profiles.yaml` y `config/prices.yaml` (Helm no lee fuera del chart), montado en solo lectura en `session-api`, `semantic-agent` y `anonymizer-proxy`. `scripts/check-config-copy.sh` exige el mismo SHA-256 que los originales de `config/`. Control negativo: una copia con un byte distinto falla. | Nivel 0 |
| NFR10.16 | Nuevo | Los `Job` que borran o crean cuentas solo los lanza el humano (VE-12, BR5.1 de U13, F7 de U3). | Los `Job` de retención y de `create-admin` viven en el chart `deploy/jobs/`, que la `Application` de Argo CD no incluye. Llevan `backoffLimit: 0` y `activeDeadlineSeconds`. Nunca hay un `CronJob` (NFR10.5). El de retención usa la imagen de `session-api`, monta en lectura y escritura los volúmenes de reportes y de audio de `session-api` y sale solo a PostgreSQL y a Redis. Controles negativos: un `Job` con `backoffLimit: 1`, o una `Application` cuyo `path` incluye `deploy/jobs`, fallan. | Nivel 0 |
| NFR10.17 | Nuevo | Sondas de salud de C16 (FR12.5). | `session-api`, `semantic-agent`, `audio-worker` y `anonymizer-proxy` declaran `livenessProbe` sobre `/healthz` y `readinessProbe` sobre `/readyz`, en un puerto interno que no expone el `Ingress`. Control negativo: un `Deployment` sin sonda falla. | Nivel 0 |
| NFR10.18 | Nuevo | Cada dependencia declarada tiene su regla, y ninguna regla sobra (R-01). | `scripts/check-network-deps.sh` cruza la tabla `deploy/network-deps.yaml` (la de §3 de `tech-stack-decisions.md`) con las `NetworkPolicy` renderizadas: 0 dependencias sin regla y 0 reglas sin dependencia. Incluye el operador de CloudNativePG hacia las instancias (8000 y 5432), las instancias hacia el API server y `session-api` hacia `audio-worker` por la ruta interna de síntesis. Controles negativos: una regla de más y una dependencia sin regla. | Nivel 0 |
| NFR10.19 | Nuevo | Ningún *canary* llega a los logs (AC9.1.4, AC11.6.3). | En el entorno de integración de nivel 1, un turno con un *canary* único sembrado termina, y el *canary* no aparece en los logs capturados de ningún contenedor. U2 aporta la captura de logs de todos los contenedores y la búsqueda; el turno lo siembra la prueba de U4. | Nivel 1 |

### NFR11 — Integridad

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | Cambia | La sincronización nunca borra la base ni relanza borrados (AC10.7.1). | La `Application` de Argo CD (SHOULD) usa una *deploy key* de solo lectura. Desactiva *prune* (`argocd.argoproj.io/sync-options: Prune=false`) sobre el `Cluster` de CloudNativePG, sus PVC, el PVC de Redis y los volúmenes de reportes y de audio. No incluye `deploy/jobs/` (NFR10.16). La sincronización real se verifica a mano. | Nivel 0 y manual |
| NFR11.2 | Nuevo | Las colas sobreviven a un reinicio de Redis (P3 = A, R-07). | La configuración renderizada de Redis tiene `appendonly yes` y `appendfsync everysec`, con `dir` sobre un PVC. Prueba de nivel 1 de U2: después de escribir 10 entradas en un *stream* y reiniciar el contenedor, las 10 siguen. | Nivel 0 y nivel 1 |

### NFR8 — Recursos y salud

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.1 | Se mantiene | Todo contenedor declara `requests` y `limits` (FR12.2). | 100 % de los contenedores e `initContainers`, incluidos los `Job`, con `requests` y `limits` de CPU y memoria; control negativo. Los valores por máquina los fija Infrastructure Design. | Nivel 0 |
| NFR8.2 | Nuevo | El 98 % de NFR8 se mide fuera de U2 (R-04). | U2 entrega `values-cpu.yaml` con los `limits` que fije Infrastructure Design. Build and Test corre las 50 sesiones en tandas de 3 y cuenta los `OOMKilled` y los *timeouts* con el chart de U2 (≥ 98 %). U2 solo cubre la parte de manifiestos de NFR8. | Build and Test |
| NFR8.3 | Nuevo | La prueba de humo comprueba la salud de los cuatro servicios. | `scripts/smoke.sh <url-base>` termina con código 0 solo si `/healthz` de `session-api`, `semantic-agent`, `audio-worker` y `anonymizer-proxy` responde 200 y si pasa `frontend/e2e/smoke.spec.ts` (`team.md`). El *N* de segundos lo fijan U4 y U11. | Nivel 3 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | Cambia | `deploy/` no contiene datos (R-07). | `gitleaks` sin hallazgos y `scripts/check-no-data.sh` sin hallazgos. El *script* comprueba que cada `ConfigMap` del render solo tiene claves de la lista permitida (`profiles.yaml`, `prices.yaml`, el *prompt*, `Corefile`, la configuración de Redis y la de Grafana) y que ningún archivo de `deploy/` trae el marcador de transcripción del conjunto sintético. Control negativo: un `ConfigMap` con una clave `transcript` falla. | Nivel 0 |
| NFR12.2 | Nuevo | El chart no monta corpus. | Ningún volumen del render apunta a rutas del piloto ni a `evaluation/`. Las entrevistas del piloto solo entran por la consola o por la CLI fuera de Git (NFR12 de Inception). Control negativo. | Nivel 0 |

### NFR2 — CPU primero

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR2.1 | Cambia | El chart corre completo sin GPU con el perfil `todo-local`. | `values-cpu.yaml` es el valor por defecto, despliega los servidores locales que nombra el perfil `todo-local` y no pide `nvidia.com/gpu`. Solo `values-gpu.yaml` lo pide. `helm template` con cada archivo de valores pasa las mismas políticas. | Nivel 0 |

### NFR15 — Observabilidad (SHOULD)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR15.1 | Cambia | La regla AIR solo avisa (US10.8, AC10.8.1, AC10.8.2). | La `PrometheusRule` dispara cuando `veridicus_session_dismissal_ratio > 0.25`, una fracción que U5 calcula sobre las últimas *W* decisiones (`dismissal_window_w` de C25; CD-07). No propone umbral y no hace nada que cambie un perfil o un *prompt*. `promtool test rules` usa los *fixtures* 5 de 20 (no alerta) y 6 de 20 (alerta). El render falla si *W* sigue en `null`. | Nivel 0 |
| NFR15.2 | Nuevo | Prometheus raspa las métricas sin exponerlas. | Prometheus alcanza `/metrics` de `session-api` y de `semantic-agent` en el puerto interno (C15, NFR15 de Inception), y ningún `Ingress` lo expone. El panel de Grafana viene como `ConfigMap` versionado. | Nivel 0 |

## 4. Correspondencia con AUTONOMIA-01..05

| Regla | Qué aporta U2 | Requisitos |
|---|---|---|
| AUTONOMIA-01 | Todo cambio al clúster es un artefacto revisado; nada lo aplica solo ni lanza trabajos en ZINE; los `Job` de borrado y de cuentas los lanza el humano | NFR10.5, NFR10.10, NFR10.16, NFR11.1 |
| AUTONOMIA-02 | Cada requisito tiene su comando y su control negativo | Todas |
| AUTONOMIA-03 | La regla AIR solo avisa | NFR15.1 |
| AUTONOMIA-04 | Una sola salida con datos, y seudonimizados; las claves solo en el proxy; DNS cerrado; modelos locales y verificados; frontera por componente | NFR1.1–NFR1.7, NFR10.4, NFR10.11, NFR10.12, NFR10.19 |
| AUTONOMIA-05 | No aplica a U2: la verificación de citas vive en U11 | — |

## 5. Lo que fija otra etapa

| Qué | Quién |
|---|---|
| Distribución de Kubernetes, CNI, ruta del PV de modelos, Corefile concreto y valores de `requests`/`limits` | Infrastructure Design de U2 |
| Modelos concretos del juez y del verificador | NFR Requirements de U11 (perfiles) |
| *W* de la regla AIR | U5 (`dismissal_window_w` de C25) |
| *N* segundos de la prueba de humo | U4 y U11 |
| El 98 % de NFR8 | Build and Test |
| Import-linter sobre `semantic-agent` (AC11.6.4) | U4 |

## 6. Riesgos residuales

| Riesgo | Por qué queda | Mitigación |
|---|---|---|
| `anonymizer-proxy` y `argocd-repo-server` pueden abrir una conexión por 443 a una IP literal | Una `NetworkPolicy` no filtra por dominio | El módulo solo conecta a los dominios de su lista (AC11.5.1) y Argo CD solo a la URL del repositorio. CoreDNS no resuelve ningún otro dominio (NFR1.4). Se acepta para el MVP (P5 = A) |
| El CNI no hace cumplir las `NetworkPolicy` | Depende de la máquina | Infrastructure Design elige Calico; las verificaciones manuales de NFR1.1 y NFR1.7 lo confirman antes de la sustentación |
| La copia de los perfiles en el chart se desincroniza | Helm no lee fuera del chart | NFR10.15 falla en cada PR que toque cualquiera de las dos copias |

## 7. Precisiones y decisiones aplicadas (NFR-U2-xx)

Cada fila sale de una fuente aprobada o de P5. «Precisa» nombra el artefacto aprobado que la fila matiza, y
«—» indica que solo se aplica la fuente. Ningún original se edita: el humano decide en la aprobación si
alguno se actualiza.

| ID | Precisa | Qué | Requisitos | Origen |
|---|---|---|---|---|
| NFR-U2-01 | `requirements.md` (FR12.3) | Además de `anonymizer-proxy`, hay una sola salida declarada: `argocd-repo-server` hacia `github.com` por 22 y 443, sin datos y sin entrada a `veridicus` | NFR1.7 | P5 = A |
| NFR-U2-02 | `stories.md` (AC11.5.2) | La lista blanca de CoreDNS es la del anonimizador **más** una lista cerrada de infraestructura (`github.com`, con su motivo). La igualdad exacta se comprueba contra los dominios de proveedores | NFR1.4 | P5 = A |
| NFR-U2-03 | `stories.md` (AC9.1.1, AC9.1.2) y Functional Design de U10 (F9, paso 2) | La política admite una lista cerrada de dos excepciones. La verificación manual también excluye a `argocd-repo-server`, que tiene su propia comprobación. U2 pasa a F9 el Corefile renderizado sin la lista de infraestructura | NFR1.1, NFR1.4, NFR1.7 | P5 = A |
| NFR-U2-04 | — | `semantic-agent` deja de alcanzar PostgreSQL. Alcanza Redis, el juez, el verificador y `anonymizer-proxy` | NFR10.7, NFR10.18 | C9 «Retirado», CD-06, C21 (punto 1) |
| NFR-U2-05 | — | La salida del proxy es 443 a `0.0.0.0/0` con `except` de los rangos privados y los del clúster. F9 corre sobre el Corefile. El riesgo de la IP literal queda declarado | NFR1.5, §6 | FR12.3, FD-U10-05, FD-U10-06 (punto 2) |
| NFR-U2-06 | `unit-of-work.md` (U2, qué entrega) | Hay un servidor por modelo local del perfil (juez y verificador) más `model-whisper` y `model-tts`. Sale `model-embeddings` | NFR1.3, NFR10.8 | C14, FR14.4 (punto 3) |
| NFR-U2-07 | — | Perfiles y precios van en un `ConfigMap` copiado en el chart, con comprobación de SHA-256 | NFR10.15 | C21; precedente del *prompt* en `project.md` (punto 4) |
| NFR-U2-08 | — | Tres usuarios de base de datos, cada uno con su Secret y su único consumidor | NFR10.7, NFR10.13 | A-2, NFR11 de Inception, F7 de U3 (punto 5) |
| NFR-U2-09 | `team.md` (Deployment: «Argo CD sincroniza automáticamente») y Functional Design de U13 (§11, pregunta 4) | Los `Job` de retención y de `create-admin` viven en `deploy/jobs/`, que Argo CD no sincroniza. Llevan `backoffLimit: 0` y `activeDeadlineSeconds`. El de retención también alcanza Redis (CD-06) | NFR10.16, NFR11.1 | VE-12, BR5.1 de U13, F7 de U3 (punto 6) |
| NFR-U2-10 | — | Rutas nuevas: `session-api` → `audio-worker` (síntesis, con token por Secret), el operador de CloudNativePG → instancias y las instancias → API server. Cada dependencia se cruza con su regla | NFR10.13, NFR10.18 | D4 de U9; R-01 (punto 7) |
| NFR-U2-11 | `infrastructure-specification.md` de U2 (revisión 1) | La negación de la salida también aplica a `ingress-nginx`, `cnpg-system`, `monitoring`, `keda` y `argocd`. Grafana va sin conexión | NFR1.6 | FR12.3, «todos los pods» (punto 8) |
| NFR-U2-12 | — | TLS en el *ingress*, con un certificado local que crea el humano | NFR10.14 | C1 (cookie `Secure`), grabación de voz en contexto seguro; R-06 (punto 9) |
| NFR-U2-13 | — | Se cierran R-02 (PV estático, sin `hostPath`), R-03 (digest de imágenes propias y excepciones con caducidad), R-04 (NFR8 parcial, el 98 % en Build and Test), R-05 (TTS) y R-07 (AOF medido, comando para NFR12.1, expresiones regulares en NFR10.5) | NFR10.11, NFR10.1, NFR8.2, NFR10.8, NFR11.2, NFR12.1, NFR10.5 | Revisión 1 (punto 10) |
| NFR-U2-14 | — | La comprobación AUTONOMIA-01 también busca `sbatch`, `ssh`, `scp` y `rsync` hacia ZINE | NFR10.5 | AC9.5.2 (punto 11) |
| NFR-U2-15 | — | La regla AIR alerta por encima de 0,25 sobre las *W* de C25, con los *fixtures* 5 de 20 y 6 de 20, sin proponer umbral | NFR15.1 | US10.8, CD-07, US10.6 «Retirada» (punto 12) |
| NFR-U2-16 | — | Sondas `/healthz` y `/readyz` en los cuatro servicios, y `smoke.sh` comprueba los cuatro | NFR10.17, NFR8.3 | C16, FR12.5 (punto 13) |
| NFR-U2-17 | — | El *canary* se busca en los logs de todos los contenedores en nivel 1 | NFR10.19 | AC9.1.4, AC11.6.3 (punto 14) |
