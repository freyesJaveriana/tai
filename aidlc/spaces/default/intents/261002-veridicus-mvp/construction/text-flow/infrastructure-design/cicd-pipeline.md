# Pipeline de CI/CD — U4 text-flow

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Salen `libs.yml` y `ai-eval-gate.yml`, sustituidos por `analyzer.yml` y
  `analyzer-level2-gate.yml` de U11 (IDS-U4-12, IDS-U11-08), y el nivel 2 por `port-forward` al juez.
  `semantic-agent.yml` pasa a orquestar la biblioteca de U11 y suma las fronteras de D18. La migración de U4
  pierde `truthframe`, `pgvector` y los roles del juez y del indexador.
- **Numeración.** §1–§4 conservan su tema; lo nuevo empieza en §5.

**Insumos.** Comandos de `nfr-requirements/tech-stack-decisions.md` (§5) y dependencias (§4); calidad y
textos de `nfr-design/logical-components.md` (logical-components §5); pruebas de
`nfr-design/security-design.md` (security-design §2, §6–§12), `nfr-design/reliability-design.md`
(reliability-design §3, §4, §9–§14), `nfr-design/performance-design.md` (performance-design §1, §3, §8,
§9), `nfr-design/scalability-design.md` (scalability-design §1) y `nfr-design/observability-design.md`
(observability-design §1, §2); escenarios E5–E55 de `functional-design/functional-spec.md`
(functional-spec); procesos de `inception/domain-design/components.md` (components); C1–C3, C6, C17 y C25
de `inception/contract-design/contract-summary.md` (contract-summary); `cicd-pipeline.md` de U2, U3 y U11;
`infrastructure-specification.md` de esta carpeta; `## Testing Posture` y `## Deployment` de `team.md`.

## 1. *Workflows*

Todos con `permissions: contents: read`, acciones fijadas por SHA, sin `kubeconfig` ni claves de
proveedores; solo el *job* `build` de cada imagen tiene `packages: write`, y solo en `main`. Ninguna prueba
de los niveles 0 y 1 descarga un modelo, llama a un proveedor, exige GPU ni se reintenta (NFR2.1): C17 y el
`ModelGateway` se sustituyen por *fakes* deterministas; PostgreSQL 16 (imagen oficial, sin `pgvector`) y
Redis 7.2 son reales en contenedor. Las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos C2, C3
y C6 se escriben primero y se ven en rojo antes de implementar (`team.md`).

Los *workflows* de U4 siguen el patrón de IDS-U11-07: se disparan con todo PR, un *job* `changes` filtra por
rutas y un *job* `gate` es la única comprobación obligatoria (verde si todo pasó o si no había trabajo).

