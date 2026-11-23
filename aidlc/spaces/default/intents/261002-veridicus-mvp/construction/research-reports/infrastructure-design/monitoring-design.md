# Diseño de monitoreo — U12 research-reports

**Revisión 1 (2026-11-23): primera pasada.** Todo es nuevo.

**Insumos.** Líneas de log, métricas y salud de `nfr-design/observability-design.md` (observability-design
§1–§6); presupuestos y memoria de `nfr-design/performance-design.md` (performance-design §1, §3, §5, §8);
señales que se degradan primero de `nfr-design/scalability-design.md` (scalability-design §7); plazos y
degradación de `nfr-design/reliability-design.md` (reliability-design §1, §8); lista blanca y *canary* de
`nfr-design/security-design.md` (security-design §5, §7); radio de impacto de
`nfr-design/logical-components.md` (logical-components §3); estados del diálogo de subida de
`functional-design/functional-spec.md` (functional-spec §3); ResearchReports en
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de U2 y monitoreo de
`session-api` de U3; `infrastructure-specification.md` de esta carpeta.

U12 no publica métricas propias (`research-reports-no-metrics` prohíbe `prometheus_client` en su módulo) y
C15 no cambia. Se observa con tres fuentes que ya existen: la línea de log `research_report.upload`, las
métricas genéricas que U3 publica para todas las rutas en el puerto `metrics` 8081 de `session-api` y la
memoria del contenedor que da el kubelet. Usa la pila de U2: Prometheus y Grafana desde el módulo 8, sin
Alertmanager, sin Loki y sin trazas; antes del módulo 8, `kubectl logs` y `scripts/smoke.sh`.

## 1. Métricas y KPI

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| Memoria del contenedor `session-api` / `limits.memory` (1 792 MiB, IDS-U12-01) | `container_memory_working_set_bytes` del kubelet (U2) | > 0,9 durante 5 min | Dos subidas máximas suman hasta 512 MiB al proceso común; pasar de 0,9 es acercarse al `OOMKilled` de todas las unidades de la API (T18, scalability-design §7) |
| `veridicus_problem_responses_total{status="503"}` | `session-api` `:8081/metrics` (métrica genérica de U3) | > 0 durante una corrida de `smoke.sh`; se muestra en el panel | Incluye los `503` de la subida (`upload_slots`, `upload_read_timeout`, `db`); la causa se lee en el log (§4) |
| `veridicus_problem_responses_total{status="500"}` | Ídem | > 0 en 15 min (regla de U3) | Un fallo del código de U12 deja `500` `system.internal` y 0 filas (logical-components §3) |
| `session-api` lista | kube-state-metrics | No lista durante 2 min (regla de U3) | Con un catálogo de referencia roto el pod nuevo nunca pasa a listo (reliability-design §6) |
| Tamaño de las cuatro tablas de U12 | `pg_total_relation_size`, consulta manual en la revisión de B12 | > 1,5 GiB o más de 900 reportes | Disparador de la paginación y de revisar el PVC (scalability-design §4 y §5; IDS-U12-08) |

Ninguna serie lleva el `research_report_id`, el SHA-256 ni valores del reporte. Un contador de subidas
futuro entra como precisión a C15 con la etiqueta `outcome` de la lista cerrada de U1 (observability-design
§4); esta revisión no lo crea.

## 2. Alertas

