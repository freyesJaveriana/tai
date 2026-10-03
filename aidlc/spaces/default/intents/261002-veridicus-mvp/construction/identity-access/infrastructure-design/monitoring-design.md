# Diseño de monitoreo — U3 identity-access

**Insumos.** Logs, métricas, indicadores y trazas de `nfr-design/observability-design.md`
(observability-design); presupuestos de `nfr-design/performance-design.md` (performance-design);
fallas y salud de `nfr-design/reliability-design.md` (reliability-design); capacidad de
`nfr-design/scalability-design.md` (scalability-design); controles de `nfr-design/security-design.md`
(security-design); radio de impacto de `nfr-design/logical-components.md` (logical-components);
eventos de F1–F7 de `functional-design/functional-spec.md` (functional-spec); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); procesos de
`inception/domain-design/components.md` (components); pila común de
`platform/infrastructure-design/monitoring-design.md`; `infrastructure-specification.md` de esta
carpeta.

U3 usa la pila de U2: Prometheus y Grafana desde el módulo 8, sin Alertmanager; logs JSON por salida
estándar con `kubectl logs`; sin trazas.

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| p95 de `veridicus_auth_login_duration_seconds` | `session-api` `:8081/metrics`, `ServiceMonitor` cada 30 s | > 1,0 s durante 15 min | NFR3.1; un p95 alto apunta a CPU escasa para Argon2id |
| `veridicus_auth_login_total{outcome="error"}` | Ídem | > 0 en 5 min | `503` por base, Redis o cola del semáforo (NFR10.12) |
| `veridicus_auth_login_total{outcome="throttled"}` | Ídem | > 20 en 15 min | Posible prueba de contraseñas (observability-design §3) |
| `veridicus_auth_rejections_total` por `code` | Ídem | `auth.csrf` > 0 en 15 min | Un rechazo de CSRF en uso normal indica un fallo de la consola o un ataque |
| Memoria de `session-api` / `limits.memory` | cAdvisor (pila de U2) | > 0,9 durante 5 min | El semáforo de Argon2id debe mantenerla bajo 768 MiB (NFR8.1) |
| `session-api` lista (`readinessProbe`) | kube-state-metrics | No lista durante 2 min | Sin base o sin configuración, nada autenticado funciona |
| Redis disponible para U3 | Sin exportador ni sonda externa: se ve por `veridicus_auth_login_total{outcome="error"}` y por el `/readyz` completo de `scripts/smoke.sh` | > 0 errores en 5 min | La sonda de Kubernetes ya no mira Redis (P1 = B), así que esta es la señal de que el inicio de sesión está cerrado |

## 2. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusLoginSlow` | `histogram_quantile(0.95, …login_duration…[15m]) > 1` | warning (P3) | Panel «Veridicus — latencia» |
| `VeridicusLoginErrors` | `increase(veridicus_auth_login_total{outcome="error"}[5m]) > 0` | warning (P3) | Panel «Veridicus — acceso» |
| `VeridicusLoginThrottling` | `increase(veridicus_auth_login_total{outcome="throttled"}[15m]) > 20` | info (P3) | Panel «Veridicus — acceso»; revisión manual |
| `VeridicusCsrfRejections` | `increase(veridicus_auth_rejections_total{code="auth.csrf"}[15m]) > 0` | info (P3) | Panel «Veridicus — acceso» |
| `VeridicusSessionApiNotReady` | Pod de `session-api` no listo durante 2 min | critical (P3) | Panel «Veridicus — plataforma» de U2 |

Las reglas viven en la `PrometheusRule` del subchart `session-api`, cada una con su anotación
`runbook` y su prueba en `promtool test rules` (un caso que dispara y otro que no). Ninguna notifica a
nadie en el MVP.

## 3. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| p95 del inicio de sesión correcto | ≤ 1,0 s (NFR3.1) | Prueba `perf` de nivel 1 (30 peticiones) y 1 h móvil en Prometheus |
| p95 del costo de F2 en una ruta autenticada | ≤ 25 ms (NFR3.2) | Prueba `perf` de nivel 1 (200 peticiones); no hay histograma por ruta en producción |
| p95 de la respuesta `429` | ≤ 50 ms (NFR3.3) | Prueba `perf` de nivel 1 (50 peticiones) |
| Inicios de sesión con `outcome="error"` durante `scripts/smoke.sh` | 0 (observability-design §3) | Cada corrida de la prueba de humo |
| 10 inicios de sesión simultáneos sin `503` | 10 de 10 (performance-design §4) | Prueba de nivel 1 |

Limitación conocida: detrás de ingress-nginx en Minikube, todos los navegadores de la máquina de la
demostración llegan con la misma dirección de origen, así que el contador por dirección del limitador
(NFR10.5) es común a todos. Con un solo analista en la sustentación no afecta; con varios, 5 fallos de
uno bloquean a todos 15 minutos y `VeridicusLoginThrottling` lo deja visible.

## 4. Logs

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con la lista blanca de observability-design §1 (`timestamp`, `level`, `service`, `request_id`, `user_id`, `route`, `method`, `status`, `code`, `duration_ms`); nunca usuario, contraseña, token, cookie ni `Authorization` (NFR10.7, NFR15.2) |
| Eventos | `401`, `403`, `429` en `INFO` con su `code`; `503` en `ERROR` con `cause` `db`, `redis` o `argon2_queue`; altas y cambios de usuarios; `bootstrap.admin_created` / `bootstrap.admin_exists` del `Job` (NFR15.3) |
| Correlación | `X-Request-ID`: ingress-nginx genera uno por petición, pero no es un UUID v4, así que `session-api` lo reemplaza por uno propio y lo devuelve en la respuesta |
| Dónde se leen | `kubectl logs -n veridicus deploy/session-api`; los del `Job` hasta 600 s después de terminar (`ttlSecondsAfterFinished`) |
| Retención | Rotación del kubelet (10 MiB × 5 archivos); no hay agregación central en el MVP |

## 5. Trazas

No hay trazas distribuidas (observability-design §4): U3 no llama a otros servicios y el
`request_id` correlaciona la consola con su línea de log.

## 6. Paneles

| Panel | Lo que aporta U3 |
|---|---|
| Veridicus — acceso (nuevo, de U3) | Inicios de sesión por `outcome`, p95 del inicio de sesión, rechazos por `code`, intentos bloqueados en 15 min |
| Veridicus — latencia (de U2) | Serie del p95 del inicio de sesión con la línea de 1 s |
| Veridicus — plataforma (de U2) | Memoria de `session-api` frente a 768 MiB y estado de la sonda |

El panel de acceso es un JSON en `deploy/veridicus/dashboards/` con la etiqueta
`grafana_dashboard: "1"`; solo muestra contadores y etiquetas de enum cerradas (BR8.2 de U1).
