# Preguntas de Functional Design — U4 text-flow

**Unidad.** U4 `text-flow` (sin tipo): cargar e indexar un escenario y elegirlo (US1.1, US1.3), crear la
sesión (US2.1), enviar turnos sin bloquear (US2.2), evaluar con la guardia del umbral antes del juez y
sin alertas parciales (US3.1–US3.3, US4.1, US4.3), Paquete de Contexto de Traspaso (US4.2), creación de
sugerencias, escaneo de vocabulario prohibido (US5.5) y base de accesibilidad (US5.6).

**Lo que ya está decidido y no se vuelve a preguntar.** Guardia por afirmación antes del juez (ADR-006,
AC4.1.1–AC4.1.5); «no documentada» del juez se trata como por debajo del umbral; CoT interrumpida
determinista sin LLM; salida estricta C6 y alerta C7; colas C2–C4; cita literal entre «…» y lista de 9
términos (Functional Design de U1); 1 MB, Markdown o texto UTF-8 (FR2.1); 3 pasajes en el paquete
(FR5.3). Quedan los cinco huecos que `requirements.md` §7 y `contract-summary.md` asignaron a esta etapa.

---

## P1 — Regla para dividir un turno en afirmaciones (AC3.1.5)

La regla debe ser determinista y cada afirmación debe ser una subcadena literal del turno. Cada
afirmación se recupera y se califica por separado, así que la regla decide qué se puede alertar.

A. Por oración: cortar tras `.`, `?`, `!` o `…` seguidos de espacio o fin de línea, y en cada salto de
   línea; quitar espacios de los bordes y descartar trozos sin letras. Un turno sin esos signos es una
   sola afirmación. (Recomendada)
B. El turno completo es una sola afirmación.
C. Lo de A más cortes en `;` y en las conjunciones «y», «pero», «aunque» precedidas de coma.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Cómo se segmenta el escenario en pasajes (FR2.2)

Cada pasaje es lo que se cita en una alerta (cita literal) y lo que se compara por similitud con cada
afirmación.

A. Por párrafo (bloques separados por línea vacía) y por encabezado Markdown; un párrafo largo se parte
   en oraciones completas hasta un máximo de caracteres por pasaje, y nunca se parte una oración.
   (Recomendada)
B. Ventanas de tamaño fijo con solapamiento, sin mirar párrafos ni oraciones.
C. Una oración por pasaje.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Qué es el «identificador de documento» que cita la alerta

La alerta exige un ID de documento que pertenezca a la versión de escenario (AC3.1.2), y el PRD pide
enlazar la cita con «el identificador de documento dentro de la base de conocimiento». Un escenario es
un solo archivo, pero puede reunir varias piezas documentales (actas, informes).

A. Cada encabezado de primer nivel con la forma `# [DOC-…] Título` abre un documento con ese ID; si el
   archivo no tiene ninguno, todo el archivo es un documento con ID `DOC-1`. El ID es único dentro de la
   versión o la carga se rechaza. (Recomendada)
B. El ID de documento es siempre el de la versión de escenario (un documento por archivo).
C. El ID de documento es el encabezado Markdown más cercano al pasaje, tal como esté escrito.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Cuántos pasajes se recuperan por afirmación (top_k)

Los pasajes recuperados son lo único que el juez ve y lo único que la CoT puede citar (AC3.1.4); el
paquete muestra 3 (FR5.3). Más pasajes dan más contexto al juez pero alargan el *prompt* en CPU.

A. 3 por afirmación, los mismos que guarda el registro de evaluación y que muestra el paquete.
   (Recomendada)
B. 5 por afirmación al juez; el registro y el paquete guardan los 3 primeros.
C. Configurable entre 3 y 8, con 3 por defecto; el valor queda en la instantánea de la sesión.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Tamaño máximo de un turno

`contract-summary.md` dejó para esta etapa el tamaño máximo de un turno. Un turno largo es más lento en
CPU y produce más afirmaciones en un solo llamado al juez.

A. 2 000 caracteres; más largo se rechaza con `422` y el mensaje «El turno supera 2 000 caracteres.
   Divídelo en turnos más cortos». (Recomendada)
B. 4 000 caracteres, con el mismo tratamiento.
C. 8 000 caracteres, con el mismo tratamiento.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-21)

