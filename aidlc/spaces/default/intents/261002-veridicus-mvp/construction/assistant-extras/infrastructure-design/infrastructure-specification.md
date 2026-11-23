# Especificación de infraestructura — U8 assistant-extras

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** La revisión 1 encendía tres extras (segunda lectura del juez, pregunta sugerida e indicio
  afectivo) con `values-extras.yaml` en una máquina de demostración aparte. Ahora U8 entrega dos cosas:
  - las **aclaraciones neutras**, que la biblioteca arma sin llamar a ningún modelo;
  - la **permutación del verificador**, activa en todos los perfiles de `config/profiles.yaml`.

  Ninguna de las dos se enciende por despliegue. Con eso salen `values-extras.yaml`, los dos `ConfigMap`,
  las banderas y la regla de plazo y reclamo (IDS-U8-01).
- **Numeración.** §1–§5 conservan su tema. §1.1 y §1.2 quedan «Retirado». La tabla de precisiones de la
  revisión 1 (§6) se retira entera y la sustituye la tabla IDS-U8-01 a IDS-U8-12 (§8). Lo nuevo empieza en
  §7, y §9 cierra los hallazgos de `reviews/review-01.md`.
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU, sin máquina GPU, con Minikube de 50 GiB y
  16 CPU, como decidió U2 (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna en esta pasada (`infrastructure-design-questions.md`, sección del 2026-11-23).

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 2):
  - performance-design §1, §3–§6 y §8;
  - security-design §1–§7 y la tabla NFRD-U8-01 a NFRD-U8-12;
  - scalability-design §1–§5;
  - reliability-design §1, §4, §5, §7, §9 y §10;
  - observability-design §1–§4;
  - logical-components §1–§5.
- `functional-design/functional-spec.md` (functional-spec): F4–F9 y la frontera AUTONOMIA-04 de §1.
- InterviewSession, AnalysisWorker, ConsoleApi y la tabla de fronteras de
  `inception/domain-design/components.md` (components).
- C1, C3, C6, C8, C15, C16, C19 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- `nfr-requirements/tech-stack-decisions.md`: D3, D8, D9, D11–D14, §2, §4 y §5.
- Infrastructure Design revisión 2 de otras unidades:
  - U2: §1, §2, §4, §5, §7 e IDS-U2-01 a IDS-U2-15;
  - U4: §1, §1.1, §2, §3 e IDS-U4-01 a IDS-U4-15;
  - U11: `cicd-pipeline.md` §2, §4, §5 e IDS-U11-04 a IDS-U11-09.
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

U8 **no pone procesos nuevos en el clúster**. Su código viaja en tres imágenes de U4:
- `libs-incoherence-analyzer`, dentro de `semantic-agent`;
- `session-api`, con la API y el trabajador;
- `frontend`.

