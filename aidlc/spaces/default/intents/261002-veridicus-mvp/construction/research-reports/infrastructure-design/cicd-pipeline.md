# Pipeline de CI/CD — U12 research-reports

**Revisión 1 (2026-11-23): primera pasada.** Todo es nuevo.
- U12 no tiene imagen ni *workflow* propios: su código entra en `session-api.yml` (U3) y M8 en
  `frontend.yml` (U4), y sus manifiestos son los de U2 (`deploy-level0.yml`). Este documento fija los
  *jobs* y pasos que U12 añade a esos *workflows*, sin cambiar sus puertas ni su patrón `changes` + `gate`.

**Insumos.** Comandos de `nfr-requirements/tech-stack-decisions.md` (§5) y dependencias (§4); pruebas de
`nfr-design/security-design.md` (security-design §1–§10), `nfr-design/reliability-design.md`
(reliability-design §2–§6, §9), `nfr-design/performance-design.md` (performance-design §7, §8),
`nfr-design/scalability-design.md` (scalability-design §3, §5) y `nfr-design/observability-design.md`
(observability-design §1–§4); guardias de `nfr-design/logical-components.md` (logical-components §1);
escenarios E1–E40 de `functional-design/functional-spec.md` (functional-spec); ResearchReports en
`inception/domain-design/components.md` (components); C1, C19 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); `cicd-pipeline.md` de U2, U3 y U4;
`infrastructure-specification.md` de esta carpeta; `## Testing Posture` y `## Deployment` de `team.md`.

## 1. *Workflows* y *jobs*

Todos con `permissions: contents: read`, acciones fijadas por SHA, sin `kubeconfig` ni claves de
proveedores; solo el *job* `build` de cada imagen tiene `packages: write`, y solo en `main`. Las pruebas de
los niveles 0 y 1 de U12 no descargan modelos, no exigen GPU, no salen a la red (`pytest-socket` solo deja la
conexión a PostgreSQL de la prueba) y no se reintentan (NFR2.1). Usan **reportes sintéticos** del generador
`tests/fixtures/make_research_reports.py` y PostgreSQL 16 real en contenedor. Las pruebas de las guardias
(validación, contraste y rechazos sin eco) y del contrato C19 se escriben primero y se ven en rojo antes de
implementar (`team.md`).

