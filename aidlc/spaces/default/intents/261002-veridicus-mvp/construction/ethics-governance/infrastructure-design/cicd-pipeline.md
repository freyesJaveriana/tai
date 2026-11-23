# Pipeline de CI/CD — U13 ethics-governance

**Revisión 1 (2026-11-23): primera pasada.** Todo es nuevo.
- U13 no tiene imagen ni *workflow* propios: su código entra en `session-api.yml` (U3), la consola en
  `frontend.yml` (U4) y las plantillas del `Job` en `deploy/jobs/`, que valida `deploy-level0.yml` (U2). Este
  documento fija los *jobs* y pasos que U13 añade a esos *workflows*, sin cambiar sus puertas ni su patrón
  `changes` + `gate`, y el procedimiento con el que el humano lanza el borrado.

**Insumos.** Comandos de `nfr-requirements/tech-stack-decisions.md` (§5) y dependencias (§4); pruebas de
`nfr-design/security-design.md` (security-design §1–§13), `nfr-design/reliability-design.md`
(reliability-design §1–§8), `nfr-design/performance-design.md` (performance-design §6, §7),
`nfr-design/scalability-design.md` (scalability-design §4, §6) y `nfr-design/observability-design.md`
(observability-design §1–§4); guardias y fronteras de `nfr-design/logical-components.md` (logical-components
§6); F7, F8, F10 y E1–E54 de `functional-design/functional-spec.md` (functional-spec); EthicsGovernance en
`inception/domain-design/components.md` (components); C1, C23, C24 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); `cicd-pipeline.md` de U2, U3 y U4;
`infrastructure-specification.md` de esta carpeta; `## Testing Posture` y `## Deployment` de `team.md`.

## 1. *Workflows* y *jobs*

Todos con `permissions: contents: read`, acciones fijadas por SHA, sin `kubeconfig` ni claves; solo el *job*
`build` de cada imagen tiene `packages: write`, y solo en `main`. Las pruebas de los niveles 0 y 1 de U13 no
descargan modelos, no exigen GPU, no salen a la red (`pytest-socket` solo deja PostgreSQL y Redis de la
prueba) y no se reintentan (NFR2.1). Usan **datos sintéticos** de `tests/fixtures/make_ethics_fixtures.py` y
de `contracts/integrity/testimony-warning-cases.v1.yaml`, con PostgreSQL 16 y Redis 7.2 reales en contenedor.
Las pruebas de las guardias (selección y argumentos del `Job`, orquestación por sesión con su acta,
comparación de testimonio, logs sin la nota) y de los contratos C23 y C24 se escriben primero y se ven en rojo
antes de implementar (`team.md`).

