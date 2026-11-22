# Diseño de observabilidad — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y NFR Requirements revisión 2
de U3.** Sustituye a la revisión 1 del 2026-10-03.
- **Se mantienen:** formateador JSON con lista blanca, `request_id` y sin trazas distribuidas.
- **Cambian:** los campos suman `demo`; la etiqueta `code` pasa a `error_code` y suma `demo`; los eventos
  suman el registro de acceso y los `500`.
- **Nuevos:** `veridicus_access_log_failures_total` y `veridicus_problem_responses_total`; métricas en el
  puerto interno 8081 (NFR10.23).

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D10) de esta unidad, revisión 2; flujos F1–F6, F10, F11 y F13 de
`functional-design/functional-spec.md` (functional-spec); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); formato de fecha y lista de etiquetas
del NFR Design de U1, revisión 2.

## 1. Logs estructurados (NFR15.2, NFR15.3)

- Un formateador JSON único emite una línea por evento con solo estos campos: `timestamp`
  (`AAAA-MM-DDTHH:MM:SSZ`, forma de U1), `level`, `service`, `event`, `request_id`, `user_id` (si hay
  principal), `route` (plantilla, nunca la URL con identificadores), `method`, `status`, `code`, `demo`,
  `duration_ms` y, en los eventos que los nombran, `resource_type`, `resource_id`, `cause` y
  `exc_type`. Cualquier otro campo se descarta.
- Nunca: nombre de usuario, contraseña, token, cookie, cabecera `Authorization`, cuerpo de la petición,
  mensaje de excepción ni texto de testimonio (NFR10.7, BR8.2).
- `request_id`: un *middleware* genera un UUID v4 por petición, lo pone en `X-Request-ID` y en el
  contexto del *logger*, y es el `instance` del Problem Details. Un `X-Request-ID` entrante solo se acepta
  si es un UUID válido.
- `demo` es `true` cuando la operación lleva `x-veridicus-demo` (BR4.5).

| Evento | Nivel | `code` y campos |
|---|---|---|
| Inicio de sesión correcto | `INFO` | — |
| `401`, `403`, `422` de autorización o validación, `429` | `INFO` | El de la respuesta |
| Alta, desactivación, reactivación o cambio de rol | `INFO` | `user.created`, `user.deactivated`, `user.reactivated`, `user.role_changed` |
| `AccessLog.record` falla o vence | `WARNING` | `access_log.record_failed`, con `resource_type` y `resource_id` |
| Arranque con el adaptador por defecto de `AccessLog` o de `PendingSessions` | `WARNING` | `access_log.not_configured`, `pending_sessions.default` |
| Cabecera `X-Forwarded-For` ausente o inválida desde el proxy de confianza | `WARNING` | `auth.forwarded_for_missing` |
| `503` por base, Redis, *pool* o cola del semáforo | `ERROR` | `system.unavailable`, con `cause`: `db`, `redis`, `pool` o `argon2_queue` |
| `500` | `ERROR` | `system.internal`, con `exc_type` y la huella de la pila, sin mensaje |
| `create-admin` | `INFO` o `ERROR` | `bootstrap.admin_created`, `bootstrap.admin_exists`, `bootstrap.invalid_input` |
| Configuración inválida al arrancar | `ERROR` | `config.invalid_limit` u otro `code` de arranque, con el nombre del ajuste o la ruta, nunca su valor |

Los `code` de evento que no son de C1 (`access_log.*`, `bootstrap.*`, `pending_sessions.default`,
`auth.forwarded_for_missing`) son nombres de evento del log, no respuestas HTTP. Prueba de nivel 1 que
captura los logs de E1, E4, E5, E32, E33, E36, E38 y del `429` y comprueba nivel y campos.

## 2. Métricas (NFR15.1, NFR10.23)

`prometheus-client` sirve `/metrics` en el puerto `metrics` 8081, con su propio servidor en un hilo; la
aplicación de la API (8080) no monta `/metrics` y el Ingress solo enruta a 8080, así que
`/metrics` por el Ingress responde `404` (prueba de humo). Son métricas internas de `session-api`, fuera
de C15 (NFR-U3-03); siguen la regla de etiquetas de U1: solo valores de enum.

| Métrica | Tipo | Etiquetas | Dónde se actualiza |
|---|---|---|---|
| `veridicus_auth_login_total` | counter | `outcome`: `success`, `invalid_credentials`, `throttled`, `error` | Al final de F1, una vez por petición |
| `veridicus_auth_login_duration_seconds` | histogram (0,1; 0,25; 0,5; 1; 2; 5 s) | — | Alrededor de F1 |
| `veridicus_auth_rejections_total` | counter | `error_code`: `auth.unauthenticated`, `auth.csrf`, `auth.forbidden`, `session.not_owner`, `validation.invalid_request`; `demo`: `true`, `false` | En `GuardedRoute`, pasos 2–8 |
| `veridicus_access_log_failures_total` | counter | `resource_type`: `session`, `suggestion`, `report_version` | En `record_access` |
| `veridicus_problem_responses_total` | counter | `status`: `500`, `503` | En el manejador único |

Prueba de nivel 0: recorre el registro y falla si una etiqueta toma un valor fuera de su enum. Prueba de
nivel 1: cada contador sube 1 en su escenario (E1, E4, E5, E31, E32, E33, E36 y el `429`).

## 3. Indicadores y umbrales de revisión

| Indicador | Fuente | Umbral de revisión manual |
|---|---|---|
| p95 del inicio de sesión | `veridicus_auth_login_duration_seconds` | > 1,0 s sostenido (NFR3.1) |
| Intentos bloqueados | `veridicus_auth_login_total{outcome="throttled"}` | > 20 en 15 min: posible ataque o bloqueo inducido (T11) |
| Errores del sistema | `veridicus_problem_responses_total` | > 0 en una corrida de `scripts/smoke.sh` |
| Registro de acceso | `veridicus_access_log_failures_total` | > 0 tras cablear U13 |

Sin alertas que despierten a alguien (`project.md`: sin Alertmanager); el panel de Grafana es SHOULD de
U2.

## 4. Trazas

Sin trazas distribuidas en el MVP: U3 no llama a otros servicios. El `request_id` en el log, en la
cabecera y en el `instance` del Problem Details basta para correlacionar un error de la consola con su
línea de log.
