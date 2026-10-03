# Especificación de infraestructura — U6 session-lifecycle

**Insumos.** Presupuestos del pegado, latido, revisión y recursos de `nfr-design/performance-design.md`
(performance-design); frontera, entrada acotada, permisos de la base y Redis sin texto de
`nfr-design/security-design.md` (security-design); réplicas, límites del pegado y señales de
`nfr-design/scalability-design.md` (scalability-design); *timeouts*, ajustes, marca de lote y
suspensión sin competir de `nfr-design/reliability-design.md` (reliability-design); métricas y eventos
de `nfr-design/observability-design.md` (observability-design); inventario, radio de impacto, recursos
compartidos y entrega a Infrastructure Design de `nfr-design/logical-components.md`
(logical-components); flujos F1–F6 y máquina de estados de `functional-design/functional-spec.md`
(functional-spec); procesos de `inception/domain-design/components.md` (components); C1, C2, C4, C11,
C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); infraestructura común
de U2 (`platform/infrastructure-design/infrastructure-specification.md`), despliegue de `session-api`
de U3 (`identity-access/infrastructure-design/infrastructure-specification.md`) y trabajador, consola y
recursos de U4 (`text-flow/infrastructure-design/infrastructure-specification.md`); requisitos de
`nfr-requirements/` de esta unidad; `infrastructure-design-questions.md` (sin preguntas abiertas).

U6 **no añade procesos, imágenes, servicios de infraestructura ni reglas de red**: todo vive en la API y
el trabajador de `session-api` y en `frontend`, que ya despliegan U3 y U4. Lo que fija esta unidad son
tres ajustes, un hilo más en el trabajador, una migración y su configuración de Redis y de CI.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Modelo de cómputo | Contenedores en los `Deployment` existentes: `session-api` (API, U3) atiende `/transcript`, `/heartbeat`, `/resume`, `GET /sessions` y `/scenarios/{id}/versions`; `session-api-worker` (U4) ejecuta `SuspensionSweeper`; `frontend` (U4) sirve M1, los diálogos de pegado y reanudación y el historial lateral | logical-components §1 y §4: nada de U6 justifica un proceso propio |
| Réplicas | 1 de cada proceso; el diseño admite más (`FOR UPDATE SKIP LOCKED`, restricción única del lote, `WATCH` de la marca), así que el segundo pod transitorio del `RollingUpdate` (`maxSurge: 1`) no duplica suspensiones ni lotes | scalability-design §1 (NFR8.2) |
| Hilos del trabajador | Cuatro bajo la supervisión de U4: ingesta, plazos, indexador y `SuspensionSweeper` (cada 30 s). Un hilo muerto termina el proceso y Kubernetes lo reinicia; el `/readyz` del trabajador comprueba el latido en memoria de los cuatro | reliability-design §3 (NFR10.12) |
| Sondas | API: `/readyz?probe=kubernetes` de U3 (configuración, incluidos los tres ajustes de U6, y base; sin Redis). Trabajador: `/readyz` de U4 con el cuarto hilo. Con Redis caído el pod de la API sigue en el Service y solo el pegado responde `503` | logical-components §2; C16 |
| Red | Entrada solo por el `Ingress` de U2 (`/api/` → 8080) y `monitoring` → 8081. Salida: API → `veridicus-pg`, `veridicus-redis`; trabajador → además `veridicus-embeddings` (indexación de U4). Ningún destino nuevo; ambos pods bajo `veridicus-default-deny` y `deny-external-egress` de U2 y la lista blanca de CoreDNS de U10 sin zonas nuevas | security-design §1 (NFR1.1, AUTONOMIA-04) |
| Entrada HTTP | Cuerpo del pegado ≤ 524 288 bytes y versión de escenario ≤ 1 048 576 bytes: caben en el `proxy-body-size` del `Ingress` (el mayor tamaño de C1 del catálogo); el pegado de peor caso tarda ≤ 2 s, dentro del `proxy-read-timeout` de 30 s | security-design §2; performance-design §1 |
| Almacenamiento | Sin PVC nuevos. Tablas y columnas en `veridicus-pg` (§2.1); la marca del lote en `veridicus-redis` (< 100 bytes, 24 h) | scalability-design §4 (NFR8.7) |
| Recursos | Sin cambios: API 0,5 / 384 MiB – 2 / 768 MiB (U3); trabajador 0,5 / 512 MiB – 1,5 / 960 MiB (U4). Cuenta en §1.1 | performance-design §7 (NFR8.1) |
| Entornos | Los dos de U2: máquina de desarrollo (Minikube 20 GiB / 10 CPU, `values-cpu.yaml`) y de demostración (Minikube 28 GiB, `values-gpu.yaml` más `values-extras.yaml` de U8). U6 tiene los mismos valores en las dos; sin *staging* ni producción | team.md `## Deployment`; NFR2.2 |
| IaC | Valores en el chart `deploy/veridicus` (los `ConfigMap` de la API y del trabajador) y una revisión de Alembic en `db/migrations/` aplicada por el `migrations-job` de U2. Todo por PR; ningún paso aplica cambios al clúster sin la fusión aprobada | AUTONOMIA-01; security-design §5 |

