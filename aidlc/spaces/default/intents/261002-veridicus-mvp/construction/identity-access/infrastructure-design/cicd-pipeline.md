# Pipeline de CI/CD — U3 identity-access

**Insumos.** Comandos de verificación, dependencias y D1–D12 de
`nfr-requirements/tech-stack-decisions.md`; pruebas de `nfr-design/performance-design.md`
(performance-design §4), `nfr-design/reliability-design.md` (reliability-design §5),
`nfr-design/scalability-design.md` (scalability-design §1), `nfr-design/security-design.md`
(security-design §6–§8) y `nfr-design/observability-design.md` (observability-design §2); componentes
de `nfr-design/logical-components.md` (logical-components); F7 y F8 de
`functional-design/functional-spec.md` (functional-spec); C1, C12 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); procesos de
`inception/domain-design/components.md` (components); flujo común de promoción y despliegue de
`platform/infrastructure-design/cicd-pipeline.md`; `infrastructure-specification.md` de esta carpeta;
`## Testing Posture`, `## Way of Working` y `## Code Style` de `team.md`.

U3 crea el *workflow* de `session-api`, que después usan U4–U7 sin cambiar sus puertas. La promoción
de la imagen al clúster, el despliegue y la reversión son los de U2.

## 1. *Workflow* `session-api.yml`

Se dispara con todo PR que toca `services/session-api/**`, `libs/**`, `contracts/**` o el propio
*workflow*, y con cada *push* a `main` sobre esas rutas. `permissions: contents: read` por defecto;
acciones fijadas por SHA; sin `kubeconfig`.

| # | *Job* | Pasos | Bloquea | Requisitos |
|---|---|---|---|---|
| 1 | `lint` | `uv sync --frozen`; `ruff check` (reglas `S` incluidas) y `ruff format --check`; `mypy --strict`; `lint-imports` (capas y fronteras, regla del umbral de NFR11.2) | Sí | team.md, NFR11.2 |
| 2 | `test-level0` | `pytest -m "not integration and not perf"` con `--cov`; incluye contratos con C1, la prueba de etiquetas de métricas de enum cerrado, el arranque que falla con rutas sin roles o duraciones distintas del catálogo, y el validador de la política de contraseñas | Sí | NFR10.2, NFR10.9, NFR15.1 |
| 3 | `test-level1` | Contenedores de servicio PostgreSQL 16 con `pgvector` y Redis 7.2 por digest (los mismos de U2); `alembic upgrade head` con un rol dueño y pruebas con el rol de la aplicación; `pytest -m integration` | Sí | NFR8.2, NFR10.3, NFR10.5, NFR10.7, NFR10.12–NFR10.15, NFR11.1 |
| 4 | `test-perf` | `pytest -m perf` en el mismo entorno del paso 3; una sola corrida, sin reintentos | Sí | NFR3.1–NFR3.3 |
| 5 | `coverage` | Une la cobertura de 2 y 3; `--cov-fail-under=80` sobre `services/session-api` | Sí | team.md |
| 6 | `audit` | `pip-audit` sobre `uv.lock` (bloquea `HIGH`+ con corrección); `gitleaks` | Sí | NFR10.7 |
| 7 | `build` | Construye la imagen en varias etapas (`hadolint` antes), la escanea con Trivy (bloquea `HIGH`/`CRITICAL` con corrección) y comprueba que corre sin root. En PR no publica; en `main` publica en GHCR con la etiqueta del SHA y escribe el digest en el resumen. Único *job* con `packages: write`, y solo en `main` | Sí | NFR10.1 de U2 |

La prueba común de la convención de auditoría (F8, US8.4) corre en `test-level1` y la heredan las
demás unidades de `session-api` porque comparten el *workflow*.

## 2. Datos de prueba

Usuarios, contraseñas y tokens de las pruebas salen del catálogo sintético de U1 y se declaran en
`mentions` (NFR12.1). La clave HMAC de las pruebas se genera en cada corrida; ningún secreto vive en
el *workflow* ni en el repositorio.

## 3. Del PR al clúster

| Paso | Qué pasa | Dónde está el detalle |
|---|---|---|
| 1 | PR de código con `session-api.yml` en verde; revisa y fusiona el autor (squash) | team.md |
| 2 | En `main`, `build` publica la imagen y su digest | §1, paso 7 |
| 3 | Si hay cambio de esquema, su PR de migración entra **antes** que el código que lo usa (*expand–contract*) | U2 cicd-pipeline §5 |
| 4 | PR de despliegue con el digest nuevo en los valores; `deploy-level0.yml` en verde | U2 cicd-pipeline §3 |
| 5 | Aplicación manual (antes del módulo 8) o sincronización de Argo CD; `RollingUpdate` sin indisponibilidad | U2 cicd-pipeline §4; `infrastructure-specification.md` §1 |
| 6 | `scripts/smoke.sh https://veridicus.local`: `/readyz` completo de `session-api` responde `200` y el inicio de sesión de la prueba E2E no da `outcome="error"` | `monitoring-design.md` §3 |

### 3.1 Primer despliegue de U3

1. PR de migraciones de U3 (tablas, índices y permisos de solo inserción en `user_change`).
2. PR del código de `session-api` y su PR de despliegue.
3. El humano crea `veridicus-bootstrap-admin` con `create-secrets.sh` y aplica `create-admin-job` con
   `createAdmin.enabled=true` (F7). Se comprueba con `kubectl logs` que el `Job` terminó con
   `bootstrap.admin_created` y código 0.
4. `scripts/smoke.sh` en verde.

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` falla tras desplegar `session-api` | `git revert` del PR de despliegue y nueva aplicación o sincronización (U2) |
| Una migración de U3 | Solo avanza: se corrige con una migración nueva; el código anterior funciona con el esquema expandido |
| `create-admin-job` falla | `backoffLimit: 0`: no reintenta. Se revisa el log, se corrige el Secret o la imagen y se vuelve a aplicar; si ya existe un `admin`, sale con código 2 sin cambiar nada (NFR10.14) |
| Se filtró la clave HMAC o la contraseña del primer `admin` | Se rota en el `.env`, se regeneran los Secrets con `create-secrets.sh` y se reinicia `session-api` (los contadores del limitador vuelven a cero) |

## 5. Puertas y su evidencia en el PR

| Puerta | Evidencia adjunta al PR |
|---|---|
| Nivel 0, nivel 1, rendimiento y cobertura | Resumen del *workflow* `session-api.yml` |
| Imagen | Informe de Trivy y digest publicado (en `main`) |
| Despliegue | Salida de `scripts/smoke.sh` y, en el primer despliegue, el log de `create-admin-job` |