**Unidad.** U4 `text-flow` (sin tipo, MUST, L; Bolt B3): crear la sesión con su entrevista, su
consentimiento y su perfil (US13.1, US15.4, US2.1); enviar turnos sin bloquear (US2.2); el
AnalysisWorker en `semantic-agent`, que consume corridas, llama a la biblioteca de U11 (C17) y publica la
salida de C6 sin resultados parciales (cruces US3.2, US3.6); la ingesta en InterviewSession, la creación
de sugerencias de revisión en HumanReview y su presentación con las dos citas (US3.1), la limitación del
modo fragmentado (cruce US3.7) y el registro de modelos de solo lectura (cruce US12.5, AC12.5.3); el aviso
de propósito limitado (US15.5); el escaneo de vocabulario prohibido de salida e interfaz con el escáner de
U11 (US5.5); el contrato de import-linter de `semantic-agent` (mitad de AC11.6.4); la base de
accesibilidad y la suite `axe` (US5.6). La revisión 1 (2026-10-03) es anterior al cambio 01 y se revisa
por Modify.

**Lo que ya está decidido y no se vuelve a preguntar.**
- *Sale de U4* (unit-of-work revisión 3, «Sale»; `docs/iteracion2.md` §2.5 y §2.8; regla de `project.md`
  sobre el cambio 01): escenarios, indexación y catálogo (US1.1, US1.3), guardia del umbral, afirmaciones,
  pasajes, *embeddings*, CoT interrumpida y Paquete de Contexto de Traspaso (US4.1–US4.3), ModelGateway y
  el prompt del juez (pasan a U11), y la propiedad del escáner (pasa a U11; FD-U1-09). Con ellos salen las
  respuestas P1–P4 de esta página.
- *Sesión:* exige entrevista, un perfil aprobado y el bloque `consentimiento`; queda ligada a su
  configuración efectiva y su `config_sha256` toda su vida; un perfil comercial sin
  `autoriza_transferencia` da `422` `profile.transfer_not_authorized`; ningún perfil viene preseleccionado
  (C1 `POST /sessions` y `Consent`; AC2.1.1–AC2.1.5, AC13.1.1–AC13.1.4, AC15.4.1–AC15.4.5; ADR-006; CD-10).
- *Turnos:* hablante `ENT` o `TEST` elegido por el analista, numeración sin huecos, `client_request_id`,
  `202` sin esperar, `413` `limits.exceeded` por encima de `turn_max_chars` (AC2.2.1–AC2.2.6, C1, C25). La
  cifra de P5 la fija NFR Requirements en el catálogo C25, no esta etapa.
- *Colas:* sobres de C2 y C3, entrega al menos una vez con `XAUTOCLAIM` y *stream* de fallidos, plazo de la
  corrida vigilado por InterviewSession (`analysis.system`), cancelación con la clave
  `veridicus:run-cancelled:{run_id}` (CD-06), reintento humano con `attempt + 1` y descarte de intentos
  viejos, corridas `cancelled` o vencidas (C2, C3, P3 de Contract Design; AC2.2.3, AC2.2.4, AC3.2.3).
- *Ingesta:* `salida` inválida → `analysis.invalid_output`; `estado: error` → se guardan la corrida y su
  `registro` sin hallazgos; vocabulario prohibido en `hecho` u `observaciones` → toda la corrida en
  `analysis.invalid_output`, sin quitar hallazgos en silencio (C3; U1 F3 y BR5.4, R-09); incidente
  (`incidente_anonimizacion` o una llamada externa con `anonimizado: false`) → sesión `blocked` con
  `anonymizer.incident`, `AnonymizationIncident` y `409` `session.blocked` a toda corrida nueva (ADR-013,
  AC11.3.8, CD-11, B3 punto 6).
- *Sugerencias:* `SuggestionProposer.propose` guarda cada hallazgo como sugerencia pendiente y une sin
  duplicar por el par no ordenado (turno, cita normalizada en espacios), conservando el estado de lo ya
  decidido; abre la ronda 1 si hace falta (C10, AC3.6.3, AC2.7.2).
