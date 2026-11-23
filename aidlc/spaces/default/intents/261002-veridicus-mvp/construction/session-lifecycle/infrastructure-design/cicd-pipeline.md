# Pipeline de CI/CD — U6 session-lifecycle

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Salen la marca de lote y sus casos de reenvío, la versión de escenario, el plazo por
  turno, el nivel 2 por `port-forward` (`golden.run --paste-parity`, `golden.paste_max`), la comparación de
  los tres ajustes entre perfiles y la referencia a `ai-eval-gate.yml`. Entran la importación, el modo
  final, la pausa, la terminación, la retirada, la cancelación, los dos módulos guardia y la medición a
  demanda del modo final (NFR3.17).
- **Numeración.** §1–§5 conservan su tema; §6 (nueva) es la correspondencia con AUTONOMIA.

**Insumos.** Comandos de `nfr-requirements/tech-stack-decisions.md` (§5); calidad, cobertura y textos de
`nfr-design/logical-components.md` (logical-components §5); pruebas de `nfr-design/security-design.md`
(security-design §1–§7, §10–§12), `nfr-design/reliability-design.md` (reliability-design §1–§4, §6, §8–§12),
`nfr-design/performance-design.md` (performance-design §1–§4, §6, §8–§10), `nfr-design/scalability-design.md`
(scalability-design §1, §2, §4, §6) y `nfr-design/observability-design.md` (observability-design §1, §2);
escenarios E4–E47 de `functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C1, C2, C6, C11, C15 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); `cicd-pipeline.md` de U2, U3 y U4;
`infrastructure-specification.md` de esta carpeta; `## Testing Posture` y `## Deployment` de `team.md`.

U6 **no crea *workflows* ni comprobaciones obligatorias nuevas**: añade pruebas a `session-api.yml` (U3) y a
`frontend.yml` (U4), un archivo de prueba a la suite de `deploy-level0.yml` (U2) y dos *scripts* que el humano
lanza. Todos siguen con `permissions: contents: read`, acciones fijadas por SHA, sin `kubeconfig` ni claves de
proveedores, y con `packages: write` solo en el *job* `build` sobre `main`.

## 1. Etapas de *build* y prueba

Ninguna prueba de los niveles 0 y 1 descarga un modelo, llama a un proveedor, exige GPU ni se reintenta
(NFR2.1): el analizador es el *fake* de C17; PostgreSQL 16 (imagen oficial, sin `pgvector`) y Redis 7.2 son
reales en contenedor, por digest. Las pruebas de las guardias (tabla de transiciones, admisión y cancelación,
AUTONOMIA-04 y -05) y de los contratos (C1 de U6, C2 por `RunEnqueuer`, C6 de la importación, C25) se escriben
primero y se ven en rojo antes de implementar (`team.md`).

| *Workflow* | Rutas que lo activan | *Job* | Qué añade U6 (comando y umbral en §2) | Bloquea |
|---|---|---|---|---|
| `session-api.yml` (U3) | `services/session-api/**`, `libs/**`, `contracts/**`, `db/**` | `lint` | `lint-imports` con el contrato que prohíbe a los módulos de U6 importar la biblioteca de U11, la ingesta o `veridicus:results` (NFR10.7); `mypy --strict` y `ruff` | Sí |
| | | `test-level0` | División con los ejemplos de `speaker-markers.v1.yaml` y Hypothesis; cifras de C25 sin literales; cada cifra en el límite y en el límite + 1; reglas de arranque con código de salida y su control positivo (NFRD-U6-09); OpenAPI de C1 sin `status` en los cuerpos; `code` de cada `409`, `413`, `415` y `422` con su estado; escáner de vocabulario sobre el catálogo de U6; datos sintéticos de U1 sobre los *fixtures* | Sí |
| | | `guards` | `session_transitions.py` y `run_admission.py` se suman a `.coveragerc-guards` de U4 con 100 % de ramas (NFR13.1) | Sí |
| | | `test-level1` | Pegado todo o nada (fallo tras el turno 1 000), reenvío antes del estado, dos envíos a la vez, Redis detenido tras el `COMMIT`; importación sin disco (directorio temporal vigilado), con claves duplicadas, profundidad > 32, *canary* en cada campo y consentimiento; modo final simultáneo; cancelación con 0 llamadas nuevas del *fake* tras pausar, terminar o retirar y con Redis cortado al escribir la clave; dos supervisores, bordes de 165, 179, 180 y 210 s; pares concurrentes con 0 `40P01`; permisos de solo inserción y `DELETE` solo para `veridicus_retention`; prueba centinela en logs y Problem Details; raspado de los dos `/metrics`; reconstrucción de una sesión por sus logs; equivalencia escrito, pegado e importado | Sí |
| | | `test-perf` | NFR3.1–NFR3.4, NFR3.9, NFR3.13, NFR3.15 y NFR3.16 con el pico de RSS de NFR8.1, en el *runner* de IDS-U3-09 | Sí |
| | | `coverage` | ≥ 80 % de líneas en `services/session-api` con U6 incluido | Sí |
| `frontend.yml` (U4) | `frontend/**`, `contracts/**` | `test` | Vista previa con los mismos ejemplos que `pytest` (≤ 300 ms con 250 000 caracteres, 0 peticiones); Web Worker de la importación con ajv de `contracts/ts/` (≤ 1 500 ms con 2 MiB, hilo principal sin retraso > 100 ms, 0 peticiones); cuenta de ventanas con los ejemplos de U11; progreso con temporizadores falsos; `aria-disabled` con motivo y `aria-live`; literal visible fuera del catálogo = fallo; ≥ 80 % de líneas | Sí, por `frontend / gate` |
| `deploy-level0.yml` (U2) | `deploy/**`, `scripts/**`, `config/**`, `contracts/limits.v1.yaml`, `.github/**` | Paso 8 y paso 10 | `promtool test rules` de las reglas de U6 (§2 de `monitoring-design.md`); `deploy/tests/level0/test_session_lifecycle_limits.py` (IDS-U6-04) con su control negativo; `check-ingress-limits.sh` ya cubre `import_body_max_bytes`; `check-no-cluster-apply.sh` con `evaluation/session_lifecycle/` en su alcance (petición IDS-U6-05) | Sí |
| `ai-eval-gate.yml` | — | — | **Retirado** en U4 (IDS-U4-12). U6 no toca *prompts*, perfiles, adaptadores ni esquemas de salida, así que no dispara `analyzer-level2-gate.yml` de U11 | — |