| *Workflow* | Rutas que activan el trabajo | *Job* | Comando y umbral (AUTONOMIA-02) | Bloquea |
|---|---|---|---|---|
| `session-api.yml` (de U3) | `services/session-api/**`, `libs/**`, `contracts/**`, `config/**` y, por IDS-U12-05, `evaluation/labels/**` | `lint` | U12 añade a `uv run --directory services/session-api lint-imports` los contratos `research-reports-no-egress` y `research-reports-no-metrics`: 0 violaciones, y cada módulo de control negativo de `tests/import_contracts/` hace fallar su contrato (NFR1.2, NFR15.1); `mypy --strict` y `ruff check` con 0 errores | Sí |
| | | `test-level0` | `uv run --directory services/session-api pytest -m "not integration and not perf" tests/research_reports`: un *fixture* por regla de validación, 8 MiB de `[` en ≤ 1 s sin `RecursionError`, entero de 4 301 cifras → `out_of_range`, clave repetida con el *canary*, `detail` siempre de plantilla, comprobación AST de aperturas del catálogo y de argumentos del *logger*, arranque con cada archivo del catálogo ausente, inválido o con clave repetida (E37), OpenAPI sin `PUT`, `PATCH` ni `DELETE` (E39), tabla de frontera igual a la del README, ningún bucle de reintento ni `tenacity`, `CHECK` en toda columna de texto de la migración; verde | Sí |
| | | `guards` | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards`: U12 suma `research_reports/domain/validation/`, `domain/contrast.py` y `domain/problems.py`; 100 % de ramas (NFR13.2) | Sí |
| | | `test-level1` | `uv run --directory services/session-api pytest -m integration tests/research_reports`: matriz del *canary* en todas las columnas de texto de `information_schema`, respuesta y logs (E2–E6, NFR12.1); sin disco con `tempfile` y `open` de escritura sustituidos (NFR10.4); tope mientras se lee con un espía del flujo (≤ tope + 64 KiB); CSRF y rol con 0 bytes leídos; rol quitado entre T1 y T3 → `403` y 0 filas; atomicidad con fallo tras la primera hija, corte de conexión y espera de 16 s → `503` y 0 filas; duplicados en paralelo 20 veces → 1 fila (E8); tercera subida → `503` en ≤ 5,5 s; cliente a 1 KiB/s → `503` a los 30 s; re-subida tras vaciar las tablas; claves de la línea de log; ningún `interview_sha256` en la base; verde | Sí |
| | | `test-perf` | `uv run --directory services/session-api pytest -m perf tests/research_reports` (50 repeticiones, mediana y p95) en el *runner* `ubuntu-24.04` de U3: NFR3.1–NFR3.6, NFR3.8 (RSS ≤ 256 MiB con una subida máxima y ≤ 512 MiB con dos), NFR3.10 (`test_upload_does_not_slow_polling`, + ≤ 200 ms) y NFR3.11 (≤ 1,5 × `source_bytes`). Una falla inestable va a cuarentena con un *issue*; nunca se reintenta ni se baja el umbral | Sí |
| | | `coverage` | ≥ 80 % de líneas en `services/session-api`, con U12 dentro (NFR13.1) | Sí |
| | | `audit`, `build` | `pip-audit` sin `HIGH`+ con corrección (incluye `python-multipart` fijado con *hashes*, NFR10.13); `hadolint` del `Dockerfile` que copia `evaluation/labels/`; Trivy `HIGH`/`CRITICAL` con corrección; en `main` publica `veridicus-session-api:<sha>` | Sí |
| | | `gate` | Depende de todos los anteriores; única comprobación obligatoria | Sí |
| `frontend.yml` (de U4) | `frontend/**`, `contracts/**` | `test` | U12 añade M8 a `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck`: `<img src=x onerror=alert(1)>` en `profile_name` pintado como texto (NFR10.12), `react/no-danger` como error, literal visible fuera del catálogo = fallo (NFR14.1), escáner de vocabulario de U4 sobre los textos de M8 (NFR11.5), `retry: false` en la mutación, «Cancelar» y Escape durante `uploading`; ≥ 80 % de líneas | Sí |
| | | `audit`, `build`, `gate` | Los de U4, sin cambios (`npm audit --audit-level=high`) | Sí |
| `deploy-level0.yml` (de U2) | `deploy/**`, `scripts/**`, `config/**`, `contracts/limits.v1.yaml`, `.github/**` | Los de U2 | De U12: `check-ingress-limits.sh` comprueba `veridicus-research-reports` (tres anotaciones sin disco y 8 454 144 = `research_report_max_bytes` + 64 KiB); `check-limits-env.sh` sin ninguna `VERIDICUS_LIMIT_RESEARCH_REPORT_*` mayor que C25; `deploy/tests/level0` con el `limits.memory` de la API ≥ 1 792 MiB (IDS-U12-01) y la anotación `checksum/veridicus-profiles` en la plantilla del pod (IDS-U12-04); `promtool test rules` sobre `VeridicusSessionApiNearMemoryLimit` (IDS-U12-09); `check-no-cluster-apply.sh` | Sí |

U12 no tiene puerta de nivel 2: no toca *prompts*, perfiles, adaptadores de modelos ni esquemas de salida
del analizador. Un PR de U11 que cambie C19 dispara `session-api.yml` por `contracts/**` y la prueba del
validador compilado de U12 lo detecta antes de fusionar.

## 2. Nivel 3, fuera de la CI

| Prueba | Dónde y cómo | Evidencia |
|---|---|---|
| E2E de M8 | `npx --prefix frontend playwright test e2e/research-reports.spec.ts` en WSL2 contra `https://veridicus.local:8443`, con un investigador sintético del `.env` no versionado y reportes sintéticos: subida, lista, detalle, comparación, 0 violaciones `serious` o `critical` de `axe` y recorrido solo con teclado (E40), filtro en ≤ 300 ms con 1 000 filas (NFR3.7) | Reporte de Playwright en el PR de la entrega |
| Humo | `scripts/smoke.sh https://veridicus.local:8443` de U2 tras cada despliegue. U12 no añade casos: `/readyz` de `session-api` solo responde `200` si el catálogo de referencia cargó (reliability-design §6) | Salida de `smoke.sh` en el PR de despliegue |
| Conteo de reportes | Consulta de conteo y de `pg_total_relation_size` en la revisión de B12, por `kubectl exec` de solo lectura de la lista cerrada de U2 | Las dos cifras en la revisión de B12 (IDS-U12-08) |

Nada de esto aplica cambios al clúster: Playwright y `smoke.sh` solo usan HTTP y `port-forward`.

## 3. Del PR al clúster

| Paso | Qué pasa |
|---|---|
| 1 | **PR de migraciones de U12**, antes que el código: las cuatro tablas con sus `CHECK`, el índice único de `source_sha256`, el índice `uploaded_at DESC`, la marca `veridicus-audit` y la llamada a `veridicus_apply_audit_grants()`. Solo avanza (*expand–contract*) y corre como el `Job` de migraciones de U2 en su propio PR, nunca al arrancar un pod (`project.md`) |
| 2 | PR de U1 con las cifras de U12 en C25 (incluida `research_report_read_timeout_s`) y C19 v2, si aún no están en `main` |
| 3 | PR de código con `session-api.yml` y `frontend.yml` en verde. Requiere el lector compartido que entrega B7 (IDS-U12-02) |
| 4 | En `main`, `build` publica `session-api` y `frontend` por SHA |
| 5 | PR de despliegue con los digests en `values-cpu.yaml` y, en el mismo PR o antes, el `limits.memory` de 1 792 MiB (IDS-U12-01); `deploy-level0.yml` valida el render; la fusión en `main` protegida es la aprobación registrada |
| 6 | Antes del módulo 8, el humano aplica el chart ya fusionado (instalación en dos pasos de U2); después, Argo CD sincroniza. La API se reemplaza con `RollingUpdate` |
| 7 | `scripts/smoke.sh`; si falla, reversión de §4 |

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la E2E tras desplegar (p. ej. catálogo roto: el pod nuevo no pasa a listo) | `git revert` del PR de despliegue en un PR, fusión y nueva aplicación o sincronización (`team.md`); con `maxUnavailable: 0`, el pod viejo sigue atendiendo mientras tanto |
| Un cambio de perfiles o precios deja de aceptar reportes ya hechos (E18, E19) | No es un fallo del despliegue: se suben los reportes antes de fusionar el cambio o se crea un perfil con otro nombre (pregunta abierta 5 del Functional Design) |
| `OOMKilled` de la API con subidas | `git revert` del PR de despliegue; el hallazgo se corrige en el código y se vuelve a medir NFR3.8; el límite no se sube en silencio |
| Una migración | Solo avanza; se corrige con una migración nueva |
| Una subida cortada por el despliegue | No deja filas; el investigador reintenta y recibe `201` o `409` |

## 5. Secretos en CI/CD

- U12 no añade Secrets: usa `veridicus-db-app` de la API, como las demás unidades de `session-api`.
- La CI no tiene ningún Secret del clúster; las pruebas de nivel 1 usan contraseñas efímeras del contenedor
  de prueba generadas en el propio *job*.
- Las credenciales del investigador sintético de la E2E viven en el `.env` no versionado del humano.
- `gitleaks` (`secrets-scan.yml` de U2) corre en todo PR.

## 6. Correspondencia con AUTONOMIA

| Regla | Comprobación | Dónde |
|---|---|---|
| AUTONOMIA-01 | `check-no-cluster-apply.sh` de U2: 0 apariciones; la CI sin `kubeconfig`; migración en su `Job` y su PR | `deploy-level0.yml`; §3 |
| AUTONOMIA-02 | Cada *job* nombra su comando y su umbral (§1, §2) | Este documento |
| AUTONOMIA-03 | M8 sin hallazgos ni etiquetas de veracidad; escáner de vocabulario sobre sus textos (nivel 0) y sobre el texto renderizado (nivel 3) | `frontend.yml`; E2E |
| AUTONOMIA-04 | `research-reports-no-egress` con su control negativo; matriz del *canary*; sin reglas de red nuevas | `session-api.yml` (`lint`, `test-level1`) |
| AUTONOMIA-05 | No aplica: U12 no emite hallazgos | — |