- *Trabajador:* sin usuario de base de datos, una corrida a la vez, misma salida que la CLI salvo fechas,
  `InputRejected` → `analysis.system` y fallidos, `Cancelled` → confirma sin publicar (components
  AnalysisWorker; C17; AC2.2.7; U11 §9). Arma el gateway con el cliente HTTP de C21, llama a
  `check_ready()` y no puede importar ni instalar `libs-anonymizer`: contrato `semantic-agent-no-anonymizer`
  más las comprobaciones de lockfile, imagen y `sys.modules` (FD-U10-03; C13; B3 punto 5).
- *Consentimiento y estados de U6:* tras la retirada no se encola ni analiza ninguna corrida
  (VE-10 (a), DD-06, C2); pausar, terminar, retirar, reanudar, importar y el modo final son rutas de U6
  (C1, «Ruta de cada unidad»).
- *Consola:* causas de cada `error.codigo` (AC3.2.5, CD-08), estado de sesión bloqueada en M4 (mockups
  revisión 3), aviso de propósito limitado servido por ConsoleApi desde C8 (US15.5, R-03), sondeo con cursor
  (P6 de Contract Design, intervalo en C25), rótulos de los 7 tipos (FD-U1-08), registro de modelos de
  solo lectura (M4 §6.8), texto del modo fragmentado (AC3.7.1), anuncios `aria-live` por corrida
  (mockups, tabla de precisiones).
- *Lo que U3 ya le pide a U4 con propuesta clara:* el puerto `PendingSessions.count_pending` (FD-U3-04),
  el actor `analysis-worker` (FD-U3-08), `AnalysisRun` como `history` con una tabla propia de cambios de
  estado (FD-U3-10) y el orden de bloqueo usuario → sesión → ronda (FD-U3-13).
- *Lo que U10 y U11 le dejan a U4:* el efecto de `anonimizador_no_disponible` en la sesión (UG-02, CD-01,
  FD-U10-16) y el bloqueo ante el incidente (U11 F8); la deduplicación entre corridas ya la resuelve C10.

**Cómo se registra la revisión 2.** Igual que en las demás segundas pasadas (regla de `project.md`): los
ID que siguen se conservan, los que salen quedan «Retirado» sin renumerar y lo nuevo toma la numeración
siguiente.
- *Entidades:* quedan «Retirado» Scenario, ScenarioVersion, ScenarioDocument, Passage, Claim,
  TurnEvaluation, ClaimEvaluation, HandoffPackage, ThresholdConfig y JudgePrompt. Siguen
  InterviewSessionRecord, SessionStatusChange y Turn (con sus atributos de components revisión 3);
  ReviewSuggestion y ReviewRound pasan a citarse como entidades de HumanReview (U5) que U4 solo crea por
  C10. Entran ConsentRecord, AnalysisRun, ModelCall, DiscardedCandidate, AnonymizationIncident y la tabla
  de cambios de estado de la corrida (FD-U3-10).
- *Reglas:* quedan «Retirado» BR1.x–BR3.x, BR6.x, BR7.x, BR8.3, BR9.2, BR10.x y BR13.5
  (`iteracion2` §2.8); cambian BR4.1, BR8.x, BR9.1, BR11.x, BR12.x y BR13.2; lo nuevo empieza en BR14.1.
- *Flujos, escenarios y consola:* F1, F2 y F9 quedan «Retirado»; F3–F8 y F10 cambian; lo nuevo empieza en
  F11. Los escenarios que dependen del umbral o del paquete quedan «Retirado» y los nuevos empiezan en E24.
  ScenarioCatalog, UploadScenarioDialog, HandoffPanel y UndocumentedNotice quedan «Retirado» en
  `frontend-components.md`.
- *Precisiones:* la tabla del §9 conserva sus filas de la revisión 1 marcadas «Superado» y suma filas
  `FD-U4-01` en adelante, como las demás unidades.
- *Revisión 1 (`reviews/review-01.md`):* R-01 (b) se resuelve con P9; R-01 (a) y R-02 quedan resueltos por
  C1 y C3 y por lo que sigue; R-03, R-04 y R-05 quedan «Retirado», porque el juez, los pasajes y la
  división en afirmaciones salen de U4.

**Lo que el diseño resolverá sin preguntar** (va como propuesta a la tabla de precisiones de
`functional-spec.md`; puedes objetarlo en la aprobación):
- El estado de cada turno se deriva del último intento de la última corrida incremental que lo cubre; en
  una sesión importada, de la corrida final. El modo final se muestra en su franja y no en cada turno.