### 1.1 Recursos con el pegado de peor caso (NFR8.1)

| Contenedor | Pico previo | Lo que añade U6 | Pico estimado | `limits` de memoria | Margen |
|---|---|---|---|---|---|
| `session-api` (API) | ≈ 360 MiB (base ≈ 200 MiB + 2 × 64 MiB de Argon2id + margen, U3) | ≤ 50 MiB (cuerpo de 512 KiB leído una vez y ≤ 200 turnos) | ≈ 410 MiB | 768 MiB | ≈ 87 % |
| `session-api-worker` | ≤ 768 MiB (U4) | ≈ 0 (la revisión solo guarda identificadores) | ≤ 768 MiB | 960 MiB | 25 % |

Si la medición de NFR3.1 supera el +50 MiB, se corrige por PR con la medición; los márgenes de ≥ 20 % de
U4 se mantienen con holgura, así que el presupuesto de Minikube de U4 no cambia.

### 1.2 Configuración de U6 (prefijo `VERIDICUS_`)

| Ajuste | Valor en los *values* | Regla validada al arrancar | Procesos |
|---|---|---|---|
| `HEARTBEAT_TIMEOUT_SECONDS` (*T*) | 180 | Entero 60–1 800 | API y trabajador |
| `SUSPENSION_SWEEP_SECONDS` | 30 | Entero 5 – *T*/2 | API y trabajador |
| `HEARTBEAT_WRITE_MIN_SECONDS` | 15 | Entero 1 – *T*/4 | API y trabajador |
| Límites del pegado (60 de testimonio, 200 turnos, 100 000 caracteres, 2 000 por turno, 524 288 bytes) | No van en los *values*: se leen de `contracts/limits.v1.yaml` dentro de la imagen; una variable solo puede bajarlos | Catálogo de U1 | API y consola |

Los tres ajustes van en el bloque común de los *values* que renderiza el mismo par clave–valor en los
`ConfigMap` de ambos procesos; así la API no valida el mínimo del latido contra un *T* distinto del que
usa el trabajador (reliability-design §1, NFR10.10). La paridad entre las dos máquinas sale de que ningún
archivo de perfil (`values-cpu.yaml`, `values-gpu.yaml`, `values-extras.yaml`) los sobrescribe; una
prueba de `deploy-level0.yml` lo comprueba.

