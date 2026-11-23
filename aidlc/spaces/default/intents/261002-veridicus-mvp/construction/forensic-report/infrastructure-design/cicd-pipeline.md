# Pipeline de CI/CD — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design revisión 2.**
Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.**
  - Las pruebas pasan a `tests/review_report`.
  - Entran la exportación, la purga, la función de bloqueo de U13 y el cursor de lo revisado.
  - Salen el `Job` de verificación, su rol y su `NetworkPolicy`; `verify_store` corre por `kubectl exec`.
  - `export_store` pasa al runbook (IDS-U7-07).
  - La comprobación de la cuota pasa a una prueba de `deploy/tests/level0/` (IDS-U7-04).
  - El corte por despliegue tiene comando y umbral (IDS-U7-11).
  - Desaparecen `values-gpu.yaml` y las dos máquinas.
- **Numeración.** §1–§6 conservan su tema. La nueva §7 es la correspondencia con AUTONOMIA.

**Insumos.**
- Pruebas `perf` de `nfr-design/performance-design.md` (performance-design).
- Políticas de montaje, cabeceras, exportación, retención y centinela de `nfr-design/security-design.md`
  (security-design).
- Réplica única y política de estrategia de `nfr-design/scalability-design.md` (scalability-design).
- Fallos inyectados, cancelación, barrido, `verify_store`, exportación y purga de
  `nfr-design/reliability-design.md` (reliability-design).
- Reglas de `nfr-design/observability-design.md` (observability-design).
- Cobertura, ramas, fronteras y glosario de `nfr-design/logical-components.md` (logical-components §5).
- Flujos F1–F10 de `functional-design/functional-spec.md` (functional-spec).
- ReviewReport de `inception/domain-design/components.md` (components).
- C1, C8, C11, C12, C16, C23, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- Comandos de `nfr-requirements/tech-stack-decisions.md` §5.
- `cicd-pipeline.md` de U2, U3, U4 y U6, e `infrastructure-specification.md` de esta carpeta.
- `## Testing Posture` y `## Deployment` de `team.md`.

U7 **no crea *workflows* ni comprobaciones obligatorias nuevas**. Añade pruebas a `session-api.yml` (U3) y a
`frontend.yml` (U4), una política y una prueba a la suite de `deploy-level0.yml` (U2) y un *script* de solo
HTTP. Todos siguen con:
- `permissions: contents: read`;
- acciones fijadas por SHA;
- sin `kubeconfig` ni claves de proveedores;
- `packages: write` solo en el *job* `build` sobre `main`.

La CI nunca despliega, nunca ejecuta `verify_store`, `export_store` ni `import_store` contra el clúster y nunca
toca el respaldo (AUTONOMIA-01).

## 1. Etapas de *build* y prueba

Ninguna prueba de los niveles 0 y 1 usa modelos, GPU ni red, ni se reintenta (NFR2.1). PostgreSQL 16 (imagen
oficial, sin `pgvector`) corre en contenedor por digest, y el volumen es un directorio real del contenedor,
nunca `tmpfs`. Las pruebas de las guardias de AUTONOMIA-03 (entrada única, quién y cuándo, cursor, escaneo,
solo inserción) y de los contratos (C1 de U7, C11, C23, C24) se escriben primero y se ven en rojo antes de
implementar (`team.md`).

