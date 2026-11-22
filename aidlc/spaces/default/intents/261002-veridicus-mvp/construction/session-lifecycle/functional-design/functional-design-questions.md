# Preguntas de Functional Design — U6 session-lifecycle

**Unidad.** U6 `session-lifecycle` (tipo `service`): versión nueva de un escenario (US1.2), pegar una
transcripción (US2.3), lista de sesiones (US2.5), suspensión y reanudación (US7.1), progreso (US10.1,
SHOULD) e historial lateral (US11.2, COULD).

**Lo que ya está decidido y no se vuelve a preguntar.** Versión nueva con SHA-256 propio e inmutable
(FR2.4, AC1.2.1–AC1.2.4); la suspensión por falta de latido con *T* de NFR Requirements y el sondeo como
latido (contract-design P6); el diálogo de reanudación (AC7.1.2); los turnos pegados siguen el mismo
camino que los enviados uno a uno, con tope de 2 000 caracteres por turno (Functional Design de U4,
P5). Quedan los tres huecos que `requirements.md` §7 y `contract-summary.md` asignaron a esta etapa.

---

## P1 — Formato de la marca de hablante

Una transcripción se divide en turnos por línea vacía o por marca de hablante (FR3.3), y
`requirements.md` dejó a esta etapa el formato exacto de la marca (un prefijo de línea del tipo
`Nombre:`).

A. Una línea que empieza por 1 a 30 caracteres sin dígitos ni `:` seguidos de `:` y espacio (p. ej.
   «Compareciente: », «Analista: ») abre un turno nuevo; la marca se guarda aparte como hablante y no
   entra en el texto del turno. (Recomendada)
B. Solo cuentan como marca las etiquetas de una lista fija («Compareciente:», «Analista:»,
   «Entrevistador:»).
C. La marca abre un turno nuevo pero se conserva dentro del texto del turno.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué pasa con las líneas del entrevistador

Una transcripción real alterna preguntas del analista y respuestas del compareciente. Si todo se evalúa,
las preguntas del analista se contrastan con el marco de verdad como si fueran testimonio.

A. Los turnos cuyo hablante es el entrevistador (marca de una lista configurable, por defecto
   «Analista» y «Entrevistador») se guardan como contexto, no se evalúan y sí cuentan como turnos
   previos del paquete; los demás se evalúan. (Recomendada)
B. Todos los turnos se evalúan, sin importar el hablante.
C. Los turnos del entrevistador se descartan: no se guardan.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Tamaño máximo de una transcripción pegada

`contract-summary.md` dejó a esta etapa el tamaño máximo de una transcripción pegada. Todos sus turnos
entran a la cola a la vez, y cada uno respeta el tope de 2 000 caracteres.

A. Hasta 100 turnos y 100 000 caracteres; un turno de más de 2 000 caracteres se marca en la vista
   previa e impide confirmar hasta corregirlo. (Recomendada)
B. Hasta 50 turnos y 50 000 caracteres, con el mismo tratamiento.
C. Sin tope de turnos; solo los 2 000 caracteres por turno.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-22)

**Unidad, segunda pasada.** U6 `session-lifecycle` (tipo `service`) entrega ahora: pegar un bloque
(US2.3), la lista de sesiones (US2.5), importar una transcripción con turnos y páginas (US2.6), lanzar el
modo final (US2.7), reanudar una sesión interrumpida (US7.1), pausar o terminar el análisis y registrar la
retirada del consentimiento (US15.2, VE-10), el progreso (US10.1, SHOULD) y el historial lateral (US11.2,
COULD). Sale la versión nueva de un escenario (US1.2) (`unit-of-work.md` U6, revisión 3).

## Lo que ya está decidido y no se vuelve a preguntar

