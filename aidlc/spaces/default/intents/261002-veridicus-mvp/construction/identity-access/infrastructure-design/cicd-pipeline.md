# Pipeline de CI/CD — U3 identity-access

**Revisión 2 (2026-11-23), segunda pasada por el cambio 01, la adenda 02 y el NFR Design revisión 2 de
U3.** Sustituye a la revisión 1 del 2026-10-03.
- **Se mantienen:** el *workflow* `session-api.yml` con sus siete *jobs*, datos de prueba sintéticos,
  promoción por digest y reversión con `git revert` de U2.
- **Cambian:** `lint-imports` ya no lleva la regla del umbral (NFR11.2 Retirado); la prueba común de
  auditoría tiene su marca; el `create-admin` vive en `deploy/jobs/`; el primer despliegue borra el Secret
  del primer `admin` (cierra R-04).
- **Nuevos:** las puertas de los manifiestos y de las reglas de U3 con su comando y su umbral (§1.1,
  cierra R-02), el *runner* fijado y el criterio ante una falla inestable (cierra R-08).

**Insumos.** Comandos de verificación, dependencias y D1–D17 de
`nfr-requirements/tech-stack-decisions.md` (revisión 2); pruebas de `nfr-design/performance-design.md`
(performance-design §4), `nfr-design/reliability-design.md` (reliability-design §6),
`nfr-design/scalability-design.md` (scalability-design §1 y §2), `nfr-design/security-design.md`
(security-design §3, §9 y §10) y `nfr-design/observability-design.md` (observability-design §1 y §2);
componentes de `nfr-design/logical-components.md` (logical-components); F7, F8 y F13 de
`functional-design/functional-spec.md` (functional-spec); C1, C12, C16 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); procesos de
`inception/domain-design/components.md` (components); políticas, `deploy-level0` y comprobaciones del NFR
Design de U2 (§2, §3.3, §5, §8, §9, §11); `infrastructure-specification.md` y `monitoring-design.md` de
esta carpeta; `## Testing Posture`, `## Way of Working`, `## Code Style` y `## Deployment` de `team.md`.

U3 crea el *workflow* de `session-api`, que después usan U4–U9, U12 y U13 sin cambiar sus puertas. La CI
no despliega: no tiene `kubeconfig`, declara `permissions: contents: read` por defecto y fija las
acciones por SHA. La promoción al clúster, el despliegue y la reversión son los de U2.

## 1. *Workflow* `session-api.yml`

Se dispara con todo PR que toca `services/session-api/**`, `libs/**`, `contracts/**`, `db/**` o el propio
*workflow*, y con cada *push* a `main` sobre esas rutas. Corre en el *runner* estándar de GitHub para
repositorios públicos, `ubuntu-24.04` (4 vCPU), fijado por nombre en el *workflow* (IDS-U3-09).

| # | *Job* | Pasos | Bloquea | Requisitos |
|---|---|---|---|---|
| 1 | `lint` | `uv sync --frozen`; `ruff check` (reglas `S`) y `ruff format --check`; `mypy --strict`; `lint-imports` (capas y fronteras) | Sí | `team.md`, NFR13.1 |
| 2 | `test-level0` | `uv run --directory services/session-api pytest -m "not integration and not perf"` con `--cov`; incluye contratos con C1 y C25, el arranque que falla ante cada caso de security-design §3.1, la matriz de permisos, `config_write`, la prueba AST de escritura de configuración, la regla estática de contraseñas en `db/migrations/`, el `DOMAIN` frente a `actor-systems.v1.yaml` y las etiquetas de enum de las métricas | Sí | NFR10.2, NFR10.9, NFR10.16, NFR10.19, NFR10.20, NFR11.3, NFR11.4, NFR15.1 |
| 3 | `test-level1` | Contenedores de servicio PostgreSQL 16 y Redis por digest (los de U2, PostgreSQL sin `pgvector`); `alembic upgrade head` con un usuario dueño y pruebas con `veridicus_app`; `pytest -m integration` y `pytest -m audit_convention` | Sí | NFR8.2, NFR8.3, NFR10.3, NFR10.5, NFR10.7, NFR10.12–NFR10.15, NFR10.17, NFR10.21, NFR11.1, NFR11.3, NFR11.5 |
| 4 | `test-perf` | `uv run --directory services/session-api pytest -m perf` en el entorno del paso 3; una sola corrida, sin reintentos | Sí | NFR3.1–NFR3.4, NFR8.1, NFR8.4 |
| 5 | `coverage` | Une la cobertura de 2 y 3; `--cov-fail-under=80` sobre `services/session-api` | Sí | NFR13.1, `team.md` |
| 6 | `audit` | `pip-audit` sobre `uv.lock` (bloquea `HIGH`+ con corrección); `gitleaks detect` | Sí | NFR10.19 |
| 7 | `build` | `hadolint`; imagen en varias etapas; Trivy (bloquea `HIGH`/`CRITICAL` con corrección); comprueba que corre sin root. En PR no publica; en `main` publica en GHCR con la etiqueta del SHA y escribe el digest en el resumen. Único *job* con `packages: write`, y solo en `main` | Sí | NFR10.1 de U2 |

