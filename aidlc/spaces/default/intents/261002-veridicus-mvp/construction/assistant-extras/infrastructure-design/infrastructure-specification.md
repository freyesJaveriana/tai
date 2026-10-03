# Especificación de infraestructura — U8 assistant-extras

**Insumos.** Presupuestos por tramo, plazo base y reclamo con extras de
`nfr-design/performance-design.md` (performance-design); frontera, *prompt* y lista inmutables,
autorización e integridad de `nfr-design/security-design.md` (security-design); capacidad con extras y
memoria sin cambios de `nfr-design/scalability-design.md` (scalability-design); *timeouts*, fallos del
juez por llamada y validación al arrancar de `nfr-design/reliability-design.md` (reliability-design);
métricas y reglas informativas de `nfr-design/observability-design.md` (observability-design);
inventario, recursos compartidos y entrega a Infrastructure Design de
`nfr-design/logical-components.md` (logical-components); flujos F1–F3 de
`functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C1–C3, C6, C8, C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); ajustes y D1–D10 de
`nfr-requirements/tech-stack-decisions.md`; respuesta **P1 = A** de `infrastructure-design-questions.md`
(`values-extras.yaml` fijo en la máquina de demostración tras el PR con el reporte de nivel 2; la
máquina de desarrollo nunca lo incluye); infraestructura de U2, U3 y U4 (sus
`infrastructure-specification.md`).

U8 no pone procesos nuevos en el clúster: añade pasos dentro de `semantic-agent` y de la API y el
trabajador de `session-api` (U4), dos `ConfigMap` de solo lectura, un archivo de *values* para los
extras y una migración de dos tablas. Con los extras apagados —como queda siempre la máquina de
desarrollo— el despliegue de U4 no cambia en nada.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Sin `Deployment`, réplicas, puertos ni imágenes nuevas: el código de U8 viaja en las imágenes `semantic-agent` y `session-api` de U4 | logical-components §4; scalability-design §1 (la capacidad la fija la ranura única del juez) |
| Activación (P1 = A) | Archivo `deploy/veridicus/values-extras.yaml` que se suma **solo** a `values-gpu.yaml` en la `Application` de la máquina de demostración. Lleva únicamente las banderas de los extras cuyo reporte de nivel 2 cumplió sus umbrales (§1.1), más el plazo y el reclamo de §1.2 y el tiempo del humo | NFR10.9 y NFR11.4 (activación solo por despliegue y versionada); NFR8.1 y NFR3.12 (la carga y el humo de la máquina de desarrollo con extras apagados) |
| *Values* base | `VERIDICUS_EXTRAS_PERMUTATION`, `_SUGGEST_QUESTION` y `_AFFECTIVE` en `"false"` en `values-cpu.yaml` y `values-gpu.yaml`; sin valor por defecto en el código (falta el ajuste → el pod no arranca) | tech-stack-decisions D8; team.md (configuración faltante impide arrancar) |
| *Prompt* de la pregunta | `deploy/veridicus/charts/semantic-agent/files/suggest-question.v1.md` → `ConfigMap` `veridicus-semantic-agent-question-prompt`, montado `readOnly` en `/etc/veridicus/question-prompt/`; `VERIDICUS_QUESTION_PROMPT_SHA256` en los *values* | security-design §3 (NFR10.3, NFR5.2); mismo patrón del *prompt* del juez de U4 (Helm solo lee archivos del chart) |
| Lista afectiva | `deploy/veridicus/charts/semantic-agent/files/affective-keywords.v1.yaml` → `ConfigMap` `veridicus-semantic-agent-affective`, montado `readOnly` en `/etc/veridicus/affective/` | tech-stack-decisions D7; precisión en §6 por el cambio de ruta |
| Validación al arrancar | `semantic-agent` valida siempre el SHA-256 del *prompt* y la lista (aunque los extras estén apagados); `session-api` valida las banderas y la regla de plazo y reclamo; si falla, termina y `/readyz` responde `503` | reliability-design §4 (NFR10.14); sondas de U4 sin cambios |
| Recursos | Los `requests` y `limits` de U4 no cambian: juez 3 / 6 CPU y 7 / 8,5 GiB, `semantic-agent` 0,25 / 1 CPU y 384 / 640 MiB, trabajador 0,5 / 1,5 CPU y 512 / 960 MiB | scalability-design §2 (NFR8.3): los extras no suben picos; el margen del 20 % ya está en U4 |
| Máquinas | Desarrollo: Minikube con 20 GiB y 10 CPU, `values-cpu.yaml`, **nunca** `values-extras.yaml`. Demostración (32 GB): Minikube con 28 GiB, `values-gpu.yaml` + `values-extras.yaml` | P1 = A; decisiones de U4 (P1, P2) |
| Almacenamiento | Tablas `suggested_question` y `question_decision` en `veridicus-pg` (PVC de 10 GiB de U2); < 5 MB en el MVP, sin particiones ni purga | scalability-design §4 (NFR8.5) |
| IaC | Chart paraguas `deploy/veridicus` de U2; el humano aplica o Argo CD sincroniza tras la fusión del PR | team.md; AUTONOMIA-01 |
| Estrategia | `RollingUpdate` de U4; activar o apagar un extra es un PR de *values* que reinicia `session-api` y `semantic-agent` | Las opciones se copian a la sesión al crearla: las sesiones en curso conservan las suyas (NFR10.9) |

### 1.1 Qué extras entran en `values-extras.yaml`

Cada bandera se pone en `"true"` solo si el reporte de nivel 2 adjunto al PR, corrido en CPU con
`--extras` sobre ese extra (NFR2.2), cumple sus umbrales; `scripts/check-eval-report.py` lo comprueba
(`cicd-pipeline.md` §2).

| Extra | Umbrales para encenderlo | Requisitos |
|---|---|---|
| `permutation` | Umbrales de NFR4 de team.md con las dos lecturas; tasa en línea `sustained / candidatas` > 65 %; detección sin bajar de la de U4; Escenario A con el mismo conjunto de alertas sostenidas | NFR4.1, NFR4.3, NFR4.4, NFR5.1 |
| `suggest_question` | 0 preguntas en el caso de Hecho No Documentado; 0 preguntas marcadas por idioma; 0 publicadas con texto de inyección; omisiones por vocabulario listadas y revisadas | NFR4.3, NFR14.2, NFR5.1, NFR10.5 |
| `affective` | Repetibilidad de NFR4.5 (mismos turnos con indicio en dos corridas) | NFR4.5, NFR10.10 |
| Cualquiera | p95 ≤ 150 s, 0 `turn.error.timeout`, picos de memoria dentro de los topes de U4, `model_digest` igual en las tres llamadas, dos corridas idénticas | NFR3.1, NFR8.7, NFR8.3, NFR5.2, NFR4.5 |

### 1.2 Ajustes de `values-extras.yaml`

| Ajuste | Valor | Procesos | Requisito |
|---|---|---|---|
| `VERIDICUS_EXTRAS_*` | `"true"` solo para los extras aprobados en §1.1 | `session-api` | NFR10.9 |
| `VERIDICUS_TURN_DEADLINE_BASE_SECONDS` | 600 | API y trabajador | NFR3.6 (peor caso 482,2 s) |
| `VERIDICUS_QUEUE_RECLAIM_IDLE_SECONDS` | 510 | Trabajador y `semantic-agent` | NFR3.7 |
| `VERIDICUS_QUESTION_TIMEOUT_SECONDS`, `VERIDICUS_QUESTION_MAX_TOKENS` | 60 y 160 (también en los *values* base, porque se validan siempre) | `semantic-agent` | NFR10.11, NFR3.5 |
| `smoke.timeoutSeconds` | 300 (120 en los *values* base) | `scripts/smoke.sh --values …` | NFR3.12 |

```yaml
# deploy/veridicus/values-extras.yaml (ilustrativo)
sessionApi:
  env:
    VERIDICUS_EXTRAS_SUGGEST_QUESTION: "true"
    VERIDICUS_EXTRAS_AFFECTIVE: "true"
    VERIDICUS_EXTRAS_PERMUTATION: "false"   # hasta que su reporte pase §1.1
    VERIDICUS_TURN_DEADLINE_BASE_SECONDS: "600"
    VERIDICUS_QUEUE_RECLAIM_IDLE_SECONDS: "510"