| *Workflow* | Rutas que activan el trabajo | *Job* | Comando y umbral (AUTONOMIA-02) | Bloquea |
|---|---|---|---|---|
| `session-api.yml` (de U3) | `services/session-api/**`, `libs/**`, `contracts/**`, `config/**` | `test-level0` | U4 añade: `uv run --directory services/session-api pytest -m "not integration and not perf"` con la segunda línea de C6 (E14 a–h, E16, E17), el plazo (4 filas de NFR3.5), límites antes de encolar con el *fixture* límite de U1 y el mismo con un carácter más, piso de 270 s, ajustes fuera de rango, ningún número de límite literal y ningún literal visible fuera del catálogo; verde | Sí |
| | | `guards` | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards`: 100 % de ramas en `output_check.py`, `incident.py`, `run_currency.py` y `deadline.py` (NFR13.2) | Sí |
| | | `test-level1` | `uv run --directory services/session-api pytest -m integration`: entrega al menos una vez, ingesta idempotente con dos consumidores de C3, publicación fallida con Redis detenido tras el `COMMIT`, supervisor con reloj controlado (huérfana, Redis reiniciado, carrera, espera sin liberar), ruta mínima del incidente (E36, E37, E51, sesión purgada), cancelación con reinicio de Redis, sondeo en una instantánea, *canary* con 0 apariciones en logs, `XRANGE` y `XPENDING`; verde | Sí |
| | | `test-perf` | `uv run --directory services/session-api pytest -m perf`: NFR3.1 (tramo de U4 ≤ 10 s, ingesta ≤ 5 s), NFR3.2 (≤ 300 ms con el trabajador bloqueado), NFR3.3 (sondeo ≤ 200 ms, carga completa ≤ 1 s) y NFR3.13 (liberación ≤ 1 s) en el *runner* de IDS-U3-09 | Sí |
| | | `coverage` | ≥ 80 % de líneas en `services/session-api` (NFR13.1) | Sí |
| `semantic-agent.yml` (U4) | `services/semantic-agent/**`, `libs/**`, `contracts/**` | `lint` | `ruff check`, `ruff format --check`, `mypy --strict` con 0 errores; `uv run --directory services/semantic-agent lint-imports` con los contratos `semantic-agent-no-anonymizer`, `semantic-agent-no-db` y `semantic-agent-layers`: 0 violaciones y cada módulo de prueba que los viola hace fallar el contrato (NFR1.3, NFR10.6); `hadolint` | Sí |
| | | `lock-boundary` | `uv run --directory services/semantic-agent python -m scripts.check_lock_no_anonymizer`: 0 apariciones de `libs-anonymizer` en `uv.lock`; control negativo con un lockfile que lo nombra | Sí |
| | | `test-level0` | `uv run --directory services/semantic-agent pytest -m "not integration and not perf"`: huella de `effective_config` al consumir (NFRD-U4-15), tope de 3 entregas sin llamar (NFRD-U4-01), `VERIDICUS_ANONYMIZER_PROXY_URL` fuera del clúster impide arrancar, piso de 270 s, paridad con la CLI campo a campo (NFR4.6), etiquetas de métricas dentro de `text-flow.v1.yaml`; verde | Sí |
| | | `test-level1` | `uv run --directory services/semantic-agent pytest -m integration` con Redis 7.2 real y los *fakes* de C17 y del proxy: renovación con `XCLAIM … JUSTID` que no sube el contador (`XPENDING`), dos renovaciones fallidas sin publicar, trabajador matado a mitad con ≤ 3 invocaciones del mismo mensaje, 0 llamadas nuevas tras cancelar y tras reiniciar Redis (E31, E52), proxy detenido con `/readyz` 503 y el bucle sin consumir (E47), una sola corrida a la vez con 3 sesiones; verde | Sí |
| | | `coverage` | ≥ 80 % de líneas en `services/semantic-agent` (NFR13.1) | Sí |
| | | `audit` | `pip-audit` sin `HIGH`+ con corrección; comprobación de datos sintéticos de U1 sobre `services/semantic-agent/tests/` con 0 hallazgos (NFR12.1) | Sí |
| | | `build` | Imagen sin root; `python -c "import libs.anonymizer"` dentro de la imagen termina en `ModuleNotFoundError` y, tras arrancar con un perfil local, `sys.modules` no contiene `libs.anonymizer` (E46); Trivy con `--exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed`; en `main` publica `veridicus-semantic-agent:<sha>` | Sí |
| | | `gate` | Depende de todos los anteriores | Sí (obligatoria) |
| `frontend.yml` (U4, base de la consola) | `frontend/**`, `contracts/**` | `test` | `npm ci`; ESLint (`react/no-danger` como error) y Prettier; `npm --prefix frontend run typecheck` estricto; `npm --prefix frontend run test -- --coverage` con Vitest, React Testing Library y `vitest-axe`: sondeo con un servidor *fake* que falla 3 veces sin perder cambios, *upsert* por ID, literal visible fuera del catálogo de U1 = fallo, escáner de U11 sobre catálogo y plantillas con un control negativo por término; ≥ 80 % de líneas | Sí |
| | | `audit`, `build` | `npm audit` sin `HIGH`+ con corrección; imagen `nginx-unprivileged` con Trivy; en `main` publica `veridicus-frontend:<sha>` | Sí |
| | | `gate` | Depende de los anteriores | Sí (obligatoria) |
| `libs.yml` | — | — | **Retirado**: lo sustituye `analyzer.yml` de U11 (IDS-U11-08) | — |
| `ai-eval-gate.yml` | — | — | **Retirado**: lo sustituye `analyzer-level2-gate.yml` de U11, con el par C19 v2 y su YAML en `evaluation/reports/level2/` (IDS-U11-04) | — |
| `deploy-level0.yml` (de U2) | `deploy/**`, `scripts/**`, `config/**`, `.github/**` | Los de U2 | De U4: el render incluye el trabajador y `semantic-agent` con `Recreate` y `terminationGracePeriodSeconds: 30` (IDS-U4-01/02/04), `/tmp` en memoria, sondas (`require-probes`), Secrets de IDS-U4-10 con su control negativo, ninguna `VERIDICUS_LIMIT_*` mayor que el catálogo; `promtool test rules` sobre las reglas de U4; `check-no-cluster-apply.sh` con `evaluation/load/` en su alcance (IDS-U4-07) | Sí |

Un PR que solo toca `libs/incoherence_analyzer/**` dispara `semantic-agent.yml` (la imagen lleva la
biblioteca) y, si toca rutas de IA, `analyzer-level2-gate.yml` de U11. U4 no tiene puerta de nivel 2 propia:
`semantic-agent` no cambia *prompts*, perfiles, adaptadores ni esquemas de salida.

## 2. Nivel 3 y prueba de carga, fuera de la CI

| Prueba | Dónde y cómo | Evidencia |
|---|---|---|
| Humo (nivel 3) | `scripts/smoke.sh https://veridicus.local:8443` en WSL2 tras cada despliegue: `/healthz` de cada servicio, `/readyz` por `port-forward` (IDS-U2-15) y `frontend/e2e/smoke.spec.ts` con `comercial-piloto` sobre transcripciones sintéticas: ≥ 1 hallazgo con sus dos citas en ≤ 300 s para la contradicción sembrada y 0 hallazgos para el relato coherente (NFR3.10, NFR8.6) | Salida de `smoke.sh` en el PR de despliegue |
| E2E (nivel 3) | Suite Playwright con `@axe-core/playwright` y el escáner de vocabulario sobre el texto renderizado de M3 y M4, antes de etiquetar | Reporte de Playwright en el PR de la entrega |
| Carga (NFR8.5) | `uv run --directory evaluation python -m load.run_batches --profile comercial-piloto --sessions 50 --concurrency 3 --report out/nfr8.json`, lanzado por el humano en WSL2 contra la API por `port-forward` (IDS-U4-08); registra `config_sha256` por sesión y falla con un perfil de `permutation: false` (NFRD-U4-13) | `out/nfr8.json` (solo cifras) adjunto al PR que lo motiva |
| Límites del piloto | `python scripts/count-transcript-limits.py <ruta-fuera-de-git>`, lo corre el humano; imprime 2 cifras | Las dos cifras en el PR de U1 si hay que subir C25 |

Nada de esto aplica cambios al clúster: `smoke.sh` y `run_batches.py` solo usan HTTP y `port-forward`.

## 3. Del PR al clúster

| Paso | Qué pasa |
|---|---|
| 1 | **PR de migraciones de U4**, antes que el código: tablas de sesión, turnos, corridas, intentos, `ModelCall`, `RunPublicationHold`, `AnonymizationIncident`; disparadores de inmutabilidad; `turn_count` y `char_count` (NFRD-U4-17); índices de NFRD-U4-11; `veridicus_purge_lock_session` (NFRD-U13-05). Solo avanza (*expand–contract*) y corre como el `Job` de migraciones de U2 en su propio PR, nunca al arrancar un pod |
| 2 | PR de código con `session-api.yml`, `semantic-agent.yml` y `frontend.yml` en verde |
| 3 | En `main`, `build` publica `session-api`, `semantic-agent` y `frontend` por SHA |
| 4 | PR de despliegue con los digests en `values-cpu.yaml`; `deploy-level0.yml` valida el render; la fusión en `main` protegida es la aprobación registrada |
| 5 | Antes del módulo 8, el humano aplica el chart ya fusionado (instalación en dos pasos de U2); después, Argo CD sincroniza. El trabajador y `semantic-agent` se reemplazan con `Recreate` y el runbook pide hacerlo sin corridas en `processing` (IDS-U4-04) |
| 6 | `scripts/smoke.sh`; si falla, reversión de §4 |

## 4. Reversión y puerta de etiquetado

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la suite E2E tras desplegar | `git revert` del PR de despliegue en un PR, fusión y nueva aplicación o sincronización (`team.md`) |
| Una versión de la biblioteca de U11 rompe `semantic-agent` | `git revert` del PR de despliegue (U2) y después del PR de U11 |
| Una migración | Solo avanza; se corrige con una migración nueva |
| Corridas que quedan en curso tras un fallo | El supervisor las pasa a `error` (`analysis.system`) ≤ 30 s después de `deadline_at`; el analista reintenta desde la consola con `attempt + 1` |

**Puerta de etiquetado (IDS-U4-13).** Una etiqueta del producto exige, para el mismo SHA, la salida de
`smoke.sh` y el reporte de Playwright, y un par de nivel 2 en `evaluation/reports/level2/` para la versión de
`libs-incoherence-analyzer` del `uv.lock` de `semantic-agent`, comprobado con `check-level2-report.py` de
U11. Sin los tres, no se etiqueta.

## 5. Secretos en CI/CD

- La CI no tiene ningún Secret del clúster: ni `veridicus-db-app`, ni `veridicus-redis-auth`, ni
  `veridicus-model-api-key`, ni claves de proveedores. Las pruebas de nivel 1 usan contraseñas efímeras del
  contenedor de prueba, generadas en el propio *job*.
- En el clúster, los manifiestos solo referencian Secrets por `secretKeyRef`; los valores los crea el humano
  con `create-secrets.sh` desde el `.env` no versionado (U2). Las credenciales del analista sintético de la
  prueba de carga también viven en el `.env` (IDS-U4-08).
- `gitleaks` (`secrets-scan.yml` de U2) corre en todo PR.

## 6. Correspondencia con AUTONOMIA

| Regla | Comprobación | Dónde |
|---|---|---|
| AUTONOMIA-01 | `check-no-cluster-apply.sh` de U2 sobre `scripts/`, `.github/`, `deploy/` y `evaluation/load/` (IDS-U4-07): 0 apariciones; la CI sin `kubeconfig` | `deploy-level0.yml` |
| AUTONOMIA-02 | Cada *job* nombra su comando y su umbral (§1, §2) | Este documento |
| AUTONOMIA-03 | Escáner en la ingesta (nivel 0), sobre catálogo y plantillas (nivel 0) y sobre el texto renderizado (nivel 3) | `session-api.yml`, `frontend.yml`, E2E |
| AUTONOMIA-04 | import-linter, lockfile e imagen sin `libs.anonymizer`; proxy obligatorio (E47); cancelación (E31, E52); incidente (E36, E37, E51); `veridicus-db-app` fuera de `semantic-agent` | `semantic-agent.yml`, `session-api.yml`, `deploy-level0.yml` |
| AUTONOMIA-05 | Segunda línea de C6, campos obligatorios y `estado: error` sin sugerencias con 100 % de ramas | `session-api.yml` (`guards`) |
