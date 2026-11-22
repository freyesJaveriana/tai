# Componentes lógicos — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y NFR Requirements revisión 2
de U3.** Sustituye a la revisión 1 del 2026-10-03. Entran `GuardedRoute`, `RouteSecurityRegistry`,
`OwnerResolverRegistry`, `RequestValidator`, `ProblemDetailsHandler`, `AccessLogRecorder`, los puertos
por defecto y la convención de auditoría; `AuthorizeDependency` queda **Retirado** (lo sustituye
`GuardedRoute`). El radio de impacto de Redis se corrige (cierra R-01).

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad, revisión 2; `functional-design/functional-spec.md`
(functional-spec); C1, C12, C16, C23 y C25 de `inception/contract-design/contract-summary.md`
(contract-summary); los demás documentos de diseño de esta carpeta.

## 1. Inventario

| Componente lógico | Capa en `services/session-api/` | Responsabilidad | Patrones de NFR que aplica |
|---|---|---|---|
| `AuthorizeDependency` | — | **Retirado** | — |
| `GuardedRoute` | `api/` | F2 completo: sesión, CSRF, bloqueo, actividad, rol, dueño, validación, registro, `COMMIT` | Niega por defecto, falla cerrada, transacción única |
| `RouteSecurityRegistry` | `api/` | `RouteSecurity` por `operationId` desde C1 al arrancar | Arranque fallido ante declaración mala (BR4.7) |
| `OwnerResolverRegistry` | `api/` | Resolvedores del dueño que registra cada unidad | Sin resolvedor en operación implementada → no arranca |
| `RequestValidator` | `api/` | Validadores `jsonschema` compilados por operación; lectura JSON con tope | Validación después del rol; sin disco |
| `ProblemDetailsHandler` | `api/` | F10: `code`, estado del catálogo, `detail` en español, reversión | Sin datos sensibles |
| `AccessLogRecorder` | `api/` | F11 en punto de guardado; `record_access_strict` para U7 | Plazo de 500 ms, degradación aceptada |
| `AuthRoutes`, `UserRoutes` | `api/` | `/auth/*` y `/users*` de C1 | `Cache-Control: no-store` |
| `IdentityAccess` (implementa `Authenticator` de C12) | `application/` | F1, F3–F7, F12 | Dos transacciones en el inicio de sesión; bloqueos de §5.4 |
| `PasswordPolicy`, `UserRules`, `PermissionMatrix` | `domain/` | BR1–BR4 puros | Sin E/S |
| `PasswordVerifier` | `adapters/` | Argon2id con semáforo y señuelo | *Bulkhead* de 2 con espera de 5 s |
| `LoginThrottle` | `adapters/` | Scripts Lua `reserve`, `succeed`, `release` | *Timeout* 0,5 s, falla cerrada |
| `UserRepository`, `WebSessionRepository`, `UserChangeRepository`, `UserDirectory` | `adapters/` | PostgreSQL con SQLAlchemy | `statement_timeout`, *pool* acotado |
| `PendingSessionsDefault`, `AccessLogDefault` | `adapters/` | Puertos por defecto (0 sesiones; no registra) | Avisan en `/readyz` y en el log |
| `SessionSweeper` | `application/` | Barrido de `WebSession` por lotes | Idempotente con varias réplicas |
| `CreateAdminCommand` | `cli/` | F7 desde un `Job` | Bloqueo asesor, sin imprimir secretos |
| `HealthRoutes` | `api/` | `/healthz`, `/readyz` (C16) | Comprueba base y Redis, informa puertos |
| `RequestContext`, `JsonLogFormatter`, `AuthMetrics` | `api/` y `libs/` | `request_id`, logs con lista blanca, métricas en 8081 | Etiquetas de enum |
| Convención de auditoría | `db/migrations/`, `db/audit/actor-systems.v1.yaml`, `tests/audit_convention/` | Marca, `DOMAIN` de `ActorSystem`, `veridicus_apply_audit_grants()`, prueba común | Permisos derivados de la marca |

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue funcionando | Radio |
|---|---|---|---|
| PostgreSQL | Toda `session-api` | Nada de la consola | Todo el sistema |
| Redis | Inicio de sesión al instante; tras el umbral de la sonda, **toda** `session-api` sale del Service (NFR10.13, 1 réplica) | `/healthz`; el pod no se reinicia | Toda la consola hasta que Redis vuelva (cierra R-01) |
| Cola del semáforo | Inicios de sesión en exceso durante 5 s | Rutas autenticadas | Picos de inicio de sesión |
| Adaptador de `AccessLog` | El registro de lecturas | Las lecturas y sus escrituras | Solo el registro (riesgo aceptado de NFR) |
| Declaración mala en C1 o configuración inválida | El arranque | La réplica anterior, si la hay | El despliegue nuevo |
| Proceso de `session-api` | Toda la API | — | Todo el sistema hasta que el pod reinicie |

## 3. Recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| Proceso `session-api` | U4–U9, U12, U13 | Capas e import-linter; el semáforo solo envuelve Argon2id; `GuardedRoute` es la única entrada de `/api/v1` |
| Base PostgreSQL | Las unidades de `session-api` y los `Job` de migraciones y retención | Tres usuarios (`veridicus_owner`, `veridicus_app`, `veridicus_retention`) con permisos derivados de la marca |
| Redis | Colas de U4, U6, U9 y la clave de cancelación de U13 | Prefijo `veridicus:auth:` y claves que caducan solas |
| C1 y C25 de U1 | Todos los servicios | Solo lectura desde el paquete `veridicus-contracts` instalado |
| Lista `ActorSystem` | Todas las unidades con historial | `DOMAIN` único; cambia por PR con el YAML |

## 4. Entrega a Infrastructure Design

| Tema | Qué necesita U3 | Origen |
|---|---|---|
| Memoria | `limits.memory` de `session-api` con ≥ 160 MiB sobre la base del proceso para Argon2id | NFR8.1 |
| Puertos | `http` 8080 (API, `/healthz`, `/readyz`) y `metrics` 8081 (solo Prometheus) | NFR10.23 |
| Sondas | `liveness` en `/healthz`; `readiness` en `/readyz`, sabiendo que con Redis caído toda la consola sale del Service | NFR10.13 |
| Ingress | Solo HTTPS (BR1.8); ruta `/api/` sin escribir en disco ni el cuerpo de la petición ni el de la respuesta, y `proxy-body-size` por encima del mayor tope de C25 de cada ruta para que el `413` lo dé `session-api` | NFR10.22, NFR-U6-06, NFR-U7-07, NFR-U12-05 |
| Secrets | `VERIDICUS_RATE_LIMIT_HMAC_KEY` (≥ 32 bytes), datos del primer `admin` (solo `create-admin`), `veridicus-db-app` | NFR10.5, NFR10.8, NFR-U2-08 |
| Proxy de confianza | `VERIDICUS_TRUSTED_PROXY` = pod CIDR, nunca vacío | NFR10.5, `project.md` |
| Usuarios de base | `managed.roles` de CloudNativePG con `passwordSecret` para los tres usuarios | D16, NFR10.19 |
| `create-admin` | `Job` en `deploy/jobs/`, fuera de Argo CD, `backoffLimit: 0`, `ttlSecondsAfterFinished: 3600`, sin root | NFR10.8, NFR-U2-09 |
| Sistema de archivos | `readOnlyRootFilesystem` en `session-api`: la configuración no se puede escribir en ejecución | NFR11.4 |
