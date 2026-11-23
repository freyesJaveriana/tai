# Diseño de monitoreo — U3 identity-access

**Revisión 2 (2026-11-23), segunda pasada por el cambio 01, la adenda 02 y el NFR Design revisión 2 de
U3.** Sustituye a la revisión 1 del 2026-10-03.
- **Se mantienen:** pila de U2 (Prometheus y Grafana desde el módulo 8, sin Alertmanager), logs JSON por
  salida estándar, sin trazas.
- **Cambian:** la caída de Redis se ve en la sonda de disponibilidad (cierra R-01 a); la etiqueta `code`
  pasa a `error_code`; reglas y panel pasan a `charts/monitoring-rules/` (IDS-U3-10).
- **Nuevos:** alertas sobre `veridicus_problem_responses_total` y `veridicus_access_log_failures_total`.

**Insumos.** Logs, métricas e indicadores de `nfr-design/observability-design.md`
(observability-design); presupuestos de `nfr-design/performance-design.md` (performance-design); fallas
y salud de `nfr-design/reliability-design.md` (reliability-design); capacidad de
`nfr-design/scalability-design.md` (scalability-design); controles y lista blanca de
`nfr-design/security-design.md` (security-design); radio de impacto de `nfr-design/logical-components.md`
(logical-components); eventos de F1–F7, F10, F11 y F13 de `functional-design/functional-spec.md`
(functional-spec); C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary);
procesos de `inception/domain-design/components.md` (components); observabilidad de la plataforma del NFR
Design de U2 (§11); `infrastructure-specification.md` de esta carpeta.

Antes del módulo 8 no hay Prometheus: las señales son `kubectl get pods`, `kubectl logs` y
`scripts/smoke.sh`. Desde el módulo 8, un `ServiceMonitor` `veridicus-session-api` raspa el puerto
`metrics` cada 30 s, y la CPU y la memoria salen del `kubelet` (U2 §2.1).

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| p95 de `veridicus_auth_login_duration_seconds` | `session-api` `:8081/metrics` | > 1,0 s durante 15 min | NFR3.1; un p95 alto apunta a CPU escasa para Argon2id |
| `veridicus_auth_login_total{outcome="error"}` | Ídem | > 0 en 5 min | `503` por base, Redis, *pool* o cola del semáforo (NFR10.12, NFR8.4) |
| `veridicus_auth_login_total{outcome="throttled"}` | Ídem | > 20 en 15 min | Posible prueba de contraseñas o bloqueo inducido (T11; IDS-U3-14) |
| `veridicus_auth_rejections_total{error_code="auth.csrf"}` | Ídem | > 0 en 15 min | Un rechazo de CSRF en uso normal indica un fallo de la consola o un ataque |
| `veridicus_problem_responses_total{status="500"}` | Ídem | > 0 en 15 min | Error no previsto (NFR10.17); el log lleva `exc_type` y la huella de la pila |
| `veridicus_problem_responses_total{status="503"}` | Ídem | > 0 en una corrida de `scripts/smoke.sh` | observability-design §3 |
| `veridicus_access_log_failures_total` | Ídem | > 0 en 15 min, tras cablear U13 | El registro de lecturas se degradó (NFR10.21) |
| Memoria de `session-api` / `limits.memory` | `kubelet` (cAdvisor) | > 0,9 durante 5 min | El semáforo debe mantenerla bajo el límite (NFR8.1) |
| `session-api` lista (`readinessProbe`) | kube-state-metrics | No lista durante 2 min | Sin base **o sin Redis**, toda la consola queda sin servicio (reliability-design §2) |

La fila «Redis disponible para U3» de la revisión 1 queda «Retirado»: la `readinessProbe` ya consulta
Redis, así que su caída dispara `VeridicusSessionApiNotReady` (IDS-U3-01).

## 2. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusLoginSlow` | `histogram_quantile(0.95, sum by (le) (rate(veridicus_auth_login_duration_seconds_bucket[15m]))) > 1` | warning | Panel «Veridicus — acceso» |
| `VeridicusLoginErrors` | `increase(veridicus_auth_login_total{outcome="error"}[5m]) > 0` | warning | Panel «Veridicus — acceso» |
| `VeridicusLoginThrottling` | `increase(veridicus_auth_login_total{outcome="throttled"}[15m]) > 20` | info | Panel «Veridicus — acceso»; revisión manual |
| `VeridicusCsrfRejections` | `increase(veridicus_auth_rejections_total{error_code="auth.csrf"}[15m]) > 0` | info | Panel «Veridicus — acceso» |
| `VeridicusInternalErrors` | `increase(veridicus_problem_responses_total{status="500"}[15m]) > 0` | warning | Panel «Veridicus — acceso»; leer el log por `request_id` |
| `VeridicusAccessLogFailures` | `increase(veridicus_access_log_failures_total[15m]) > 0` | warning | Panel «Veridicus — acceso» |
| `VeridicusSessionApiNotReady` | Pod de `veridicus-session-api` no listo durante 2 min | critical | Panel «Veridicus — plataforma» de U2 |

