# Especificación de infraestructura — U13 ethics-governance

**Revisión 1 (2026-11-23): primera pasada.** Todo es nuevo.
- **Qué despliega U13.** Un solo recurso propio: el `Job` de retención, en dos manifiestos de `deploy/jobs/`
  (borrado `veridicus-retention` y simulación `veridicus-retention-dry-run`) que aplica el humano, fuera de
  Argo CD. Lo demás corre en procesos de otras unidades: las rutas, la fachada y el adaptador de `AccessLog`
  en la API de `session-api` (forma de U3, recursos de U2); el comando de consulta por `kubectl exec` en su
  contenedor; la consola en la imagen `frontend` (U4).
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU y sin máquina GPU; Minikube con 50 GiB y
  16 CPU, decidido por U2 (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna (`infrastructure-design-questions.md`, sección del 2026-11-23).
- **Precisiones y peticiones.** IDS-U13-01 a IDS-U13-13, en §8.

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 1): logical-components §1–§5; security-design §1, §2, §4, §7–§10,
  §16 y la tabla NFRD-U13-01 a NFRD-U13-14; reliability-design §1–§4 y §7; performance-design §1, §4 y §5;
  scalability-design §1–§7; observability-design §3–§5.
- `functional-design/functional-spec.md` (functional-spec: F7, F8, F10 y las preguntas abiertas 4 y 5 de
  §11).
- EthicsGovernance y la tabla de frontera del clúster de `inception/domain-design/components.md`
  (components).