| *Workflow* | Rutas que activan el trabajo | *Job* | Comando y umbral (AUTONOMIA-02) | Bloquea |
|---|---|---|---|---|
| `session-api.yml` (de U3) | `services/session-api/**`, `libs/**`, `contracts/**`, `config/**` | `lint` | U13 añade a `uv run --directory services/session-api lint-imports` los contratos `ethics-governance-no-egress`, `ethics-governance-no-metrics` y las fronteras de NFR13.3 (dominio sin `adapters` ni `sqlalchemy`; sin ConsoleApi; InterviewSession solo por `EthicsSessionPort`, HumanReview por su resolvedor y cada unidad por `Purgeable`): 0 violaciones, y cada módulo de control negativo de `tests/import_contracts/` hace fallar su contrato (NFR1.2, NFR13.3, NFR15.1); `mypy --strict` y `ruff check` con 0 errores | Sí |
| | | `test-level0` | `uv run --directory services/session-api pytest -m "not integration and not perf" tests/ethics_governance`: casos de `testimony-warning-cases.v1.yaml` y su lista de espacios (NFR10.6); AST sin cachés ni globales mutables en `testimony.py` y sin `note` en ningún *logger*; reglas de uso ausentes, inválidas, con dos puntos o clave repetida (E9); `--as-of` sin `--dry-run` → código 2 con un *fake* de conexión que falla si se llama (E44); `retention.py` sin `os.environ` para la hora; comando sin escrituras a archivo; OpenAPI sin `DELETE` ni `PUT` y sin rutas de lectura del registro; cada `code` de U13 forzado; migración sin `text` sin `CHECK` ni claves foráneas en `access_log_entry` y `retention_act`; tabla de frontera igual a la del README; ningún bucle de reintento ni `tenacity`; verde | Sí |
| | | `guards` | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards`: U13 suma `ethics_governance/domain/`, `application/retention_run.py`, `retention.py` (argumentos), `domain/testimony.py` y `domain/log_fields.py`; 100 % de ramas (NFR13.2) | Sí |
| | | `test-level1` | `uv run --directory services/session-api pytest -m integration tests/ethics_governance`: nota con *canary* en camino feliz, `413`, `422`, `503` y `CHECK` violado, con el log de PostgreSQL de la prueba arrancado con `log_error_verbosity = terse` (NFR10.5); `gc` sin el *canary* (NFR10.6); permisos de la marca con `veridicus_app` y `veridicus_retention` (NFR11.1, NFR11.2, E48); `FOR UPDATE` directo con `veridicus_retention` falla y la función bloquea (`55P03`); registro con tabla bloqueada en lectura y exportación y adaptador de 600 ms (NFR10.13); fallo en la sesión 2 de 3 (E42); Redis detenido y 0,6 s de latencia (NFR10.18); `SIGKILL` tras la primera de tres (NFR10.20); dos `Job` a la vez → 0 y 3 (NFR10.19); simulación con fecha futura sin cambios (E45); acta y salida sin *canary* (E47); `SELECT current_user` = `veridicus_retention`; dos `PATCH` simultáneas → 1 `retention_change` (NFR3.12); verde | Sí |
| | | `test-perf` | `uv run --directory services/session-api pytest -m perf tests/ethics_governance` (50 repeticiones salvo NFR3.6, mediana y p95; `psutil` y `tracemalloc`) en el *runner* `ubuntu-24.04` de U3: NFR3.1, NFR3.3–NFR3.7 y NFR3.9–NFR3.12, con las cifras de `monitoring-design.md` §3. Una falla inestable va a cuarentena con un *issue*; nunca se reintenta ni se baja el umbral | Sí |
| | | `coverage` | ≥ 80 % de líneas en `services/session-api`, con U13 dentro y sin exclusiones nuevas (NFR13.1) | Sí |
| | | `audit`, `build` | `pip-audit` sin `HIGH`+ con corrección (U13 no suma dependencias de ejecución; `psutil` solo en desarrollo, NFR10.9); Trivy `HIGH`/`CRITICAL` con corrección sobre la imagen que también usa el `Job`; en `main` publica `veridicus-session-api:<sha>` | Sí |
| | | `gate` | Depende de todos los anteriores; única comprobación obligatoria | Sí |
| `frontend.yml` (de U4) | `frontend/**`, `contracts/**` | `test` | U13 añade `frontend/src/features/ethics-governance/` a `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck`: casos compartidos de `testimony.ts` con 100 % de ramas (NFR13.2); 0 peticiones en la comparación y en el recordatorio (`fetch` simulado); desvío del recordatorio ≤ 1 s con reloj simulado; `<img src=x onerror=alert(1)>` en la nota y en un punto de las reglas pintado como texto (NFR10.12); `react/no-danger` como error; literal visible fuera del catálogo = fallo (NFR14.1); escáner de vocabulario de U4 sobre los textos de U13 con las reglas como `notice_text` (NFR11.5); `retry: false` en las tres mutaciones; ≥ 80 % de líneas | Sí |
| | | `audit`, `build`, `gate` | Los de U4, sin cambios (`npm audit --audit-level=high`) | Sí |
| `deploy-level0.yml` (de U2) | `deploy/**`, `scripts/**`, `config/**`, `contracts/limits.v1.yaml`, `.github/**` | Los de U2 | De U13: `helm lint deploy/jobs` y `helm template deploy/jobs` de las dos plantillas, también con `retention.dryRun.asOf`; `kubeconform -strict`; Kyverno `job-shape` (`backoffLimit: 0`, `restartPolicy: Never`, `activeDeadlineSeconds` presente, sin `ttlSecondsAfterFinished`, IDS-U13-02), `retention-job-identity`, `volume-consumers`, `secret-consumers` y la `NetworkPolicy` `retention-job` (NFR1.3, NFR10.11); `check-limits-env.sh` sin `VERIDICUS_LIMIT_RETENTION_MAX_DAYS` (NFRD-U13-10); `check-no-cluster-apply.sh` sin `CronJob` ni lanzamiento del `Job` (E49); `uv run pytest deploy/tests/level0 -k retention_job`: `--as-of` ausente en el borrado aunque se pase el valor (IDS-U13-01), claves de `configMapKeyRef` presentes en el `ConfigMap` y control negativo sin `VERIDICUS_DB_LOCK_TIMEOUT_MS` (IDS-U13-03), mismo digest que `session-api` (IDS-U13-05), mismos montajes y rutas que la API (IDS-U13-06) | Sí |

U13 no tiene puerta de nivel 2: no toca *prompts*, perfiles, adaptadores de modelos ni esquemas de salida del
analizador.

## 2. Nivel 3 y pruebas en el clúster, fuera de la CI

| Prueba | Dónde y cómo | Evidencia |
|---|---|---|
| E2E de U13 | `npx --prefix frontend playwright test e2e/ethics-governance.spec.ts` en WSL2 contra `https://veridicus.local:8443`, con un analista sintético del `.env` no versionado: diálogo y franja, panel con aviso de testimonio, plazo, avisos de bienestar; 0 violaciones `serious` o `critical` de `axe` (BR8.1); NFR3.2 y NFR3.8; escáner de vocabulario sobre el texto renderizado | Reporte de Playwright en el PR de la entrega |
| Humo | `scripts/smoke.sh https://veridicus.local:8443` de U2 tras cada despliegue. U13 no añade casos: `session-api` solo abre el puerto si las reglas de uso y el adaptador de `AccessLog` están bien (reliability-design §3) | Salida de `smoke.sh` en el PR de despliegue |
| Borrado en el clúster (demo de B13) | Procedimiento de §4, solo el humano: simulación con fecha futura, borrado real de una sesión sintética del día anterior con plazo de 1 día y acta con el comando de consulta (F8, FD-U13-09) | Salida de los dos `Job` y del comando, sin texto, pegada en la revisión de B13 |
| Duración del `Job` | Medición de 500 sesiones típicas (marca `perf`) | La cifra y el `activeDeadlineSeconds` resultante en el PR de B13 (IDS-U13-13) |

Nada de esto lo ejecuta un *script* que cambie el clúster: Playwright y `smoke.sh` solo usan HTTP y
`port-forward`, y el `Job` lo aplica el humano.

## 3. Del PR al clúster

| Paso | Qué pasa |
|---|---|
| 1 | PR de U1 con las siete cifras de U13 en C25 (incluida `ethics_body_max_bytes`), C24 v1.1.0 con `count_session` y `testimony-warning-cases.v1.yaml` con `whitespace_code_points`, si aún no están en `main` |
| 2 | PR de U3 que admite `retention_insert` en la marca y fija el conjunto de funciones de `veridicus_retention` en la prueba común (NFRD-U13-04) |
| 3 | **PR de migraciones**, antes que el código: las funciones de bloqueo de U4 y de U7 (en sus migraciones, si no están ya) y las cinco tablas de U13 con sus marcas, `CHECK` e índices. Solo avanzan (*expand–contract*) y corren con el `Job` de migraciones de U2 en su propio PR, nunca al arrancar un pod (`project.md`) |
| 4 | PR de código con `session-api.yml` y `frontend.yml` en verde |
| 5 | En `main`, `build` publica `session-api` y `frontend` por SHA |
| 6 | PR de despliegue con los digests en `values-cpu.yaml` y el mismo digest de `session-api` en `deploy/jobs/` (IDS-U13-05); `deploy-level0.yml` valida los dos renders; la fusión en `main` protegida es la aprobación registrada |
| 7 | Antes del módulo 8, el humano aplica el chart ya fusionado (instalación en dos pasos de U2); después, Argo CD sincroniza `deploy/veridicus`. `deploy/jobs/` nunca se sincroniza |
| 8 | `scripts/smoke.sh`; si falla, reversión de §5 |
| 9 | El borrado, cuando haga falta, con el procedimiento de §4 |

## 4. Borrado: procedimiento del humano (AUTONOMIA-01)

Vive en `docs/operacion/retencion.md` (IDS-U13-11), fuera del alcance de `check-no-cluster-apply.sh` porque
es documentación que lee y ejecuta el humano. Ningún *script*, *workflow* ni Argo CD lo ejecuta.

| Paso | Qué hace el humano |
|---|---|
| 1 | Comprueba que el `main` que va a aplicar es el fusionado y que el digest de `deploy/jobs/` es el de la API desplegada |
| 2 | Si quedó un `Job` anterior con el mismo nombre, lee su salida con `kubectl logs` y lo borra |
| 3 | Renderiza `templates/retention-dry-run.yaml` de `deploy/jobs/` (con `retention.dryRun.asOf` si quiere simular una fecha) y lo aplica; lee el `retention.summary` (código 0, `would_purge` por candidata) |
| 4 | Si lo que vencería es lo esperado, borra el `Job` de simulación, renderiza `templates/retention.yaml` y lo aplica |
| 5 | Lee la salida: código 0 sin `failed`; con 1, lee el `code` de cada `failed` y relanza tras corregir la causa (Redis, base); con 3, espera a que termine la otra ejecución |
| 6 | Comprueba las actas con `kubectl exec deploy/veridicus-session-api -c session-api -- python -m session_api.ethics_governance.query retention-acts --job-run <id>` |
| 7 | Nunca redirige la salida del `Job` ni del comando a un archivo dentro del repositorio (NFR12.2) |

## 5. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` tras desplegar (reglas de uso rotas o tabla sin permiso: la API no abre el puerto) | `git revert` del PR de despliegue en un PR, fusión y nueva aplicación o sincronización (`team.md`). Con `Recreate` (IDS-U7-03) la consola queda caída hasta entonces, riesgo ya aceptado |
| El `Job` termina con 1 | No se revierte nada: lo confirmado ya tiene su acta; se corrige la causa y se relanza (reliability-design §4.4) |
| El `Job` vence `activeDeadlineSeconds` | Lo confirmado queda, lo demás se revierte en la base; se relanza y se mide de nuevo (IDS-U13-13) |
| Un `Job` aplicado con un digest equivocado | Lo impide la prueba de IDS-U13-05; si ocurre, el humano lo borra antes de que termine y relanza con lo fusionado. Una sesión confirmada no se recupera salvo desde el último respaldo |
| Una migración | Solo avanza; se corrige con una migración nueva |
| Un archivo borrado en una transacción que se revirtió | La siguiente ejecución termina la sesión con `file_missing: true` (E43) |

## 6. Secretos en CI/CD

- U13 usa `veridicus-db-retention` solo en el `Job` y `veridicus-redis-auth` como archivo; los crea el humano
  con `scripts/create-secrets.sh` de U2 desde su `.env`. La API sigue con `veridicus-db-app`.
- La CI no tiene ningún Secret del clúster; las pruebas de nivel 1 usan contraseñas efímeras de los
  contenedores de prueba, generadas en el propio *job*, y crean los roles `veridicus_app` y
  `veridicus_retention` con las mismas marcas que la migración.
- Las credenciales del analista sintético de la E2E viven en el `.env` no versionado del humano.
- `gitleaks` (`secrets-scan.yml` de U2) corre en todo PR.

## 7. Correspondencia con AUTONOMIA

| Regla | Comprobación | Dónde |
|---|---|---|
| AUTONOMIA-01 | `check-no-cluster-apply.sh` de U2: 0 apariciones, sin `CronJob` (E49); `deploy/jobs/` fuera de la `Application`; el `Job` solo en el runbook; la consulta en la lista cerrada; migración en su `Job` y su PR | `deploy-level0.yml`; §3 y §4 |
| AUTONOMIA-02 | Cada *job* nombra su comando y su umbral (§1, §2) | Este documento |
| AUTONOMIA-03 | Textos de U13 del catálogo con el escáner de vocabulario (nivel 0) y sobre el texto renderizado (nivel 3); ninguna categoría es una etiqueta de veracidad | `frontend.yml`; E2E |
| AUTONOMIA-04 | `ethics-governance-no-egress` con su control negativo; la `NetworkPolicy` `retention-job` sin salida a internet; nota sin salir de su columna; claves de cancelación antes del borrado | `session-api.yml` (`lint`, `test-level1`); `deploy-level0.yml` |
| AUTONOMIA-05 | No aplica: U13 no emite hallazgos | — |
