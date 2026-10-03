# Requisitos de observabilidad — U3 identity-access

**Insumos.** Flujos F1–F6 de `functional-design/functional-spec.md` (functional-spec) y reglas de
`functional-design/rules.md` (rules); NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary).

## 1. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Logs estructurados sin datos sensibles. | JSON en una línea con `timestamp` (BR8.1 de U1), `level`, `request_id`, `user_id` (si hay principal), `route`, `status` y `code`; nunca nombre de usuario, contraseña, token ni cookie (NFR10.7). |
| NFR15.3 | Los rechazos de seguridad quedan registrados. | Cada `401`, `403`, `429` y cada cambio de usuario deja una línea `INFO` con su `code`; un fallo de base o Redis deja una línea `ERROR`. Prueba de nivel 1 que captura los logs de E1, E4, E5 y del `429`. |

## 2. Métricas (Prometheus, en `/metrics` de `session-api`)

| ID | Métrica | Tipo | Etiquetas |
|---|---|---|---|
| NFR15.1 | `veridicus_auth_login_total` | counter | `outcome`: `success`, `invalid_credentials`, `throttled`, `error` |
| NFR15.1 | `veridicus_auth_login_duration_seconds` | histogram | ninguna |
| NFR15.1 | `veridicus_auth_rejections_total` | counter | `code`: `auth.unauthenticated`, `auth.csrf`, `auth.forbidden`, `session.not_owner` |

Las etiquetas solo llevan valores de enum (BR8.2 de U1). Se añaden a C15 por un PR de U1 (precisión
en `security-requirements.md` §5).

## 3. Alertas

Sin alertas que despierten a alguien en el MVP. El panel de Grafana (SHOULD, U2) puede mostrar
`veridicus_auth_login_total{outcome="throttled"}`; más de 20 en 15 minutos indica un intento de
adivinar contraseñas y se revisa a mano.