- C1, C16, C23, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements/` de esta unidad: NFR-U13-07 a NFR-U13-12 y `tech-stack-decisions.md` (D1, D4, §2 y §5).
- Infrastructure Design de esta etapa: U2 revisión 2 (§1, §2.1, §2.5, §4, §7, §10), U3 revisión 2 (§1, §2.1,
  §2.2), U4 revisión 2 (§2, IDS-U4-03, IDS-U4-10), U5 (IDS-U5-01, IDS-U5-02), U6 (IDS-U6-02), U7 (§1, §1.2,
  IDS-U7-09, IDS-U7-10, IDS-U7-16) y U9 (§2.1, IDS-U9-08).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Rutas, fachada, dominio y adaptador de `AccessLog` en el contenedor `session-api` del `Deployment` `veridicus-session-api` (namespace `veridicus`); `Job` `veridicus-retention` con la imagen de `session-api` y la orden `python -m session_api.ethics_governance.retention`; comando de consulta `python -m session_api.ethics_governance.query` por `kubectl exec`; consola en `veridicus-frontend` | logical-components §1 y §2 (`hosts`); D1 |
| Réplicas | API: 1, sin autoescalado (la de U3 y U7). `Job`: un pod, una ejecución a la vez garantizada por `pg_try_advisory_lock` aunque el humano lo lance dos veces (código 3) | scalability-design §1; reliability-design §4.1 |
| Lanzamiento | Solo el humano, desde un manifiesto ya fusionado en `main`; nunca `CronJob`, *script*, CI ni Argo CD (`deploy/jobs/` fuera de la `Application`) | AUTONOMIA-01; security-design §9; U2 `cicd-pipeline.md` §4.2 |
| Ejecución del `Job` | `restartPolicy: Never`, `backoffLimit: 0`, `activeDeadlineSeconds: 3600`, **sin** `ttlSecondsAfterFinished` (su salida queda en el log del pod hasta que el humano borra el `Job`) | NFR-U13-07; reliability-design §4.4 y §4.5; IDS-U13-02 |
| Identidad del pod | Mismo `runAsUser` y `runAsGroup` que el contenedor `session-api`, sin root, `readOnlyRootFilesystem: true`, `/tmp` en memoria de 16 MiB, *helper* de seguridad de U2; `ServiceAccount` `veridicus-retention` sin `Role` y `automountServiceAccountToken: false` | NFR-U13-07; Kyverno `retention-job-identity` de U2; Pod Security `restricted` |
| Almacenamiento | El `Job` monta en escritura `veridicus-reports` (en `/var/lib/veridicus/reports-volume`, como la API) y `veridicus-audio` (en la misma ruta que la API), porque `purge_session` de U7 y de U4 borra los archivos. Las rutas y las claves `VERIDICUS_REPORTS_DIR` y `VERIDICUS_AUDIO_DIR` son las mismas que en la API (IDS-U13-06) | IDS-U7-16; IDS-U9-08; nodo único con PVC `ReadWriteOnce` |
| Tablas de U13 | Cinco tablas en `veridicus-pg` por la migración de `session-api` en su propio PR (§3) | security-design §8; `project.md` (migraciones en un `Job`) |
| Red | La API no suma reglas. El `Job` usa la `NetworkPolicy` `retention-job` de U2: salida solo a `veridicus-pg-rw:5432`, `veridicus-redis:6379` y DNS; sin entrada | security-design §2; NFR1.3 |
| Entornos | Una sola máquina de 64 GB, solo CPU, con el mismo digest que publica la CI. Sin *staging* ni producción | Supuesto del brief; IDS-U2-01 |
| IaC | Plantillas del `Job` en el chart `deploy/jobs/` de U2 (IDS-U13-01); la API, en el subchart `session-api` del chart paraguas con `values-cpu.yaml`; la migración, en el `Job` de migraciones de U2 | AUTONOMIA-01; D3 de U2 |
| Recursos | `Job`: 0,25 CPU / 256 MiB → 1 CPU / 512 MiB, ya en U2 §4. API: **sin cambio** (§1.1) | NFR-U13-07; performance-design §4 |
| Clasificación | `veridicus.io/data-class: sensitive` en `session-api` y en `retention-job` (la de U2): manejan testimonio y lo borran | Frontera de components; security-design §1 |

### 1.1 Memoria, conexiones y presupuesto de Minikube

| Pieza | Cifra de U13 | Frente a lo que ya fijó la etapa |
|---|---|---|
| Rutas en la API | La comparación retiene un turno a la vez y ≤ 1 000 tuplas de la nota (< 1 MiB); las reglas de uso son un texto inmutable de pocos KiB | Despreciable frente al hueco de ≈ 370 MiB que dejó U5 para U6, U9, U12 y U13 |
| Comando de consulta (`kubectl exec`) | Segundo intérprete en el *cgroup* de la API, ≤ 64 MiB (performance-design §5) | Comparte el hueco de 64 MiB del proceso de `exec` que contó U7. Aun a la vez que un `export_store`: 1,2 × (785 + 64) MiB ≈ 1 019 MiB ≤ 1 152 MiB (IDS-U13-08) |
| `Job` de retención | Pico ≤ 256 MiB (recibos de la sesión en curso, ≈ 20 000 UUID); límite 512 MiB = 2 × pico | Transitorio: U2 no suma los `Job` al presupuesto (≈ 41 GiB y 14,5 CPU pedidos). Mientras corre, sus 256 MiB de `requests` caben en los 9 GiB de margen |
| Conexiones de `veridicus_retention` | 1 durante toda la ejecución, más un cliente de Redis | U4 reservó ≤ 2 (IDS-U4-03) |
| Conexiones de `veridicus_app` del comando | 1, fuera del *pool* de la API | Pico con `Recreate`: 10 (API) + 4 (trabajador) + 1 (`create-admin`) + 1 = 16 ≤ 25 (30 pedido); `max_connections = 50` sin cambio (IDS-U13-09) |

**U13 no cambia ninguna cifra de pod** ni el presupuesto de U2.

## 2. `Job` de retención

| Campo | Borrado (`veridicus-retention`) | Simulación (`veridicus-retention-dry-run`) |
|---|---|---|
| Plantilla | `deploy/jobs/templates/retention.yaml` | `deploy/jobs/templates/retention-dry-run.yaml` |
| Argumentos | Ninguno: `as_of` = `clock.now()` | `--dry-run` y, solo si el humano pasa `retention.dryRun.asOf`, `--as-of <fecha ISO 8601 UTC>` |
| Qué hace | Por sesión vencida: bloquea, escribe claves de cancelación, borra en el orden de C24, inserta el acta y confirma | Una transacción `REPEATABLE READ READ ONLY`, `count_session` de cada unidad; no bloquea, no escribe claves, no borra ni escribe actas |
| Pod | El mismo en las dos: imagen, identidad, volúmenes, Secrets, configuración, recursos, plazo y etiqueta `app.kubernetes.io/component: retention-job` | Ídem |
| Salida | Una línea JSON `retention.candidate` por candidata y un `retention.summary`; códigos 0, 1, 2 y 3 | Ídem con `outcome: would_purge`; código 0 |

- **`--as-of` nunca llega al borrado.** La plantilla de borrado no lee `retention.dryRun.asOf`: renderizada
  con ese valor, sus argumentos siguen vacíos (prueba de `deploy/tests/level0`). El programa además termina
  con código 2 si recibe `--as-of` sin `--dry-run`, antes de abrir conexiones (E44).
- **Por qué dos plantillas y no una con un modo.** Un error al pasar valores nunca convierte una simulación
  en un borrado: el nombre del `Job` dice lo que hace y cada uno tiene su línea en el runbook.
- **Relanzar.** Un `Job` es inmutable y no lleva TTL: el humano lee la salida, borra el `Job` anterior y
  aplica de nuevo (`cicd-pipeline.md` §4). Relanzar es seguro: cada sesión confirmada ya tiene su acta y no
  se vuelve a seleccionar (reliability-design §4.4).

### 2.1 Configuración del `Job`

Cada clave se referencia una por una con `configMapKeyRef` (sin `optional`), no con `envFrom`: si falta, el
pod no arranca y el render nombra la clave, así la comprobación de U5 y la de U13 la ven (IDS-U13-03).

| Variable | De dónde | Para qué |
|---|---|---|
| Host, base y modo TLS de PostgreSQL; host de Redis | `veridicus-session-api-config` (U3 §2.1) | Las mismas direcciones que la API (`veridicus-pg-rw`, `verify-full`; `veridicus-redis`) |
| `VERIDICUS_DB_STATEMENT_TIMEOUT_MS`, `VERIDICUS_DB_LOCK_TIMEOUT_MS` | Ídem (2000 y 2000) | Plazos por conexión de `db.py` (U3, IDS-U5-02) |
| `VERIDICUS_REDIS_TIMEOUT_MS` | Ídem (500) | `socket_timeout` y `socket_connect_timeout` del cliente de `EthicsSessionPort` |
| Las siete claves de U7 (`VERIDICUS_REPORTS_DIR` y las de almacén, consolidación, huérfanos, espacio libre, cuota y barrido) | Ídem | `purge_session` de U7 usa el mismo almacén que la API (IDS-U7-16) |
| `VERIDICUS_AUDIO_DIR` | Ídem | `purge_session` de U4 borra `TurnAudio` (IDS-U9-08) |
| `VERIDICUS_LIMITS_PATH` | Catálogo C25 dentro de la imagen | Las siete cifras de U13 y `retention_max_days`; **ninguna** `VERIDICUS_LIMIT_RETENTION_MAX_DAYS` (NFRD-U13-10) |
| `VERIDICUS_RETENTION_SESSION_TIMEOUT_S` | Valor `retention.sessionTimeoutS` del chart de `deploy/jobs/` (`"60"`, entero de 10 a 300) | Plazo por sesión; fuera de rango, código 2 antes de abrir la base |
| Usuario y contraseña de `veridicus_retention` | Secret `veridicus-db-retention` (`kubernetes.io/basic-auth`) por `secretKeyRef` (IDS-U13-04) | Solo en este `Job` (`secret-consumers.yaml`) |
| Contraseña de Redis | Secret `veridicus-redis-auth`, clave `password`, como archivo de solo lectura | Como el resto de clientes de U2 (IDS-U2-10) |
| CA de `veridicus-pg` | Igual que en la API | `sslmode=verify-full` |

### 2.2 Duración, plazos y acta

| Tramo | Cifra | De dónde |
|---|---|---|
| `activeDeadlineSeconds` | 3 600 s hasta medirlo; luego, por PR, 2 × la ejecución medida con 500 sesiones típicas (IDS-U13-13) | NFR-U13-07; scalability-design §5 |
| Una sesión | `VERIDICUS_RETENTION_SESSION_TIMEOUT_S` = 60 s, por reloj monotónico | reliability-design §1 |
| Inactividad en la transacción | `SET LOCAL idle_in_transaction_session_timeout = '15s'` con `idle_timeout_s` de `db.py`, en cada transacción por sesión y en la de la simulación; nunca en el `Cluster`, el rol ni la conexión (IDS-U13-07) | NFRD-U13-14; IDS-U6-02 |
| Sentencias y esperas de bloqueo | 2 s y 2 s por conexión | U3; IDS-U5-02 |
| Redis | 0,5 s por operación; si falla, la sesión queda `failed` sin borrar | NFR-U13-05 |
| Cada archivo de la purga | 5 s (`VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS` y el de U4) | reliability-design §1 |
| Sesión máxima | p95 ≤ 10 s | performance-design §4 |
| 50 sesiones típicas; simulación de 500 (200 vencidas) | ≤ 5 min; ≤ 60 s | NFR3.6 |
| Acta de la sesión máxima | ≈ 0,8 MiB en `jsonb` (≈ 20 000 UUID), dentro de 1 MiB; PostgreSQL la guarda en TOAST y la inserción cabe en los 2 s de `statement_timeout`. Si la medición pasa de 1 MiB, se corrige el formato por PR; el umbral no sube | NFR3.9; performance-design §4 |

## Fragmento: forma del `Job` de retención

```yaml
# Ilustrativo: lo que fija U13; el manifiesto completo lo escribe Code Generation
kind: Job
metadata: {name: veridicus-retention, labels: {app.kubernetes.io/component: retention-job}}
spec:
  backoffLimit: 0
  activeDeadlineSeconds: 3600        # sin ttlSecondsAfterFinished
  template:
    spec:
      restartPolicy: Never
      serviceAccountName: veridicus-retention
      automountServiceAccountToken: false
      containers:
        - name: retention
          image: ghcr.io/<org>/veridicus-session-api@sha256:<el de la API>
          args: ["python", "-m", "session_api.ethics_governance.retention"]
