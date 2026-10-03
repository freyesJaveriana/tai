# Pipeline de CI/CD — U6 session-lifecycle

**Insumos.** Pruebas de tiempo de `nfr-design/performance-design.md` (performance-design); entrada
acotada, permisos y centinela de `nfr-design/security-design.md` (security-design); prueba con dos
instancias de `nfr-design/scalability-design.md` (scalability-design); pruebas de publicación y de
suspensión de `nfr-design/reliability-design.md` (reliability-design); etiquetas de métricas de
`nfr-design/observability-design.md` (observability-design); dobles, cobertura y textos de
`nfr-design/logical-components.md` (logical-components §5); flujos de
`functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C1, C2, C4 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); comandos de verificación de
`nfr-requirements/tech-stack-decisions.md`; flujo común de U2
(`platform/infrastructure-design/cicd-pipeline.md`), *workflow* `session-api.yml` de U3
(`identity-access/infrastructure-design/cicd-pipeline.md`) y *workflows* de U4
(`text-flow/infrastructure-design/cicd-pipeline.md`); `infrastructure-specification.md` de esta
carpeta; `## Testing Posture` y `## Deployment` de `team.md`.

U6 no crea *workflows*: añade pruebas a `session-api.yml` y `frontend.yml`, una comprobación a
`deploy-level0.yml` y dos pasos al arnés de nivel 2. Todos siguen con `permissions: contents: read`,
acciones fijadas por SHA, sin `kubeconfig` y con `packages: write` solo en `build` sobre `main`.

## 1. Etapas de *build* y prueba

| *Workflow* | Se dispara con | Qué añade U6 | Bloquea |
|---|---|---|---|
| `session-api.yml` (U3) | `services/session-api/**`, `libs/**`, `contracts/**` | `test-level0`: división con el archivo compartido, plazos `n₀`, catálogo de límites, OpenAPI sin rutas peligrosas, ajustes con su control positivo, `PASTE_MARKER_TTL_S > 3600`, *fixtures* sintéticos. `test-level1`: pegado todo o nada, reenvío con marca (casos a–d), dos instancias y dos revisiones, bordes de 165/179/180/210 s, permisos de solo inserción, centinela, equivalencia pegado/escrito con el *fake*. `test-perf`: NFR3.1–NFR3.5 y NFR3.9 | Sí |
| `frontend.yml` (U4) | `frontend/**`, **`contracts/fixtures/transcript-split.v1.json`**, **`contracts/limits.v1.yaml`** (precisión en `infrastructure-specification.md` §6) | Vitest de la vista previa (≤ 200 ms con 100 000 caracteres, 0 peticiones), mismos ejemplos que `pytest`, «Suspendida» con icono y texto, temporizadores falsos del progreso, literales fuera del catálogo = fallo | Sí |
| `deploy-level0.yml` (U2) | `deploy/**` | Comprueba que los tres ajustes de U6 tienen el mismo valor en los `ConfigMap` de API y trabajador con cada combinación de perfiles (`values-cpu`, `values-gpu`, `values-gpu` + `values-extras`) | Sí |
| `ai-eval-gate.yml` (U4) | Rutas de IA | Sin cambios: U6 no toca *prompt*, modelo, umbral ni recuperación | — |

## 2. Puertas con comando y umbral (AUTONOMIA-02)

