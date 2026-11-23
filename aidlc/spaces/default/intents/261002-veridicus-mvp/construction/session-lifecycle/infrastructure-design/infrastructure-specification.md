# Especificación de infraestructura — U6 session-lifecycle

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Salen la versión nueva de un escenario, la marca de lote en Redis, los tres ajustes
  `VERIDICUS_HEARTBEAT_*` del `ConfigMap`, `veridicus_now()`, la sonda `probe=kubernetes` y las dos máquinas
  con `values-gpu.yaml`. `SuspensionSweeper` pasa a `SessionSupervisor`, cuarto hilo del trabajador con su
  conexión. Entran la importación con lector en memoria, el modo final, la pausa, la terminación, la
  retirada y la cancelación con las claves de U4.
- **Numeración.** §1–§5 conservan su tema. La tabla de precisiones de la revisión 1 (§6) se retira entera
  (IDS-U6-01) y la sustituye la tabla IDS-U6-01 a IDS-U6-15. §7 (nueva) cierra los hallazgos de
  `reviews/review-01.md`.
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU y sin máquina GPU; Minikube con 50 GiB y
  16 CPU, decidido por U2 (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna en esta pasada (`infrastructure-design-questions.md`, sección del 2026-11-23).

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 2): performance-design §1–§4 y §6–§10; security-design §1–§5,
  §10–§12 y la tabla NFRD-U6-01 a NFRD-U6-19; scalability-design §1–§6; reliability-design §1–§4 y §6–§12;
  observability-design §1–§4; logical-components §1–§6.
- `functional-design/functional-spec.md` (functional-spec: F2–F9, máquina de §3 y §8) y
  `functional-design/entities.md` revisión 2.
- InterviewSession, ConsoleApi, la tabla de fronteras y las dependencias externas de
  `inception/domain-design/components.md` (components).
- C1, C2, C6, C11, C15, C16 y C25 de `inception/contract-design/contract-summary.md` (contract-summary), con
  CD-06.
- `nfr-requirements/tech-stack-decisions.md` (D1–D13, §2 y §5).
- Peticiones de NFR Design de otras unidades que tocan a U6: NFRD-U7-01 y NFRD-U7-03 (plazo de inactividad),
  NFRD-U9-08 (motivo de la cancelación, sin infraestructura) y el lector compartido que reutilizan U9 y U12.
- Infrastructure Design revisión 2 de U2 (§1, §2, §4, §5, §7 e IDS-U2-01 a IDS-U2-15), de U3 (IDS-U3-01 e
  IDS-U3-09) y de U4 (§1, §2, §6 e IDS-U4-01 a IDS-U4-15).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