Lo único que U8 añade al despliegue es una migración de dos tablas, dos contadores en el puerto `metrics` y
dos paneles.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Sin `Deployment`, réplicas, puertos ni imágenes nuevas. `validate_clarifications` corre dentro de `analyze` de U11, en `veridicus-semantic-agent` y en la CLI. `ClarificationIngest` corre en `veridicus-session-api-worker`, y la decisión en la API `veridicus-session-api` | logical-components §1 y §4; scalability-design §1 (una corrida a la vez, U4) |
| Activación | **Ninguna por despliegue**. Las aclaraciones salen siempre en modo incremental con `estado: ok`. La permutación vive en `config/profiles.yaml` (`permutation: true` en todos los perfiles), que U2 monta como `ConfigMap` `veridicus-profiles` | D8; security-design §3 (NFR10.9); F8 |
| *Values* | Ningún ajuste propio en `values-cpu.yaml`: U8 no tiene variables `VERIDICUS_*` (tech-stack-decisions §2). `values-extras.yaml` y `values-gpu.yaml` quedan **Retirado** (IDS-U8-01, IDS-U2-02) | tech-stack-decisions §2 |
| Regla `neutral-clarification` | Viaja en el paquete `veridicus_contracts` **dentro de las imágenes** de `semantic-agent` y `session-api`. Se carga al arrancar con el cargador seguro de U1, sin ruta del disco ni `ConfigMap` | security-design §3; NFRD-U8-12 |
| Validación al arrancar | `semantic-agent`, la API y el trabajador validan la regla y su `schema_version`. Si falla, el proceso termina antes de abrir el puerto y `/readyz` responde `503`. Las sondas son las de U4 y U3, sin cambios | reliability-design §4 (NFR10.14) |
| Recursos | Los de U2 §4, sin cambios: `semantic-agent` 0,25 CPU / 512 MiB → 1 CPU / 960 MiB y trabajador 0,25 CPU / 384 MiB → 1 CPU / 640 MiB. Caben con el módulo (§1.3) | performance-design §6; scalability-design §2 |
| Máquina | Una sola máquina de 64 GB, solo CPU, con el mismo digest que publica la CI. No hay *values* por máquina ni petición de `nvidia.com/gpu` | IDS-U2-01, IDS-U2-02; IDS-U4-15 |
| Almacenamiento | Tablas `conductor_observation` y `conductor_observation_decision` en `veridicus-pg` (PVC de 10 GiB de U2). Ocupan menos de 5 MB en el MVP, sin particiones | scalability-design §4 (NFR8.5) |
| Migración | Un PR propio, después de las migraciones de U3 y U4, que corre como el `Job` de migraciones de U2 con `veridicus_owner`. Nunca corre al arrancar un pod (§2 e IDS-U8-04) | security-design §6; `project.md` |
| IaC | Ninguna plantilla nueva. El chart paraguas `deploy/veridicus` de U2 no cambia por U8, salvo las dos filas del panel de U4 (§4 e IDS-U8-05) | logical-components §4; AUTONOMIA-01 |
| Estrategia de actualización | La de U4: API con `RollingUpdate`, y trabajador y `semantic-agent` con `Recreate` (IDS-U4-01 e IDS-U4-02, pedidos a U2). U8 no añade restricciones | IDS-U4-01, IDS-U4-02 |
| Clasificación | Igual que U4: `veridicus.io/data-class: sensitive` en la API, el trabajador y `semantic-agent`, porque el tema de la aclaración es testimonio | security-design §1 |

### 1.1 Qué extras entran en `values-extras.yaml` · Retirado

Retirado: no hay extras que encender (IDS-U8-01). El criterio para apagar la permutación en un perfil es
NFR8.7, medido en §7, y se aplica por PR al perfil y a la prueba `profiles_permutation` (security-design §3).

### 1.2 Ajustes de `values-extras.yaml` · Retirado

Retirado: salen `VERIDICUS_EXTRAS_*`, `VERIDICUS_QUESTION_*`, el plazo base de 600 s, el reclamo de 510 s y
`smoke.timeoutSeconds`. El plazo de la corrida es el de U11 y la prueba de humo usa *N* = 300 s
(performance-design §3 y §5).

### 1.3 Memoria de los pods con el módulo (NFR8.3)

| Contenedor | Pico de U4 | Suma de U8 | `/tmp` en memoria | 1,2 × (pico + U8 + `/tmp`) | `limits.memory` de U2 | ¿Cabe? |
|---|---|---|---|---|---|---|
| `semantic-agent` | 768 MiB | ≤ 5 MiB (`validate_clarifications` con 50 hallazgos) | 16 MiB | 947 MiB | 960 MiB | Sí, con 13 MiB de margen |
| Trabajador de `session-api` | 512 MiB | 0: la ingesta cabe en el pico de U4 con un `RunResult` de 2 MiB | 16 MiB | 634 MiB | 640 MiB | Sí |
| API de `session-api` | Cifra de U3 y U7 | Una transacción corta por decisión, sin carga en memoria | 16 MiB | — | 1,125 GiB | Valor de U2 |
| `model-verifier` | ≤ 14 GB | 0: la llamada permutada usa la misma ranura y la misma caché (`--parallel 1`) | — | — | 14 GiB | Sí; se mide con `VmHWM` en §7 |

U8 **no cambia el presupuesto** de Minikube de U2 (≈ 41 GiB y 14,5 CPU pedidos, de 50 GiB y 16 CPU). La
permutación duplica las llamadas al verificador por candidato, pero en serie y en la misma ranura: cuesta
tiempo y no memoria. Ese tiempo se mide con NFR8.7 (§7). El margen de `semantic-agent` es estrecho: si la
medición de B8 sube el pico, el límite sube por PR de U2 (IDS-U8-02).

