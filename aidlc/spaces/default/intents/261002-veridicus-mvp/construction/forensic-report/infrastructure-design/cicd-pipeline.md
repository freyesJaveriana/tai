# Pipeline de CI/CD — U7 forensic-report

**Insumos.** Pruebas `perf` de `nfr-design/performance-design.md` (performance-design); políticas de
montaje, cabeceras y centinela de `nfr-design/security-design.md` (security-design); réplica única y
política de estrategia de `nfr-design/scalability-design.md` (scalability-design); fallos inyectados,
cancelación, barrido y `verify_store` de `nfr-design/reliability-design.md` (reliability-design); regla
del volumen de `nfr-design/observability-design.md` (observability-design); cobertura, ramas,
fronteras y glosario de `nfr-design/logical-components.md` (logical-components §5); flujos F1–F7 de
`functional-design/functional-spec.md` (functional-spec); módulo ForensicReport de
`inception/domain-design/components.md` (components); C1, C8, C11, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); comandos de verificación de
`nfr-requirements/tech-stack-decisions.md` §5; respuestas **P1 = A** (`Recreate` y política Kyverno),
**P2 = A** (respaldo conjunto y restauración que termina con `verify_store`) y **P3 = A** (cuota y
*gauges* propios) de `infrastructure-design-questions.md`; flujo común de U2
(`platform/infrastructure-design/cicd-pipeline.md`), *workflow* `session-api.yml` de U3 y *workflows* de
U4; `infrastructure-specification.md` de esta carpeta; `## Testing Posture` y `## Deployment` de
`team.md`.

U7 no crea *workflows*: añade pruebas a `session-api.yml` y `frontend.yml` y comprobaciones a
`deploy-level0.yml`. Todos siguen con `permissions: contents: read`, acciones fijadas por SHA, sin
`kubeconfig` y con `packages: write` solo en `build` sobre `main`. La CI nunca despliega, nunca crea el
`Job` de verificación y nunca toca el respaldo (AUTONOMIA-01).

## 1. Etapas de *build* y prueba

| *Workflow* | Se dispara con | Qué añade U7 | Bloquea |
|---|---|---|---|
| `session-api.yml` (U3) | `services/session-api/**`, `libs/**`, `contracts/**`, `db/migrations/**` | Nivel 0 de `tests/forensic_report` (render determinista, guardias, configuración con los siete ajustes, etiquetas de métricas, catálogo); ramas al 100 % de los módulos guardia; nivel 1 con PostgreSQL 16 real y un directorio real (permisos, CSRF, atomicidad, carreras, fallos inyectados, cancelación, barrido, cuota, `export_store`/`import_store`, `verify_store`, centinela); `perf` | Sí |
| `frontend.yml` (U4) | `frontend/**`, `contracts/**` | Vitest de diálogos, vista como texto, descarga y `retry: false`; `vitest-axe` | Sí |
| `deploy-level0.yml` (U2) | `deploy/**`, `scripts/**` | Políticas `veridicus-reports-single-writer` y `veridicus-reports-mounts` con controles negativos; cuota = tamaño del PVC; `Job` de verificación fuera de la `Application`; `promtool` de la regla del volumen; `shellcheck` de `backup-db.sh` y `check-no-cluster-apply.sh` | Sí |
| `ai-eval-gate.yml` (U4) | Rutas de IA | Sin cambios: U7 no toca *prompt*, modelo, umbral ni recuperación | — |

## 2. Puertas con comando y umbral (AUTONOMIA-02)