```

## 3. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-pg` (U2) | database | Rutas: `veridicus_app` por el *pool* de U3. `Job`: una conexión de `veridicus_retention`. Comando: una conexión de `veridicus_app` con `SET TRANSACTION READ ONLY`. `log_error_verbosity: "terse"` y `log_parameter_max_length` y `_on_error` a 0, ya en el `Cluster` (U2 §2.1) | Sin parámetros nuevos en el `Cluster` ni en los roles. `terse` impide que una violación de `CHECK` deje la nota en el log del servidor (NFRD-U13-09) |
| Esquema de U13 | database | `analyst_acknowledgement`, `access_log_entry`, `problem_report`, `retention_change` y `retention_act`, con marca `veridicus-audit` (`owner_unit: U13`), `CHECK` de patrón o enum, sin claves foráneas en el registro y el acta, y los índices de scalability-design §4 (incluidos los tres por hora de NFRD-U13-12). `veridicus_apply_audit_grants()` de U3 concede: `veridicus_app` `SELECT` e `INSERT`; `veridicus_retention` `SELECT`, `DELETE` en `problem_report` y `retention_change` e `INSERT` solo en `retention_act` (`retention_insert`, NFRD-U13-04) | Entra con el `Job` de migraciones y `veridicus_owner`, en su propio PR, después del cambio de U3 a la función de permisos |
| Funciones de bloqueo | database | `veridicus_purge_lock_session(uuid)` (migración de U4) y `veridicus_purge_lock_report_versions(uuid)` (migración de U7), `SECURITY DEFINER` de `veridicus_owner`, `EXECUTE` solo para `veridicus_retention` | PostgreSQL exige `UPDATE` para `FOR UPDATE` y `veridicus_retention` nunca lo tiene (NFRD-U13-05, IDS-U7-10) |
| Volumen de PostgreSQL | database | PVC de 10 GiB de U2, **sin cambio**. U13 ocupa ≤ 150 MiB con 500 sesiones típicas: ≤ 40 MiB del registro (150 000 accesos), ≤ 100 MiB de actas y ≤ 10 MiB del resto | scalability-design §3; IDS-U13-10 |
| Respaldo | database | `scripts/backup-db.sh` de U2 vuelca también las cinco tablas; la poda por `retention_max_days` impide que un volcado con testimonio sobreviva al plazo (NFR-U13-11, ya en U2 §6) | RPO el último volcado manual; RTO una restauración manual |
| `veridicus-redis` (U2) | queue | El `Job` escribe solo claves de cancelación por `EthicsSessionPort`: `veridicus:run-cancelled:{run_id}` con el TTL de U4 y `veridicus:voice-cancelled:{session_id}` con el de U9, antes del `COMMIT` | Claves de pocos bytes dentro de `maxmemory 384mb`. Con `noeviction` lleno, la escritura falla y la sesión queda `failed` sin borrar: el fallo cerrado de NFR-U13-05. El AOF conserva las claves tras un reinicio |
| PVC `veridicus-reports` y `veridicus-audio` (U2) | object-store | Montados en escritura por la API y por `retention-job`; el `Job` borra archivos solo dentro de `purge_session` de U7 y U4 | `volume-consumers` y `retention-job-identity` de U2 |
| `ingress-nginx` (U2) | load-balancer | Las tres rutas de U13 entran por `/api/` de `veridicus-web` (tope 2 113 536, sin disco). El cuerpo de U13 es ≤ 32 768 bytes (`ethics_body_max_bytes`): el `413` lo da `session-api` | Sin `Ingress` nuevo ni cambio |
| `cdn`, `search`, caché | — | No aplica | Sin caché en U13 (performance-design, introducción) |