U6 **no añade procesos, imágenes, servicios de infraestructura, reglas de red, Secrets ni volúmenes**: todo
vive en la API y el trabajador de `session-api` y en `frontend`, que despliegan U3 y U4. Lo propio de U6 es el
cuarto hilo del trabajador (ya adoptado por U4), una migración, sus cifras en C25, sus métricas, su fila del
panel y sus pruebas.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Contenedores en los `Deployment` existentes del namespace `veridicus`: `veridicus-session-api` (API, U3) atiende las nueve rutas de U6 (`/transcript`, `/sessions/import`, `/final-runs`, `/heartbeat`, `/resume`, `/analysis`, `/terminate`, `/consent-withdrawal`, `GET /sessions`); `veridicus-session-api-worker` (U4) ejecuta `SessionSupervisor` como hilo 4; `veridicus-frontend` (U4) sirve M1, M7, los diálogos, la franja del modo final y el historial lateral | logical-components §1 y §4: nada de U6 justifica un proceso propio |
| Réplicas | 1 de cada uno, sin HPA ni KEDA. El diseño admite dos instancias (`change_cursor.bump`, restricción única (`session_id`, `client_request_id`), `UPDATE … WHERE status = 'suspended'`, `bump` sin esperar en la revisión) | scalability-design §1 (NFR8.2) |
| Estrategia de actualización | API: `RollingUpdate` (`maxSurge: 1`, `maxUnavailable: 0`); los dos pods transitorios no duplican lotes, corridas finales ni transiciones. Trabajador: `Recreate` (IDS-U4-02), así que nunca hay dos `SessionSupervisor` (IDS-U6-10) | scalability-design §1; reliability-design §3 |
| Hilos del trabajador | Cuatro, cada uno con su conexión: `ResultIngestor`, `RunSupervisor`, `HoldReleaser` (U4) y `SessionSupervisor` (U6, cada `session_sweep_interval_s` = 30 s). Un hilo que muere termina el proceso y Kubernetes lo reinicia | DS4; NFRD-U6-05; reliability-design §3 (NFR10.12) |
| Sondas | API: las de U3, con `readinessProbe` sobre el `/readyz` completo, que incluye Redis (IDS-U3-01): con Redis caído toda la consola queda fuera de servicio y solo sigue la revisión de suspensión (NFRD-U6-08, IDS-U6-13). Trabajador: `livenessProbe` sobre `/healthz` con los **cuatro** hilos con señal en los últimos 45 s (IDS-U4-06) | reliability-design §1 y §12; logical-components §2 |
| Configuración inválida | Una cifra de U6 fuera de regla (*T* ≥ 4 × `poll_interval_s`, `session_sweep_interval_s` ≤ *T*/2, 1 ≤ `heartbeat_write_min_s` ≤ *T*/4) termina el proceso antes de abrir el puerto: el pod nunca pasa a listo y el `RollingUpdate` conserva el anterior | NFRD-U6-09 (NFR10.10) |
| Red | Entrada: `ingress-nginx` → 8080 de la API (`/api/`) y Prometheus → 8081 de la API y del trabajador. Salida: API → `veridicus-pg`, `veridicus-redis` (y `audio-worker` de U9, ajeno a U6); trabajador → `veridicus-pg`, `veridicus-redis`. **Ningún destino nuevo**; los dos bajo la salida negada de U2 | security-design §1 (NFR1.1, AUTONOMIA-04); U4 §3 |
| Entrada HTTP | Pegado: `transcript_body_max_bytes` = 1 004 096 < tope de `veridicus-web` (2 113 536), así que el `413` siempre lo da la API. Importación: `import_body_max_bytes` = 2 113 536, igual al tope del Ingress (IDS-U6-09). `veridicus-web` va sin *buffering* a disco (`proxy-request-buffering: off`, `proxy-buffering: off`, `proxy-max-temp-file-size: 0`), así que ni el pegado ni el archivo tocan el disco del Ingress. El peor caso (importación ≤ 3 s) cabe en el `proxy-read-timeout` de 30 s | security-design §2 y §10; NFRD-U6-01; NFRD-U6-11; U2 §2.4 |
| Almacenamiento | Sin PVC ni volúmenes nuevos. Filas en `veridicus-pg` (§2.1); en Redis solo los mensajes C2 y las claves de cancelación de U4. El archivo importado vive en un `bytearray` acotado de la API (`MultipartMemoryReader`), nunca en disco; la API ya tiene `readOnlyRootFilesystem` y `/tmp` en memoria de 16 MiB (IDS-U2-14) | security-design §10 (NFR10.13, DS9); scalability-design §4 |
| Recursos | Sin cambios: API 0,5/512 MiB → 2/1,125 GiB y trabajador 0,25/384 MiB → 1/640 MiB (U2 §4). Cuenta en §1.1 | performance-design §7 (NFR8.1) |
| Entornos | Una sola máquina de 64 GB, solo CPU, con `values-cpu.yaml` y el mismo digest que publica la CI. Sin *staging* ni producción; sin archivo de valores GPU | IDS-U2-01; IDS-U2-02; NFR2.2 |
| IaC | U6 no tiene plantillas propias: su código entra en la imagen de `session-api` y de `frontend`; su migración en `db/migrations/` la aplica el `Job` de migraciones de U2; su fila del panel y sus reglas van en el chart paraguas de U2. Todo por PR; ningún paso aplica cambios al clúster sin la fusión aprobada | AUTONOMIA-01; security-design §5 |
| Clasificación | `veridicus.io/data-class: sensitive` en la API y el trabajador (testimonio pegado e importado); `internal` en `frontend` | Tabla de clasificación de U2 |

### 1.1 Recursos frente a los picos (NFR8.1)