## 2. Servicios de infraestructura

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-pg` | database | Rol `veridicus_app` y pools de U3/U4 sin cambios; `statement_timeout` 2 s y `SET LOCAL statement_timeout = '5s'` en las transacciones del pegado y de la revisión; `idle_in_transaction_session_timeout` 5 s | Sin conexiones nuevas: la revisión usa el pool de 3 del trabajador y las rutas el de la API (reliability-design §1, NFR10.9) |
| `veridicus-redis` | queue | Redis 7.2 de U2 con `maxmemory 384mb`, `maxmemory-policy noeviction` y AOF `appendfsync everysec` (sin cambio). U6 publica en `veridicus:turns` (C2, sin cambio) y escribe `veridicus:paste-published:<paste_batch_id>` = `1` con `EX 86400` en la misma `MULTI`/`EXEC`; `socket_timeout` 0,5 s | `noeviction` garantiza que la marca no se desaloje (reliability-design §2, NFR8.10, NFR10.11); el AOF conserva `XADD` y marca juntos o ninguno |
| `veridicus-embeddings` | other | Lo usa el indexador de U4 para la versión nueva de un escenario; sin configuración propia | NFR9.1 |
| `load-balancer` | load-balancer | `Ingress` de U2 sin cambios | §1 |
| `cache`, `search`, `cdn`, `dns` | — | No aplica | La lista es una consulta agregada en PostgreSQL |

### 2.1 Migración de U6 (un PR propio, antes del código)

| Objeto | Cambio | Permisos de `veridicus_app` |
|---|---|---|
| `turn` | Columnas `speaker`, `role`, `paste_batch_id` (anulables, aditivas) | Los de U4 |
| `interview_session` | Columna `suspended_at`; índice parcial de expresión `((COALESCE(last_heartbeat_at, created_at))) WHERE status = 'open'` (con `CREATE INDEX CONCURRENTLY` fuera de transacción) | Los de U4 |
| `transcript_paste` | Tabla nueva; restricción única `(session_id, client_request_id)` | `INSERT, SELECT` |
| `session_status_change` | Tabla nueva | `INSERT, SELECT` |
| `scenario_version` | Restricción única `(scenario_id, version_number)` si no existe | Sin `DELETE` (U4) |
| `veridicus_now()` | Función `STABLE` que devuelve `now()` | `EXECUTE` |
| `human_review.session_pending_suggestions` | Vista de solo lectura que publica la migración de U5; la de U6 depende de ella | `SELECT` |

La versión de `veridicus_now()` que lee una hora inyectada **no** se instala en el clúster: la crea el
*fixture* de las pruebas de nivel 1 con el rol dueño del contenedor de la CI. En el clúster ningún rol
puede adelantar el reloj de la suspensión (D3 de tech-stack-decisions: «en las pruebas»).

## 3. Frontera y datos que cruzan (AUTONOMIA-04)

| Componente | Dentro o fuera del clúster | Datos que cruzan | Destino |
|---|---|---|---|
| Rutas de U6 en la API | Dentro | Testimonio pegado (HTTPS desde el navegador por el `Ingress`); `SessionSummary` sin texto de turnos hacia el navegador | Navegador |
| `TranscriptIntake` | Dentro | Turnos de testimonio en C2 y el UUID del lote | `veridicus-pg`, `veridicus-redis` |
| `HeartbeatWriter`, `SessionResume`, `SuspensionSweeper` | Dentro | Identificadores y horas | `veridicus-pg` |
| `ScenarioVersionUpload` | Dentro | Documento sintético (C4) y pasajes hacia el indexador | `veridicus-pg`, `veridicus-redis`, `veridicus-embeddings` |
| Consola (vista previa) | Navegador | Nada: la división se calcula localmente, 0 peticiones | — |

Ningún componente de U6 tiene destino externo, así que no hay *payload* que pase por el anonimizador.

## 4. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `session-api` (API) | U3 | U4–U7 | Rutas por unidad con `authorize` de U3; U6 no cambia recursos ni sondas |
| `session-api-worker` | U4 | U6 (`SuspensionSweeper`), U7, U8 | Un hilo por tarea bajo la misma supervisión; cada unidad añade su configuración por PR |
| `ConfigMap` de API y trabajador | U4 | U6 | U6 solo añade sus tres claves en el bloque común |
| Fila `interview_session` y `change_seq` | U4 | U6, U7, U5 | Latido y revisión con `SKIP LOCKED`; orden único sesión → ronda; el latido no incrementa `change_seq` |
| `veridicus-redis` | U2 | U3, U4, U6, U8, U9 | Contraseña única; U6 usa el prefijo `veridicus:paste-published:` con expiración y C2 sin cambios |
| `veridicus-pg` y `migrations-job` | U2 (`session-api` dueño del esquema) | Todas | Migraciones aditivas por PR; U6 depende de la vista de U5 |
| Vista `human_review.session_pending_suggestions` | U5 | U6 (ConsoleApi) | Solo `SELECT`; U6 no lee tablas de U5 |
| `contracts/fixtures/transcript-split.v1.json` y `contracts/limits.v1.yaml` | U1 | U6 (API y consola) | Cambian solo por PR y disparan las suites de `session-api` y de `frontend` |
| `frontend` | U4 | U3, U5–U9 | Una imagen; U6 añade M1 y sus diálogos por PR |

## 5. Comportamientos operativos documentados

| Situación | Qué pasa | Por qué se acepta |
|---|---|---|
| `minikube stop` / `start` o la API caída más de 180 s con el trabajador vivo | En la primera revisión con base disponible, las sesiones `open` sin latido pasan a `suspended` (`actor_kind = system`) | La reanudación es un clic del dueño, no pierde nada (NFR8.8) y la condición se evalúa sobre el estado, no sobre un temporizador en memoria |
| Redis caído | Solo el pegado responde `503`; lista, latido y reanudación siguen | logical-components §2 |
| Trabajador caído | Las suspensiones se retrasan hasta que reinicia; ninguna se pierde | reliability-design §3 |
| Restauración de `pg_dump` | Las tablas de U6 viajan con el esquema; las marcas de Redis no hacen falta porque expiran antes de cualquier restauración útil (24 h > tope de 3 600 s) | Respaldo de U2 |

## 6. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado ni de otra unidad; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `text-flow/infrastructure-design/infrastructure-specification.md` §1.2 y §6 | El `/readyz` de `session-api-worker` comprueba el latido de **cuatro** hilos (añade `SuspensionSweeper`), no tres | reliability-design §3; logical-components §1 |
| `text-flow/infrastructure-design/cicd-pipeline.md` §1 (`frontend.yml`) | El filtro de rutas de `frontend.yml` añade `contracts/fixtures/transcript-split.v1.json` y `contracts/limits.v1.yaml`; hoy solo `frontend/**`, y un cambio del archivo de división no ejecutaría Vitest | NFR13.2; D5 de tech-stack-decisions |
| `text-flow/infrastructure-design/infrastructure-specification.md` §2.1 | La tabla de configuración suma `HEARTBEAT_TIMEOUT_SECONDS`, `SUSPENSION_SWEEP_SECONDS` y `HEARTBEAT_WRITE_MIN_SECONDS` en API y trabajador | reliability-design §1 (NFR10.10) |
| `session-lifecycle/nfr-requirements/tech-stack-decisions.md` (D3) | `veridicus_now()` del clúster devuelve solo `now()`; la variante con hora inyectada la instala el *fixture* de nivel 1 | security-design §5; mínimo privilegio |