## 4. Red de U13 (NFR1.1–NFR1.3, AUTONOMIA-04)

| Proceso | Entrada | Salida |
|---|---|---|
| API de `session-api` (rutas de U13) | `ingress-nginx` → 8080 (regla de U3) | `veridicus-pg` 5432 (regla de U3). Nada más |
| `Job` de retención (borrado y simulación) | Ninguna | `veridicus-pg-rw` 5432, `veridicus-redis` 6379 y DNS (`NetworkPolicy` `retention-job` de U2) |
| Comando de consulta | — (lo abre el humano con `kubectl exec`) | La conexión de la API a `veridicus-pg` |
| Consola | — | `https://veridicus.local:8443` por el `port-forward` del Ingress (IDS-U2-04) |

U13 no suma filas a `deploy/network-deps.yaml`: la fila de `retention-job` ya existe en U2. El contrato
`ethics-governance-no-egress` impide en el código cualquier cliente HTTP, `socket`, `libs.model_gateway` o
`libs.anonymizer` (security-design §2).

### 4.1 Frontera por componente (AUTONOMIA-04)

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera |
|---|---|---|
| Diálogo, franja, panel, plazo y avisos de bienestar | Navegador del analista, en Windows | **Entra** al clúster la nota del reporte por el Ingress con TLS; la comparación local con los turnos no sale del navegador |
| Rutas, fachada, dominio y adaptador de `AccessLog` | Dentro, en la API de `session-api` | Ninguno sale del clúster; solo filas hacia `veridicus-pg` |
| `Job` de retención | Dentro, pod propio | Ninguno: borra testimonio; su salida y sus actas solo llevan IDs, reglas, conteos y SHA-256 |
| Comando de consulta | Dentro, en el contenedor `session-api` | **Sale** hacia la terminal del humano en la misma máquina (incluida la nota de los reportes de problemas); no se escribe en archivos dentro del repositorio (NFR12.2) |

