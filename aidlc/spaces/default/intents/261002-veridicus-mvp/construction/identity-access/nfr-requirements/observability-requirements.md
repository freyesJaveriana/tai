# Requisitos de observabilidad — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design vigente
de U3.** Sustituye a la revisión 1 del 2026-10-03. Los requisitos conservan su ID; cada fila dice si **se
mantiene** o **cambia**. Ninguno entra ni se retira.

**Insumos.** Flujos F1–F6, F10, F11 y F13 de `functional-design/functional-spec.md` (functional-spec,
revisión 2) y reglas BR4.5, BR8.2 y BR9.3 de `functional-design/rules.md` (rules); NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements, revisión 3); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary).

## 1. Logs

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.2 | cambia | Logs estructurados sin datos sensibles. | JSON en una línea con `timestamp` (BR8.1 de U1), `level`, `request_id`, `user_id` (si hay principal), `route`, `status`, `code` y `demo` (`true` en rutas `x-veridicus-demo`, BR4.5); nunca nombre de usuario, contraseña, token, cookie, mensaje de excepción ni texto de testimonio (NFR10.7, BR8.2). |
| NFR15.3 | cambia | Los rechazos de seguridad y los fallos de dependencias quedan registrados. | Cada `401`, `403`, `429` y cada cambio de usuario deja una línea `INFO` con su `code`; cada fallo de `AccessLog.record`, una línea `WARNING` con `resource_type` y el ID del recurso (BR9.3); un fallo de base o Redis y cada `500`, una línea `ERROR`; el arranque con el adaptador por defecto de `AccessLog`, un `WARNING` (BR9.5). Prueba de nivel 1 que captura los logs de E1, E4, E5, E32, E36, E38 y del `429`. |

## 2. Métricas (Prometheus, en el puerto interno `/metrics` de `session-api`)

Son métricas **internas** de `session-api`: no forman parte de C15, que es el contrato de AIR de U5
(cierra R-05; NFR-U3-03). Siguen igual la regla de etiquetas de U1: solo valores de enum (BR8.2 de U1).

| ID | Estado | Métrica | Tipo | Etiquetas |
|---|---|---|---|---|
| NFR15.1 | cambia | `veridicus_auth_login_total` | counter | `outcome`: `success`, `invalid_credentials`, `throttled`, `error` |
| NFR15.1 | se mantiene | `veridicus_auth_login_duration_seconds` | histogram | ninguna |
| NFR15.1 | cambia | `veridicus_auth_rejections_total` | counter | `error_code`: `auth.unauthenticated`, `auth.csrf`, `auth.forbidden`, `session.not_owner`, `validation.invalid_request`; `demo`: `true`, `false` |
| NFR15.1 | cambia | `veridicus_access_log_failures_total` | counter | `resource_type`: `session`, `suggestion`, `report_version` (BR9.3) |
| NFR15.1 | cambia | `veridicus_problem_responses_total` | counter | `status`: `500`, `503` |

La etiqueta se llama `error_code` (antes `code`) para coincidir con la lista de U1. Prueba de nivel 1:
cada contador sube 1 en su escenario (E1, E4, E5, E31, E32, E33, E36 y el `429`).

## 3. Alertas

Sin alertas que despierten a alguien en el MVP (`project.md`: sin Alertmanager). El panel de Grafana
(SHOULD, U2) puede mostrar:
- `veridicus_auth_login_total{outcome="throttled"}`: más de 20 en 15 minutos indica un intento de
  adivinar contraseñas o un bloqueo inducido (T11), y se revisa a mano;
- `veridicus_access_log_failures_total`: cualquier valor mayor que 0 tras cablear U13 se revisa a mano.