| Tema | Qué está decidido | Fuente |
|---|---|---|
| Rutas y códigos de U6 | `GET /sessions`, `/sessions/import`, `/transcript`, `/final-runs`, `/heartbeat`, `/resume`, `PATCH /analysis`, `/terminate`, `/consent-withdrawal`, con sus `409` (`session.paused`, `session.terminated`, `session.consent_withdrawn`, `session.closed_to_new_turns`, `session.not_suspended`, `run.final_in_progress`), `413` `limits.exceeded`, `415` e `import.*` | `contract-summary.md` C1 (rutas, `ErrorCode`, tabla «Ruta de cada unidad») |
| Máquina de la sesión | Enum único `open, paused, suspended, finalized, terminated, blocked, consolidated`; la pausa es solo `open ↔ paused`; la retirada no es un estado: fija `ConsentRecord.withdrawn_at` y `closed_to_new_turns`; `blocked_code` permanente; `blocked → finalized` por el dueño (FD-U4-18, que esta unidad acepta) | C1 `SessionStatus`; Functional Design de U4 §3, BR5.5, FD-U4-18 |
| Rechazo de turnos por estado | Orden de las comprobaciones y code por situación; en pausa el turno se guarda con `202` y sin corrida; `session.suspended` para una sesión suspendida | U4 BR5.5, FD-U4-07 |
| Turnos ENT y TEST | Hablante `ENT` o `TEST`; un turno `ENT` se guarda sin corrida y es contexto del `TEST` siguiente | FR3.2; C1 `Turn`; FD-U4-01 |
| Pegado | Vista previa en la consola y autoridad en el servidor con la misma especificación y los mismos ejemplos; una sola corrida incremental `desde_turno = n`, `hasta_turno = n+k−1`; límites del catálogo con `413` y mensaje «El bloque tiene N turnos; el máximo es M» | FR3.3, FR4.9; AC2.3.1–AC2.3.4; M4 §6.7 |
| Importación | Formato de entrada de C6 con su bloque `consentimiento` (A-4); nace cerrada a turnos nuevos y sin corridas; `modo: final` obligatorio; `perfil` igual al del formulario; primer problema y total; límites en el exacto y en el +1; vista previa con turnos, páginas, ENT y plegados; el archivo no se guarda tal cual; las 10 entrevistas del piloto se pueden importar en el Minikube local, nunca en Git ni en la CI | FR3.6, FR3.7; AC2.6.1–AC2.6.5; C1 `/sessions/import`; M7; `docs/iteracion2.md` P5 y P7 = A |
| Modo final | Se lanza en una guiada finalizada o en una importada; se relanza mientras no esté consolidada y cuenta el último; dos lanzamientos simultáneos dan `202` y `409`; se deduplica por par no ordenado y lo decidido conserva su estado; la corrida la aportan U4 y U11 | FR4.9; AC2.7.1–AC2.7.6; U4 F12, BR11.2; `docs/iteracion2.md` P6 = A |
| Pausa, terminación, retirada | Pausar cancela lo encolado sin llamar a modelos y guarda los turnos sin encolar; terminar cancela y cierra a turnos nuevos y se puede consolidar después; tras la retirada no se encola ni se analiza ninguna corrida nueva; cancelación con la clave `veridicus:run-cancelled:{run_id}`; los estados se leen con texto en M4 y en M1; los botones van en la barra de M4 | VE-10 y DD-06 (a) y (b); AC15.2.1–AC15.2.4; CD-06; U4 BR15.4; `mockups.md` precisiones de la revisión 3 |
| Suspensión y reanudación | El sondeo del dueño es el latido; *T*, el intervalo de revisión y el sondeo lento los fija NFR Requirements; diálogo de reanudación con su texto; sin duplicados al reanudar; `403` a otro analista | FR8; AC7.1.1–AC7.1.5; contract-design P6; M1 |
| Lista e historial | Columnas entrevista, origen, perfil, dueño, fecha y estado, con filtro «Solo las mías», estado vacío, paginación de 25 y estado con texto e icono; el `admin` en solo lectura; historial lateral con la misma ruta | AC2.5.1–AC2.5.3; AC11.2.1; M1 |
| Finalizar y consolidar | Finalizar y consolidar son de U7; U6 solo deja permitidas las transiciones en su máquina | `unit-of-work.md` U6 «Límites» y U7 |
| Cifras | Todas las cifras (*T*, plazos, límites de turnos y caracteres) viven en el catálogo C25 y las fija NFR Requirements | `project.md` (catálogo único de límites); C25 |
| Corte del calendario | Las partes SHOULD/COULD de B7 se recortan antes que su alcance MUST, y nunca se rebaja una prueba | `bolt-plan.md` B7 y «Si el calendario no alcanza» |

## Cómo se registra la revisión 2

- Los artefactos de la primera pasada (revisión 1, 2026-10-02) se reescriben como **revisión 2**
  conservando los ID. Lo que sale queda **«Retirado»** con su número, sin renumerar (`project.md`):
  F1, BR1.1–BR1.4, `ScenarioVersion` y US1.2 (cambio 01); `InterviewerLabels` y la marca libre
  `Nombre:` (P1 y P2 de la primera pasada, superadas por el hablante `ENT`/`TEST`); el tope de P3
  (superado por el catálogo C25 y `limits.exceeded`); `SessionListItem.pending_suggestions` (R-05 de la
  revisión 1, sin historia que lo respalde).
- Lo que cambia conserva su ID con «cambia» (BR2.x, BR3.x, BR4.x, BR5.x, F2–F6), y lo nuevo toma los
  grupos siguientes: BR7 importación, BR8 modo final, BR9 pausa, terminación y retirada (y F7–F9).