| *Workflow* | Rutas que lo activan | *Job* | Qué añade U7 (comando y umbral en §2) | Bloquea |
|---|---|---|---|---|
| `session-api.yml` (U3) | `services/session-api/**`, `libs/**`, `contracts/**`, `db/**` | `lint` | `lint-imports`: `review_report.domain` sin E/S; `consolidate` solo desde la ruta; `purge` solo desde el `Job` y las pruebas; sin clientes de red, Redis, `model_gateway` ni `anonymizer`; con control negativo. `mypy --strict` y `ruff`; glosario sin `forensic_report` | Sí |
| | | `test-level0` | Render y exportación deterministas (dorados, Hypothesis, dos `PYTHONHASHSEED`); guardia y cursor; escaneo de C8 más VE-02 con exclusiones; tope de `report_max_bytes`; los siete ajustes con sus reglas de arranque; etiquetas de métricas contra su enum; catálogo de textos; almacén *fake* con el `CancelToken` | Sí |
| | | `guards` | `consolidation_guard.py`, `correction_policy.py`, `export_policy.py`, `consolidate.py`, `export.py`, `purge.py`, `orphan_sweep.py` y `volume_report_store.py` en `.coveragerc-guards`, con 100 % de ramas | Sí |
| | | `test-level1` | Permisos por ruta y actor; CSRF; atomicidad con fallo inyectado en cada paso, incluido el `COMMIT` (DS4); carreras sin `40P01`; cursor desactualizado; plazos (almacén de 6 s y de 4,5 s con la conexión real, base retenida 3 s, `AccessLog` de 600 ms); *executor* colgado; barrido; cuota y `/readyz`; exportación todo o nada; purga con `veridicus_retention` y la función de bloqueo; `export_store` con RSS ≤ 64 MiB e `import_store`; `verify_store` al final; centinela; reconstrucción por logs | Sí |
| | | `test-perf` | NFR3.1–NFR3.14 con el pico de RSS de NFR8.1, en el *runner* de IDS-U3-09 | Sí |
| | | `coverage` | ≥ 80 % de líneas en `services/session-api` con U7 incluido | Sí |
| `frontend.yml` (U4) | `frontend/**`, `contracts/**` | `test` | Vitest de diálogos, cursor congelado, vista previa sin HTML, exportación con `Blob`, `retry: false`, 0 peticiones del sondeo a la vista previa y a la exportación; `vitest-axe`; ≥ 80 % de líneas | Sí, por `frontend / gate` |
| `deploy-level0.yml` (U2) | `deploy/**`, `scripts/**`, `config/**`, `contracts/limits.v1.yaml`, `.github/**` | Pasos 6, 7, 8 y 10 | `kyverno test` de `veridicus-reports-single-writer` con sus dos controles negativos (IDS-U7-04); `volume-consumers` de U2 ya cubre los montajes; `promtool test rules deploy/veridicus/tests/report-rules.yaml`; `deploy/tests/level0/test_review_report_volume.py`; `check-no-cluster-apply.sh` con `evaluation/mttv/` en su alcance (petición IDS-U7-14) | Sí |
| `analyzer-level2-gate.yml` (U11) | Rutas de IA | — | Sin cambios: U7 no toca *prompts*, perfiles, adaptadores ni esquemas de salida | — |

## 2. Puertas con comando y umbral (AUTONOMIA-02)

| Gate | Comando | Umbral | Requisitos |
|---|---|---|---|
| Nivel 0 | `uv run --directory services/session-api pytest tests/review_report -m "not integration and not perf"` | Verde | NFR7.3, NFR8.9, NFR10.9, NFR10.10, NFR10.17, NFR10.22, NFR12.1, NFR14.1 |
| Ramas de guardias | `uv run --directory services/session-api pytest tests/review_report --cov-branch --cov-config=.coveragerc-guards` | 100 % de ramas | NFR13.2 |
| Nivel 1 | `uv run --directory services/session-api pytest tests/review_report -m integration` | Verde; tras la suite y el barrido a +301 s, `verify_store` con código 0 | NFR8.4, NFR8.5, NFR8.8, NFR8.10, NFR10.1–NFR10.21, NFR10.23–NFR10.27, NFR11.1–NFR11.8, NFR15.1–NFR15.5 |
| Auditoría común (U3) | `uv run --directory services/session-api pytest -m integration -k audit_convention` | `report_version` y `report_export` registradas; `UPDATE` y `DELETE` fallan con `veridicus_app`; `DELETE` pasa con `veridicus_retention` | NFR11.1, NFR11.8 |
| Rendimiento | `uv run --directory services/session-api pytest tests/review_report -m perf` | p95 de `monitoring-design.md` §3; RSS ≤ +192 MiB con 3 consolidaciones máximas; una corrida, sin reintentos | NFR3.1–NFR3.14, NFR7.2, NFR8.1–NFR8.3 |
| Cobertura | `uv run --directory services/session-api pytest --cov --cov-fail-under=80`; `npm --prefix frontend run test -- --coverage` | ≥ 80 % de líneas en cada uno | NFR13.1 |
| Consola | `npm --prefix frontend run test -- src/report` y `npm --prefix frontend run typecheck` | Verde; 0 errores | NFR3.9–NFR3.11, NFR3.15, NFR10.4, NFR10.18 |
| Tipos y fronteras | `mypy --strict`, `ruff check` y `lint-imports` en `services/session-api` | 0 errores; el control negativo que importa `httpx` desde `review_report` falla | NFR1.1, NFR11.2, NFR13.3, NFR14.2 |
| Auditoría de dependencias | `pip-audit`, `npm audit`, `gitleaks`, Trivy | 0 `HIGH`+ con corrección; 0 secretos | `team.md` |
| Manifiestos | `helm template deploy/veridicus -f deploy/values-cpu.yaml`, `kubeconform -strict`, `kyverno apply deploy/policies/` y `kyverno test deploy/policies/tests/` en `deploy-level0.yml` | 0 violaciones; cada control negativo (2 réplicas, `RollingUpdate`, un `CronJob` con el PVC) produce 1 violación | NFR1.2, NFR8.6, NFR10.6 |
| Volumen en el render | `uv run pytest deploy/tests/level0 -k review_report_volume` | Cuota = `requests.storage` del PVC en bytes; montaje en `/var/lib/veridicus/reports-volume` en la API y en el `Job` de retención; el contenedor de la línea de `verify_store` existe en el render | NFR15.3, NFR10.20 |
| Reglas | `promtool test rules deploy/veridicus/tests/report-rules.yaml` | Verde (volumen al 75 %, al 85 % durante 9 min y durante 10 min; `not_recorded` 0 y 1; `integrity_mismatch` 0 y 1) | NFR15.3, NFR15.5 |
| Nivel 3 (fuera de la CI) | `npx --prefix frontend playwright test e2e/report.spec.ts` contra `https://veridicus.local:8443` | 0 fallos; 0 violaciones `serious`/`critical` de axe | NFR8.7, NFR3.10, NFR3.11 |
| Corte por despliegue (tras cada despliegue de la API) | `scripts/measure-cutover.sh https://veridicus.local:8443` | Racha más larga sin respuesta de `session-api` ≤ 90 s | NFR8.6 (IDS-U7-11) |
| Nivel 2 (fuera de la CI) | `uv run --directory evaluation python -m mttv.mttv --run out/level2.json --report out/mttv.json` | Media < 600 s | NFR7.1 |