- Las reglas viven en la `PrometheusRule` del subchart `charts/monitoring-rules/` de U2, cada una con su
  anotación `runbook` y su prueba en `charts/monitoring-rules/tests/session-api-auth.test.yaml` (un caso
  que dispara y otro que no). El comando y su umbral están en `cicd-pipeline.md` §1.1 (cierra R-02).
- Ninguna notifica a nadie en el MVP (`project.md`: sin Alertmanager); la severidad ordena el panel.
- Un `VeridicusSessionApiNotReady` con `VeridicusLoginErrors` y logs `cause: redis` indica Redis caído;
  la consola vuelve sola cuando Redis responde.

## 3. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| p95 del inicio de sesión correcto | ≤ 1,0 s (NFR3.1) | Prueba `perf` de nivel 1 (30 inicios con Argon2id real) y 1 h móvil en Prometheus |
| p95 del costo de F2 en una ruta de lectura | ≤ 25 ms (NFR3.2) | Prueba `perf` de nivel 1 (200 peticiones); sin histograma por ruta en el clúster |
| p95 del sobrecosto de F2 en una ruta que cambia estado | ≤ 30 ms (NFR3.4) | Prueba `perf` de nivel 1 (200 peticiones) |
| p95 de la respuesta `429` | ≤ 50 ms (NFR3.3) | Prueba `perf` de nivel 1 (50 peticiones) |
| Memoria extra con 10 inicios simultáneos | ≤ 160 MiB (NFR8.1) | Prueba `perf` de nivel 1 en subproceso |
| Respuestas `503` y `500` durante `scripts/smoke.sh` | 0 (observability-design §3) | Cada corrida de la prueba de humo |
| Disponibilidad de `session-api` | Sin SLO porcentual en el MVP: una sola réplica y una sola máquina; la meta es 0 `VeridicusSessionApiNotReady` durante la demostración | Ensayo y demostración |

Limitación conocida (IDS-U3-14): en Minikube sobre WSL2 todos los navegadores llegan con la misma
dirección de origen, así que el contador por origen del limitador es común a todos. Con un analista en
la demostración no afecta; con varios, 5 fallos de uno bloquean a todos 15 minutos y
`VeridicusLoginThrottling` lo deja visible.

## 4. Logs

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con la lista blanca de observability-design §1 (`timestamp`, `level`, `service`, `event`, `request_id`, `user_id`, `route`, `method`, `status`, `code`, `demo`, `duration_ms` y, cuando aplica, `resource_type`, `resource_id`, `cause`, `exc_type`, más los campos que suman las peticiones de otras unidades); nunca usuario, contraseña, token, cookie ni `Authorization` (NFR10.7, NFR15.2) |
| Eventos | `401`, `403`, `422`, `429` en `INFO` con su `code`; `503` en `ERROR` con `cause` `db`, `redis`, `pool` o `argon2_queue`; `500` en `ERROR` con `exc_type`; altas y cambios de usuarios; `access_log.*`; `bootstrap.*` del `Job` (NFR15.3) |
| Uvicorn | `--no-access-log`; `uvicorn.error` solo recibe lo que deja el manejador único |
| Correlación | `X-Request-ID` UUID v4 propio de `session-api`; uno entrante solo se acepta si es UUID válido; es el `instance` del Problem Details |
| Dónde se leen | `kubectl logs -n veridicus deploy/veridicus-session-api -c session-api`; los del `Job` hasta 3 600 s después de terminar (`ttlSecondsAfterFinished`) |
| Retención | Rotación del kubelet (10 MiB × 5 archivos); sin agregación central (sin Loki, U2 §11) |
| Datos sintéticos | La captura de logs de nivel 1 de U2 busca el *canary* del turno de U4 en todos los contenedores, incluido `session-api` (NFR10.19 de U2) |

## 5. Trazas

No hay trazas distribuidas (observability-design §4): U3 no llama a otros servicios y el `request_id`
correlaciona la consola con su línea de log.

## 6. Paneles

| Panel | Lo que aporta U3 |
|---|---|
| Veridicus — acceso (de U3) | Inicios de sesión por `outcome`, p95 del inicio de sesión con la línea de 1 s, rechazos por `error_code` y `demo`, respuestas `500`/`503`, fallos del registro de acceso |
| Veridicus — latencia (de U2) | **Retirado** para U3: la serie del p95 del inicio de sesión pasa al panel de acceso, porque U2 ya no define un panel de latencia común (U2 §11: uno por unidad) |
| Veridicus — plataforma (de U2) | Memoria de `session-api` frente a su límite y estado de la sonda |

El panel de acceso es un `ConfigMap` versionado en `charts/monitoring-rules/dashboards/` (U2 §11); solo
muestra contadores y etiquetas de enum cerradas. La ruta `deploy/veridicus/dashboards/` de la revisión 1
queda «Retirado» (IDS-U3-10).