| Puerta | Comando | Umbral | Requisitos |
|---|---|---|---|
| Nivel 0 | `uv run --directory services/session-api pytest tests/forensic_report -m "not integration and not perf"` | Verde | NFR7.3, NFR10.9, NFR10.10, NFR10.22, NFR12.1, NFR14.1, NFR10.17 (configuración) |
| Ramas de guardias | `uv run --directory services/session-api pytest tests/forensic_report --cov-branch --cov-config=.coveragerc-guards` | 100 % de ramas | NFR13.2 |
| Nivel 1 | `uv run --directory services/session-api pytest tests/forensic_report -m integration` | Verde; tras la suite, `verify_store` con código 0 | NFR8.4, NFR8.5, NFR8.8, NFR10.1–NFR10.21, NFR11.1–NFR11.6, NFR15.1–NFR15.4 |
| Auditoría común (U3) | `uv run --directory services/session-api pytest -m integration -k audit_convention` | `report_version` registrada; `UPDATE`/`DELETE` fallan | NFR11.1 |
| Rendimiento | `uv run --directory services/session-api pytest tests/forensic_report -m perf` | p95 de NFR3.1–NFR3.8; RSS ≤ +96 MiB; una corrida sin reintentos | NFR3.1–NFR3.8, NFR7.2, NFR8.1–NFR8.3 |
| Cobertura | `pytest --cov --cov-fail-under=80` en `services/session-api`; `npm --prefix frontend run test -- --coverage` | ≥ 80 % de líneas en cada uno | NFR13.1 |
| Consola | `npm --prefix frontend run test -- src/report` y `npm --prefix frontend run typecheck` | Verde; 0 errores | NFR3.9–NFR3.11, NFR10.4, NFR10.18 |
| Tipos y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en `services/session-api` | 0 errores; control negativo que importa `httpx` falla | NFR1.1, NFR11.2, NFR13.3, NFR14.2 |
| Auditoría de dependencias | `pip-audit`, `npm audit`, `gitleaks`, Trivy | 0 `HIGH`+ con corrección; 0 secretos | team.md |
| Manifiestos | `helm template deploy/veridicus -f deploy/values-cpu.yaml` (y `values-gpu.yaml`) `\| kubeconform -strict - && kyverno apply deploy/policies/ --resource -` y `kyverno test deploy/policies/tests/` | 0 violaciones; cada control negativo (2 réplicas, `RollingUpdate`, otro pod que monta el PVC, `Job` sin `readOnly`) produce 1 violación | NFR1.2, NFR8.6, NFR10.6 |
| Cuota = PVC | `scripts/check-report-quota.sh` sobre cada render | `VERIDICUS_REPORT_VOLUME_QUOTA_BYTES` igual a `requests.storage` del PVC en bytes | NFR15.3 (P3 = A) |
| Regla del volumen | `promtool test rules deploy/prometheus/tests/volume.yaml` | Verde (75 % / 85 % 9 min sin alerta; 85 % 10 min con alerta) | NFR15.3 |
| Nivel 3 | `npx --prefix frontend playwright test e2e/report.spec.ts` | 0 fallos; 0 violaciones `serious`/`critical` de axe | NFR8.7, NFR3.10, NFR3.11 |
| Nivel 2 (fuera de la CI) | `uv run --directory evaluation python -m golden.mttv --run out/level2.json --report out/mttv.json` | Media < 600 s | NFR7.1 |

Ninguna prueba de los niveles 0 y 1 usa modelos, GPU ni red, ni se reintenta (NFR2.1).

## 3. Despliegue y orden de cambios

| Paso | Qué pasa | Aprobación |
|---|---|---|
| 1 | PR de U1: códigos nuevos, glosario (`cancel_token`, `view_outdated`) y los dos *gauges* en C15 | Fusión del PR |
| 2 | PR de la base: rol gestionado `veridicus_report_ro` en el `Cluster` de U2 y Secret referenciado (el humano crea el valor desde `.env` con el *script* de U2) | Fusión del PR |
| 3 | Antes de aplicar la migración, el humano ejecuta `scripts/backup-db.sh` (base y archivos) | Paso humano |
| 4 | PR de migración de U7 (`report_version`, índices, permisos de `veridicus_app` y `veridicus_report_ro`), solo aditiva; `migrations-job` en la onda −1 | Fusión del PR |
| 5 | PR de código de U7 con `session-api.yml` y `frontend.yml` en verde | Fusión del PR |
| 6 | En `main`, `build` publica `session-api` y `frontend` por SHA | Automático, sin clúster |
| 7 | PR de despliegue: digests, `strategy: Recreate` y gracia de 30 s, montaje y siete ajustes, PVC con `Prune=false`, políticas, regla, panel, `NetworkPolicy` y manifiesto del `Job` | Fusión con `deploy-level0.yml` en verde |
| 8 | Antes del módulo 8, el humano aplica el artefacto fusionado; después, Argo CD sincroniza. Con `Recreate`, la API vieja termina (≤ 30 s) y la nueva barre y queda lista | La fusión del paso 7 |
| 9 | `scripts/smoke.sh https://veridicus.local` y `e2e/report.spec.ts`; el corte medido debe ser ≤ 60 s | Salida adjunta al PR |