Los tres últimos los lanza el humano en WSL2 (IDS-U7-15). Solo hablan HTTP con la API, no cambian el clúster y
usan solo datos sintéticos. Sus reportes llevan solo cifras y se adjuntan al PR que los motiva o al de la
entrega etiquetada.

## 3. Del PR al clúster

| Paso | Qué pasa | Aprobación |
|---|---|---|
| 1 | PR de U1: cuerpo `{expected_cursor}` y `report.view_outdated` en C1 (NFRD-U7-04), `count_session` en C24 (NFRD-U13-08), glosario (`cancel_token`, `view_outdated`) y `report_max_bytes` en C25 | Fusión del PR |
| 2 | Antes de la migración, el humano ejecuta `scripts/backup-db.sh` y, si ya hay reportes, el paso `export_store` del runbook | Paso humano |
| 3 | PR de migración de U7 (§2.1 de `infrastructure-specification.md`), después de las de U4 y U5; solo aditiva | Fusión del PR |
| 4 | PR de código de U7 (B7) con `session-api.yml` y `frontend.yml` en verde | Fusión del PR |
| 5 | En `main`, `build` publica `session-api` y `frontend` por SHA | Automático, sin clúster |
| 6 | PR de despliegue: digests en `values-cpu.yaml`, `strategy: Recreate` con gracia de 30 s (si U2 adoptó IDS-U7-03), montaje y siete ajustes, PVC con `Prune=false`, la política de escritor único, las reglas y la fila del panel | Fusión con `deploy-level0.yml` en verde |
| 7 | Antes del módulo 8, el humano aplica lo fusionado con la instalación en dos pasos de U2 (migraciones primero); después, Argo CD sincroniza, con el `Job` de migraciones como *hook* `Sync`. Con `Recreate`, la API vieja termina (≤ 30 s) y la nueva barre y queda lista | La fusión del paso 6 |
| 8 | `scripts/measure-cutover.sh https://veridicus.local:8443` durante el paso 7; después, `scripts/smoke.sh https://veridicus.local:8443` y, antes de etiquetar, `e2e/report.spec.ts`. Salidas adjuntas al PR | — |

Ningún paso de un plan de tareas ejecuta `kubectl apply`, `helm install`, `helm upgrade`, una migración,
`import_store` o el `Job` de retención sin la fusión previa del PR y la acción del humano (AUTONOMIA-01).

## 4. Verificación del almacén y respaldo

