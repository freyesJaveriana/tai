# Requisitos de seguridad — U6 session-lifecycle

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U6. Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **IDs.** Los requisitos que siguen conservan su ID. Lo que sale queda «Retirado» sin renumerar. Lo nuevo
  toma el número siguiente de su grupo: NFR1.3–NFR1.4, NFR10.13–NFR10.14 y NFR11.3. Cada fila dice si
  **se mantiene**, **cambia**, es **nuevo** o está **Retirado**.
- **Preguntas.** Ninguna en esta pasada: todo lo fijan las fuentes (sección de segunda pasada de
  `nfr-requirements-questions.md`). Lo aplicado sin preguntar está en la tabla NFR-U6 de §6.
- **Revisión 1:** R-03 queda caduco (las cifras de 60 y 200 turnos salen con C25); R-04, cubierto por la
  ingesta idempotente de U4 (`reliability-requirements.md`, NFR10.11).

**Insumos.**
- Frontera AUTONOMIA-04 de §1, flujos F2–F9, máquina de estados de §3, escenarios E4–E47 y tabla
  FD-U6-01 a FD-U6-24 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR2–BR10 de `functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`.
- FR3.3, FR3.6, FR3.7, FR8, NFR1, NFR10, NFR11 y NFR12 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3), y VE-10 y A-4 de `requirements-adenda-02.md`.
- C1 (rutas de U6), C2, C6, C11, C15, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3), con CD-06.
- Lo que fijaron hoy los NFR de U1, U2, U3, U4, U10 y U11; reglas AUTONOMIA-01..05 de `team.md` y
  prohibiciones de `project.md`.

Niveles de `team.md`: nivel 0 (unitarias, contratos y políticas, cada PR), nivel 1 (integración con
PostgreSQL y Redis reales y *fakes* de C17, cada PR), nivel 3 (E2E y humo) y manual. Los comandos están
en `tech-stack-decisions.md` §5. La autenticación, el anti-CSRF y la convención de auditoría son de U3; la
tubería de corridas, la clave de cancelación y el borrado de mensajes de Redis son de U4. Aquí solo se
exige que U6 los use y se añade lo propio de U6.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| ConsoleApi (rutas de U6) | `session-api`, dentro del clúster | Testimonio pegado o importado desde el navegador; lista de sesiones (entrevista, origen, perfil, dueño, fecha, estado, pendientes) hacia el navegador; todo dentro del clúster (C1) | Restringido |
| InterviewSession (pegado, importación, modo final, latido, suspensión, pausa, terminación, retirada) | API y trabajador de `session-api`, dentro | Mensajes C2 y la clave de cancelación por Redis interno; nada sale | Restringido |
| Supervisor de sesiones (`session-supervisor`) | Trabajador de `session-api`, dentro | Ninguno | Interno |
| AnalystConsole (M1, M7, diálogos, franja del modo final, historial lateral) | Navegador, servido por `frontend` | Solo habla con ConsoleApi (ADR-004); la vista previa del pegado y la validación del archivo se calculan en el navegador sin enviar nada | Restringido |
| Ingress de `session-api` (U2) | Dentro del clúster | El cuerpo del pegado (hasta ≈ 1 MB) y el archivo importado (hasta 2 MiB) pasan por él; **no debe escribirlos en disco** (NFR10.13, NFR-U6-06) | Restringido |
| Corridas que lanza U6 (bloque, modo final, reanudación del análisis) | `semantic-agent` (U4) y `anonymizer-proxy` (U10) | La única salida posible, por la tubería de U4 y con el anonimizador delante, solo si el perfil tiene un papel comercial y el consentimiento autoriza la transferencia | Sale seudonimizado |

