# Requisitos de seguridad — U6 session-lifecycle

**Insumos.** Flujos F1–F6, la tabla de frontera de §1 y §8 «Errores y bordes» de
`functional-design/functional-spec.md` (functional-spec); reglas BR1–BR6 de `functional-design/rules.md`
(rules) y entidades de `functional-design/entities.md`; FR2.4, FR3.3, FR8 y NFR1, NFR10–NFR12 de
`inception/requirements-analysis/requirements.md` (requirements); C1 (rutas de U6) y C2 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`; reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de team-practices: nivel 0
(unitarias, contratos y políticas, cada PR), nivel 1 (integración con PostgreSQL + `pgvector` y Redis
reales, cada PR), nivel 2 (evaluación de IA, PR que tocan la IA y entregas), nivel 3 (E2E y humo) y
manual. Los comandos están en `tech-stack-decisions.md` §5. La autenticación, la sesión web, el
anti-CSRF y la convención de auditoría vienen de U3; la validación de C2, el borrado de mensajes con
`XDEL` y los logs con solo identificadores vienen de U4 (NFR10.1, NFR10.7, NFR10.9 de U4). Aquí solo se
exige que U6 los use y se añade lo propio de U6.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| ConsoleApi (rutas de U6) | `session-api`, dentro del clúster | Testimonio pegado desde el navegador hacia `session-api`; lista de sesiones (escenario, versión, dueño, fecha, estado, conteo de pendientes) hacia el navegador; todo dentro del clúster (C1) | Confidencial |
| InterviewSession (pegado, latido, suspensión, reanudación) | API y trabajador de `session-api`, dentro | Turnos de testimonio hacia `veridicus:turns` (C2) en Redis interno; nada sale | Confidencial |
| TruthFrame (versiones nuevas) | API y trabajador de `session-api`, dentro | Documento del escenario hacia el indexador de U4 y pasajes hacia `model-embeddings` interno (C14); nada sale | Interna (escenarios sintéticos) |
| AnalystConsole (M1, diálogos de pegado y reanudación, historial lateral) | Navegador, servido por `frontend` | Solo habla con ConsoleApi (ADR-004); la vista previa del pegado se calcula en el navegador sin enviar nada | Confidencial |

**Ningún componente de U6 hace una llamada fuera del clúster.** Los pods de `session-api` (API y
trabajador) quedan bajo la `NetworkPolicy` de salida denegada de U2 igual que `semantic-agent` (hallazgo
R-04 de la revisión de U4): U6 no añade destinos de red. El testimonio pegado se trata como dato
confidencial aunque en el MVP todos los datos sean sintéticos (NFR12).

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Pegado enorme (cuerpo de varios MB o miles de turnos mínimos) que agota memoria o alarga la transacción | Denial of service | Medio | NFR10.1 |
| T2 | La consola manipulada envía una división distinta o marca turnos de testimonio como entrevistador para que no se evalúen | Tampering | Medio | NFR10.1 (el servidor vuelve a dividir y nunca acepta roles del cliente) |
| T3 | Otro analista pega en una sesión ajena, la reanuda o la mantiene viva con sondeos | Elevation of privilege | Medio | NFR10.2, NFR10.3 |
| T4 | Un cliente fuerza `suspended` u otro estado, o modifica una versión o un pasaje por la API | Tampering | Medio | NFR10.6, NFR11.1 |
| T5 | Texto pegado en logs, métricas, Problem Details o en Redis después de usarse | Information disclosure | Alto | NFR10.4, NFR10.5 |
| T6 | Borrar o reescribir el historial de estados de la sesión o una versión de escenario | Repudiation | Medio | NFR11.1, NFR11.2 |
| T7 | Una suspensión sin autor reconocible («¿quién suspendió mi sesión?») | Repudiation | Bajo | NFR11.2 (actor sistema con `actor_kind`) |
| T8 | Un pegado evita la guardia del umbral (alerta o pregunta bajo el umbral) | Tampering | Alto | NFR10.7 |
| T9 | Etiqueta de veracidad en los textos nuevos de U6 (estados, diálogos) | Tampering | Bajo | NFR10.8 |
| T10 | La lista de sesiones expone más de lo que FR1.2 permite | Information disclosure | Bajo | NFR10.2 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | U6 no abre ningún destino de red nuevo. | Las rutas y tareas de U6 solo usan PostgreSQL, Redis y el indexador de U4 dentro del clúster; ninguna dependencia nueva de U6 hace llamadas de red (revisión de dependencias en el PR y `pip-audit`). Los `/readyz` de la API y del trabajador de `session-api` pasan con la `NetworkPolicy` de U2 aplicada. | Nivel 1 y manual en el clúster, junto con NFR1.2 de U4 |
| NFR1.2 | La vista previa no sale del navegador. | La división de BR2.1 corre en el navegador; la prueba Vitest de NFR3.6 comprueba 0 peticiones al pulsar «Continuar» y «Cancelar». | Vitest |

### NFR10 — Seguridad de la aplicación

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | El pegado se valida en el servidor antes de crear filas. | El servidor deja de leer el cuerpo al pasar 524 288 bytes y responde `422` `transcript.too_large` sin crecer la memoria del proceso más de 20 MiB (prueba con 5 MB). Luego vuelve a dividir con BR2.1 (nunca usa la división ni los roles de la consola; el cuerpo solo admite `text` y `client_request_id`) y rechaza con `422` `transcript.too_large` si hay más de **60 turnos de testimonio**, más de 200 turnos en total o más de 100 000 caracteres, y con `422` `turn.too_long` si algún turno supera 2 000 caracteres (NFR8.3). Cada rechazo deja 0 filas y 0 mensajes en C2. Casos E6 (61 turnos de testimonio) y E7, y uno con 201 turnos del entrevistador. | Nivel 1 |
| NFR10.2 | Las rutas de U6 aplican rol, dueño y anti-CSRF de U3. | `/transcript`, `/heartbeat` y `/resume`: `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true`; `/scenarios/{id}/versions`: `[analista, admin]`; todas las de escritura exigen `X-CSRF-Token`. `GET /sessions` la pueden leer ambos roles (FR1.2) y solo devuelve los campos de `SessionSummary`, sin texto de turnos. Pruebas `403`: otro analista pega, reanuda o envía latido en una sesión ajena (E14); un `admin` pega; petición sin anti-CSRF; todas con 0 filas. | Nivel 1 |
| NFR10.3 | Solo el dueño mantiene viva su sesión. | El sondeo `GET /sessions/{id}` de otro usuario (analista o `admin`) no cambia `last_heartbeat_at` (BR4.1); prueba de nivel 1 en la que solo sondea otro usuario y la sesión se suspende a tiempo (NFR3.7). | Nivel 1 |
| NFR10.4 | Los logs y errores de U6 solo llevan identificadores. | Campos permitidos: los de NFR10.7 de U4 más `paste_batch_id`, `scenario_id`, conteos (`turn_count`, `testimony_count`, `char_count`) y `idle_seconds`. Prueba de nivel 1: con una cadena centinela sembrada en una transcripción pegada (aceptada y rechazada por tamaño) y en el nombre de un hablante, 0 coincidencias en los logs capturados de la API y del trabajador y en el `detail` de los Problem Details. | Nivel 1 |
| NFR10.5 | Los mensajes de un pegado no se quedan en Redis. | Los turnos pegados usan C2 tal cual, con el `XDEL` tras confirmar de NFR10.9 de U4. Prueba de nivel 1: tras evaluar un pegado de 15 turnos, `XRANGE` de `veridicus:turns` y `veridicus:results` no contiene el texto. | Nivel 1 |
| NFR10.6 | No hay ruta que cambie el estado a `suspended` ni que modifique versiones o pasajes. | La comprobación del OpenAPI de C1 falla si existe `PUT`, `PATCH` o `DELETE` sobre `/scenarios/*`, `/scenario-versions/*` o pasajes, o si alguna ruta acepta `status` en el cuerpo (BR1.2, E2). La transición `open → suspended` solo la hace la tarea del trabajador. | Nivel 0 |
| NFR10.7 | El pegado no evita la guardia del umbral (AUTONOMIA-05). | Los turnos de testimonio pegados se publican en C2 con la misma instantánea del umbral de la sesión que los turnos escritos (BR4.1 de U4) y pasan por la misma guardia de `semantic-agent`. Prueba de nivel 1: el caso de Hecho No Documentado pegado produce 0 alertas, 0 preguntas y 1 paquete, igual que enviado turno a turno. Los turnos `interviewer` nunca se publican en C2 (BR2.2). | Nivel 1 |
| NFR10.8 | Los textos nuevos de U6 no llevan etiquetas de veracidad (AUTONOMIA-03). | Los rótulos y mensajes de M1, del diálogo de pegado, del de reanudación y del historial lateral salen del catálogo de U1 y pasan el escáner `scan(text, literal_sources)` de `libs/integrity_policy` en nivel 0 y sobre la interfaz renderizada en nivel 3, con 0 coincidencias. | Niveles 0 y 3 |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | Versiones y pasajes son inmutables (FR2.4). | El usuario de la aplicación no tiene `UPDATE` ni `DELETE` sobre pasajes ni `DELETE` sobre `ScenarioVersion`; solo el permiso propio del indexador cambia el estado de indexación (NFR11.1 de U4). Prueba de nivel 1: `UPDATE` y `DELETE` directos sobre un pasaje y `DELETE` sobre una versión fallan por permisos; cargar la versión 2 deja la versión 1 con el mismo SHA-256 y el mismo número de pasajes (E1). | Nivel 1 |
| NFR11.2 | El historial de estados de la sesión solo admite inserciones. | Cada `SessionStatusChange` de U6 lleva hora y actor: `open → suspended` con `actor_kind = system` y sin usuario; `suspended → open` con `actor_kind = user` y el dueño. La tabla ya está en `AuditConvention` (NFR11.1 de U4); la prueba común de U3 cubre las filas nuevas y `UPDATE`/`DELETE` fallan. `TranscriptPaste` también es solo de inserción. | Nivel 1 (prueba común de U3) |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Los *fixtures* de U6 son sintéticos y marcados. | Transcripciones pegadas, ejemplos de división compartidos y versiones de escenario de prueba usan el catálogo de nombres y las marcas de datos sintéticos de U1; la comprobación de U1 corre sobre las carpetas de pruebas de U6 y sobre el archivo de ejemplos de división con 0 hallazgos. | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U6 |
|---|---|
| AUTONOMIA-01 | U6 no aplica nada al clúster; las columnas y tablas nuevas (`role`, `speaker`, `paste_batch_id`, `TranscriptPaste`, `suspended_at`, índice parcial) entran por un `Job` de migraciones en su propio PR, aditivas (*expand–contract*) |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.8, NFR11.2 |
| AUTONOMIA-04 | §1, NFR1.1, NFR1.2, NFR10.4, NFR10.5 |
| AUTONOMIA-05 | NFR10.7 y la equivalencia NFR4.1 (`reliability-requirements.md`) |

## 5. Riesgo aceptado

**Un pegado largo ocupa la cola.** Un pegado de 60 turnos de testimonio deja la cola del juez ocupada
unos 45–60 minutos y los turnos de otras sesiones esperan detrás (el plazo proporcional evita que fallen
hasta el tope de 3 600 s). En el MVP trabaja un solo analista; se vigila con
`veridicus_turn_queue_depth` (U4) y la profundidad que deja cada pegado (`observability-requirements.md`).

## 6. Precisiones a artefactos ya aprobados

Estas decisiones precisan artefactos ya aprobados. No los edité; decides en la aprobación si se
actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `functional-design/rules.md` de U6 (BR2.3) y `entities.md` (`TranscriptPaste.turn_count`, máx. 100) | El límite de 100 turnos pasa a **60 turnos de testimonio**; los del entrevistador no cuentan para ese límite, y el total de turnos queda acotado en 200 para limitar la transacción (T1). Más de 60 de testimonio o más de 200 en total → `422` `transcript.too_large`. Sin cambio en los 100 000 caracteres ni en los 2 000 por turno. El escenario E6 pasa a «61 turnos de testimonio». | P2 = A; NFR8.3 de U4 (≈ 60 turnos caben en el tope de 3 600 s) |
| `contract-design/contract-summary.md` (C1 `/sessions/{id}/transcript`) | Declarar las respuestas `422` (`transcript.too_large`, `turn.too_long`), `409` (`session.finalized`, `session.not_open`) y `503` (`system.unavailable`, precisión de U3); un cuerpo de más de 524 288 bytes responde `422` `transcript.too_large` sin leerse entero. Los `code` `transcript.too_large`, `turn.too_long` y `session.not_open` ya están en las tablas de precisiones de U6, U4 y U1. | NFR10.1, NFR10.11 |
| `functional-design/rules.md` de U6 (BR4.1) y C1 (`GET /sessions/{id}`) | El latido se escribe como máximo una vez cada 15 s por sesión (solo si el valor registrado tiene 15 s o más), con la hora de la base. | Respuesta P1 (escritura acotada); NFR3.8 |
| `functional-design/rules.md` de U6 (BR4.5) | Reanudar también pone `last_heartbeat_at` en la hora actual dentro de la misma transacción; si no, la siguiente revisión volvería a suspender la sesión al instante. | NFR8.9 |
| `functional-design/rules.md` de U6 (BR2.5) y de U4 (BR5.3) | Si la transacción del pegado se confirmó pero la publicación en C2 falló, la API responde `503` `system.unavailable`; un reenvío con el mismo `client_request_id` devuelve los mismos turnos **y vuelve a publicar** los de testimonio que siguen `queued` sin haber empezado (la ingesta es idempotente por (`turn_id`, `attempt`)). | NFR10.11 |
| `functional-design/entities.md` de U6 (`InterviewerLabels`) | «Configurable» se implementa como un archivo versionado que comparten la consola y el servidor (con los ejemplos de BR2.1) y que solo cambia por PR, no como variable de entorno: así la vista previa y la división del servidor nunca discrepan. Se propone `contracts/fixtures/transcript-split.v1.json`, carpeta de U1. | NFR13.2; corrección de `project.md` sobre ajustes «configurables» |
| `functional-design/rules.md` de U6 (BR2.6) | La comparación pegado frente a turno a turno usa como clave el **ordinal entre los turnos de testimonio** (el número de turno difiere si el pegado trae líneas del entrevistador) y se exige sobre la forma sin líneas del entrevistador de cada transcripción; con ellas, la diferencia se mide y se reporta sin bloquear. | NFR4.1 |
| `contract-design/contract-summary.md` (C15) | Las métricas de U6 de `observability-requirements.md` §2 se añaden a C15 por un PR de U1, como las de U3 y U4. | NFR15.1 |