| Operación | Cómo | Cuándo | Resultado esperado |
|---|---|---|---|
| `verify_store` en la CI | Al final del nivel 1, contra el directorio y la base del contenedor, tras el barrido a +301 s | Cada PR | Código 0 (NFR8.8) |
| `verify_store` en el clúster | El humano: `kubectl exec deploy/veridicus-session-api -c session-api -- python -m session_api.review_report.verify_store` (lista cerrada de U2) | Tras una restauración, antes de la sustentación y ante `VeridicusReportIntegrityMismatch` | Código 0: 0 versiones sin archivo, 0 SHA-256 distintos |
| Respaldo conjunto | El humano: `scripts/backup-db.sh` y, justo después, el paso `export_store` del runbook con su `sha256sum -c` (IDS-U7-07) | Antes de la sustentación, de cada cambio de esquema y de recrear el nodo | `backups/veridicus-<fecha>.dump` y `backups/veridicus-reports-<fecha>.tar` con su `.sha256` |
| Restauración | Manual, en el runbook: `pg_restore` → `import_store` → reinicio de la API → `verify_store` | Pérdida del PVC o de la base, o `integrity_mismatch` | `verify_store` con código 0; RTO ≤ 30 min |

`backup-db.sh` solo lee del clúster con el `pg_dump` de la lista cerrada. `export_store` e `import_store`
viven solo en el runbook, nunca en un *script*: `check-no-cluster-apply.sh` de U2 lo comprueba en nivel 0.

## 5. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh`, la E2E o el corte medido tras desplegar | `git revert` del PR de despliegue en un PR, fusión y nueva aplicación o sincronización. Con `Recreate`, el corte se repite. La migración aditiva se queda: el código anterior no lee `report_export` |
| Un ajuste de U7 inválido | El proceso termina y la API no queda lista. Con `Recreate` no hay pod viejo, así que la consola queda caída hasta el `git revert` (riesgo aceptado en P1 = A). `deploy-level0.yml` valida los ajustes antes de fusionar |
| La migración | Solo avanza; se corrige con otra migración (*expand–contract*) |
| `integrity_mismatch` o pérdida del volumen | Restauración del último respaldo (§4) y `verify_store` |
| La cuota se llena | PR que acorta la retención (U13) o amplía `reports.size` (PVC y cuota a la vez); nunca se borran reportes a mano |
| El corte pasa de 90 s | Se investiga el tramo (descarga de capas, arranque o barrido) y se corrige por PR; el umbral no se sube en silencio |

## 6. Entornos y secretos

| Aspecto | Diseño |
|---|---|
| Entornos | CI (PostgreSQL 16 en contenedor por digest y un directorio temporal como volumen) y el único equipo de 64 GB con `values-cpu.yaml`; mismas imágenes por SHA. Sin archivo de valores GPU (IDS-U2-02) |
| Secretos en la CI | Ninguno del clúster. Las pruebas de nivel 1 usan contraseñas efímeras y crean `veridicus_app`, `veridicus_retention` y `veridicus_owner` en cada corrida para probar permisos y la función `SECURITY DEFINER` |
| Secretos en el clúster | U7 no añade ninguno: la API usa `veridicus-db-app` y el `Job` de retención `veridicus-db-retention`, por `secretKeyRef`. Sale `veridicus-db-report-ro` (IDS-U7-02). Las credenciales del analista sintético del arnés de MTTV y de la E2E viven en el `.env` no versionado |
| Datos | *Fixtures*, dorados y reportes de prueba sintéticos del catálogo de U1; la comprobación de marcas corre en nivel 0 (NFR12.1). Los respaldos quedan en `backups/`, ignorado por git y podado por `retention_max_days` (petición IDS-U7-08) |

## 7. Correspondencia con AUTONOMIA · nuevo

| Regla | Comprobación | Dónde |
|---|---|---|
| AUTONOMIA-01 | Migración en su `Job` y su PR; `verify_store` solo desde la lista cerrada; `export_store` e `import_store` solo en el runbook; `check-no-cluster-apply.sh` con `evaluation/mttv/` (IDS-U7-14); la CI sin `kubeconfig` | `deploy-level0.yml`; §3 y §4 |
| AUTONOMIA-02 | Cada puerta nombra su comando y su umbral, incluido el corte por despliegue | §2 |
| AUTONOMIA-03 | Entrada única de `consolidate` (import-linter); quién y cuándo del servidor; cursor de lo revisado; escaneo de vocabulario antes del SHA-256; solo inserción en `report_version` y `report_export`; 100 % de ramas en las guardias | `session-api.yml` (`lint`, `test-level0`, `guards`, `test-level1`) |
| AUTONOMIA-04 | Sin clientes de red en `review_report`; ningún destino nuevo en la `NetworkPolicy`; exportación sin copias en disco ni en `/tmp`; `Ingress` sin disco; respaldos que nunca salen de la máquina | `session-api.yml`; `deploy-level0.yml` |
| AUTONOMIA-05 | No aplica directamente: el reporte copia los hallazgos ya verificados por U11 y U4, con sus dos citas, sin reescribirlos | — |