## 5. Comando de consulta (NFR-U13-08, NFR-U13-09)

| Aspecto | Diseño |
|---|---|
| Línea | `kubectl exec deploy/veridicus-session-api -c session-api -- python -m session_api.ethics_governance.query {access-log\|problem-reports\|retention-acts} …`, ya en `readonly-exec-allowlist.yaml` de U2 |
| Usuario | `veridicus_app` del proceso, `SET TRANSACTION READ ONLY` como primera sentencia |
| Tope | `--limit` 1 000 por defecto, 10 000 como máximo; línea `{"truncated": true}` si hubo más |
| Recursos | ≤ 64 MiB en el *cgroup* de la API; ≤ 2 s con `--session` y ≤ 5 s con `--limit 10000` sobre 150 000 filas |
| Quién | Solo el humano, a mano; nunca un *script* (`check-no-cluster-apply.sh` rechaza todo `kubectl exec` fuera de la lista) |

## 6. Consola

| Aspecto | Diseño |
|---|---|
| Contenido | `frontend/src/features/ethics-governance/` dentro de la imagen `veridicus-frontend` de U4; sin recursos ni cabeceras nuevas (la CSP de U4 ya cubre `fetch` a `'self'`) |
| Recursos | Sin cambio en `frontend` (0,05 / 32 MiB → 0,2 / 64 MiB de U2): archivos estáticos |
| Peticiones | Tres mutaciones con `retry: false`; el recordatorio de bienestar y la comparación local no hacen peticiones |