| Contenedor | Pico sin U6 | Lo que añade U6 | Pico con U6 | 1,2 × pico | `limits.memory` de U2 | ¿Cabe? |
|---|---|---|---|---|---|---|
| API de `session-api` | ≈ 588 MiB: base ≈ 220 MiB, Argon2id 160 MiB, `/tmp` 16 MiB y 3 consolidaciones máximas de U7 ≤ 192 MiB | ≤ 100 MiB (pegado de 250 000 caracteres o archivo de 2 MiB leído una vez, turnos sin copiar el texto entero) | ≈ 688 MiB | ≈ 826 MiB | 1 152 MiB (1,125 GiB) | Sí, aun con U6 y U7 a la vez |
| Trabajador de `session-api` | ≤ 512 MiB (`RunResult` de 2 MiB, U4) más 16 MiB de `/tmp` | < 1 MiB residente: la pila del hilo 4 (8 MiB) es memoria virtual que solo ocupa las páginas que usa, y `SessionSupervisor` solo guarda identificadores de las ≤ 50 sesiones abiertas | ≤ 529 MiB | ≈ 635 MiB | 640 MiB | Sí, con poco margen; es la cuenta de U4 (634 MiB). Si la corrida de NFR8 mide más, el límite sube por PR |

CPU: la división (≤ 200 ms) y el armado de la entrada del modo final (≤ 400 ms) corren en la API fuera del
bloqueo, dentro de su límite de 2 CPU. U6 **no cambia** ninguna cifra de pod ni suma al presupuesto de
41 GiB y 14,5 CPU de U2. Si la medición de NFR3.1 o NFR3.13 supera los +100 MiB, el límite sube por PR con
la medición (performance-design §7).

### 1.2 Cifras de U6 · cambia

Ya no hay ajustes `VERIDICUS_HEARTBEAT_*` en el `ConfigMap` (IDS-U6-03). Las cifras viven en
`contracts/limits.v1.yaml` (C25), dentro de la imagen (`VERIDICUS_LIMITS_PATH`), y API y trabajador las leen
con `limits.load`.

| Cifra de C25 | Valor | Regla validada al arrancar | Procesos |
|---|---|---|---|
| `heartbeat_timeout_s` (*T*) | 180 | ≥ 4 × `poll_interval_s` | API y trabajador |
| `session_sweep_interval_s` | 30 | ≤ *T*/2 | API y trabajador |
| `heartbeat_write_min_s` | 15 | Entre 1 y *T*/4 | API y trabajador |
| `import_file_max_bytes` | 2 097 152 | `import_file_max_bytes` < `import_body_max_bytes` | API y consola |
| `transcript_body_max_bytes`, `import_body_max_bytes` | 1 004 096 y 2 113 536 (NFRD-U6-01, por PR de U1 antes de B7) | Cifras derivadas de U1 | API e Ingress |
| `transcript_max_turns`, `transcript_max_chars`, `turn_max_chars` | 2 000, 250 000, 20 000 | Catálogo de U1 | API y consola |

`values-cpu.yaml` no define ninguna `VERIDICUS_LIMIT_*` de U6. Si algún día se baja una, va en los dos
`Deployment` con el mismo valor: lo comprueba `deploy/tests/level0/test_session_lifecycle_limits.py`, que U6
aporta a la suite de `deploy-level0.yml` (IDS-U6-04); `check-limits-env.sh` de U2 sigue rechazando cualquier
valor mayor que el catálogo.

