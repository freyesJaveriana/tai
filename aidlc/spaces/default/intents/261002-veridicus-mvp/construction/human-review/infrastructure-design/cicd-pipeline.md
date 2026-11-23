# Pipeline de CI/CD — U5 human-review

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Las pruebas siguen las del NFR Design revisión 2: observaciones en vez de CoT, rol
  `investigador`, `404` uniforme, `discard_correction_round`, `purge_session` con `veridicus_retention`, cifras
  de C25 y reconciliación de series. Entran el escaneo de nivel 0 sobre el catálogo (cierra R-04) y la prueba
  del empate de los dos plazos (cierra R-03). La regla AIR se prueba en el *workflow* de U2 con el *fixture* de
  U5, sin caso de dos pods (cierra R-01).
- **Numeración.** §1–§6 conservan su tema; §7 es nueva.

**Insumos.** Comandos de `nfr-requirements/tech-stack-decisions.md` (§5); pruebas de
`nfr-design/performance-design.md` (performance-design §1–§3, §6), `nfr-design/reliability-design.md`
(reliability-design §1–§4, §6), `nfr-design/scalability-design.md` (scalability-design §2–§5),
`nfr-design/security-design.md` (security-design §1–§6, §8) y `nfr-design/observability-design.md`
(observability-design §1, §2); cobertura, fronteras y textos de `nfr-design/logical-components.md`
(logical-components §5); escenarios E1–E33 de `functional-design/functional-spec.md` (functional-spec);
HumanReview de `inception/domain-design/components.md` (components); C1, C10, C11, C15 v2, C24 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); `cicd-pipeline.md` de U2, U3 y U4;
`infrastructure-specification.md` de esta carpeta; `## Testing Posture` y `## Deployment` de `team.md`.

U5 no crea *workflows*: añade pruebas a `session-api.yml` (U3), a `frontend.yml` (U4) y casos a
`deploy-level0.yml` (U2), sin cambiar sus puertas, sus permisos (`contents: read`), sus acciones fijadas por
SHA, la ausencia de `kubeconfig` ni las comprobaciones obligatorias de `main`.

## 1. Etapas y puertas en la CI

Las pruebas de las guardias y de los contratos (máquina de estados, observaciones exigidas en el servidor,
cuerpo de C1, etiquetas de C15 v2, recibo de C24) se escriben primero y se ven fallar antes de implementar
(`team.md`, Testing Posture). Ninguna prueba de U5 descarga modelos, pide GPU ni se reintenta (NFR2.1);
PostgreSQL 16 es real en contenedor.