- «Reintentar» responde `409` con la sesión en pausa (`session.paused`) o consolidada, como el modo final
  en AC2.7.5 (código propuesto `session.consolidated`, nuevo en C1). Si `propose` rechaza en la ingesta
  (p. ej. `review.round_locked` por una carrera), la corrida queda en `error` con `analysis.system`, el
  mensaje se confirma y no se guarda ninguna sugerencia; lo cubre una prueba de nivel 1 (cierra R-02 de la
  revisión 1).
- Toda escritura que cambia la sesión toma el orden usuario → sesión → ronda y hace `change_cursor.bump`
  sobre la fila de la sesión (FD-U3-13; regla de NFR Design).
- `AnalysisRun.anonymized` es verdadero solo si todas sus llamadas externas lo son, y no aplica a una
  corrida solo local.
- Tras la muerte de un trabajador, la corrida se repite entera (AC2.2.4); el registro guarda solo las
  llamadas de la entrega que publica el resultado, y se declara como limitación del costo informado.
- Una sola cola FIFO para incrementales y finales (C2); la prioridad o las réplicas las decide NFR
  Requirements si la latencia lo pide.
- `GET /notice` pasa a ser pública (`security: []`), porque el aviso debe verse también en M0, antes de
  iniciar sesión (AC15.5.1; precisión de C1).
- `session.consent_missing` en los turnos (AC15.4.2) queda como guardia defensiva probada con un
  *fixture*, porque C1 ya exige el consentimiento al crear la sesión; sin la constancia del mandato
  (AC15.4.4) la creación responde `422`, como dice el esquema de `Consent`.
- U4 crea `retention_days` y `retention_until` sin valor en InterviewSessionRecord; el campo del formulario
  y su validación (AC15.7.1, AC15.7.3) entran con U13 como cambio menor de `POST /sessions`. U4 implementa
  `Purgeable` (C24) para sus tablas.
- Textos propuestos para el catálogo, a confirmar en la aprobación: la causa de `analysis.system`
  («El análisis no terminó a tiempo o no se pudo completar. Revisión manual requerida») y el aviso de turno
  plegado de AC3.1.4.

Quedan seis decisiones de criterio.

---

## P6 — Qué pasa con la sesión cuando el anonimizador no está disponible (UG-02)

El fallo cerrado (`anonimizador_no_disponible`, `analysis.anonymizer_unavailable` en C1) significa que no
salió ninguna llamada (AC11.3.3). No solo ocurre cuando el proxy está caído: según C21, un PR que cambia un
perfil hace que todas las sesiones creadas con la versión anterior reciban `409` en sus llamadas externas
y terminen en este código. CD-01 dejó a esta etapa decidir si, además de fallar la corrida, bloquea la
sesión.

A. Solo falla la corrida: queda en `error` con `analysis.anonymizer_unavailable` y su causa (AC3.2.5); la
   sesión sigue en su estado y el dueño puede «Reintentar» cuando el proxy vuelva. El bloqueo queda
   reservado al incidente, que es cuando sí salió algo. (Recomendada)
B. Falla la corrida y la sesión pasa a `blocked`, como con el incidente.
C. Falla la corrida y, tras *N* fallos seguidos de este código en la misma sesión (*N* en C25), la sesión
   pasa a «Análisis en pausa» con actor `analysis-worker`, para que el analista decida cuándo reanudar.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — Qué admite una sesión bloqueada por un incidente y si se desbloquea

AC11.3.8 y C3 solo fijan que la sesión pasa a `blocked`, rechaza corridas nuevas y registra el incidente.
No dicen si se aceptan turnos, si se pueden decidir y consolidar los hallazgos que ya había, ni si el
bloqueo termina alguna vez. No existe ninguna ruta para desbloquear.

A. Bloqueo definitivo del análisis: se rechazan corridas y turnos nuevos con `409` `session.blocked` y se
   cancelan las corridas en curso; se pueden leer y decidir las sugerencias existentes, finalizar y
   consolidar, y el reporte (U7) declara el incidente. No hay desbloqueo en el MVP. (Recomendada)
B. Bloqueo definitivo y total: solo lectura; no se deciden sugerencias ni se consolida.
C. Como A, pero los turnos nuevos se aceptan y se guardan sin analizar, como en pausa.
D. Como A, y además un `Job` revisable que lanza el humano desbloquea la sesión tras revisar el incidente,
   con actor y hora en SessionStatusChange.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P8 — Alcance del incidente fuera de su sesión