| Puerta | Comando | Umbral | Requisitos |
|---|---|---|---|
| Nivel 0 | `uv run --directory services/session-api pytest -m "not integration and not perf"` | Verde | NFR3.10, NFR8.3, NFR10.6, NFR10.10, NFR12.1, NFR13.2 |
| Nivel 1 | `uv run --directory services/session-api pytest -m integration` | Verde | NFR8.2, NFR8.6, NFR8.8–NFR8.12, NFR10.1–NFR10.5, NFR10.7, NFR10.11, NFR10.12, NFR11.1, NFR11.2, NFR4.1 (*fake*), NFR15.3 |
| Rendimiento | `uv run --directory services/session-api pytest -m perf` | p95 de NFR3.1–NFR3.5 y NFR3.9; una corrida sin reintentos | NFR3.1–NFR3.5, NFR3.9, NFR8.1 |
| Cobertura | `pytest --cov --cov-fail-under=80` sobre `services/session-api`; `npm --prefix frontend run test -- --coverage` | ≥ 80 % de líneas en cada uno | NFR13.1 |
| Consola | `npm --prefix frontend run typecheck` y Vitest | 0 errores; 100 % de ejemplos de división | NFR3.6, NFR13.2, NFR14.1 |
| Tipos y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en `services/session-api` | 0 errores | team.md |
| Auditoría | `pip-audit`, `npm audit`, `gitleaks`, Trivy | 0 `HIGH`+ con corrección; 0 secretos | team.md |
| Render del chart | `helm template` → `kubeconform` → Kyverno CLI en `deploy-level0.yml` | Verde, ajustes iguales en ambos procesos | NFR10.10 |
| Nivel 3 | `npx --prefix frontend playwright test e2e/session-lifecycle.spec.ts` | 0 violaciones `serious`/`critical` de axe; 0 coincidencias de vocabulario prohibido; cambio de etapa visible ≤ 3 s | NFR3.12, NFR10.8, NFR14.2 |
| Nivel 2 (fuera de la CI) | `uv run --directory evaluation python -m golden.run --profile cpu --paste-parity --report out/level2-paste.json` | 100 % de coincidencia | NFR4.1 |
| Nivel 2 a demanda | `uv run --directory evaluation python -m golden.paste_max --turns 60 --profile cpu --report out/paste60.json` | 0 `turn.error.timeout`; versión de 1 MB `ready` < 180 s | NFR3.11, NFR9.1 |

Ninguna prueba de los niveles 0 y 1 descarga un modelo, pide GPU o se reintenta (NFR2.1). Los reportes
de nivel 2 se adjuntan al PR de la entrega etiquetada; los corre el humano con `scripts/eval-level2.sh`
de U4, que solo abre `port-forward` y no cambia el clúster.

## 3. Despliegue y orden de migraciones

| Paso | Qué pasa | Aprobación |
|---|---|---|
| 1 | PR de U1 con las claves nuevas de `contracts/limits.v1.yaml` y `transcript-split.v1.json` | Fusión del PR |
| 2 | PR de migraciones de U6 (§2.1 de `infrastructure-specification.md`), después del de U5 que crea la vista; solo aditivas | Fusión del PR |
| 3 | PR de código de U6 con `session-api.yml` y `frontend.yml` en verde | Fusión del PR |
| 4 | En `main`, `build` publica `session-api` y `frontend` por SHA | Automático, sin clúster |
| 5 | PR de despliegue: digests nuevos, tres ajustes en el bloque común de los *values*, panel de §5 de monitoring-design y las reglas de §2 | Fusión del PR |
| 6 | Antes del módulo 8, el humano aplica el artefacto fusionado (`migrations-job` en la onda −1, servicios en la 0); después, Argo CD sincroniza | La fusión del paso 5 |
| 7 | `scripts/smoke.sh https://veridicus.local` y `e2e/session-lifecycle.spec.ts` | Salida adjunta al PR |

Estrategia `RollingUpdate` (`maxSurge: 1`, `maxUnavailable: 0`) de U4: durante el cambio pueden correr
dos revisiones de suspensión y dos API; el diseño lo tolera (scalability-design §1). Ningún paso de un
plan de tareas ejecuta `kubectl apply`, `helm upgrade` ni una migración sin la fusión previa
(AUTONOMIA-01).

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la E2E tras desplegar | `git revert` del PR de despliegue y nueva aplicación o sincronización; la migración aditiva se queda (el código anterior ignora las columnas nuevas) |
| Un ajuste de U6 inválido | El pod no queda listo y el `RollingUpdate` conserva el anterior; se corrige con `git revert` del PR |
| La migración | Solo avanza; se corrige con una migración nueva (*expand–contract*) |
| NFR3.11 falla en CPU | PR que baja `transcript_max_testimony_turns` en el catálogo o usa el perfil GPU para la demostración; nunca se sube el tope de 3 600 s |

## 5. Entornos y secretos

| Aspecto | Diseño |
|---|---|
| Entornos | CI (contenedores PostgreSQL 16 con `pgvector` y Redis 7.2 por digest, iguales a U2), máquina de desarrollo y máquina de demostración; mismas imágenes por SHA y mismos valores de U6 en las dos |
| Secretos | U6 no añade ninguno: usa las contraseñas de `veridicus_app` y de Redis de U2 por `secretKeyRef`. En la CI, los roles del contenedor se crean en cada corrida y el rol dueño solo instala la variante de prueba de `veridicus_now()` |
| Datos | Transcripciones, archivo de división y versiones de escenario sintéticos del catálogo de U1; la comprobación de marcas corre en nivel 0 (NFR12.1) |