## 2. Puertas con comando y umbral (AUTONOMIA-02)

| Gate | Comando | Umbral | Requisitos |
|---|---|---|---|
| Nivel 0 | `uv run --directory services/session-api pytest -m "not integration and not perf"` | Verde | NFR8.3, NFR10.1, NFR10.6, NFR10.8, NFR10.10, NFR10.14, NFR12.1, NFR13.2 |
| Guardias | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % de ramas en `session_transitions.py` y `run_admission.py` | NFR13.1 |
| Nivel 1 | `uv run --directory services/session-api pytest -m integration` | Verde | NFR1.1, NFR1.3, NFR1.4, NFR4.1, NFR8.2, NFR8.6, NFR8.8–NFR8.11, NFR10.1–NFR10.7, NFR10.11–NFR10.18, NFR11.1–NFR11.3, NFR15.2–NFR15.5 |
| Rendimiento | `uv run --directory services/session-api pytest -m perf` | p95 de `monitoring-design.md` §3; una corrida, sin reintentos; cuarentena con *issue* si es inestable | NFR3.1–NFR3.4, NFR3.7, NFR3.9, NFR3.13, NFR3.15, NFR3.16, NFR8.1 |
| Cobertura | `uv run --directory services/session-api pytest --cov --cov-fail-under=80`; `npm --prefix frontend run test -- --coverage` | ≥ 80 % de líneas en cada uno | NFR13.1 |
| Consola | `npm --prefix frontend run typecheck` y Vitest | 0 errores; 100 % de los ejemplos de división y de los *fixtures* de importación | NFR1.2, NFR3.6, NFR3.12, NFR3.14, NFR13.2, NFR14.1 |
| Tipos y fronteras | `mypy --strict`, `ruff check` y `lint-imports` en `services/session-api` | 0 errores | NFR10.7; `team.md` |
| Auditoría | `pip-audit`, `npm audit`, `gitleaks`, Trivy | 0 `HIGH`+ con corrección; 0 secretos | `team.md` |
| Render y reglas | `helm template` → `kubeconform` → Kyverno CLI, `promtool test rules` y `uv run pytest deploy/tests/level0` en `deploy-level0.yml` | Verde; cada control negativo falla como se espera | NFR10.10, NFR15.1 |
| Nivel 3 (fuera de la CI) | `npx --prefix frontend playwright test e2e/session-lifecycle.spec.ts` contra `https://veridicus.local:8443` | 0 violaciones `serious`/`critical` de axe; 0 coincidencias de vocabulario prohibido; flujos solo con teclado; cambio de etapa visible ≤ 3 s | NFR3.12, NFR10.8, NFR14.2 |
| Carga (fuera de la CI) | Sección de U6 en `uv run --directory evaluation python -m load.run_batches …` de U4 | p95 de `/transcript`, sondeo y `/final-runs`; 0 respuestas 5xx; 0 suspensiones de sesiones sondeadas; falla si falta la sección | NFR8.13, NFR8.14 |
| Modo final máximo (a demanda) | `uv run --directory evaluation python -m session_lifecycle.final_run_max --profiles comercial-piloto,todo-local --report out/final-run-max.json` | Una sección por perfil; falla si falta una; la revisión humana compara duración y plazo | NFR3.17 |

Los dos últimos los lanza el humano en WSL2 contra la API por `https://veridicus.local:8443`, con el
analista sintético del `.env` y solo datos sintéticos (IDS-U6-06); solo usan HTTP y no cambian el clúster.
Sus reportes llevan solo cifras y se adjuntan al PR que los motiva o al de la entrega etiquetada.