semanticAgent:
  env:
    VERIDICUS_QUEUE_RECLAIM_IDLE_SECONDS: "510"
smoke:
  timeoutSeconds: 300
```

## 2. Servicios de infraestructura

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-judge` (U2) | other | La ranura única de U4: segunda lectura con el mismo `system` y `cache_prompt: true`, pregunta con su propio `system`; hasta 3 llamadas en serie por turno; temperatura 0 y `seed` 20261002 | NFR3.3, NFR4.5; reintento acotado solo en la segunda lectura (NFR10.12) |
| `veridicus-pg` (U2) | database | Tablas `suggested_question` (restricción única `(turn_id, attempt)`, índice `(session_id, change_seq)`, `GRANT UPDATE (status, decided_by, decided_at)`, disparador `BEFORE UPDATE` que rechaza cambios fuera de `proposed`, sin `DELETE`) y `question_decision` (solo `INSERT` y `SELECT` para `veridicus_app`); columnas `forward_grade`, `reversed_grade` y `sustained` de solo inserción en la evaluación de la afirmación | NFR11.1–NFR11.3, NFR8.5, NFR3.9; sin roles nuevos ni conexiones nuevas (pools de U4) |
| `veridicus-redis` (U2) | queue | Sin colas nuevas: `options` viaja en C2 y la pregunta, el indicio y la permutación en C3 | NFR8.4; los 384 MB `noeviction` de U2 no cambian |
| `migrations-job` (U2) | other | Migración Alembic de las dos tablas, el disparador y los permisos por columna, en su propio PR antes del código | team.md; project.md (nunca al arrancar un pod) |
| `ConfigMap` del *prompt* de la pregunta y de la lista afectiva | other | Montados `readOnly`; cambian solo por PR (el del *prompt* con reporte de nivel 2) | NFR10.3, NFR10.10, NFR11.4 |
| `veridicus-embeddings`, `cdn`, `search`, `load-balancer` | — | No aplica | U8 no calcula *embeddings* nuevos ni expone rutas fuera del `Ingress` de U2 |