**Ningún componente de U6 hace una llamada fuera del clúster** ni añade destinos de red: los pods de
`session-api` siguen bajo la `NetworkPolicy` de salida denegada de U2. Pausar, terminar y registrar la
retirada impiden toda llamada nueva (NFR1.3).

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Pegado o archivo enorme, o JSON con anidamiento profundo, que agota memoria o alarga la transacción | Denial of service | Medio | NFR10.1, NFR10.13 |
| T2 | La consola manipulada envía una división distinta o turnos fuera de la regla | Tampering | Medio | NFR10.1 (el servidor vuelve a dividir; el cuerpo solo admite `text` y `client_request_id`) |
| T3 | Otro analista, el `admin` o el `investigador` pegan, importan, lanzan el modo final, pausan, terminan, retiran o mantienen viva una sesión ajena | Elevation of privilege | Medio | NFR10.2, NFR10.3 |
| T4 | Un cliente fuerza un estado (`suspended`, `open` tras `terminated`) o reabre una sesión cerrada a turnos | Tampering | Medio | NFR10.6, NFR11.1 |
| T5 | Testimonio, nombre del archivo o constancias en logs, métricas, Problem Details, Redis o disco | Information disclosure | Alto | NFR10.4, NFR10.5, NFR10.13 |
| T6 | Borrar o reescribir el historial de estados, la retirada o un bloque pegado | Repudiation | Medio | NFR11.1, NFR11.2, NFR11.3 |
| T7 | Una suspensión sin autor reconocible | Repudiation | Bajo | NFR11.2 (`session-supervisor`) |
| T8 | Sale una llamada a un modelo después de pausar, terminar o registrar la retirada (VE-10 (a)) | Information disclosure | Alto | NFR1.3 |
| T9 | Un archivo importado sin consentimiento, o con un perfil comercial sin autorización de transferencia | Information disclosure | Alto | NFR1.4 |
| T10 | Una transcripción real declarada `sintetico` para evitar el bloque de consentimiento (FD-U6-05) | Information disclosure, Repudiation | Medio | NFR1.4 y riesgo aceptado de §5 |
| T11 | Etiqueta de veracidad en los textos nuevos de U6 (estados, diálogos, franja) | Tampering | Bajo | NFR10.8 |
| T12 | La lista de sesiones expone más de lo que FR1.2 permite o la ve el `investigador` | Information disclosure | Bajo | NFR10.2 |
| T13 | Un archivo con claves duplicadas que la consola y el servidor leen distinto | Tampering | Bajo | NFR10.13 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | cambia | U6 no abre ningún destino de red nuevo. | Las rutas y tareas de U6 solo usan PostgreSQL y Redis dentro del clúster; U6 no añade dependencias que hagan llamadas de red (revisión de dependencias en el PR y `pip-audit`). Los `/readyz` de la API y del trabajador de `session-api` pasan con la `NetworkPolicy` de U2 aplicada | Nivel 1 y manual en el clúster, junto con la verificación de U2 |
| NFR1.2 | cambia | La vista previa del pegado y la validación del archivo no salen del navegador. | La división de BR2.1 y la validación de BR7.1–BR7.4 corren en el navegador; las pruebas Vitest de NFR3.6 y NFR3.14 cuentan 0 peticiones hasta «Confirmar» o «Importar» | Vitest |
| NFR1.3 | nuevo | Ninguna llamada nueva sale después de pausar, terminar o registrar la retirada (VE-10 (a), CD-06; BR9.1, BR9.3–BR9.6). | Para cada una de las tres acciones, con dos corridas en cola y una final en proceso, el *fake* del `ModelGateway` registra **0 llamadas nuevas** después de la respuesta; las claves `veridicus:run-cancelled:{run_id}` existen al responder; tras la retirada, turno, bloque, modo final, reintento y «Reanudar análisis» responden `409` `session.consent_withdrawn` con 0 filas (E39, E42). Una llamada ya en curso no se deshace (límite declarado) y su resultado se descarta. 100 % de ramas en la decisión de cancelar (NFR13.1) | Nivel 1 |
| NFR1.4 | nuevo | La importación no abre una vía sin consentimiento ni sin autorización de transferencia (BR7.4, BR7.5, A-4, VE-07). | `corpus` sin bloque → `422` «Falta el bloque de consentimiento»; bloque que no autoriza la transferencia con un perfil que tiene un papel comercial → `422` `profile.transfer_not_authorized`; perfil del archivo distinto del elegido → `422` `import.profile_mismatch`; en todos, 0 filas (E27, E29). `sintetico` sin bloque crea `ConsentRecord` `sintetico` (E28), con quién y cuándo, y el log `session.imported` registra `origin` para que una importación sintética se pueda auditar | Nivel 1 |

