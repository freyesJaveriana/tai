# Diseño de observabilidad — U3 identity-access

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D10) de esta unidad; flujos F1–F7 de `functional-design/functional-spec.md`
(functional-spec); C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary);
respuestas P1–P2 de `nfr-design-questions.md`; formato de fecha de U1.

## 1. Logs estructurados (NFR15.2, NFR15.3)

- Un formateador JSON único en `libs/` emite una línea por evento con: `timestamp` (forma de U1,
  `AAAA-MM-DDTHH:MM:SSZ`), `level`, `service`, `request_id`, `user_id` (si hay principal), `route`
  (plantilla, no la URL con identificadores), `method`, `status`, `code` y `duration_ms`.
- **Lista blanca**: el formateador solo emite esos campos; cualquier otro se descarta. Nunca nombre de
  usuario, contraseña, token, cookie ni cabecera `Authorization` (security-design §6).
- **`request_id`**: un *middleware* genera un UUID v4 por petición, lo pone en `X-Request-ID` de la
  respuesta y en el contexto del *logger*. Un `X-Request-ID` entrante se acepta solo si es un UUID
  válido; si no, se reemplaza.

| Evento | Nivel | `code` |
|---|---|---|
| Inicio de sesión correcto | `INFO` | — |
| `401`, `403`, `429` | `INFO` | El de la respuesta |
| Alta, desactivación, reactivación o cambio de rol | `INFO` | `user.created`, `user.deactivated`, `user.reactivated`, `user.role_changed` |
| `503` por base, Redis o cola del semáforo | `ERROR` | `system.unavailable`, con `cause`: `db`, `redis` o `argon2_queue` |
| `create-admin` | `INFO` o `ERROR` | `bootstrap.admin_created`, `bootstrap.admin_exists` |

## 2. Métricas (NFR15.1)

Expuestas por `prometheus-client` en `/metrics` (puerto interno, solo alcanzable por Prometheus según
la `NetworkPolicy` de U2):

| Métrica | Tipo | Etiquetas | Dónde se actualiza |
|---|---|---|---|
| `veridicus_auth_login_total` | counter | `outcome`: `success`, `invalid_credentials`, `throttled`, `error` | Al final de F1, un incremento por petición |
| `veridicus_auth_login_duration_seconds` | histogram (cubetas 0,1; 0,25; 0,5; 1; 2; 5 s) | — | Alrededor de F1 completo |
| `veridicus_auth_rejections_total` | counter | `code`: `auth.unauthenticated`, `auth.csrf`, `auth.forbidden`, `session.not_owner` | En la dependencia `authorize` |

Las etiquetas son valores de enum cerrados (BR8.2 de U1); una prueba de nivel 0 recorre el registro de
métricas y falla si aparece un valor fuera del enum.

## 3. Indicadores y umbrales

| Indicador | Fuente | Umbral de revisión |
|---|---|---|
| p95 del inicio de sesión | `veridicus_auth_login_duration_seconds` | > 1,0 s sostenido (NFR3.1) |
| Intentos bloqueados | `veridicus_auth_login_total{outcome="throttled"}` | > 20 en 15 min: revisión manual de un posible ataque |
| Errores del sistema | `veridicus_auth_login_total{outcome="error"}` | > 0 en una corrida de `scripts/smoke.sh` |

Sin alertas que despierten a nadie en el MVP (observability-requirements §3); el panel de Grafana es
SHOULD de U2.

## 4. Trazas

No hay trazas distribuidas en el MVP: U3 no llama a otros servicios. El `request_id` en logs y en la
respuesta basta para correlacionar una petición de la consola con su línea de log.