## 2. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-pg` (U2) | database | Tabla `conductor_observation`: clave primaria `observation_id`, columna generada `tema_sha256 = sha256(convert_to(tema_key, 'UTF8'))`, índice único `(session_id, turnos, tema_sha256)`, índice `(session_id, change_seq)`, disparador `BEFORE UPDATE` (solo `status`, solo desde `proposed`) y disparador de restricción `DEFERRABLE INITIALLY DEFERRED` que exige el historial al confirmar. Tabla `conductor_observation_decision`: `UNIQUE (observation_id)`, índice `(session_id, change_seq)`, `CHECK (actor_kind = 'user')` y `CHECK (status IN ('approved','discarded'))`. Las claves foráneas son `ON DELETE RESTRICT` | security-design §6 (NFR11.1–NFR11.3, NFRD-U8-03, NFRD-U8-04); performance-design §4 (NFR3.9) |
| Permisos en `veridicus-pg` | database | Las marcas `veridicus-audit` (`mutable` y `history`, ambas `purgeable`, `owner_unit: U8`) y la llamada final a `veridicus_apply_audit_grants()` de U3. `veridicus_app` no tiene `DELETE`. `veridicus_retention` borra las dos tablas desde `purge_session` de U4 | NFR11.1, NFR11.5; NFRD-U8-08 (petición ya hecha a U4) |
| Conexiones y plazos | database | Sin roles ni conexiones nuevas: la ingesta va en la transacción de 5 s de U4 (`SET LOCAL`), y la decisión usa el *pool* de U3 con `statement_timeout` de 2 s. El cálculo de conexiones de U4 §2.1 no cambia | reliability-design §1; NFRD-U7-01 (nada en el `Cluster`) |
| `veridicus-redis` (U2) | queue | Sin *streams* ni claves nuevas. Las aclaraciones viajan dentro de C3 (`observaciones_conductor` de C6), con un máximo de 50 por corrida, dentro del tope del `RunResult` que ya cuenta U4 | scalability-design §1; C3, C6 |
| `model-verifier` (U2) | other (modelo) | La llamada `verifier_permuted` va al mismo servidor que `verifier`, en serie y en su única ranura. No hace falta ningún ajuste nuevo | security-design §1 (NFR1.2); performance-design §1 (NFR3.3) |
| `model-judge` (U2) | other (modelo) | U8 no lo llama. Solo cuenta para la medición de `todo-local` en la anfitriona (§7) | BR5.1 (0 llamadas nuevas) |
| `ingress-nginx` (U2) | load-balancer | `POST /api/v1/conductor-observations/{id}/decision` va por `veridicus-web` (`/api/`, sin disco). El tope del Ingress (2 113 536 bytes) es mayor que `review_body_max_bytes` (65 536), así que el `413` lo da siempre `session-api` | security-design §5 (NFRD-U8-05); U2 §2.4 |
| `migrations-job` (U2) | other | Migración Alembic de U8, descrita en IDS-U8-04 | `team.md`; `project.md` |
| `ConfigMap` del *prompt* de la pregunta y de la lista afectiva | — | **Retirado** (IDS-U8-01) | Salen la pregunta sugerida y el indicio afectivo |
| `cdn`, `search`, caché | — | No aplica | U8 no expone rutas fuera del Ingress de U2 ni busca pasajes |

## 3. Red y frontera (AUTONOMIA-04)

U8 **no añade destinos** (NFR1.1). No tiene ajustes y, por tanto, ningún campo URL. La llamada permutada
sale por el mismo camino que la directa (NFR1.2). La `NetworkPolicy` de U2 y U4 no cambia, y la lista
blanca de CoreDNS tampoco necesita entradas de U8.