Un incidente quiere decir que una llamada salió sin anonimizar, pese a que U10 garantiza
`anonymized: true` por construcción (FD-U10-16). Si la causa es un defecto del camino comercial, las demás
sesiones con perfil comercial siguen usando ese camino hasta que alguien actúe. VE-14 y AC11.3.8 solo
hablan de «la sesión».

A. Solo se bloquea la sesión del incidente, como dicen VE-14 y AC11.3.8; el incidente queda registrado
   con IDs y visible en su sesión. (Recomendada)
B. Además, mientras haya un incidente sin cierre, InterviewSession rechaza toda corrida nueva con destino
   externo en cualquier sesión (los perfiles locales siguen funcionando). El cierre lo registra un `Job`
   revisable que lanza el humano, con actor y hora. Suma un `code` a C1.
C. Como B, pero solo para las sesiones con el mismo perfil.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P9 — Quién pasa una corrida a «Procesando»

AC2.2.1 y AC2.7.3 piden ver «Procesando» y «Modo final en proceso», y `Run.status` de C1 tiene
`processing`. Pero el trabajador no escribe en la base (ADR-002) y C3 solo trae el resultado final, así que
nadie puede registrar ese paso (hallazgo R-01 (b) de la revisión 1). Más adelante, US10.1 (U6, SHOULD)
pedirá además la etapa y «ventana N de M».

A. El trabajador publica en `veridicus:results` un mensaje `RunStarted` (`run_id`, `attempt`,
   `started_at`) al tomar la corrida, como cambio menor de C3 con su prueba de contrato; InterviewSession
   lo ingiere y pasa la corrida a `processing` con actor `analysis-worker`. U6 puede ampliarlo después con
   la etapa y las ventanas. (Recomendada)
B. Sin mensaje nuevo: al componer la vista, InterviewSession deduce `processing` de los pendientes del grupo
   de consumidores en Redis. No cambia el contrato, pero la vista depende de Redis y el paso no queda
   registrado.
C. Se quita `processing`: la corrida se ve «En cola» hasta su resultado. Precisa AC2.2.1 y AC2.7.3.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P10 — Si un turno del entrevistador encola su propia corrida

AC2.2.3 dice que el turno *n* encola una corrida con `desde_turno = hasta_turno = n`. Pero M4 §6.4 muestra
el turno del entrevistador «sin estado, como contexto», y con un perfil comercial cada corrida envía la
transcripción hasta ese turno, con su costo. Una contradicción entre la pregunta `ENT` y la respuesta
`TEST` siguiente igual la encuentra la corrida del turno `TEST`, porque esa cita cae en el tramo.

A. Todo turno encola su corrida, también los `ENT` (lectura literal de AC2.2.3).
B. Un turno `ENT` se guarda sin corrida y se muestra sin estado; solo un turno `TEST` encola su corrida, y
   la corrida lleva los turnos `ENT` anteriores como contexto. AC2.2.3 se lee como «el turno *n* del
   testimonio» (precisión). El pegado de bloques (U6) no cambia. (Recomendada)
C. Un turno `ENT` queda pendiente y se une a la corrida del siguiente `TEST`, con `desde_turno` en el
   `ENT`.
X. Other (please specify)

[Answer]: B **Mode:** guided

## P11 — Un tramo incremental en error cuando el modo final ya terminó

Para consolidar hay que terminar el modo final (P6 de `iteracion2`), que analiza toda la transcripción. Un
tramo incremental que falló antes sigue con su error («Tramo no evaluado»), aunque el modo final ya cubrió
esos turnos. Lo que se decida aquí lo usa también el reporte (U7).

A. Cuando el último modo final lanzado termina bien, el tramo deja de contar como «Tramo no evaluado»: en
   M4 sigue en «Corridas» con su error y el rótulo «Cubierto por el modo final», y el reporte no lo lista
   como no evaluado. (Recomendada)
B. Sigue como «Tramo no evaluado» en la sesión y en el reporte hasta que se reintente con éxito.
C. Como A en la sesión, pero el reporte lista también los tramos incrementales que fallaron, como
   información, sin llamarlos «no evaluados».
X. Other (please specify)

[Answer]: A **Mode:** guided