## 3. Red y frontera (AUTONOMIA-04)

U8 no añade destinos (NFR1.1): la configuración de U8 no tiene campos de URL y las llamadas usan el
`ModelGateway` y `VERIDICUS_JUDGE_URL` de U4. La `NetworkPolicy` de U2 y U4 no cambia, y la lista
blanca de CoreDNS que fija U10 tampoco necesita entradas de U8 (NFR1.2).

| Componente | Proceso | Dentro o fuera del clúster | Qué datos cruzan su frontera | Hacia dónde |
|---|---|---|---|---|
| `PermutationStep` y `permutation.py` | `semantic-agent` | Dentro, bajo `deny-external-egress` | Afirmaciones candidatas y sus pasajes | `veridicus-judge` (interno) |
| `QuestionStep` y `question_policy.py` | `semantic-agent` | Dentro | Texto del turno y pasajes recuperados; la pregunta vuelve en C3 | `veridicus-judge` y `veridicus-redis` (internos) |
| `AffectiveNoteDetector` | `semantic-agent` | Dentro | Nada | — |
| `QuestionIngest` | `session-api-worker` | Dentro | Resultado C3 con la pregunta | `veridicus-pg` (interno) |
| `QuestionDecisionService` y ruta `POST /questions/{id}/decision` | `session-api` (API) | Dentro | Pregunta y su estado hacia el analista dueño | Navegador por el `Ingress` TLS de U2 |
| Tarjeta de la pregunta (M4) | `frontend`, ejecutada en el navegador | Fuera (equipo del analista), como toda la consola | Solo lo que devuelve ConsoleApi | ConsoleApi |
| `ConfigMap` del *prompt* y de la lista | Montados en `semantic-agent` | Dentro | Nada | — |

| Verificación | Cómo | Cuándo |
|---|---|---|
| Sin campos de URL en la configuración de U8 | Prueba de nivel 0 sobre el `BaseSettings` | Cada PR |
| Política de red sin cambios | El render de `values-gpu.yaml` + `values-extras.yaml` pasa las mismas políticas Kyverno que el de `values-gpu.yaml` | Cada PR de `deploy/` |
| Salida denegada con los extras activos | Verificación manual de U2 y U4 repetida en la máquina de demostración, con `/readyz` de `semantic-agent` en `200` | Antes de la sustentación |