| *Job* (*workflow*) | Qué añade U5 | Comando | Umbral (bloquea) |
|---|---|---|---|
| `lint` (`session-api.yml`) | Contratos de import-linter `human_review_domain_pure`, `human_review_no_network` y uso de C10, C11 y C24 solo por interfaz, cada uno con su módulo de control negativo | `uv run --directory services/session-api lint-imports`; `ruff check`; `mypy --strict` | 0 errores (NFR13.3, NFR1.1) |
| `test-level0` (`session-api.yml`) | Transiciones celda por celda; `dismissal_window` por tabla; Hypothesis con espacios Unicode y lista de la migración igual a la de `str.isspace()`; 2 000 y 2 001 caracteres y variable que baja la cifra; pisos de C25 y `VERIDICUS_DB_LOCK_TIMEOUT_MS` fuera de rango → el arranque falla; roles del OpenAPI frente a la matriz de FR1.2; etiquetas de C15 v2; *fixtures* sintéticos; regla estática del umbral; ningún `FOR UPDATE` de rondas fuera de `round_repository.py`; **escaneo de vocabulario sobre el catálogo de mensajes de U5 con un término sembrado que hace fallar la prueba** (R-04) | `uv run --directory services/session-api pytest tests/human_review -m "not integration and not perf"` | 0 fallos (NFR10.5, NFR10.8, NFR10.9, NFR10.18, NFR10.19, NFR11.4, NFR12.1, NFR15.3) |
| `guards` (`session-api.yml`) | `state_machine.py` y `effective_state.py` en `.coveragerc-guards` | `uv run --directory services/session-api pytest tests/human_review --cov-branch --cov-config=.coveragerc-guards` | 100 % de ramas (NFR13.2) |
| `test-level1` (`session-api.yml`) | Con la migración de U5: `401`/`403`/`404`/CSRF con 0 filas y 0 entradas de acceso; observaciones exigidas; SHA-256 de lo de la IA; `CHECK`, disparadores y permisos; `-k audit_convention` con `veridicus_app` y `veridicus_retention`; concurrencia de cuatro hilos con 50 repeticiones y 0 `40P01`; `purge_session` con otras dos sesiones contadas y fallo inyectado; `lock_timeout` → `503` en ≤ 2,5 s; **empate: una transacción retiene la sesión 3 s con `lock_timeout` = `statement_timeout` = 2 000 ms y la decisión responde `503` `system.unavailable` en ≤ 2,5 s, 0 filas y un `WARNING` con `duration_ms`, sea cual sea el plazo que salte** (IDS-U5-03); fallo de métricas → `201`; centinela fuera de logs, errores y `/metrics`; `pg_indexes` con los seis índices y `EXPLAIN` sin `Seq Scan` con 30 000 decisiones; < 50 MB; ≤ 30 series tras la reconciliación con 60 sesiones | `uv run --directory services/session-api pytest tests/human_review -m integration` y `pytest -m integration -k audit_convention` | 0 fallos (NFR10.1–NFR10.22, NFR11.1–NFR11.6, NFR8.3–NFR8.6, NFR15.2, NFR15.5) |
| `test-perf` (`session-api.yml`) | NFR3.1–NFR3.6, NFR3.9 y NFR8.2; contador ≤ 6 sentencias; ΔRSS de la API ≤ 32 MiB (NFR8.1) | `uv run --directory services/session-api pytest tests/human_review -m perf` | Umbrales de `monitoring-design.md` §3; una sola corrida en el *runner* de IDS-U3-09, sin reintentos; una prueba inestable va a cuarentena con su *issue* |
| `coverage` (`session-api.yml`) | `human_review` entra en la cobertura del servicio | `--cov-fail-under=80` | ≥ 80 % de líneas (NFR13.1) |
| `test` (`frontend.yml`) | Tarjeta: sin actualización optimista; «Aceptar» y «Editar» con `aria-disabled` hasta el `204`; reintento de `observation-views` (0,5 s, 1 s, 2 s; no ante `403`, `404`, `413`); sin reintento de decisiones; literales solo del catálogo de U1; `vitest-axe` | `npm --prefix frontend run test -- --coverage src/review`; `npm --prefix frontend run typecheck` | 0 fallos; 0 violaciones `serious`/`critical`; ≥ 80 % de líneas (NFR3.8, NFR10.16, NFR14.1) |
| `deploy-level0.yml` (de U2) | `promtool test rules` de la regla AIR con `air_series.yaml` de U5 (0,25 sin alerta, 0,375 con alerta); `check-limits-env.sh` sin ninguna `VERIDICUS_LIMIT_REVIEW_*` mayor que el catálogo; si U2 adopta IDS-U5-02, `VERIDICUS_DB_LOCK_TIMEOUT_MS` en cada contenedor con la imagen `session-api` (control negativo: el `Job` de retención sin ella) | Los de U2 | Cada regla dispara y no dispara según su caso; código 0 |
| `build` (`session-api.yml`) | Sin cambios: imagen sin root, Trivy, publica por SHA solo en `main` | — | Puertas de U3 |

## 2. Nivel 3, fuera de la CI

| Prueba | Cuándo | Comando | Umbral |
|---|---|---|---|
| `frontend/e2e/review.spec.ts` con `@axe-core/playwright` y el escáner de vocabulario (nota y reformulación como `literal_sources`) | Antes de etiquetar una entrega | `npx --prefix frontend playwright test e2e/review.spec.ts` | 0 fallos; 0 violaciones `serious`/`critical`; clic → estado ≤ 1 s; 0 `WARNING` `system.unavailable` (NFR8.7, NFR3.7, NFR10.9) |
| Humo | Tras cada despliegue | `scripts/smoke.sh https://veridicus.local:8443` en WSL2 | Código 0; incluye `/readyz` de `veridicus-session-api` por `port-forward` (IDS-U2-15), que solo responde si la configuración de U5 es válida |

## 3. Despliegue y orden de migraciones