### NFR10 — Seguridad de la aplicación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | El pegado se valida en el servidor antes de crear filas (BR2.3, BR2.5, BR2.7). | El servidor deja de leer el cuerpo al pasar 4 × `transcript_max_chars` + 4 096 bytes (1 004 096) y responde `413` `limits.exceeded` sin crecer la memoria del proceso más de 20 MiB (prueba con 5 MB). Luego vuelve a dividir con BR2.1 (nunca usa la división de la consola) y responde `413` `limits.exceeded` si el bloque pasa de `transcript_max_turns`, de `transcript_max_chars` o algún turno de `turn_max_chars`, **o si llevaría la sesión por encima de los totales** (NFR-U6-02). Cada cifra en el límite exacto da 202 y en el límite + 1 da 413 (E6, E7). Cada rechazo deja 0 filas y 0 mensajes en C2. Todas las cifras salen de `limits.load` (C25); una prueba de nivel 0 falla si U6 usa un número de límite literal | Nivel 0 y nivel 1 |
| NFR10.2 | cambia | Las rutas de U6 aplican rol, dueño y anti-CSRF de U3 (BR3.4, BR10.1). | `/transcript`, `/final-runs`, `/heartbeat`, `/resume`, `/analysis`, `/terminate` y `/consent-withdrawal`: `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true`; `/sessions/import`: `[analista]`; `GET /sessions`: `[analista, admin]`. Toda ruta de escritura exige `X-CSRF-Token`. Pruebas `403`: otro analista en cada ruta de dueño (`session.not_owner`, E14); `admin` e `investigador` en cada ruta de escritura (`auth.forbidden`); `investigador` en `GET /sessions` (E46); petición sin anti-CSRF; todas con 0 filas. `GET /sessions` solo devuelve los campos de `SessionSummary`, sin texto de turnos | Nivel 1 |
| NFR10.3 | se mantiene | Solo el dueño mantiene viva su sesión (BR4.1). | El sondeo de otro usuario (analista o `admin`) no cambia `last_heartbeat_at`; prueba de nivel 1 en la que solo sondea otro usuario y la sesión se suspende a tiempo (NFR3.7) | Nivel 1 |
| NFR10.4 | cambia | Los logs y errores de U6 solo llevan identificadores (BR7.9, §8 del Functional Design). | Campos permitidos: los de U4 más `paste_batch_id`, `origin`, tamaños en bytes, conteos (`turn_count`, `char_count`, `problem_count`), `idle_seconds` y `code`. Prueba de nivel 1: una cadena centinela sembrada en un bloque pegado (aceptado y rechazado), en un turno de un archivo importado (aceptado y rechazado por esquema), en el **nombre del archivo** y en `constancia` del bloque de consentimiento aparece 0 veces en los logs de la API y del trabajador y en el `detail` de los Problem Details (E32) | Nivel 1 |
| NFR10.5 | cambia | Los mensajes de un bloque o de un modo final no se quedan en Redis. | Las corridas de U6 usan C2 tal cual, con el borrado tras confirmar de U4. Prueba de nivel 1: tras una corrida de un bloque y una final, `XRANGE` de `veridicus:runs` y `veridicus:results` no contiene el texto; la clave de cancelación no lleva texto | Nivel 1 |
| NFR10.6 | cambia | El estado de la sesión solo cambia por las transiciones de §3 del Functional Design (BR9.8). | Ninguna ruta acepta `status` en el cuerpo; la comprobación del OpenAPI de C1 falla si aparece. La tabla de transiciones es código puro con 100 % de ramas y una prueba por transición prohibida (p. ej. `terminated → open`, `paused → suspended`, `consolidated → terminated`) que responde `409` con el `code` de la situación y 0 filas. `open → suspended` solo lo hace el supervisor. La parte de versiones de la revisión 1 queda **Retirada** con US1.2 | Nivel 0 y nivel 1 |
| NFR10.7 | cambia | Lo pegado y lo importado no evitan las guardias del análisis (AUTONOMIA-05). | Las corridas de un bloque, del modo final y de «Reanudar análisis» entran por la misma tubería de U4 (C2, trabajador, ingesta con verificación de citas y deduplicación por par) que un turno escrito; U6 no tiene camino propio hacia el analizador ni hacia la ingesta (import-linter). Prueba de nivel 1: un hallazgo con una cita alterada en la salida *fake* de un modo final no crea sugerencia | Nivel 0 y nivel 1 |
| NFR10.8 | cambia | Los textos nuevos de U6 no llevan etiquetas de veracidad (AUTONOMIA-03). | Los rótulos y mensajes de M1, M7, los diálogos de pegado, reanudación, terminar y retirada, la franja del modo final y el historial lateral salen del catálogo de U1 y pasan el escáner `scan(text, literal_sources)` en nivel 0 y sobre la interfaz renderizada en nivel 3, con 0 coincidencias y un control negativo | Niveles 0 y 3 |
| NFR10.13 | nuevo | El archivo importado se lee de forma segura y nunca toca el disco (BR7.1–BR7.3, BR7.9). | (a) El servidor lee el cuerpo `multipart` con tope de `import_file_max_bytes` + 16 384 bytes y responde `413` `limits.exceeded` antes de analizar el JSON (NFR3.13). (b) La parte `file` se guarda solo en memoria: nada se escribe en disco (sin archivo temporal de la aplicación, prueba que vigila el directorio temporal) y el Ingress no guarda el cuerpo en disco (NFR-U6-06). (c) Se decide por el contenido: JSON en UTF-8 o `415` `import.invalid_type`, sea cual sea el tipo declarado (NFR-U6-12). (d) Claves duplicadas o anidamiento mayor de 32 niveles → `422` `import.invalid_transcript` (NFR-U6-11). (e) Los mensajes de `ImportProblem` se arman con la posición, el campo y la regla, **nunca con el texto del validador**, que puede citar el valor; prueba con un *canary* en cada campo de un turno. (f) El nombre del archivo no se guarda ni se registra | Nivel 1 |
| NFR10.14 | nuevo | Todo error de U6 sale como Problem Details con un `code` de C1. | `413` `limits.exceeded` (nunca `422`, regla de U1), `415` `import.invalid_type`, `422` `import.invalid_transcript`, `import.profile_mismatch`, `profile.not_approved`, `profile.transfer_not_authorized`; `409` con el `code` de la situación de la tabla de §3 del Functional Design (incluidos `session.not_paused` y `session.not_finalized`, FD-U6-01 y FD-U6-02, que entran por PR de U1). `detail` en español, sin trazas, SQL ni testimonio | Nivel 0 y nivel 1 |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia | Lo que U6 cierra no se reabre. | Disparadores: `closed_to_new_turns` solo pasa de false a true; `ConsentRecord.withdrawn_at` y `withdrawn_by` solo pasan de nulo a valor, juntos; `blocked_code` nunca vuelve a nulo. Prueba de nivel 1: un `UPDATE` directo que intenta revertir cada uno falla. La inmutabilidad de versiones y pasajes de la revisión 1 queda **Retirada** con US1.2 | Nivel 1 |
| NFR11.2 | cambia | El historial de estados y los bloques solo admiten inserciones (BR4.6). | Cada `SessionStatusChange` de U6 lleva hora y actor: suspensión con `actor_kind = system` y `actor_system = session-supervisor` (valor de `ActorSystem`, FD-U6-13); importación, pausa, reanudación del análisis, reanudación y terminación con la persona. `TranscriptPaste` es `history` con la marca `veridicus-audit`. La prueba común de U3 cubre las tablas y filas nuevas y `UPDATE`/`DELETE` fallan con el usuario de la aplicación; solo el usuario de la retención borra, por `purge_session` (FD-U6-22) | Nivel 1 (prueba común de U3) |
| NFR11.3 | nuevo | La retirada lleva quién y cuándo fijados por el servidor (BR9.4). | La ruta no tiene cuerpo; `withdrawn_at` es la hora del servidor y `withdrawn_by` el dueño; una segunda retirada responde `409` `session.consent_withdrawn` y 0 filas (E43); `SessionSnapshot` expone solo la hora (FD-U6-21) | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | cambia | Los *fixtures* de U6 son sintéticos y marcados, también los que declaran `corpus`. | Bloques pegados, archivos de importación y los ejemplos de `speaker-markers.v1.yaml` usan el catálogo de nombres y las marcas de U1; la comprobación de U1 corre sobre las carpetas de pruebas de U6 con 0 hallazgos; `gitleaks` en la CI. Las entrevistas del piloto solo se importan en el Minikube local, nunca en Git ni en la CI (`project.md`) | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U6 |
|---|---|
| AUTONOMIA-01 | U6 no aplica nada al clúster. Las columnas y tablas nuevas (`TranscriptPaste`, ampliaciones de `ConsentRecord`, `Turn` y la máquina de la sesión, índice parcial) entran por un `Job` de migraciones en su propio PR, aditivas (*expand–contract*); las cifras nuevas de C25 entran por PR de U1 |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5); la medición sin umbral de NFR3.17 cumple con reporte por secciones y control negativo |
| AUTONOMIA-03 | NFR10.8, NFR11.2, NFR11.3 |
| AUTONOMIA-04 | §1, NFR1.1–NFR1.4, NFR10.4, NFR10.5, NFR10.13 |
| AUTONOMIA-05 | NFR10.7 y la equivalencia de turnos NFR4.1 (`reliability-requirements.md`) |