Reglas informativas en `charts/monitoring-rules/` de U2, cada una con su anotación `runbook` y su prueba
`promtool test rules` con un caso que dispara y otro que no; solo se renderizan con
`monitoring.enabled: true`. Ninguna notifica a nadie ni cambia nada (`project.md`: sin Alertmanager).

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusSessionApiNearMemoryLimit` (nueva, IDS-U12-09) | `container_memory_working_set_bytes{container="session-api"} / on(pod) kube_pod_container_resource_limits{resource="memory", container="session-api"} > 0.9` durante 5 min | warning (P3) | Panel «Veridicus — plataforma» de U2; el runbook pide buscar líneas `research_report.upload` y exportaciones de U7 en curso, y si se repite, medir de nuevo NFR3.8 |
| `VeridicusInternalErrors` (de U3) | `increase(veridicus_problem_responses_total{status="500"}[15m]) > 0` | warning (P3) | Panel «Veridicus — acceso»; leer el log por `request_id` |
| `VeridicusSessionApiNotReady` (de U3) | Pod de `veridicus-session-api` no listo durante 2 min | critical (P3) | Panel «Veridicus — plataforma»; con un despliegue reciente, buscar `config.invalid_reference_catalog` |

U12 no crea una alerta por los `503` de la subida: con un investigador y decenas de reportes, un `503` con
`cause: upload_slots` es una respuesta prevista (`Retry-After: 10`) y su causa ya queda en el log.

## 3. SLIs / SLOs

Son objetivos de verificación del MVP (pruebas `perf` de nivel 1 y Playwright de nivel 3), no SLO con
ventana de producción: U12 no tiene objetivo de disponibilidad propio y está disponible cuando lo están
`session-api` y PostgreSQL (reliability-design, introducción).

| SLI | SLO target | Measurement window |
|---|---|---|
| p95 de la subida típica, de punta a punta en el servidor | ≤ 2 s (NFR3.1) | 50 repeticiones de la marca `perf` |
| p95 de la subida del peor caso estimado y del máximo | ≤ 6 s y ≤ 12 s (NFR3.2) | Ídem |
| Rechazos tempranos (`413`, `409`, `json_depth`, `encoding`) | ≤ 1 s (NFR3.3) | Ídem |
| p95 de la lista con 1 000 reportes | ≤ 500 ms (NFR3.4) | Ídem |
| p95 del detalle | ≤ 500 ms típico; ≤ 2 s peor caso (NFR3.5) | Ídem |
| p95 de la comparación | ≤ 1 s típicos; ≤ 4 s peor caso (NFR3.6) | Ídem |
| Aumento de RSS de la API | ≤ 256 MiB con una subida máxima; ≤ 512 MiB con dos (NFR3.8) | Marca `perf`, con `psutil` |
| Aumento del p95 del sondeo de U4 durante una subida máxima | ≤ 200 ms (NFR3.10) | Caso `test_upload_does_not_slow_polling` |
| Espacio por reporte | ≤ 1,5 × `source_bytes` (NFR3.11) | Nivel 1 con `pg_total_relation_size` |
| Respuesta de M8 con 1 000 filas | ≤ 300 ms (NFR3.7) | Playwright con `performance.now()` |
| Memoria de la API en el clúster | < 0,9 del límite fuera de picos de 5 min | Desde el módulo 8, `VeridicusSessionApiNearMemoryLimit` |

## 4. Logs & Tracing

| Aspecto | Diseño |
|---|---|
| Línea de la subida | `research_report.upload` en un `finally`, con el formateador único y la lista blanca de U3: comunes (`timestamp`, `level`, `service`, `request_id`, `route`, `method`, `user_id`), `outcome`, `status`, `code`, `rule`, `problem_count`, `resource_type`, `resource_id`, `source_sha256`, `source_bytes`, `cause`, `duration_ms` (observability-design §1). `INFO` en `accepted`, `WARNING` en `rejected` y `aborted`, `ERROR` en `503` |
| Línea de arranque | `research_reports.catalog_loaded` con `catalog_sha256`, `price_table_version`, `profile_count` y `c19_version`; ante un fallo, `ERROR` `config.invalid_reference_catalog` con el archivo y la regla, nunca su contenido |
| Sin contenido | Ni cuerpo, ni documento JSON, ni `filename`, ni mensajes de `json` o `jsonschema`; acceso de Uvicorn apagado (`--no-access-log`). La captura de logs con el *canary* de U2 (`deploy-level1.yml`) cubre también `session-api` |
| Dónde se leen | `kubectl logs -n veridicus deploy/veridicus-session-api -c session-api` (solo lectura), filtrando por `event`; rotación del kubelet (10 MiB × 5) |
| Qué responde | Quién subió y cuándo (`user_id`, fila con `uploaded_by` y `uploaded_at`); por qué se rechazó (`code`, `rule`, `problem_count`, mismo SHA-256 que ve M8); si los cortes son por huecos o por plazo (`cause`); con qué catálogo arrancó el pod (`catalog_sha256`) |
| Retención | Sin retención especial: las líneas solo llevan IDs, enums, cifras y hashes |
| Trazas | Sin trazas distribuidas: U12 no llama a otros servicios; el `request_id` correlaciona M8 con su línea |

## 5. Paneles

| Panel | Contenido de U12 |
|---|---|
| Veridicus — plataforma (U2) | Memoria de `session-api` frente a su límite de 1 792 MiB, con la línea de 0,9 |
| Veridicus — acceso (U3) | Las respuestas `500` y `503`, que ya incluyen las de `/research-reports*` |

U12 no añade un panel propio: sin métricas nuevas, una fila más solo repetiría las de U3 y U2.