## 4. Recursos compartidos

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| Ranura única de `veridicus-judge` | U2 | U4, U8 | Un turno a la vez; las llamadas de U8 van en serie dentro del turno de U4 |
| `semantic-agent` | U4 | U8 | Pasos de U8 en `application/` y `domain/` propios; mismo consumidor de C2 |
| `session-api` y `session-api-worker` | U3 y U4 | U8 | Capas e import-linter; transacción corta de decisión; ingesta en la transacción de U4 |
| `veridicus-pg` | U2 | Todas | Tablas de U8 con permisos por columna y de solo inserción |
| `frontend` | U4 | U8 (tarjeta en M4) | Una sola imagen; textos del catálogo de U1 |
| `values-extras.yaml` | U8 | Solo la `Application` de la máquina de demostración | Cambia solo por PR con reporte de nivel 2; la de desarrollo no puede incluirlo (`cicd-pipeline.md` §1) |
| Prometheus y Grafana | U2 | U4, U8 | Métricas en el puerto 8081 que ya recoge el `ServiceMonitor` de U4 |

## 5. Capacidad con los extras activos

| Configuración | p95 por turno | Turnos en cola sin vencer | Límite declarado |
|---|---|---|---|
| Extras apagados (desarrollo) | ≤ 60 s | 60 | El de U4 |
| Extras de `values-extras.yaml` (demostración) | ≤ 150 s en CPU; menor con el juez en GPU | 24 | Una sesión a la vez con extras (scalability-design §1) |

Si `veridicus_turn_queue_depth` pasa de 20 con extras activos, el orden de respuesta es: apagar la
permutación por PR, usar el perfil GPU y, por último, la segunda pareja juez + `semantic-agent` de U4
(scalability-design §5). Ninguna medida sube el tope de 3 600 s.

## 6. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado ni de otra unidad; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `assistant-extras/nfr-requirements/tech-stack-decisions.md` (D7) | La lista afectiva vive en `deploy/veridicus/charts/semantic-agent/files/affective-keywords.v1.yaml` y no en `contracts/integrity/`, porque Helm solo publica en un `ConfigMap` archivos dentro del chart; `libs/integrity_policy` y las pruebas la leen desde esa ruta, y la comprobación de esquema de U1 apunta allí. Una sola copia | Mismo criterio que el *prompt* del juez en U4 |
| `assistant-extras/nfr-requirements/tech-stack-decisions.md` (D4) | El *prompt* `suggest-question.v1.md` vive en `deploy/veridicus/charts/semantic-agent/files/` | Ídem |
| `assistant-extras/nfr-design/logical-components.md` §4 | El juego de *values* de extras es `values-extras.yaml`, sumado solo a `values-gpu.yaml` en la máquina de demostración, y lleva únicamente los extras que pasaron su reporte | P1 = A |
| `platform/infrastructure-design/cicd-pipeline.md` §4.2 y §7 | Dos `Application` (`veridicus-dev` con `values-cpu.yaml`, `veridicus-demo` con `values-gpu.yaml` + `values-extras.yaml`) en vez de una; la CI renderiza también la combinación con extras | P1 = A |
| `assistant-extras/nfr-design/performance-design.md` §5 | El tiempo del humo con extras (300 s) se lee de `smoke.timeoutSeconds` en los *values* que recibe `scripts/smoke.sh --values`, en vez de una variable del *job* | P1 = A |
| `platform/infrastructure-design/monitoring-design.md` | Los *values* de Prometheus de cada máquina fijan la etiqueta externa `cluster` (`dev` o `demo`) que usa la regla `VeridicusExtrasOnDevMachine` | P1 = A; `monitoring-design.md` §2 de esta carpeta |
| `text-flow/infrastructure-design/cicd-pipeline.md` §1 y `platform/infrastructure-design/cicd-pipeline.md` §2 | `ai-eval-gate.yml` amplía su filtro de rutas con los archivos de U8 (incluida la lista afectiva y `values-extras.yaml`), y `deploy-level0.yml` añade el render con extras y `scripts/check-extras-values.py` | `cicd-pipeline.md` §1 de esta carpeta |