## 7. Infraestructura compartida

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Proceso, `Deployment` y `Service` `veridicus-session-api` | U3 (forma), U2 (recursos), U7 (`Recreate`) | U13 entre U4–U9 y U12 | U13 no suma memoria ni conexiones al *pool*; import-linter (`ethics-governance-no-egress`, `-no-metrics`) |
| Imagen `session-api` | U3 | API, trabajador, `Job` de retención, `create-admin` | El `Job` usa el mismo digest que la API (IDS-U13-05) |
| `veridicus-session-api-config` | U3 | API, trabajador y, por claves explícitas, `Job` de retención | Una sola fuente de las cifras que comparten la API y la purga (IDS-U13-03) |
| `veridicus-pg`, roles y Secret `veridicus-db-retention` | U2 | U13 por `veridicus_retention` (solo el `Job`) | `secret-consumers.yaml`; permisos derivados de la marca |
| `veridicus-redis` | U2 | U13 solo con claves de cancelación | Por `EthicsSessionPort` de U4; prefijos de U4 y U9 |
| PVC `veridicus-reports` y `veridicus-audio` | U2 (declara), U7 y U9 (dimensionan) | U13 por `purge_session` | `volume-consumers`, `retention-job-identity` |
| `Purgeable` (C24) y `EthicsSessionPort` | U4, U5, U7 | U13 en el `Job` | Interfaces en proceso; U13 fija el orden |
| Chart `deploy/jobs/` | U2 | U3 (`create-admin`), U13 (retención) | Fuera de la `Application`; Kyverno `job-shape` |
| `readonly-exec-allowlist.yaml` | U2 | U7 (`verify_store`), U13 (consulta) | Lista cerrada; `check-no-cluster-apply.sh` |
| `frontend` | U4 | U13 (diálogo, franja, panel, plazo, avisos) | Una sola imagen; textos solo del catálogo de mensajes |
| C1, C23, C24, C25 | U1 (C23 por U7) | U13 | Cambian por PR de U1 |