- **Rendimiento en un *runner* compartido (cierra R-08).** Las pruebas de cola y de NFR8.4 usan un
  verificador falso de tiempo fijo, así que no dependen de la CPU; solo NFR3.1 y la memoria de NFR8.1 usan
  Argon2id real. Si `test-perf` falla y la causa parece la variación del *runner*, la prueba se pone en
  cuarentena con un *issue* enlazado y se arregla; nunca se reintenta ni se baja el umbral (`team.md`).
- La prueba común de la convención de auditoría (F8) corre en `test-level1` y la heredan las demás
  unidades de `session-api` porque comparten el *workflow*.

### 1.1 Puertas de los manifiestos y las reglas de U3 (cierra R-02)

Los manifiestos de U3 (subchart `session-api`, `deploy/jobs/create-admin.yaml`, la `NetworkPolicy` de
`session-api`, el `ServiceMonitor`, las reglas y el panel) los valida el *workflow* `deploy-level0` de U2,
que se dispara con `deploy/**` y `charts/**`, sin red ni `kubeconfig`. U3 aporta sus casos; cada línea
tiene su umbral:

| Comando | Qué valida de U3 | Umbral |
|---|---|---|
| `helm lint deploy/veridicus` y `yamllint deploy/` | Subchart `session-api` | 0 errores |
| `helm template` del chart con el archivo de valores de U2 y de `deploy/jobs` → `kubeconform -strict` con `deploy/schemas` | `Deployment`, `Service`, `ConfigMap`, `ServiceMonitor` y el `Job` `veridicus-create-admin` | 0 recursos inválidos |
| `kyverno apply deploy/policies` sobre ese render y `kyverno test deploy/policies/tests` | *Helper* de seguridad con `readOnlyRootFilesystem`, sin token, `requests`/`limits`, sondas, digest, consumidores de Secrets (IDS-U3-04), `job-shape` (`backoffLimit: 0`) | 0 violaciones; cada control negativo falla como se espera |
| `scripts/check-network-deps.sh deploy/network-deps.yaml <render>` | Filas de `session-api` y de `create-admin-job` (§3 de la especificación) | Código 0 |
| `scripts/check-ingress-limits.sh deploy/ingress-limits.yaml contracts/limits.v1.yaml <render>` | Ruta `/api/` con las tres anotaciones sin disco | Código 0 |
| `scripts/check-no-cluster-apply.sh` | Que ningún *workflow* ni *script* aplique `create-admin` ni migraciones (AUTONOMIA-01) | 0 apariciones |
| `promtool check rules` y `promtool test rules charts/monitoring-rules/tests/session-api-auth.test.yaml` | Las siete reglas de `monitoring-design.md` §2 | Todas las pruebas pasan; cada regla tiene un caso que dispara y otro que no |

## 2. Datos de prueba

Usuarios, contraseñas y tokens de las pruebas salen del catálogo sintético de U1
(`contracts/fixtures/synthetic-names.yaml`) y se declaran en `mentions` (NFR12.1). La clave HMAC de las
pruebas se genera en cada corrida; ningún secreto vive en el *workflow* ni en el repositorio.