## 2. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-pg` (U2) | database | Rol `veridicus_app` sin cambios; *pools* de U3 (API) y de U4 (trabajador, 4). `statement_timeout` 2 s por conexión y `lock_timeout` 2 s (U5). Cada transacción de U6 abre con `SET LOCAL statement_timeout = '5s'` y `SET LOCAL idle_in_transaction_session_timeout = '5s'` desde `session_api/shared/db.py`; la revisión de suspensión, 2 s por sesión. **Nunca** en el `Cluster`, en los roles ni por conexión (IDS-U6-02) | NFRD-U7-01; reliability-design §1 (NFR10.9). Kyverno `cnpg-cluster-hardening` de U2 rechaza el parámetro en el `Cluster` |
| Volumen de `veridicus-pg` | database | PVC de 10 GiB de U2 sin cambios. Peor caso de U6: 500 sesiones de 250 000 caracteres ≈ 125 MB de texto, ≈ 1 M de filas de turno con su sobrecarga e índices ≈ 0,3 GiB; `TranscriptPaste` y `SessionStatusChange` < 5 MB | scalability-design §4 (NFR8.7); IDS-U6-15 |
| `veridicus-redis` (U2) | queue | Sin prefijos de U6. Las corridas de U6 entran a `veridicus:runs` solo por `RunEnqueuer` de U4 (la entrada final ≈ 1,35 MB, ya en la capacidad de U4); las claves `veridicus:run-cancelled:{run_id}` (valor `1`, TTL = plazo restante + 120 s) las escribe `CancellationKeys` de U4 tras el `COMMIT`, en una canalización sin `MULTI`; `socket_timeout` 0,5 s | security-design §4 y §11; reliability-design §11. `noeviction` sigue siendo de U2 por la cola, no por U6 |
| `ingress-nginx` (U2) | load-balancer | `veridicus-web` sin disco y con tope de 2 113 536 bytes en `/api/` | IDS-U6-09 |
| `cdn`, `search`, caché, `dns` | — | No aplica | La lista es una consulta agregada en PostgreSQL; las cifras viven en la imagen |

### 2.1 Migración de U6 (B7, un PR propio antes del código) · cambia

| Objeto | Cambio | Permisos |
|---|---|---|
| `transcript_paste` | Tabla nueva (`paste_batch_id` único, `session_id`, `client_request_id`, `first_turn`, `turn_count`, `char_count`, `run_id` anulable, `created_by`, `created_at`); índice único (`session_id`, `client_request_id`); marca `veridicus-audit` | `veridicus_app`: `INSERT`, `SELECT`. `veridicus_retention`: `DELETE` para `purge_session` (IDS-U6-12) |
| `turn` (de U4) | Columnas aditivas `page`, `page_end`, `fold_state`, `paste_batch_id`; valores `pasted` e `imported` en `origin`; CHECK `page_end >= page` | Los de U4 |
| `interview_session` (de U4) | Valores de `status` de U6 en el CHECK de la máquina; `origin` `corpus` y `sintetico`; disparador de solo avance de `closed_to_new_turns`; índice parcial de expresión `((COALESCE(last_heartbeat_at, created_at)), id) WHERE status = 'open'`, con `CREATE INDEX CONCURRENTLY` fuera de transacción | Los de U4 |
| `consent_record` (de U4) | `kind` `sintetico`; `withdrawn_at` y `withdrawn_by` con el disparador de U4 (de nulo a valor, juntos) | Los de U4 |
| `session_status_change` (de U4) | Valor `session-supervisor` en `actor_system` (FD-U6-13) | Los de U4 |
| `scenario_version`, `veridicus_now()`, vista `human_review.session_pending_suggestions` | **Retirado** (IDS-U6-03) | — |

Solo avanza (*expand–contract*) y corre como el `Job` de migraciones de U2 (onda −1 o instalación en dos
pasos, IDS-U2-07), nunca al arrancar un pod. Va después de la migración de U4 (B4), que crea las tablas que
amplía.

### 2.2 Conexiones de `veridicus_app` · nuevo

U6 no abre conexiones propias: sus rutas usan el *pool* de la API (U3) y `SessionSupervisor` la cuarta
conexión del trabajador, que U4 ya contó. El pico es 25 (API 20 en rodadura, trabajador 4, `create-admin` 1),
igual al `connectionLimit: 25`; U6 respalda la petición IDS-U4-03 (30) sin pedir nada más (IDS-U6-11).

## 3. Frontera y datos que cruzan (AUTONOMIA-04) · cambia