## 8. Precisiones y peticiones (IDS-U13-xx)

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Las peticiones no se dan por aplicadas. Todas salen de las fuentes
aprobadas o de un hecho técnico, y ninguna deja salir del clúster algo que hoy no sale.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U13-01 | Infrastructure Design de U2 (`deploy/jobs/`, «forma exacta de los dos manifiestos») | **Petición a U2:** dos plantillas en `deploy/jobs/templates/`: `retention.yaml` (`Job` `veridicus-retention`, sin argumentos) y `retention-dry-run.yaml` (`veridicus-retention-dry-run`, `--dry-run` y `--as-of` solo si se pasa `retention.dryRun.asOf`). Las dos con el mismo pod, la etiqueta `app.kubernetes.io/component: retention-job` (así `volume-consumers`, `secret-consumers`, `retention-job-identity`, `job-shape` y la `NetworkPolicy` `retention-job` las cubren a las dos) y el `ServiceAccount` `veridicus-retention` sin `Role`. Prueba: la plantilla de borrado renderizada con `retention.dryRun.asOf` no lleva `--as-of` | logical-components §5; security-design §9 (T10); §2 |
| IDS-U13-02 | NFR Design de U2 §13 (Kyverno `job-shape`: control negativo con `backoffLimit: 1`) | **Petición a U2:** para `retention-job`, `job-shape` exige además `restartPolicy: Never`, `activeDeadlineSeconds` presente y `ttlSecondsAfterFinished` **ausente** (control negativo: el `Job` de retención con `ttlSecondsAfterFinished: 3600`). `create-admin` conserva su TTL de 3 600 s | security-design §9 (fila «Sin reintento de Kubernetes»); observability-requirements §3 |
| IDS-U13-03 | IDS-U7-16 («monta el `ConfigMap` o esas siete claves») e IDS-U5-02 | El `Job` referencia cada clave de `veridicus-session-api-config` con `configMapKeyRef` sin `optional` (lista de §2.1), no con `envFrom`. Prueba de `deploy/tests/level0`: cada clave de la lista está en el `Job` y existe en el render del `ConfigMap`; control negativo, el `Job` sin `VERIDICUS_DB_LOCK_TIMEOUT_MS`. `VERIDICUS_RETENTION_SESSION_TIMEOUT_S` sale del valor `retention.sessionTimeoutS` del chart de `deploy/jobs/` | §2.1; tech-stack-decisions §2 |
| IDS-U13-04 | `nfr-design/security-design.md` §9 («`VERIDICUS_DATABASE_URL` del `Job` desde el Secret `veridicus-db-retention`») | La conexión se arma igual que la de la API (U3 §2.1): host, base y TLS del `ConfigMap`; usuario y contraseña del Secret `veridicus-db-retention` (`kubernetes.io/basic-auth`) por `secretKeyRef`. Ninguna variable lleva una URL con contraseña. La prueba de nivel 1 `SELECT current_user` = `veridicus_retention` no cambia | U3 §2.1; NFR10.13 de U2 |
| IDS-U13-05 | Infrastructure Design de U2 (`cicd-pipeline.md` §3, PR de despliegue) | **Petición a U2:** el valor de imagen de `deploy/jobs/` es el digest de `session-api` de `values-cpu.yaml`; el PR de despliegue cambia los dos y una prueba de `deploy/tests/level0` falla si difieren. El `Job` llama a `purge_session` de U4, U5 y U7 y debe correr el mismo código que el esquema desplegado | reliability-design §4.2; D1 |
| IDS-U13-06 | Infrastructure Design de U9 §2.1 (`VERIDICUS_AUDIO_DIR`: «ruta de montaje de `veridicus-audio`») | U13 no fija la ruta del audio: usa la que U2 renderice para la API. Prueba de `deploy/tests/level0`: el `mountPath` de `veridicus-reports` y de `veridicus-audio` y los valores de `VERIDICUS_REPORTS_DIR` y `VERIDICUS_AUDIO_DIR` coinciden entre el contenedor `session-api` y el `Job` | IDS-U7-16; IDS-U9-08 |
| IDS-U13-07 | `nfr-design/security-design.md` NFRD-U13-14 («con el parámetro de `db.py` si U4 lo acepta, o con la `UnitOfWork` si no») | Se usa `idle_timeout_s=15` de `session_api/shared/db.py`, que U6 aceptó (IDS-U6-02), en cada transacción por sesión y en la transacción de la simulación | IDS-U6-02; NFRD-U7-01 |
| IDS-U13-08 | — | La memoria de la API no cambia por U13: el comando de consulta comparte el hueco de 64 MiB del proceso de `exec` de U7 (IDS-U7-09). Aun a la vez que un `export_store`, 1,2 × (785 + 64) MiB ≈ 1 019 MiB ≤ 1 152 MiB. Con IDS-U12-01 el margen crece | performance-design §5; §1.1 |
| IDS-U13-09 | — | Conexiones: 1 de `veridicus_retention` (U4 reservó ≤ 2) y 1 de `veridicus_app` del comando fuera del *pool*; pico de `veridicus_app` 16 ≤ 25; `max_connections = 50` sin cambio | scalability-design §7; IDS-U4-03; IDS-U7-03 |
| IDS-U13-10 | Infrastructure Design de U2 §2.1 (PVC de 10 GiB) | **Petición a U2 (informativa, sin cambio de tamaño):** su tabla de volúmenes registra que U13 ocupa ≤ 150 MiB con 500 sesiones típicas y que `access_log_entry` nunca se borra. Si el registro se acerca a 1 000 000 de filas, se revisan el PVC y la política de archivo por PR | scalability-design §3 y §8; logical-components §5 |
| IDS-U13-11 | NFR Design de U13 §10 («el runbook de `docs/operacion/`») y U2 `cicd-pipeline.md` §4.1 | U13 aporta en Code Generation `docs/operacion/retencion.md` con el procedimiento de `cicd-pipeline.md` §4 y la prohibición de redirigir la salida del `Job` o del comando a archivos dentro del repositorio. **Petición a U2:** `docs/operacion/instalacion.md` lo enlaza tras el paso de `create-admin`. El lanzamiento solo vive en el runbook, nunca en un *script* | AUTONOMIA-01; NFR12.2 |
| IDS-U13-12 | `team.md` (`## Deployment`, dos máquinas y etapa GPU) | Con el supuesto del brief, U13 no tiene valores por máquina ni petición de `nvidia.com/gpu`; sus pruebas de niveles 0 y 1 corren en CPU (NFR2.1) | IDS-U2-01; IDS-U2-02 |
| IDS-U13-13 | `nfr-requirements/security-requirements.md` NFR-U13-07 (`activeDeadlineSeconds` «propuesta: 3 600 s») | Se mantiene 3 600 s hasta medir. La medición de NFR3.11 con 500 sesiones típicas entra como evidencia en un PR de B13, que fija la cifra en 2 × esa medición en `deploy/jobs/` y en U2 §4 (NFR-U13-07 pide ≥ 2 ×). Mientras tanto, una ejecución que vence se relanza sin daño (reliability-design §4.5) | scalability-design §5; reliability-design §4.5 |
