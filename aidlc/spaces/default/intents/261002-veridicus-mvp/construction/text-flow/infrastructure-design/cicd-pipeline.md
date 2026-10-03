# Pipeline de CI/CD — U4 text-flow

**Insumos.** Comandos de verificación, ajustes y dependencias de `nfr-requirements/tech-stack-decisions.md`;
dobles de prueba, cobertura y textos de `nfr-design/logical-components.md` (logical-components §5);
medición del *prompt* de `nfr-design/performance-design.md` (performance-design §2); pruebas de
`nfr-design/reliability-design.md` (reliability-design), `nfr-design/scalability-design.md`
(scalability-design) y `nfr-design/security-design.md` (security-design §4 y §6); métricas de
`nfr-design/observability-design.md` (observability-design §2); flujos de
`functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C2–C9 y C13 de
`inception/contract-design/contract-summary.md` (contract-summary); flujo común de U2 y *workflow* de
`session-api` de U3 (sus `cicd-pipeline.md`); `infrastructure-specification.md` de esta carpeta;
`## Testing Posture` de `team.md` (niveles 0–3, Golden Dataset, guardias primero).

## 1. *Workflows*

Todos con `permissions: contents: read`, acciones fijadas por SHA y sin `kubeconfig`; el *job* `build`
de cada imagen es el único con `packages: write`, y solo en `main`.

| *Workflow* | Se dispara con | *Jobs* (en orden) | Bloquea |
|---|---|---|---|
| `session-api.yml` (de U3) | `services/session-api/**`, `libs/**`, `contracts/**` | Los de U3; U4 añade sus pruebas de rutas, ingesta, indexador y plazos al nivel 0 y 1, la validación de C7 al ingerir en la cobertura de ramas, y el trabajador a la misma imagen | Sí |
| `semantic-agent.yml` (nuevo) | `services/semantic-agent/**`, `libs/**`, `contracts/**`, `deploy/veridicus/charts/semantic-agent/files/**` | `lint` (`ruff`, `mypy --strict`, `lint-imports`) → `test-level0` (guardias, validación, armado de alerta, aislamiento del *prompt* con la cadena de inyección, tope de 1 000 *tokens* de las instrucciones, SHA-256 del *prompt* igual al de los *values*, etiquetas de métricas) → `guards` (`pytest --cov-branch --cov-config=.coveragerc-guards`, 100 % de ramas) → `test-level1` (PostgreSQL 16 con `pgvector` y Redis 7.2 reales, *fakes* de juez, *embeddings* y tokenizador: colas, reclamo, idempotencia, centinela fuera de logs y colas) → `coverage` (≥ 80 % de líneas) → `audit` (`pip-audit`, `gitleaks`) → `build` (Trivy, sin root, publica en `main`) | Sí |
| `libs.yml` (nuevo) | `libs/**` | `model_gateway` e `integrity_policy`: `ruff`, `mypy --strict`, pruebas, ≥ 80 % de líneas y 100 % de ramas en `scanner.py` | Sí |
| `frontend.yml` | `frontend/**` | `npm ci` → ESLint (`react/no-danger` como error) y Prettier → `tsc --noEmit` estricto → Vitest + React Testing Library + `vitest-axe`, literal visible fuera del catálogo de U1 = fallo, ≥ 80 % de líneas → `npm audit` (`HIGH`+ con corrección) → `build` de la imagen con Trivy | Sí |
| `ai-eval-gate.yml` (nuevo) | PR que toca rutas de IA: el *prompt*, `libs/model_gateway/**`, la recuperación y la guardia de `semantic-agent`, C6/C7, `VERIDICUS_SIMILARITY_THRESHOLD` en los *values*, `deploy/models.lock` | `scripts/check-eval-report.py`: exige un reporte de nivel 2 en el PR cuyo `prompt_sha256`, umbral, digest del modelo y versión del dataset coinciden con los del PR, y cuyas métricas cumplen los umbrales de team.md (100 % de trazabilidad factual, 0 % de error de formato, consistencia > 65 %, Hecho No Documentado con 0 alertas, 0 preguntas y 1 paquete) | Sí (nivel 2) |

Ninguna prueba de los niveles 0 y 1 descarga un modelo ni pide GPU (NFR2.1); ninguna se reintenta.

## 2. Nivel 2 y nivel 3 fuera de la CI

| Nivel | Dónde y cómo | Evidencia |
|---|---|---|
| 2 — Golden Dataset | `scripts/eval-level2.sh` en la máquina de desarrollo (CPU) o en la de demostración (perfil GPU), contra el juez y los *embeddings* del clúster (`infrastructure-specification.md` §5); temperatura 0 y semilla fija; incluye paridad de *embeddings* (D16), barrido del umbral, permutación y Escenarios A, B y C | Reporte JSON adjunto al PR; lo comprueba `ai-eval-gate.yml` |
| 3 — E2E y humo | `scripts/smoke.sh https://veridicus.local` tras cada despliegue: `/readyz` completo de cada servicio y `frontend/e2e/smoke.spec.ts` (alerta con sus 4 campos en ≤ 120 s, NFR3.10, y Hecho No Documentado con paquete y sin alerta); más la suite Playwright con escaneo `axe` y de vocabulario prohibido antes de etiquetar una entrega | Salida de `smoke.sh` y reporte de Playwright en el PR de despliegue o de la entrega |

## 3. Del PR al clúster

| Paso | Qué pasa |
|---|---|
| 1 | PR de migraciones de U4 (esquema `truthframe`, tablas del flujo, permisos de solo inserción, rol `veridicus_indexer`), antes que el código que las usa |
| 2 | PR de código con sus *workflows* en verde y, si toca IA, con el reporte de nivel 2 |
| 3 | En `main`, `build` publica `session-api`, `semantic-agent` y `frontend` por SHA |
| 4 | PR de despliegue con los digests nuevos y, si cambió, el `ConfigMap` del *prompt* con su SHA-256; `deploy-level0.yml` de U2 valida el render |
| 5 | Aplicación manual (antes del módulo 8) o Argo CD; `RollingUpdate` sin indisponibilidad |
| 6 | `scripts/smoke.sh`; si falla, `git revert` del PR de despliegue (U2 cicd-pipeline §6) |

Un cambio de umbral es un PR que solo cambia `VERIDICUS_SIMILARITY_THRESHOLD` en los *values* con el
reporte del barrido (NFR4.1, NFR11.3); un cambio de modelo cambia `deploy/models.lock` con su reporte de
nivel 2. Los dos pasan por `ai-eval-gate.yml`.

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la suite E2E tras desplegar | `git revert` del PR de despliegue y nueva aplicación o sincronización |
| Un *prompt*, umbral o modelo nuevo da peores métricas | `git revert` de su PR (el reporte anterior sigue siendo válido para la versión anterior) |
| Una migración | Solo avanza; corrección con una migración nueva (*expand–contract*) |
| Turnos atascados tras un fallo | Los plazos los pasan a `error` en ≤ 15 s tras vencer; el analista los reintenta desde la consola (C2/C3) |