- Los hallazgos R-01 a R-05 de `reviews/review-01.md` se integran en la revisión 2 y se citan por ID en
  la regla que los resuelve.
- La tabla §9 de precisiones conserva sus tres filas de la revisión 1 marcadas «Superado» y suma las
  nuevas como FD-U6-01, FD-U6-02, …; ningún artefacto aprobado se edita (`project.md`).
- `traceability.json` marca US1.2 como retirada y suma US2.6, US2.7 y US15.2.

## Lo que el diseño resolverá sin preguntar

Cada punto entra como propuesta; los que precisan un artefacto aprobado van a la tabla de precisiones
para que el humano decida en la aprobación.

1. **Pegado sobre la tubería de U4.** Reutiliza F4 de U4: bloqueo y numeración seguida, `client_request_id`
   idempotente (el reenvío devuelve los mismos turnos y la misma corrida), rechazo por estado con el orden de
   BR5.5. Un bloque sin ningún turno `TEST` no crea corrida (coherente con FD-U4-01); en pausa, los turnos
   se guardan sin corrida. La entrega fiable de R-02 se resuelve igual que en U4: si la publicación falla
   tras el commit, el supervisor de plazos (BR5.8) deja la corrida en `error` con «Reintentar tramo»; no se
   añade un *outbox*.
2. **Equivalencia del pegado (BR2.6, cambia).** Pasa a «pegar e importar producen los mismos turnos que
   escribirlos uno a uno» (definición de terminado 2 de B7); la igualdad de resultados deja de ser
   verificable con el modo incremental por bloque (`docs/iteracion2.md` C10).
3. **Suspensión (R-01).** Crear y reanudar fijan `last_heartbeat_at = ahora`; un valor nulo se lee como
   `created_at`. La tarea es idempotente y solo suspende sesiones `open`, guiadas o importadas (la demo de B7
   importa y cierra el navegador). Una sesión `paused` no se suspende: ya no analiza. El actor es el valor
   nuevo `session-supervisor` de la lista `ActorSystem` (precisión a FD-U3-08).
4. **Reanudar.** Solo desde `suspended`; si el dueño tiene varias sesiones suspendidas, el diálogo de M1
   muestra la más reciente y las demás se reanudan desde la lista.
5. **Transiciones que las fuentes no fijan.** Terminar se admite desde `open`, `paused`, `suspended` y
   `blocked` (conserva `blocked_code`); finalizar (ruta de U7) desde `open`, `paused`, `suspended` y
   `blocked`; `terminated → consolidated` lo hace U7, porque C1 dice «se puede consolidar después»
   (precisión a la máquina de U4, que marca `terminated` como final). El modo final en una sesión `paused`
   responde `409` `session.paused`.
6. **Reanudar el análisis tras la pausa.** «Reanudar análisis» encola **una** corrida incremental desde el
   primer turno `TEST` que no tiene una corrida `done` o en curso (incluidos los cancelados por la pausa)
   hasta el último turno: es la lectura de «sin encolar análisis hasta que pulso Reanudar» (AC15.2.1),
   como precisión.
7. **Retirada del consentimiento.** Hora del servidor (la ruta no lleva cuerpo) y `withdrawn_by`; diálogo
   modal porque es irreversible; se admite en cualquier estado salvo `consolidated`; un segundo registro
   responde `409` `session.consent_withdrawn` sin filas; lo ya analizado se conserva y lo borra solo la
   retención (U13). Lo que pasa con el modo final se pregunta en P6.
8. **Lista.** Los estados nuevos se leen «Análisis en pausa», «Sesión terminada» y «Bloqueada», con icono
   decorativo; filtro por estado con el enum de C1; el `investigador` recibe `403` (AC2.1.4).
9. **Importación de datos del piloto.** Permitida solo en el clúster local (P7 = A); los logs llevan solo
   IDs y nunca texto del archivo; ningún *fixture* de prueba usa datos reales.
10. **Frontera AUTONOMIA-04.** Todo lo de U6 corre en `session-api` y `frontend`, dentro del clúster; lo
    único que puede salir es la corrida, por la tubería de U4 con el anonimizador delante (U10). La
    retirada y la pausa impiden además que salga cualquier llamada nueva (clave de CD-06).
11. **Accesibilidad.** M1, M7, el diálogo de pegado, el de reanudación, los de terminar y retirar y el
    historial lateral entran en la suite `axe` de U4 (BR6.1 se mantiene).

## P4 — Marcas de hablante en el bloque pegado

La primera pasada (P1 y P2 = A) suponía un hablante libre («Compareciente:», «Analista:») y una lista de
entrevistadores. El cambio 01 fija el hablante en `ENT` o `TEST` (FR3.2, `Turn.hablante` de C1) y
`docs/iteracion2.md` P5 dice «hablante elegido por el analista». Además, la revisión 1 (R-04) mostró que
una marca libre abre turno con líneas del testimonio como «Entonces dijo: …». El cuerpo de
`POST /transcript` solo lleva `text` y `client_request_id`.