## 5. Riesgos aceptados

| Riesgo | Tratamiento |
|---|---|
| **Una transcripción real declarada `sintetico`.** FD-U6-05 (P5 = A) admite `sintetico` sin bloque y le da un consentimiento que autoriza la transferencia; el sistema no puede saber si el archivo es real | Aceptado por la decisión aprobada. Mitigan: el anonimizador siempre delante de un destino externo, el aviso de M7, el reporte que lo declara (U7), y el log y la métrica de importaciones por `origin` con quién importó (NFR1.4, NFR15.1). Se presenta en la aprobación |
| **Un bloque o un modo final grandes ocupan la cola.** Un modo final sobre 2 000 turnos puede tardar más que `run_deadline_final_s` de desarrollo | Lo mide NFR3.17; la corrida termina en error con «Relanzar modo final» (BR5.2), nunca en silencio. La cola la acota U4 con su tope de espera |
| **Doble envío de una importación** (FD-U6-23) | Límite declarado: M7 deshabilita «Importar» mientras crea; dos sesiones iguales se pueden terminar |
| **Una llamada ya en curso al pausar o retirar** | Límite declarado de CD-06: no se deshace; la clave impide las siguientes y la ingesta descarta su resultado |

## 6. Precisiones a artefactos ya aprobados (NFR-U6-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Las filas de la revisión 1 quedan como registro, marcadas
«Superado». Ninguna sale de una pregunta: todas salen de las fuentes.