## 3. Del PR al clúster

| Paso | Qué pasa | Dónde está el detalle |
|---|---|---|
| 1 | PR de código con `session-api.yml` en verde; revisa y fusiona el autor (squash) | `team.md` |
| 2 | En `main`, `build` publica la imagen y su digest | §1, paso 7 |
| 3 | Si hay cambio de esquema, su PR de migración entra **antes** que el código que lo usa (*expand–contract*) | `project.md`; flujo de U2 |
| 4 | PR de despliegue con el digest nuevo en los valores; `deploy-level0` en verde (§1.1) | Flujo de U2 |
| 5 | El humano aplica lo fusionado (antes del módulo 8) o Argo CD sincroniza; `RollingUpdate` sin indisponibilidad | U2; `infrastructure-specification.md` §1 |
| 6 | `scripts/smoke.sh https://veridicus.local`: `/healthz` y `/readyz` de `session-api` responden `200` (IDS-U3-06), la prueba E2E inicia sesión sin `outcome="error"` y `veridicus_problem_responses_total` no sube | `monitoring-design.md` §3 |

### 3.1 Primer despliegue de U3

Cada paso que toca el clúster lo ejecuta el humano **después** de fusionar el PR que lo trae, que es la
aprobación registrada (AUTONOMIA-01); ningún *script* lo hace.

1. PR de U2 con el `Cluster` y la entrada de `veridicus_app` en `managed.roles` (IDS-U3-05); el humano
   crea `veridicus-db-app`, `veridicus-redis-auth` y `veridicus-auth` con `create-secrets.sh`.
   Verificación: `kubectl get cluster veridicus-pg -n veridicus` en `Cluster in healthy state`.
2. PR de migraciones de U3 (tablas, índices, `DOMAIN`, `veridicus_apply_audit_grants()` y `DELETE` sobre
   `web_session`). Verificación: el `Job` de migraciones termina con código 0.
3. PR del código de `session-api` y su PR de despliegue. Verificación: el pod queda listo.
4. El humano crea `veridicus-bootstrap-admin` y aplica `deploy/jobs/create-admin.yaml` (F7).
   Verificación: `kubectl logs job/veridicus-create-admin -n veridicus` muestra `bootstrap.admin_created`
   y el `Job` termina con código 0.
5. El humano borra el Secret `veridicus-bootstrap-admin` y quita sus dos líneas del `.env` (cierra R-04).
   Verificación: `kubectl get secret veridicus-bootstrap-admin -n veridicus` responde `NotFound`.
6. `scripts/smoke.sh` termina con código 0.

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` falla tras desplegar `session-api` | `git revert` del PR de despliegue y nueva aplicación o sincronización (U2) |
| Una migración de U3 | Solo avanza: se corrige con una migración nueva; el código anterior funciona con el esquema expandido |
| `create-admin` falla | `backoffLimit: 0`: no reintenta. Se revisa el log, se corrige el Secret o la imagen y el humano lo vuelve a aplicar; si ya existe un `admin`, sale con código 2 sin cambiar nada (NFR10.14) |
| Redis cae | Nada que revertir: la consola queda sin servicio y vuelve sola cuando Redis responde (reliability-design §2) |
| Se filtró la clave HMAC | Se rota en el `.env`, el humano regenera `veridicus-auth` con `create-secrets.sh` y reinicia `session-api`; los contadores del limitador vuelven a cero |
| Se filtró la contraseña de `veridicus_app` | El humano regenera `veridicus-db-app`; CloudNativePG cambia la contraseña del rol y el humano reinicia `session-api` |

## 5. Puertas y su evidencia en el PR

| Puerta | Evidencia adjunta al PR |
|---|---|
| Nivel 0, nivel 1, rendimiento y cobertura | Resumen del *workflow* `session-api.yml` |
| Manifiestos y reglas | Resumen de `deploy-level0` con las líneas de §1.1 |
| Imagen | Informe de Trivy y digest publicado (en `main`) |
| Despliegue | Salida de `scripts/smoke.sh` y, en el primer despliegue, el log de `veridicus-create-admin` y el `NotFound` del Secret borrado |