## 3. Del PR al clúster

| Paso | Qué pasa | Aprobación |
|---|---|---|
| 1 | PR de U1 con `transcript_body_max_bytes`, `import_body_max_bytes`, `session_sweep_interval_s` y `heartbeat_write_min_s` en `contracts/limits.v1.yaml`, `speaker-markers.v1.yaml`, las métricas de `session-lifecycle.v1.yaml` y los `code` nuevos de C1 (NFRD-U6-01, FD-U6-01, FD-U6-02) | Fusión del PR |
| 2 | PR de migraciones de U6 (§2.1 de `infrastructure-specification.md`), después de la de U4; solo aditivas | Fusión del PR |
| 3 | PR de código de U6 (B7) con `session-api.yml` y `frontend.yml` en verde | Fusión del PR |
| 4 | En `main`, `build` publica `session-api` y `frontend` por SHA | Automático, sin clúster |
| 5 | PR de despliegue: digests nuevos en `values-cpu.yaml`, la fila del panel y las reglas de U6; `deploy-level0.yml` valida el render | Fusión del PR |
| 6 | Antes del módulo 8, el humano aplica lo fusionado con la instalación en dos pasos de U2 (migraciones primero); después, Argo CD sincroniza con el `Job` de migraciones como *hook* `Sync`. La API rueda con `RollingUpdate`; el trabajador se reemplaza con `Recreate` | La fusión del paso 5 |
| 7 | `scripts/smoke.sh https://veridicus.local:8443` y, antes de etiquetar, `e2e/session-lifecycle.spec.ts`; salida adjunta al PR | — |

Ningún paso de un plan de tareas ejecuta `kubectl apply`, `helm install`, `helm upgrade` ni una migración sin
la fusión previa del PR (AUTONOMIA-01).

## 4. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la E2E tras desplegar | `git revert` del PR de despliegue en un PR, fusión y nueva aplicación o sincronización; la migración aditiva se queda (el código anterior ignora la tabla y las columnas nuevas) |
| Una cifra de U6 fuera de regla | El pod no pasa a listo y el `RollingUpdate` de la API conserva el anterior; en el trabajador (`Recreate`) la revisión se retrasa sin perder suspensiones; se corrige con `git revert` del PR de U1 o de despliegue |
| La migración | Solo avanza; se corrige con una migración nueva (*expand–contract*) |
| El modo final máximo pasa de su plazo (NFR3.17) | PR que ajusta el perfil o el plazo (U11), o demostración con transcripciones más cortas (IDS-U6-08); nunca subir una cifra de C25 en silencio |
| Corridas de U6 cuya publicación falló | El supervisor de U4 las cierra en `error` ≤ 30 s tras `deadline_at`; el analista reintenta desde la consola |

## 5. Entornos y secretos

| Aspecto | Diseño |
|---|---|
| Entornos | CI (contenedores PostgreSQL 16 sin `pgvector` y Redis 7.2 por digest, iguales a U2) y la única máquina de 64 GB con `values-cpu.yaml`; mismas imágenes por SHA. Sin archivo de valores GPU (IDS-U2-02) |
| Secretos en la CI | Ninguno del clúster. Las pruebas de nivel 1 usan contraseñas efímeras del contenedor; los roles `veridicus_app` y `veridicus_retention` se crean en cada corrida para probar permisos |
| Secretos en el clúster | U6 no añade ninguno: usa `veridicus-db-app` y `veridicus-redis-auth` por `secretKeyRef` (IDS-U4-10). Las credenciales del analista sintético de `final_run_max.py` y `run_batches.py` viven en el `.env` no versionado |
| Datos | Bloques, archivos de importación y ejemplos de división sintéticos del catálogo de U1; las entrevistas del piloto solo se importan en el Minikube local, nunca en Git ni en la CI (`project.md`) |

## 6. Correspondencia con AUTONOMIA · nuevo

| Regla | Comprobación | Dónde |
|---|---|---|
| AUTONOMIA-01 | Migración en su `Job` y su PR; `check-no-cluster-apply.sh` con `evaluation/session_lifecycle/` (IDS-U6-05); la CI sin `kubeconfig` | `deploy-level0.yml`; §3 |
| AUTONOMIA-02 | Cada puerta nombra su comando y su umbral | §2 |
| AUTONOMIA-03 | Escáner sobre el catálogo (nivel 0) y la interfaz renderizada (nivel 3); historial con actor y hora; retirada con quién y cuándo | `session-api.yml`, `frontend.yml`, E2E |
| AUTONOMIA-04 | Importación sin disco; consentimiento y transferencia antes de crear filas; 0 llamadas nuevas tras pausar, terminar o retirar; ningún destino nuevo en la `NetworkPolicy` | `session-api.yml` (`test-level1`); `deploy-level0.yml` |
| AUTONOMIA-05 | Corridas de U6 solo por `RunEnqueuer` y la ingesta de U4, con import-linter; una cita alterada en un modo final no crea sugerencia | `session-api.yml` (`lint`, `test-level1`) |