| Componente | Dentro o fuera del clúster | Datos que cruzan | Destino |
|---|---|---|---|
| Rutas de U6 en la API | Dentro | Testimonio pegado o importado desde el navegador por el Ingress TLS sin disco; `SessionSummary` y `SessionView` sin texto de turnos hacia el navegador | Navegador |
| `TranscriptIntake`, `TranscriptImport`, `FinalRunLauncher`, `SessionLifecycle` | Dentro | Turnos en PostgreSQL; mensajes C2 y claves de cancelación hacia Redis, siempre por `RunEnqueuer` y `CancellationKeys` de U4 | `veridicus-pg`, `veridicus-redis` |
| `HeartbeatWriter`, `SessionResume`, `SessionList` | Dentro | Identificadores, horas y conteos | `veridicus-pg` |
| `SessionSupervisor` | Dentro (trabajador) | Identificadores y horas; reescribe claves de cancelación | `veridicus-pg`, `veridicus-redis` |
| Consola (vista previa y validación del archivo) | Navegador | Nada hasta «Confirmar» o «Importar» | ConsoleApi |
| Corridas que lanza U6 | `semantic-agent` (U4) y `anonymizer-proxy` (U10) | La única salida, por la tubería de U4 con el anonimizador delante | La lista de U10 |
| `final_run_max.py` | **Fuera**: WSL2 del equipo del humano | Solo datos sintéticos, por `https://veridicus.local:8443` hacia la API (IDS-U6-06) | API |

Ningún componente de U6 llama fuera del clúster, así que ninguno necesita el anonimizador delante.

## 4. Infraestructura compartida · cambia

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| API de `session-api` | U3 | U4–U9, U12, U13 | Rutas por unidad con `authorize` de U3; U6 no cambia recursos ni sondas |
| Trabajador de `session-api` | U4 | U6 (`SessionSupervisor`), U7, U8, U9 | Un hilo por responsabilidad con su conexión; orden de bloqueo usuario → sesión → corrida → ronda |
| Fila `interview_session` y `change_cursor` | U4 | U5, U6, U7, U9, U13 | Escrituras visibles con `bump`; latido y revisión nunca esperan (`SKIP LOCKED`); el latido no sube el cursor |
| `RunEnqueuer`, `CancellationKeys` | U4 | U6, U9 | Funciones en proceso; U6 no publica en Redis por su cuenta |
| `MultipartMemoryReader` (`session_api/shared/multipart_memory.py`) | U6 (lo escribe en B7) | U9, U12 | Cada ruta pasa su propio tope (NFRD-U6-10) |
| `pending_counts` de C11 | U5 | U6 | Solo lectura por el puerto; U6 no lee tablas de U5 |
| `veridicus-pg`, `veridicus-redis`, `Ingress`, Prometheus y Grafana | U2 | U6 entre otras | Tabla de infraestructura compartida de U2 §7 |
| `contracts/limits.v1.yaml`, `contracts/transcript/speaker-markers.v1.yaml`, `contracts/metrics/session-lifecycle.v1.yaml`, `contracts/ts/` | U1 | U6 (API y consola) | Cambian solo por PR y disparan `session-api.yml` y `frontend.yml` |
| `frontend` | U4 | U3, U5–U9 | Una imagen; U6 añade M1, M7 y sus diálogos por PR |

## 5. Comportamientos operativos documentados · cambia

| Situación | Qué pasa | Por qué se acepta |
|---|---|---|
| `minikube stop` / `start`, o la API caída más de 180 s con el trabajador vivo | En la primera revisión con base disponible, las sesiones `open` sin latido pasan a `suspended` con `session-supervisor` | Reanudar es un clic del dueño y no pierde nada (NFR8.8); la condición se evalúa sobre el estado |
| Redis caído | Toda la consola fuera de servicio por el `/readyz` de U3; la revisión de suspensión sigue; las corridas ya confirmadas terminan por plazo | NFRD-U6-08 |
| Trabajador caído o reemplazado con `Recreate` | Las suspensiones se retrasan hasta que arranca; ninguna se pierde; las claves pendientes se reescriben en la primera vuelta | reliability-design §3 y §12 |
| Redis falla al escribir una clave de cancelación | La transición confirmada se mantiene; la clave la reescribe U4 al reconectar y `SessionSupervisor` en ≤ 30 s; mientras tanto `semantic-agent` cuenta como cancelado un `EXISTS` que falla | reliability-design §11 (DS8) |
| Reinicio de la API a mitad de un pegado o una importación | *Rollback*; el navegador reenvía el pegado con el mismo `client_request_id`; la importación se pide de nuevo | reliability-design §12 |
| Restauración de `pg_dump` | Las tablas de U6 viajan con el esquema; Redis no guarda nada propio de U6 | Respaldo de U2 §6 |