| Componente | Proceso | Dentro o fuera del clúster | Qué datos cruzan su frontera | Hacia dónde |
|---|---|---|---|---|
| `domain/clarification.py` | `semantic-agent` | Dentro, bajo la salida denegada de U2 | Nada: arma el tema en memoria | — |
| `domain/clarification.py` | CLI de U11 (WSL2 o ZINE) | Fuera, como la CLI | Nada nuevo; las salidas siguen las reglas de la CLI | — |
| Llamada `verifier_permuted` | `semantic-agent` o la CLI | El mismo destino que `verifier` | `hecho`, `tipo` y las dos citas. **Nada sale** con los perfiles de hoy | `model-verifier` (interno) o el verificador de la anfitriona por *loopback* |
| `ClarificationIngest` | Trabajador de `session-api` | Dentro | Filas en PostgreSQL | `veridicus-pg` (interno) |
| `ConductorObservationDecisionService` | API de `session-api` | Dentro | Tema, turnos y estado hacia el navegador del dueño | Navegador por el Ingress con TLS de U2 |
| `ConductorObservationPanel` (M4) | Navegador, servido por `frontend` | Equipo del analista | Solo lo que devuelve ConsoleApi, nunca las citas | ConsoleApi |
| Arneses `evaluation/clarifications/` | WSL2 del equipo de 64 GB | Fuera | Solo enteros, *hashes* y versiones en los resúmenes (IDS-U8-07) | PR |

| Verificación | Cómo | Cuándo |
|---|---|---|
| Mismas llamadas con el módulo y sin él | Nivel 0 con un `ModelGateway` *fake* que cuenta llamadas (E11) | Cada PR |
| Mismo destino para `verifier` y `verifier_permuted` | `profiles_permutation_same_destination` con el cargador de U11 y un control negativo | Cada PR |
| `session-api` sin adaptadores comerciales | Comprobación del lockfile y de la imagen (IDS-U8-03) | Cada PR de `session-api` |
| Salida denegada en el clúster | La verificación manual de U2 (security-design §2.4 de U2), sin pasos propios | Antes de la sustentación |

## 4. Recursos compartidos

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `semantic-agent` y `libs-incoherence-analyzer` | U4 (proceso), U11 (biblioteca) | U8 | El módulo vive en `domain/` de la biblioteca; import-linter de U11 sin E/S en `domain` |
| Trabajador de `session-api` | U4 | U8 (`ClarificationIngest`) | Dentro de la transacción de ingesta de U4; orden sesión → fila |
| API de `session-api` | U3 | U8 (ruta de decisión) | `GuardedRoute` de U3 y su registro de resolvedores de dueño |
| Ranura de `model-verifier` | U2 | U4 y U11; U8 por la permutación | Directa y permutada en serie; una corrida a la vez |
| `veridicus-pg` | U2 (despliegue) y `session-api` (esquema) | Todas | Tablas de U8 con marca de auditoría; sin `DELETE` de la aplicación |
| `config/profiles.yaml` (`veridicus-profiles`) | U11 (contenido), U2 (`ConfigMap`) | U8 (`permutation`) | Cambia solo por PR con el reporte de §7 |
| `frontend` | U4 | U8 (panel en M4) | Una sola imagen; textos solo del catálogo de U1 |
| Panel de Grafana de U4 | U4 (original), U2 (empaquetado) | U8 (dos paneles) | Mismo SHA-256 que el original (IDS-U8-05) |
| Prometheus | U2 | U8 | Puerto `metrics` 8081 que ya raspan los `ServiceMonitor` de U3 y U4 |

## 5. Capacidad con la permutación

| Configuración | Meta | Dónde se mide |
|---|---|---|
| Corrida incremental con `comercial-piloto` | p95 ≤ 180 s con la permutación (meta de U11) | `permutation_cost` (§7) |
| Corridas con `todo-local` sin `tiempo_agotado` | ≥ 98 % (NFR8.7) | `permutation_cost` (§7) |
| Prueba de carga de 50 sesiones | ≥ 98 % con la permutación activa (NFR8.1) | `run_batches.py` de U4 por `port-forward` (IDS-U4-08) |
| Cola | Sin tope propio; las señales son las de U4 (`veridicus_run_queue_depth` > 20) | `monitoring-design.md` §2 de U4 |

Si `todo-local` queda por debajo del 98 %, el orden de respuesta es el de scalability-design §5:
1. apagar la permutación en `todo-local` por PR;
2. usar en la demostración `comercial-piloto`;
3. las opciones de escalado de U4.

Sin GPU no existe el «perfil más rápido» con GPU que menciona scalability-design §5 (IDS-U8-01). Ninguna
medida sube un plazo ni baja el 98 %.

## 6. Precisiones a artefactos ya aprobados (revisión 1) · Retirado