| ID | Estado | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|---|
| — (rev. 1) | Superado | `rules.md` de U6 (BR2.3) | 60 turnos de testimonio y 200 en total. Lo sustituyen las cifras de C25 de U4 | Cambio 01; C25 |
| — (rev. 1) | Superado | C1 `/transcript` | `422` `transcript.too_large` y `turn.too_long`. Lo sustituye `413` `limits.exceeded` | Regla de U1; C1 revisión 3 |
| — (rev. 1) | Superado | `rules.md` de U6 (BR4.1) | Latido como máximo cada 15 s. Sigue, ahora como NFR-U6-05 con la cifra en C25 | P1 = A |
| — (rev. 1) | Superado | `rules.md` de U6 (BR4.5) | Reanudar pone `last_heartbeat_at` en la hora actual. Ya está en BR4.5 revisión 2 | R-01 de la revisión 1 de Functional Design |
| — (rev. 1) | Superado | `rules.md` de U6 y de U4 (republicar en el reenvío) | Lo sustituye BR2.5 revisión 2 (sin republicar) y NFR-U6-10 | Functional Design revisión 2 |
| — (rev. 1) | Superado | `entities.md` (`InterviewerLabels`) | Archivo compartido de etiquetas. Lo sustituye `speaker-markers.v1.yaml` (FD-U6-08) | P4 = A |
| — (rev. 1) | Superado | `rules.md` de U6 (BR2.6) | Comparación por ordinal de testimonio. BR2.6 revisión 2 compara turnos, no hallazgos | Cambio 01 |
| — (rev. 1) | Superado | C15 | Métricas de U6 de la revisión 1. Las sustituye NFR-U6-09 | NFR15.1 |
| NFR-U6-01 | Propuesta | `contract-summary.md` (C25) y U1 (catálogo de límites) | Cifras de U6: `import_file_max_bytes` = **2 097 152** (`bytes`) y `heartbeat_timeout_s` = **180** (`s`). Cifras nuevas: `session_sweep_interval_s` = **30** (`s`) y `heartbeat_write_min_s` = **15** (`s`). Entran por PR de U1 antes del código de B7. El archivo máximo (2 000 turnos y 250 000 caracteres) ocupa ≈ 1,4 MB en el peor caso de UTF-8 sin escapes, con ≈ 200 bytes de sobre por turno: queda un margen ≥ 45 %; la cifra coincide con `run_message_max_bytes` | Pedido de U4; P1 = A de la primera pasada |
| NFR-U6-02 | Propuesta | `rules.md` de U6 (BR2.3, BR7.2) | Además de los límites del bloque, un bloque que llevaría la sesión por encima de `transcript_max_turns` o `transcript_max_chars` responde `413` `limits.exceeded` con 0 filas, como un turno escrito en U4. Así el modo final de la sesión siempre cabe en `run_message_max_bytes` | Regla de U4 (turno que pasa los totales); C25 |
| NFR-U6-03 | Propuesta | `contract-summary.md` C1 (`PATCH /sessions/{id}/analysis`) y `rules.md` de U6 (BR9.1) | La ruta declara **`202`** con `SessionView` como única respuesta 2xx, en las dos direcciones, en vez de `200`: «Reanudar análisis» encola una corrida y U1 exige `202` en toda ruta que encola IA. Si prefieres conservar `200`, la alternativa es sacar la ruta de la lista de U1 | Regla de `202` de U1 frente a C1; se presenta en la aprobación |
| NFR-U6-04 | Propuesta | `contract-summary.md` C11 (`ReviewRounds`) | Variante por lotes `pending_counts(uow, session_ids) -> dict[UUID, int]`, que completa FD-U6-20: la lista arma `pending_suggestions` de 500 sesiones con una sola consulta (NFR3.2) | FD-U6-20; NFR3.2 |
| NFR-U6-05 | Propuesta | `rules.md` de U6 (BR4.1) | El latido se escribe a lo sumo una vez cada `heartbeat_write_min_s`, con la hora de la base y **sin esperar bloqueos**: si la fila de la sesión está bloqueada por otra escritura, ese latido se omite y el sondeo responde igual (un latido omitido no es un error) | Pregunta abierta de §11 del Functional Design; NFR3.3, NFR3.8 |
| NFR-U6-06 | Propuesta | Infrastructure Design de U2 (Ingress de `session-api` y el Ingress `veridicus-voice`) | `POST /api/v1/sessions/import` y `POST /api/v1/sessions/{id}/transcript` pasan por un Ingress que no escribe en disco el cuerpo de la petición (sin *buffering*, como `veridicus-voice`, o con un búfer en memoria ≥ 2 113 536 bytes), con un tope de cuerpo de 2 113 536 bytes en el Ingress. La respuesta de la importación (una `SessionView` de 2 000 turnos) tampoco se guarda en disco. Conviene que U2 revise lo mismo para el sondeo de U4 | BR7.9; aprendizaje de Infrastructure Design (ingress-nginx escribe en disco los cuerpos de más de 16 KiB) |
| NFR-U6-07 | Hecho | §11 del Functional Design de U6 | `run_deadline_final_s` no lo fija U6: lo fijó U11 (3 600 s en desarrollo, tope 43 200 s). NFR3.17 mide el modo final sobre el archivo máximo y la decisión de cambiarlo es un PR del perfil o del despliegue | NFR Requirements de U11 |
| NFR-U6-08 | Hecho | §11 del Functional Design de U6 | `cancel_key_margin_s` = 120 (U4) basta frente al desfase de relojes: en Minikube de un nodo los pods comparten reloj; una prueba de nivel 1 con el reloj del trabajador 110 s atrasado sigue dando 0 llamadas nuevas (`reliability-requirements.md`, NFR10.14) | NFR Requirements de U4 |
| NFR-U6-09 | Propuesta | `contract-summary.md` (C15) y las etiquetas permitidas del NFR de U1 | Métricas de U6 de `observability-requirements.md` §2, por PR de U1, con etiquetas de la lista (`state`, `outcome`, `error_code`) y una nueva, `origin` (`corpus`, `sintetico`, valores de enum de C1), para auditar las importaciones sintéticas (§5) | NFR15.1; NFR1.4 |
| NFR-U6-10 | Propuesta | `rules.md` de U6 (BR2.5, BR8.3, BR9.2) y §8 del Functional Design | Si la publicación de C2 falla tras confirmar, la respuesta sigue siendo `202` (las filas ya existen), se registra `ERROR` `run.publish_failed` y la corrida la cierra el supervisor de plazos de U4 con `analysis.system`; vale igual para el modo final y para «Reanudar análisis». El reenvío con el mismo `client_request_id` no republica | BR2.5 («sin *outbox*»); §8 |
| NFR-U6-11 | Propuesta | `rules.md` de U6 (BR7.3) | Dos problemas más en la lista de BR7.3: claves duplicadas en un objeto y anidamiento de más de 32 niveles; los dos dan `422` `import.invalid_transcript` y cuentan en el total | T1, T13; NFR10.13 |
| NFR-U6-12 | Propuesta | `rules.md` de U6 (BR7.1) | El servidor decide por el contenido y no por el tipo declarado: un archivo válido como JSON en UTF-8 se acepta aunque el navegador lo envíe como `application/octet-stream` o sin tipo; lo que no es JSON en UTF-8 da `415` | Navegadores que no declaran tipo para `.json`; BR7.1 |