## 6. Precisiones y peticiones (IDS-U6-xx) · nuevo

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al original,
cada una en su propio commit. Las peticiones a U2 no se dan por aplicadas. Todas salen de las fuentes
aprobadas o de un hecho técnico, y ninguna deja salir del clúster algo que hoy no sale.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U6-01 | Revisión 1 de esta etapa, §6 (cuatro precisiones) | Se retira la tabla entera: el cuarto hilo en la sonda ya lo adoptó U4 (IDS-U4-06); el filtro de `frontend.yml` ya incluye `contracts/**` (U4); los tres ajustes salen a C25 (IDS-U6-03); `veridicus_now()` sale porque D3 revisión 2 pasa la hora como parámetro y usa `now()` de PostgreSQL | NFR Design revisión 2; tech-stack D3 |
| IDS-U6-02 | Revisión 1 de esta etapa, §2 (fila `veridicus-pg`, «`idle_in_transaction_session_timeout` 5 s» sin alcance) | El plazo de inactividad es `SET LOCAL` en cada transacción de U6 (5 s), nunca en el `Cluster`, en el rol ni por conexión. Se acepta la petición NFRD-U7-03: la función de `session_api/shared/db.py` recibe `idle_timeout_s` además del `statement_timeout`, para que U7 la llame con 15 s | NFRD-U7-01; NFRD-U7-03; reliability-design §1 |
| IDS-U6-03 | Revisión 1 de esta etapa (los cuatro artefactos) | Se retiran: `VERIDICUS_HEARTBEAT_TIMEOUT_SECONDS`, `_SUSPENSION_SWEEP_SECONDS` y `_HEARTBEAT_WRITE_MIN_SECONDS` del `ConfigMap` y su comprobación de paridad entre perfiles; la marca `veridicus:paste-published:`; `veridicus_now()`; la versión de escenario y su indexación con `veridicus-embeddings`; la vista de pendientes de U5; `suspended_at`; el `/readyz?probe=kubernetes`; las métricas y alertas de publicación por lote, de latidos y de la revisión con nombre viejo; el nivel 2 por `port-forward`; los Minikube de 20 y 28 GiB y `values-gpu.yaml` | Cambio 01; NFR Design revisión 2; IDS-U2-01; IDS-U2-02; IDS-U3-01 |
| IDS-U6-04 | `cicd-pipeline.md` de U2 (paso 10 de `deploy-level0.yml`) | U6 aporta `deploy/tests/level0/test_session_lifecycle_limits.py`: una `VERIDICUS_LIMIT_` de `heartbeat_timeout_s`, `session_sweep_interval_s` o `heartbeat_write_min_s` aparece con el mismo valor en el trabajador y en la API, o en ninguno; control negativo con un render que la baja solo en uno. No cambia el *workflow* de U2 | reliability-design §1 (NFR10.10); NFRD-U6-09 |
| IDS-U6-05 | NFR Design de U2 §9 (alcance de `check-no-cluster-apply.sh`) | **Petición a U2:** el alcance suma `evaluation/session_lifecycle/`, donde vive `final_run_max.py`, igual que IDS-U4-07 suma `evaluation/load/`. El script solo habla HTTP con la API | AUTONOMIA-01; performance-design §9 |
| IDS-U6-06 | `nfr-design/performance-design.md` §9 (NFR3.17) | `final_run_max.py` corre en WSL2 contra `https://veridicus.local:8443` (IDS-U2-04), con el analista sintético cuyas credenciales vienen del `.env` no versionado (como IDS-U4-08), solo con el archivo sintético máximo. Con `todo-local` exige `models.todoLocalJudge.enabled` (activo por defecto, IDS-U2-11); con `comercial-piloto` el cuerpo sale seudonimizado por el proxy. El reporte JSON lleva solo cifras y se adjunta al PR | NFR3.17; `project.md` (solo datos sintéticos) |
| IDS-U6-07 | Infrastructure Design de U2 (`check-config-copy.sh`, panel) | **Petición a U2:** la fila «Sesiones» del panel de U6 se empaqueta en el chart de U2 y `check-config-copy.sh` compara su SHA-256 con el original en `services/session-api/observability/`, como con la de U4 (IDS-U4-14). Las reglas de U6 solo se renderizan con `monitoring.enabled: true` | observability-design §4; IDS-U4-14 |
| IDS-U6-08 | `nfr-design/scalability-design.md` §5 («Perfil GPU para la demostración») y NFR2.2 de `tech-stack-decisions.md` («el perfil GPU es opcional») | Sin GPU, la primera acción ante la cola o un modo final más largo que su plazo es ajustar el perfil o el plazo por PR (U11) y limitar la demostración a transcripciones más cortas; nunca subir una cifra de C25 en silencio | IDS-U2-02 |
| IDS-U6-09 | Infrastructure Design de U2 §2.4 (`veridicus-web` = 2 113 536) y NFRD-U6-01 | El tope del Ingress es igual a `import_body_max_bytes`: un cuerpo mayor recibe el `413` de nginx, sin Problem Details. La consola nunca lo envía (el Web Worker compara `file.size` antes de leer, NFR3.14) y el `413` `limits.exceeded` con 5 MB y 10 MB se prueba en nivel 1 contra la API. El pegado (1 004 096) siempre recibe el `413` de la API | security-design §10; cierra R-01 de la revisión 1 |
| IDS-U6-10 | Revisión 1 de esta etapa, `cicd-pipeline.md` §3 («pueden correr dos revisiones de suspensión») | Con `Recreate` en el trabajador (IDS-U4-02) nunca hay dos `SessionSupervisor`; la tolerancia de scalability-design §1 se conserva como defensa y su prueba de nivel 1 sigue | IDS-U4-02 |
| IDS-U6-11 | Infrastructure Design de U2 §2.1 (`connectionLimit: 25`) | U6 no suma conexiones aparte de la cuarta del trabajador, ya contada por U4; respalda la petición IDS-U4-03 (30) y no hace otra | NFRD-U6-05; IDS-U4-03 |
| IDS-U6-12 | `nfr-design/security-design.md` §5 («Solo `veridicus_retention` borra») | La migración de B7 concede `DELETE` sobre `transcript_paste` solo a `veridicus_retention`; `veridicus_app` queda con `INSERT` y `SELECT`, y la prueba común de U3 lo comprueba | FD-U6-22; NFR11.1 |
| IDS-U6-13 | `nfr-requirements/reliability-requirements.md` (§4, «Sin Redis») | Con el `/readyz` completo de U3 (IDS-U3-01) la API sale del `Service` sin Redis; se adopta NFRD-U6-08 tal cual en la infraestructura | IDS-U3-01; NFRD-U6-08 |
| IDS-U6-14 | `nfr-design/observability-design.md` §4 (dos reglas informativas) | Se añade una tercera regla informativa, `VeridicusOpenSessionsHigh` (`veridicus_sessions{state="open"}` > 50 durante 15 min, P3, sin notificación), porque el supuesto de capacidad del latido y de la revisión es ≤ 50 abiertas | scalability-design §4; cierra R-04 de la revisión 1 |
| IDS-U6-15 | — | El peor caso de turnos importados (≈ 0,3 GiB con índices) cabe en el PVC de 10 GiB de `veridicus-pg`; no se pide más disco | scalability-design §4 (NFR8.7) |

## 7. Cierre de los hallazgos de la revisión 1 · nuevo

| Hallazgo | Dónde se cierra |
|---|---|
| R-01 (`proxy-body-size` frente al *multipart* de la versión de escenario) | La versión de escenario sale; el tope por grupo de U2 (2 113 536) lo comprueba `check-ingress-limits.sh` con C25; IDS-U6-09 |
| R-02 (dónde corre `pytest -m perf`) | `ubuntu-24.04` de 4 vCPU, una sola corrida y cuarentena con *issue*, nunca reintento ni umbral bajado (IDS-U3-09); `cicd-pipeline.md` §2 y `monitoring-design.md` §3 |
| R-03 (*pool* del trabajador y alcance del plazo de inactividad) | §2.2 e IDS-U6-11 (*pool* de 4, pico 25, petición de 30 de U4); §2 e IDS-U6-02 (`SET LOCAL` por transacción) |
| R-04 (umbral de `open` > 50 sin regla) | IDS-U6-14; `monitoring-design.md` §2 |