Retirado entero: sus siete filas trataban del *prompt* de la pregunta, la lista afectiva y
`values-extras.yaml`, y pedían a U2 dos `Application` y una etiqueta `cluster`. También pedían ampliar
`ai-eval-gate.yml` y `deploy-level0.yml`. Todo eso salió con el cambio 01, y las precisiones vigentes están en
§8 (IDS-U8-01).

## 7. Mediciones de nivel 2 de B8 en la máquina de 64 GB

U8 corre dos mediciones fuera de la CI con la CLI de U11 (tech-stack-decisions §5, D13):
- `clarifications.run` con `comercial-piloto` (NFR4.3, NFR4.6);
- `clarifications.permutation_cost` con `todo-local` y `comercial-piloto` (NFR3.1, NFR3.13, NFR8.7).

Las dos las lanza el humano en WSL2, fuera de Minikube y fuera del contenedor de trabajo, porque la CLI solo
acepta destinos locales por *loopback* (IDS-U11-06).

`todo-local` necesita **el juez y el verificador** en la anfitriona. El procedimiento de U11 solo levanta el
verificador y apaga el juez del clúster. Con los dos servidores en la anfitriona (24 GiB + 14 GiB) y Minikube
encendido, WSL2 no alcanza sus 56 GB. Por eso el humano detiene Minikube durante la medición (IDS-U8-08):

| Paso | Qué pasa | Memoria en WSL2 |
|---|---|---|
| 1 | `scripts/backup-db.sh` de U2 y luego `minikube stop`, sin `delete`: los PVC sobreviven (U2 §1). Solo lo hace el humano y solo figura en el runbook, nunca en un *script* | Libera Minikube |
| 2 | `scripts/host-verifier.sh start` (U11): verificador gpt-oss-20b Q8_0 en `127.0.0.1:18080`, `--memory 14g` y `--cpus 8` | 14 GiB |
| 3 | `scripts/host-verifier.sh start --role judge` (petición a U11, IDS-U8-08): la imagen de `model-judge` por digest, leída de `values-cpu.yaml`, con Qwen3.6-35B-A3B Q4_K_M de `/srv/veridicus/models`. Antes de arrancar, `sha256sum -c` con su línea de `deploy/models.lock`. Escucha en `127.0.0.1:18081` con `--memory 24g`, `--cpus 8`, `--parallel 1` y `--threads 8` | 24 GiB |
| 4 | Carga `VERIDICUS_ANTHROPIC_API_KEY` desde el `.env` no versionado (solo para `comercial-piloto`) | — |
| 5 | Corre `clarifications.run` y `permutation_cost` con `VERIDICUS_LOCAL_BASE_URL_VERIFIER=http://127.0.0.1:18080` y `VERIDICUS_LOCAL_BASE_URL_JUDGE=http://127.0.0.1:18081`. Lee el `VmHWM` de cada servidor tras la llamada de calentamiento y al final con `host-verifier.sh hwm` (IDS-U8-09) | CLI ≤ 2 GiB con el NER de U10 |
| 6 | `scripts/host-verifier.sh stop --role judge` y `stop`; luego `minikube start` y `scripts/smoke.sh https://veridicus.local:8443` | Vuelve Minikube |
| 7 | `scripts/clarifications-evidence.py` copia los dos resúmenes y escribe la evidencia (IDS-U8-07). Se commitean esos tres archivos solos | — |

- **Pico.** Unos 40 GiB de los 56 GB de WSL2: juez y verificador nunca generan a la vez, pero sus pesos
  quedan mapeados.
- **Mismos binarios y archivos.** Las dos imágenes y los dos GGUF son los del clúster, verificados con
  `sha256sum -c`, así que lo que se mide es lo que corre en `todo-local`.
- **Riesgo declarado.** El clúster está parado durante la medición. El humano la programa fuera de los
  ensayos de la demostración.