Ningún paso de un plan de tareas ejecuta `kubectl apply`, `helm upgrade`, una migración ni el `Job` sin
la fusión previa (AUTONOMIA-01).

## 4. Verificación del almacén y respaldo

| Operación | Cómo | Cuándo | Resultado esperado |
|---|---|---|---|
| `verify_store` en CI | Al final del nivel 1, contra el directorio y la base del contenedor | Cada PR | Código 0 (NFR8.8) |
| `Job` `veridicus-verify-store` | El humano: `kubectl create -f deploy/jobs/verify-store.yaml` y `kubectl logs job/<nombre>` | Tras una restauración, antes de la sustentación, ante `VeridicusReportIntegrityMismatch` | Código 0: 0 versiones sin archivo, 0 SHA-256 distintos, 0 huérfanos > 300 s |
| Respaldo conjunto | El humano: `scripts/backup-db.sh` (`pg_dump` → `export_store` → comprobación de `SHA256SUMS`) | Antes de la sustentación y de cada cambio de esquema | Código 0; `backups/veridicus-<fecha>.dump` y `backups/veridicus-reports-<fecha>.tar` con su `.sha256` |
| Restauración | Manual en `docs/operacion/instalacion.md`: `pg_restore` → `import_store` → reinicio de la API → `Job` de verificación | Pérdida del PVC o de la base, o `integrity_mismatch` | `verify_store` con código 0; RTO objetivo ≤ 30 min |

El *script* de respaldo solo lee del clúster (`kubectl exec` de `pg_dump` y `export_store`);
`check-no-cluster-apply.sh` de U2 lo comprueba en nivel 0. `import_store` sí escribe en el volumen, por
eso no está en ningún *script* ni plan: es un paso que el humano decide y ejecuta.

## 5. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la E2E tras desplegar | `git revert` del PR de despliegue y nueva aplicación o sincronización; con `Recreate` el corte se repite (≈ 20–40 s). La migración aditiva se queda: el código anterior no lee `report_version` |
| Un ajuste de U7 inválido | El proceso termina y la API no queda lista; con `Recreate` no hay pod viejo de respaldo, así que la consola queda caída hasta el `git revert` (riesgo aceptado en P1 = A; `deploy-level0.yml` valida los ajustes antes de fusionar) |
| La migración | Solo avanza; se corrige con otra migración (*expand–contract*) |
| `integrity_mismatch` o pérdida del volumen | Restauración del último respaldo (§4) y `Job` de verificación |
| La cuota se llena | PR que amplía `reports.size` (PVC y cuota a la vez); nunca se borran reportes |

## 6. Entornos y secretos

| Aspecto | Diseño |
|---|---|
| Entornos | CI (PostgreSQL 16 en contenedor por digest y un directorio temporal como volumen), máquina de desarrollo y máquina de demostración; mismas imágenes por SHA y mismos valores de U7 en ambas máquinas |
| Secretos | `veridicus_app` de U2 para la API; Secret nuevo `veridicus-db-report-ro` para el `Job`, referenciado con `secretKeyRef` y creado por el humano desde `.env`. La CI crea sus roles en cada corrida y no tiene ningún Secret del clúster |
| Datos | *Fixtures*, *golden files* y reportes de prueba sintéticos del catálogo de U1; la comprobación de marcas corre en nivel 0 (NFR12.1). Los respaldos quedan en `backups/` (ignorado por git) |