| Paso | Qué pasa | Aprobación |
|---|---|---|
| 1 | El humano ejecuta `scripts/backup-db.sh` (U2 §6) antes del cambio de esquema | Humano |
| 2 | PR de la migración de U5 (columnas de `review_round`, `review_decision`, `observations_view`, `CHECK`, disparadores, índices, permisos de `veridicus_app` y `veridicus_retention`). Requiere aplicadas las de U3 y U4; la CI corre `alembic upgrade head` en el nivel 1 | Fusión en `main` protegida (AUTONOMIA-01) |
| 3 | El humano aplica `migrations-job` con la revisión nueva (ruta manual en dos pasos de U2) o, desde el módulo 8, Argo CD lo ejecuta como *hook* `Sync` en la onda −1; se comprueba con `kubectl logs job/<migrations-job> -n veridicus` y código 0 | Humano / fusión |
| 4 | PR del código de U5 y de la clave `VERIDICUS_DB_LOCK_TIMEOUT_MS` en los valores; `session-api.yml` y `frontend.yml` en verde | Fusión |
| 5 | PR de despliegue con los digests nuevos de `session-api` y `frontend` en `values-cpu.yaml`; `deploy-level0.yml` en verde | Fusión |
| 6 | Aplicación manual del chart ya fusionado (antes del módulo 8) o sincronización de Argo CD; la API con `RollingUpdate` sin corte, el trabajador con `Recreate` | Humano / fusión |
| 7 | `scripts/smoke.sh https://veridicus.local:8443` y, para la entrega, `review.spec.ts` | Evidencia en el PR |

El `Job` de retención, que ejecuta `purge_session`, vive en `deploy/jobs/` fuera de Argo CD y solo lo lanza el
humano (U13). Ningún paso lo ejecuta la CI ni un agente: todo cambio al clúster es un artefacto revisado y
aplicado por el humano tras la fusión.

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o `review.spec.ts` tras desplegar | `git revert` del PR de despliegue en un PR, fusión y nueva aplicación o sincronización (U2); el código anterior funciona sobre el esquema expandido |
| La migración de U5 | Solo avanza: se corrige con una migración nueva. Si dañó datos, restauración manual del volcado del paso 1 (U2 §6); las consolidaciones posteriores se rehacen (IDS-U5-07) |
| Configuración de U5 inválida | El pod nuevo no arranca y el viejo sigue atendiendo (`maxUnavailable: 0`); `git revert` del PR de valores |
| Un `Job` de retención que falla en `purge_session` | Su transacción se revierte entera; el humano lo relanza tras corregir la causa |

## 5. Entornos y secretos

| Aspecto | Diseño |
|---|---|
| Entornos | Una sola máquina de 64 GB, solo CPU, con Minikube de 50 GiB (IDS-U2-01) y el mismo digest que publica la CI; sin *staging* ni producción |
| Secretos | U5 no añade ninguno. En el clúster usa los de su proceso por `secretKeyRef`: `veridicus-db-app` (API y trabajador) y `veridicus-db-retention` (`Job` de U13); los crea el humano con `create-secrets.sh` desde su `.env` |
| Secretos en la CI | Ninguno del clúster; las pruebas de nivel 1 usan contraseñas efímeras del contenedor generadas en el propio *job*; `gitleaks` corre en todo PR |
| Datos de prueba | Solo el catálogo sintético de U1 (NFR12.1) |

## 6. Evidencia por PR

| PR | Evidencia |
|---|---|
| Migración de U5 | Salida del nivel 1 con `alembic upgrade head`, nombre del archivo del volcado previo y log del `Job` de migraciones |
| Código de U5 | Resumen de `session-api.yml` (incluidos `guards` y `test-perf`) y de `frontend.yml` |
| Despliegue | Resumen de `deploy-level0.yml` y salida de `scripts/smoke.sh`; para la entrega, reporte de `review.spec.ts` |

## 7. Correspondencia con AUTONOMIA

| Regla | Comprobación | Dónde |
|---|---|---|
| AUTONOMIA-01 | Migración como `Job` en su PR; la purga la lanza el humano; `check-no-cluster-apply.sh` de U2 con 0 apariciones; la CI sin `kubeconfig` | §3; `deploy-level0.yml` |
| AUTONOMIA-02 | Cada *job* nombra su comando y su umbral | §1, §2 |
| AUTONOMIA-03 | Máquina de estados con 100 % de ramas; observaciones exigidas en el servidor; solo inserción y disparadores; escaneo de vocabulario en nivel 0 (catálogo) y nivel 3 (interfaz) | `session-api.yml`, `frontend.yml`, E2E |
| AUTONOMIA-04 | `human_review_no_network` con control negativo; centinela fuera de logs, errores y `/metrics` | `session-api.yml` |
| AUTONOMIA-05 | No aplica directamente: `propose` de U4 rechaza candidatas sin los cinco campos | — |
