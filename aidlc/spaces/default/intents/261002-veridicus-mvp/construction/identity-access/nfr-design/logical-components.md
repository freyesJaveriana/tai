# Componentes lógicos — U3 identity-access

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; `functional-design/functional-spec.md` (functional-spec);
C1, C12, C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); los demás
documentos de diseño de esta carpeta.

## 1. Inventario

| Componente lógico | Capa en `services/session-api/` | Responsabilidad | Patrones de NFR que aplica |
|---|---|---|---|
| `AuthorizeDependency` | `api/` | F2: sesión, CSRF, rol y dueño; mapa de rutas generado desde C1 | Niega por defecto, falla cerrada |
| `AuthRoutes`, `UserRoutes` | `api/` | `/auth/*`, `/users*` de C1 | `Cache-Control: no-store` |
| `IdentityAccess` (implementa `Authenticator` de C12) | `application/` | Casos de uso F1, F3–F7 | Transacciones cortas, bloqueo del último `admin` |
| `PasswordPolicy`, `UserRules` | `domain/` | Reglas puras BR1–BR3 | Sin E/S |
| `PasswordVerifier` | `adapters/` | Argon2id con semáforo y señuelo | *Bulkhead* de 2 con espera de 5 s |
| `LoginThrottle` | `adapters/` | Contadores HMAC en Redis | *Timeout* 0,5 s, falla cerrada |
| `UserRepository`, `WebSessionRepository`, `UserChangeRepository` | `adapters/` | PostgreSQL con SQLAlchemy | `statement_timeout` 2 s, pool acotado |
| `SessionSweeper` | `application/` | Barrido diario con *advisory lock* | Idempotente con varias réplicas |
| `CreateAdminCommand` | `cli/` | F7 desde un `Job` | Idempotente, sin imprimir secretos |
| `HealthRoutes` | `api/` | `/healthz`, `/readyz` (C16) | Comprueba base y Redis |
| `AuthMetrics`, `RequestLogging` | `api/` y `libs/` | Métricas y logs con lista blanca | Etiquetas de enum |

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue funcionando | Radio |
|---|---|---|---|
| PostgreSQL | Todo lo autenticado de `session-api` | Nada de la consola | Todo el sistema (la base es compartida) |
| Redis | Inicio de sesión (falla cerrada) | Sesiones ya abiertas | Usuarios que intentan entrar |
| Cola del semáforo | Inicios de sesión en exceso por 5 s | Rutas autenticadas | Picos de inicio de sesión |
| Proceso de `session-api` | Toda la API | — | Todo el sistema hasta que el pod reinicie |

## 3. Recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| Proceso `session-api` | U4–U7 | Capas y import-linter; el semáforo solo envuelve Argon2id |
| Base PostgreSQL | Todas las unidades de `session-api` y `semantic-agent` (solo lectura) | Tablas propias de U3; permisos de solo inserción en `user_change` |
| Redis | Colas de U4, U8, U9 | Prefijo `veridicus:auth:` y claves que caducan solas |
| Catálogo de límites de U1 | Todos los servicios | Solo lectura desde el paquete `contracts` |

## 4. Entrega a Infrastructure Design

- Memoria de `session-api`: reservar ≥ 160 MiB para Argon2id además de la base del proceso (NFR8.1).
- `session-api` necesita `VERIDICUS_RATE_LIMIT_HMAC_KEY` y los datos del primer `admin` desde Secrets.
- `VERIDICUS_TRUSTED_PROXY` = la dirección o red del *ingress* que fije Infrastructure Design.
- Prometheus debe alcanzar `/metrics` por un puerto interno distinto del de la API.
