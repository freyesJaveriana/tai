# Pipeline de CI/CD — U5 human-review

**Insumos.** Comandos de verificación y D1–D12 de `nfr-requirements/tech-stack-decisions.md`; pruebas
`perf` de `nfr-design/performance-design.md` (performance-design); pruebas de concurrencia y fallos de
`nfr-design/reliability-design.md` (reliability-design); carga de 10× e índices de
`nfr-design/scalability-design.md` (scalability-design); controles de
`nfr-design/security-design.md` (security-design); métricas y centinela de
`nfr-design/observability-design.md` (observability-design); cobertura, fronteras y textos de
`nfr-design/logical-components.md` (logical-components §5); flujos de
`functional-design/functional-spec.md` (functional-spec); módulo HumanReview de
`inception/domain-design/components.md` (components); C1, C10, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); flujo común de U2, *workflow*
`session-api.yml` de U3 y `frontend.yml` de U4 (sus `cicd-pipeline.md`); `infrastructure-specification.md`
de esta carpeta; `## Testing Posture` y `## Deployment` de `team.md`.

U5 no crea *workflows*: añade pruebas a `session-api.yml` (U3) y a `frontend.yml` (U4) sin cambiar sus
puertas, permisos (`contents: read`), acciones fijadas por SHA ni la ausencia de `kubeconfig`.

## 1. Etapas y puertas en la CI

Las pruebas de las guardias y de los contratos (máquina de estados, CoT exigida por el servidor,
cuerpo de C1, etiquetas de C15) se escriben primero y se ven fallar antes de implementar (`team.md`).

| *Job* (*workflow*) | Qué añade U5 | Comando | Umbral (bloquea) |
|---|---|---|---|
| `lint` (`session-api.yml`) | Contratos `human_review_domain_pure`, `human_review_no_network` y uso de C10/C11 solo por interfaz; control negativo | `uv run --directory services/session-api lint-imports`; `ruff check`; `mypy --strict` | 0 errores (NFR13.3, NFR1.1) |
| `test-level0` (`session-api.yml`) | Tabla de transiciones celda por celda, `dismissal_window` por tabla, Hypothesis de espacios Unicode y 2 000/2 001 caracteres, etiquetas de C15 validadas, `limits_match` del catálogo, *fixtures* sintéticos, regla estática del umbral, ningún `FOR UPDATE` de rondas fuera de `round_repository.py` | `uv run --directory services/session-api pytest -m "not integration and not perf"` | 0 fallos (NFR10.5, NFR10.8, NFR11.4, NFR12.1, NFR15.3) |
| `guards` (`session-api.yml`) | `state_machine.py` y `effective_state.py` en `.coveragerc-guards` | `uv run --directory services/session-api pytest tests/human_review --cov-branch --cov-config=.coveragerc-guards` | 100 % de ramas (NFR13.2) |
| `test-level1` (`session-api.yml`) | PostgreSQL 16 real con la migración de U5; `403`/CSRF con 0 filas, `CotView` exigido, SHA-256 de lo de la IA, `CHECK`, permisos de solo inserción (`-k audit_convention`), *trigger*, concurrencia (2 y 3 hilos, 50 repeticiones, 0 `40P01`), `lock_timeout` → `503` en ≤ 2,5 s, fallo de métricas → `201`, `/readyz` con configuración inválida, centinela fuera de logs, errores y `/metrics`, `pg_indexes` y `EXPLAIN` sin `Seq Scan` con 22 500 filas, < 50 MB, ≤ 40 series con 60 sesiones | `uv run --directory services/session-api pytest -m integration tests/human_review` | 0 fallos (NFR10.1–NFR10.4, NFR10.6, NFR10.7, NFR10.10–NFR10.18, NFR11.1–NFR11.3, NFR8.3–NFR8.6, NFR15.5) |
| `test-perf` (`session-api.yml`) | NFR3.1–NFR3.6 y NFR8.2; contador de sentencias ≤ 6; ΔRSS ≤ 32 MiB | `uv run --directory services/session-api pytest tests/human_review -m perf` | Umbrales de monitoring-design §3; una sola corrida, sin reintentos |
| `coverage` (`session-api.yml`) | El módulo `human_review` entra en la cobertura del servicio | `--cov-fail-under=80` | ≥ 80 % de líneas (NFR13.1) |
| `rules` (`deploy-level0.yml` de U2) | Las dos reglas nuevas y el *fixture* `air_series.yaml` | `promtool test rules deploy/veridicus/charts/session-api/tests/rules.yaml` | Cada regla dispara y no dispara según su caso |
| `frontend.yml` (U4) | Tarjeta: sin actualización optimista, botones deshabilitados hasta el `204`, reintento de `cot-views` (0,5 s, 1 s, 2 s), sin reintento de decisiones, literales solo del catálogo de U1, `vitest-axe` | `npm --prefix frontend run test -- --coverage` | 0 fallos; 0 violaciones `serious`/`critical`; ≥ 80 % de líneas (NFR3.8, NFR10.16, NFR14.1) |
| `build` (`session-api.yml`) | Sin cambios: imagen, Trivy, sin root, publica por SHA solo en `main` | — | Puertas de U3 |