## 8. Precisiones y peticiones (IDS-U8-xx)

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al original,
cada una en su propio commit. Las peticiones a U2, U3, U4 y U11 **no se dan por aplicadas** hasta que esa
unidad las acepte. Todas salen de las fuentes aprobadas o de un hecho técnico. Ninguna deja salir del
clúster algo que hoy no sale, ni cambia el tamaño de Minikube.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U8-01 | Revisión 1 de esta etapa (los cuatro artefactos) y `nfr-design/scalability-design.md` §5 («GPU o comercial») | Se retiran: `values-extras.yaml` y las dos `Application`; los `ConfigMap` del *prompt* de la pregunta y de la lista afectiva; `VERIDICUS_EXTRAS_*`, `VERIDICUS_QUESTION_*`, el plazo de 600 s, el reclamo de 510 s y `smoke.timeoutSeconds`; las métricas, alertas y el panel «Veridicus — extras»; `check-extras-values.py`; las ampliaciones de `ai-eval-gate.yml` y `deploy-level0.yml`; la etiqueta `cluster` de Prometheus; y la tabla §6 de la revisión 1. Sin GPU, la segunda medida de escalado es solo `comercial-piloto` | Cambio 01; NFRD-U8-01; IDS-U2-02 |
| IDS-U8-02 | `nfr-design/scalability-design.md` §2 (tope de `semantic-agent` ≤ 768 MiB) y performance-design §6 (≤ 5 MiB sobre el pico de U4) | El tope de 768 MiB es el pico de U4. Con los ≤ 5 MiB del módulo, el pico es ≤ 773 MiB, y 1,2 × (773 + 16) = 947 MiB cabe en los 960 MiB de U2. La medición de la prueba de carga compara con la regla de 1,2 × pico. Si la supera, el límite sube por PR de U2; nunca baja el margen | §1.3; regla de 1,2 × pico de U2 §4 |
| IDS-U8-03 | `nfr-design/logical-components.md` §5 (Fronteras) | **Petición a U3 y U4** (dueños de `session-api.yml`): `services/session-api` depende de `libs-incoherence-analyzer` **sin** el *extra* `cli`. Se suma un *job* `lock-boundary` como el de `semantic-agent`: 0 apariciones de `libs-anonymizer` en `services/session-api/uv.lock`, y `python -c "import libs.anonymizer"` dentro de la imagen termina en `ModuleNotFoundError`. Control negativo: un lockfile que lo nombra. Así el proceso con la base y el testimonio nunca lleva adaptadores comerciales | AUTONOMIA-04; IDS-U11-02 (importación diferida); AC11.6.4 |
| IDS-U8-04 | `nfr-design/logical-components.md` §4 (Migración) | La migración de U8 entra en su PR propio **después** de la de U3, que trae `veridicus_apply_audit_grants()` y la restricción de actor, y de la de U4, que trae `interview_session`, `change_cursor` y `purge_session`. Contiene: las dos tablas, `tema_sha256`, los índices de performance-design §4, los dos disparadores, las marcas `COMMENT` y la llamada final a `veridicus_apply_audit_grants()`. Corre como el `Job` de migraciones de U2 con `veridicus_owner`: a mano antes del módulo 8 y, con Argo CD, como *hook* `Sync` de la onda −1 (IDS-U2-07). Solo avanza | `team.md` (migraciones); `project.md`; IDS-U2-07 |
| IDS-U8-05 | `nfr-design/observability-design.md` §4 («U2 los empaqueta con el panel de U4») | Los dos paneles (aclaraciones ingeridas por minuto y decisiones por `state`) se añaden al original del panel de U4 en `services/session-api/observability/`. U2 lo copia al chart con el mismo SHA-256, por la petición IDS-U4-14 a `check-config-copy.sh`. Solo se renderiza con `monitoring.enabled: true` | IDS-U4-14; IDS-U2-13 |
| IDS-U8-06 | `nfr-design/observability-design.md` §2 («en `/metrics` del puerto interno de cada proceso de `session-api`») | `veridicus_conductor_observations_ingested_total` se expone en el trabajador y `veridicus_conductor_observation_decisions_total` en la API, los dos en el puerto 8081. Los raspan el `ServiceMonitor` `veridicus-session-api` de U3 y el del trabajador de U4. No hacen falta objetivos nuevos | IDS-U4-14; NFR10.23 de U3 |
| IDS-U8-07 | `nfr-design/security-design.md` NFRD-U8-09 y `tech-stack-decisions.md` §5 («adjunto al PR») | Igual que IDS-U11-04, «adjunto al PR» es un trío versionado en `evaluation/clarifications/reports/`: `<slug-del-bolt>.clarifications.json`, `<slug-del-bolt>.permutation-cost.json` (los resúmenes de esquema cerrado) y `<slug-del-bolt>.evidence.yaml`, con el esquema de evidencia de U11 (`evaluated_commit`, `host`, digests de las imágenes y SHA-256 de los modelos). Los reportes por entrevista se quedan en `out/u8-clarifications/`, y U8 añade `out/` a `.gitignore` en B8. **Petición a U11:** `analyzer-level2-gate.yml` suma un *job* `clarifications` (§3 de `cicd-pipeline.md`) | IDS-U11-04; `project.md` (sin datos reales en Git) |
| IDS-U8-08 | `nfr-design/performance-design.md` §8 («`todo-local` en la máquina de desarrollo») e IDS-U11-05 | `todo-local` en la CLI necesita el juez local en la anfitriona, y con Minikube encendido no cabe en WSL2. El procedimiento de §7 detiene Minikube (sin `delete`) mientras dura la medición. **Petición a U11:** `scripts/host-verifier.sh` suma `--role judge`: imagen de `model-judge` por digest, Qwen3.6-35B-A3B Q4_K_M con `sha256sum -c`, `127.0.0.1:18081`, `--memory 24g`, `--cpus 8`, con `start` y `stop` explícitos y sin descargas | IDS-U2-01; IDS-U2-11; IDS-U11-05, IDS-U11-06 |
| IDS-U8-09 | `nfr-design/security-design.md` NFRD-U8-11 (`VmHWM` del verificador) | **Petición a U11:** `scripts/host-verifier.sh hwm [--role judge]` imprime en kB el `VmHWM` del servidor con un `docker exec` de solo lectura sobre `/proc/1/status`. El arnés lo llama tras la llamada de calentamiento y al final, y falla si crece más de un 1 % | NFR8.3; NFRD-U8-11 |
| IDS-U8-10 | `nfr-design/security-design.md` NFRD-U8-10 y `cicd-pipeline.md` §2 de U4 | U8 añade en B8 la comprobación previa del par `verifier` y `verifier_permuted` a `frontend/e2e/smoke.spec.ts`, el *spec* de humo de U4. La forma `scripts/smoke.sh <url-base>` de `team.md` no cambia, igual que *N* = 300 s y el perfil `comercial-piloto`. No es una petición: U8 escribe esa comprobación sobre el archivo de U4 | NFR3.12; cierra R-01 de la revisión 1 |
| IDS-U8-11 | `nfr-design/logical-components.md` §5 («añadidos a `.coveragerc-guards`») | En la biblioteca, el 100 % de ramas lo comprueba `scripts/check-guard-coverage.py` de U11 con su lista de siete módulos. **Petición a U11:** `clarification.py` entra en esa lista como octavo módulo. En `session-api`, `conductor_observation_state.py` entra en `.coveragerc-guards` del *job* `guards` | NFR13.2; `cicd-pipeline.md` §2 de U11 |
| IDS-U8-12 | Tarea previa P0.1 (comprobaciones obligatorias) | U8 no crea *workflows* ni comprobaciones obligatorias nuevas. Sus pruebas van en `analyzer / gate`, `analyzer-level2-gate / check`, `semantic-agent / gate`, `frontend / gate` y los *jobs* de `session-api.yml`, ya pedidos al humano en IDS-U11-09 e IDS-U4-12 | IDS-U11-07, IDS-U11-09; IDS-U4-12 |

## 9. Cierre de los hallazgos de la revisión 1

| Hallazgo | Dónde se cierra |
|---|---|
| R-01 (`smoke.sh --values` y opciones en `false`) | Desaparece: `smoke.sh <url-base>` no cambia y la comprobación previa es por comportamiento (IDS-U8-10) |
| R-02 (evidencia en CPU y despliegue en GPU) | Desaparece: no hay GPU ni activación de extras. Las mediciones de §7 usan los mismos digests y modelos que el clúster |
| R-03 (`Application` de desarrollo con extras) | Desaparece: hay una sola configuración, `values-cpu.yaml`, y ningún extra (IDS-U8-01) |
| R-04 (filtro de rutas sin la `Application` de la demostración) | Desaparece. Las rutas de IA de U8 las exige `analyzer-level2-gate.yml` (IDS-U8-07; `cicd-pipeline.md` §3) |
| R-05 (18 GiB frente a 20 GiB) | Desaparece: U8 no repite cifras de Minikube y remite a U2 (50 GiB y 16 CPU) |