A. Una línea que empieza por `ENT:` o `TEST:`, o por un alias de una lista versionada en `contracts/`
   («Entrevistador:», «Analista:» → `ENT`; «Testimonio:», «Compareciente:» → `TEST`), sin distinguir
   mayúsculas ni tildes, abre un turno con ese hablante; cualquier otra «Palabra:» queda en el texto. Un
   bloque sin marca hereda el hablante del turno anterior, y el primero es `TEST`. Para corregir, el
   analista usa «Volver a editar» y escribe la marca; C1 no cambia. (Recomendada)
B. Solo `ENT:` y `TEST:` literales, sin alias; el resto igual que A.
C. Como A, y además el analista cambia el hablante de cada turno en la vista previa; el cuerpo de C1 suma
   un arreglo de hablantes (precisión al contrato).
D. Sin marcas: todo el bloque toma un único hablante que el analista elige antes de pegar.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Importar una transcripción sintética sin consentimiento

FR3.6 y la ruta `/sessions/import` de C1 aceptan `origen: sintetico` sin bloque `consentimiento`, y C6
también (U1, E19). Pero AC2.6.2 rechaza con `422` un «`origen` distinto de `corpus`», y U4 exige un
`ConsentRecord` en toda sesión (BR14.3: sin él, toda corrida responde `session.consent_missing`) y una
autorización de transferencia para un perfil comercial (BR14.5). Las pruebas y la demo usan
transcripciones sintéticas.

A. Se importan `corpus` (con su bloque) y `sintetico` (con o sin él); AC2.6.2 se lee «origen fuera de
   {`corpus`, `sintetico`}» (precisión). Sin bloque, la sesión guarda un `ConsentRecord` de tipo nuevo
   `sintetico` (precisión a U4: transferencia autorizada, voz y audio no), M7 muestra «Transcripción
   sintética: no corresponde a una persona real; no se registra consentimiento» y el reporte lo declara.
   (Recomendada)
B. Se importa `sintetico`, pero si el archivo no trae el bloque, M7 pide el mismo formulario de
   consentimiento de M3.
C. La consola solo importa `corpus` (lectura literal de AC2.6.2); lo sintético entra por la CLI o pegado
   en una sesión guiada.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — El modo final después de la retirada del consentimiento

C1 dice que, desde la retirada, «no se encola ni se analiza ninguna corrida», DD-06 (a) habla de
«ninguna corrida nueva» y U4 ya rechaza los reintentos con `session.consent_withdrawn` (BR5.9). Pero
AC15.2.3 dice «When lanzo el modo final o llega un turno posterior, Then ningún turno posterior a la
retirada entra en una corrida», lo que admitiría un modo final sobre los turnos anteriores.

A. Ninguna corrida tras la retirada: el modo final y los reintentos responden `409`
   `session.consent_withdrawn` y se cancela lo encolado. Lo ya analizado se conserva; la sesión se puede
   finalizar y consolidar (U7), y el reporte declara la retirada con su hora y los tramos sin evaluar.
   AC15.2.3 se precisa: tampoco hay modo final. (Recomendada)
B. Se admite el modo final y el reintento, limitados a los turnos registrados antes de la retirada
   (`hasta_turno` = último turno anterior).
C. Como A, y además la retirada pasa la sesión a `terminated`.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — Progreso del modo final (US10.1, SHOULD)

AC10.1.1 pide, en el modo final, «cuántas ventanas o llamadas van de cuántas». El trabajador no escribe en
la base (ADR-002), C3 solo trae `RunStarted` (FD-U4-02) y el resultado, y la biblioteca de U11 (ya
revisada) no avisa del progreso. Las partes SHOULD de B7 son las primeras que se recortan.

A. Una clave de Redis `veridicus:run-progress:{run_id}` (hechas / total) que escribe el trabajador y lee
   InterviewSession al armar la vista, con el mismo vencimiento que la de cancelación; exige un aviso de
   progreso en la biblioteca de U11 (precisión a U11 y a C17, cambio menor).
B. Sin cambio de contrato: etapa («En cola», «Analizando contradicciones…») y cronómetro, más el total de
   ventanas que calcula `session-api` con la ventana y el solapamiento registrados, sin «van N»; AC10.1.1
   se precisa. (Recomendada)
C. Un mensaje `RunProgress` en `veridicus:results` (cambio menor de C3) que InterviewSession ingiere y
   guarda en la base.
X. Other (please specify)

[Answer]: B **Mode:** guided