Ninguna prueba de U5 descarga modelos ni pide GPU (NFR2.1); ninguna de los niveles 0 y 1 se
reintenta.

## 2. Nivel 3, fuera de la CI

| Prueba | Cuándo | Comando | Umbral |
|---|---|---|---|
| `frontend/e2e/review.spec.ts` con `@axe-core/playwright` y escáner de vocabulario (`scan` con nota y reformulación como `literal_sources`) | Antes de etiquetar una entrega | `npx --prefix frontend playwright test e2e/review.spec.ts` | 0 fallos; 0 violaciones `serious`/`critical`; clic → estado ≤ 1 s (NFR8.7, NFR3.7, NFR10.9) |
| `scripts/smoke.sh https://veridicus.local` | Tras cada despliegue | `scripts/smoke.sh https://veridicus.local` | Código 0; incluye `/readyz` completo de `session-api`, que valida la configuración de U5 |

## 3. Despliegue y orden de migraciones

| Paso | Qué pasa | Aprobación |
|---|---|---|
| 1 | El humano ejecuta `scripts/backup-db.sh` (U2 §6) antes del cambio de esquema | Humano |
| 2 | PR de la migración de U5 (tablas, columnas `change_seq`, índices, permisos, *trigger*); requiere la migración de U4 ya aplicada; CI con `alembic upgrade head` en el nivel 1 | Fusión en `main` protegida (AUTONOMIA-01) |
| 3 | El humano aplica `migrations-job` con la revisión nueva (antes del módulo 8) o Argo CD lo sincroniza en la onda −1; se comprueba con `kubectl logs job/<migrations-job>` y código 0 | Humano / fusión |
| 4 | PR del código de U5 y de las claves del `ConfigMap`; `session-api.yml` y `frontend.yml` en verde | Fusión |
| 5 | PR de despliegue con los digests nuevos de `session-api` y `frontend`; `deploy-level0.yml` en verde (incluye `promtool`) | Fusión |
| 6 | Aplicación manual del chart (antes del módulo 8) o sincronización de Argo CD; `RollingUpdate` sin corte | Humano / fusión |
| 7 | `scripts/smoke.sh` y, para la entrega, `review.spec.ts` | Evidencia en el PR |

Ningún paso lo ejecuta la CI ni un agente: todo cambio al clúster es un artefacto revisado y aplicado
por el humano tras la fusión.

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o `review.spec.ts` tras desplegar | `git revert` del PR de despliegue y nueva aplicación o sincronización (U2); el código anterior funciona sobre el esquema expandido |
| La migración de U5 | Solo avanza: se corrige con una migración nueva. Si dañó datos, restauración manual del volcado del paso 1 (U2 §6) |
| Configuración de U5 inválida | El pod nuevo no arranca y el viejo sigue atendiendo (`maxUnavailable: 0`); `git revert` del PR del `ConfigMap` |
| Una regla de Prometheus ruidosa | `git revert` del cambio de la `PrometheusRule`; ninguna regla cambia el umbral |

## 5. Entornos y secretos

| Aspecto | Diseño |
|---|---|
| Entornos | Máquina de desarrollo (CPU, Minikube 20 GiB) y de demostración (28 GiB) con el mismo chart y los mismos valores para U5; sin *staging* ni producción |
| Secretos | U5 no añade ninguno: usa el Secret `veridicus-pg-app` de la API y la CI usa contraseñas efímeras de los contenedores de servicio |
| Datos de prueba | Solo el catálogo sintético de U1 (NFR12.1) |

## 6. Evidencia por PR

| PR | Evidencia |
|---|---|
| Migración de U5 | Salida del nivel 1 con `alembic upgrade head`, archivo del volcado previo (solo su nombre) y log del `Job` |
| Código de U5 | Resumen de `session-api.yml` (incluidos `guards` y `test-perf`) y de `frontend.yml` |
| Despliegue | Salida de `scripts/smoke.sh`; para la entrega, reporte de `review.spec.ts` |
