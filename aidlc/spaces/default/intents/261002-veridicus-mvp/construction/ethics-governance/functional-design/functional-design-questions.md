# Preguntas de Functional Design — U13 ethics-governance

- **Unidad:** U13 `ethics-governance` (tipo `service`), directorio `u13-ethics-governance`. Es una unidad de
  **demostración** (DD-01 a DD-05), de tamaño M. Va en el Bolt B13, el último antes del corte de las MUST,
  y es lo primero que se recorta si el calendario no alcanza (bolt-plan, P13 = A).
- **Qué entrega (unit-of-work § U13).** Las demostraciones de la adenda 02 en EthicsGovernance, sin
  compuertas que bloqueen el uso:
  - el reconocimiento de las reglas de uso (US15.1, DD-01);
  - el reporte de problemas con aviso de testimonio (US15.3, DD-04);
  - el registro de quién vio cada sesión (US15.6, DD-02), que además es el adaptador real del puerto
    `AccessLog` (C23) y sustituye al adaptador por defecto de U7 (AC15.8.2, UG-09);
  - el Job de retención con su acta y reloj simulado (US15.7, DD-03);
  - los avisos de bienestar (US15.9, DD-05).
- **Componentes:** EthicsGovernance (dueño de `AnalystAcknowledgement`, `AccessLogEntry`, `ProblemReport` y
  `RetentionAct`), las rutas `/acknowledgements` y `/problem-reports` de ConsoleApi con el estado del
  reconocimiento en `/auth/me`, y los diálogos y avisos de AnalystConsole.
- **Historias:** US15.1 (AC15.1.1–AC15.1.4) → US15.6 (AC15.6.1–AC15.6.2) → US15.3 (AC15.3.1–AC15.3.3) →
  US15.9 (AC15.9.1–AC15.9.2) → US15.7 (AC15.7.1–AC15.7.3), más la parte de AC15.8.2 que verifica el
  registro real. U5 dejó AC15.7.1 y AC15.7.3 «Deferred» a esta unidad.
- **Depende de:** U3 (ConsoleApi, convención de auditoría, usuario `veridicus_retention`, actor
  `retention-job`, cableado de C23), U4 (InterviewSession y `retention_days`/`retention_until` vacíos), U5
  y U7 (`purge_session` de C24). U6, U8 y U9 extienden el borrado de InterviewSession.
- **Situación:** unidad nueva del cambio 01 y de la adenda 02, sin diseño previo. Primera pasada (revisión
  1, 2026-11-22).

Contesta debajo de cada `[Answer]:` con la letra o con tu texto. Son 7 preguntas. Todo lo demás lo
resuelve el diseño con la propuesta de la sección 2, y puedes corregirlo en la aprobación.

---

## 1. Lo que ya está decidido y no se vuelve a preguntar

| Tema | Qué está decidido | Fuente |
|---|---|---|
| Nivel de exigencia | Es una demostración sin compuertas: ninguna parte de U13 rechaza abrir ni crear sesiones, ni bloquea el uso de la consola. El analizador (U10, U11 y el AnalysisWorker de U4) no se rebaja | ADR-016; DD-01 a DD-05; UG-04; bolt-plan B13 (punto 4); `project.md` (Seguimiento 1 = A) |
| Pausa, terminación y retirada | VE-10 se queda en InterviewSession (U6); U13 no la toca | DD-06; UG-05; `project.md` |
| Reconocimiento | Hay un diálogo modal justo después de M0 con los tres puntos y la versión del texto. La fila es de solo inserción y guarda usuario, hora UTC y versión. Tiene validez de 90 días: el día 90 sigue vigente y el día 91 no (reloj simulado). Si el texto cambia de versión por PR, se pide de nuevo. Sin `403`; con el reconocimiento vencido o un texto nuevo, la consola avisa y la sesión se abre igual | AC15.1.1–AC15.1.4; VE-04; DD-01; mockups (precisión rev. 3, R-04) |
| Estado del reconocimiento | `AcknowledgementStatus` (`valid`, `missing`, `expired`, `text_changed`) viaja en `GET /auth/me`. `POST /acknowledgements` es solo para el rol `analista`, con `x-veridicus-demo: true` | C1 (OpenAPI y tabla de rutas) |
| Quién escribe el registro de acceso | Lo escribe ConsoleApi en EthicsGovernance por el puerto `AccessLog` (C23), que define U7. EthicsGovernance no importa nada de ConsoleApi. ReviewReport no conoce el puerto | ADR-016; C23; UG-09; `project.md` |
| Qué se registra | `session`, `suggestion`, `report_version` y `report_export`, con usuario, tipo, ID y hora UTC, y el `export_sha256` solo en la exportación. Sin texto y de solo inserción. El sondeo con `since` no registra; la apertura, sí. La marca `x-veridicus-access-log` la pone cada ruta | C23; AC15.6.1; U3 F11 y BR9.1–BR9.4 |
| Fallo del registro | En una lectura, la respuesta sale igual, con un aviso en el log solo con IDs y la métrica `veridicus_access_log_failures_total`. En una exportación, se revierte y responde `503` `report.export_not_recorded` | U3 BR9.3; U7 BR9.5 y FD-U7-05 |
| Verificación de AC15.8.2 | U13 aporta una prueba de nivel 1 de que el adaptador real está conectado y de que la exportación queda registrada. Con U13, `/readyz` deja de informar `access_log: not_configured` | UG-09; C16; C23; U7 E22 |
| Reporte de problemas | Hay exactamente seis categorías y un panel no modal. Se abre desde un enlace en la cabecera de todas las pantallas y desde el menú de cada tarjeta, que precarga el ID. Si llega `suggestion_id`, `session_id` se deriva de la sugerencia. Lo pueden enviar el `analista` y el `admin` | AC15.3.1–AC15.3.2; UG-01; C1 (`/problem-reports`); mockups §11 |
| Testimonio en la nota | Una nota con `testimony_warning_words` (8) o más palabras seguidas de un turno de la sesión muestra «Quita el texto del testimonio de la nota». Si se envía igual, se guarda con `testimony_warning` verdadero y sin `422` | AC15.3.3; DD-04; C1; C25 |
| Retención: tope | El máximo es de 90 días y vive en el catálogo de límites, que solo cambia por PR. Más de 90 responde `422` `retention.above_maximum` sin crear filas. Un plazo fijado se puede reducir, y queda quién y cuándo, pero nunca ampliar (`422`) | AC15.7.1; AC15.7.3; VE-12; C25 |
| Retención: dónde se fija | En M3 y M7, en días, al crear la sesión. U4 dejó `retention_days` y `retention_until` vacíos; el campo y su validación llegan con U13. Reducir un plazo ya fijado no tiene ubicación en las maquetas y queda para esta etapa | FD-U4-22; mockups §11 (US15.7) |
| Job de retención | Es la única vía de borrado. Usa su propio usuario `veridicus_retention`, que tiene `SELECT` en todo, `DELETE` solo en las tablas purgables, `INSERT` solo en `RetentionAct` y nunca `UPDATE`. El actor es `retention-job`. Es un artefacto revisable que lanza el humano (AUTONOMIA-01); el sistema no lo programa | A-2; DD-03; FD-U3-08; FD-U3-09; U3 BR6.5 |
| Orden del borrado | (1) los ProblemReport de la sesión, incluidos los que se ligan por la sugerencia; (2) ReviewReport: `ReportExport` y luego `ReportVersion` de la más nueva a la más antigua, con sus archivos; (3) HumanReview; (4) InterviewSession y, al final, `InterviewSessionRecord`. Cada unidad borra lo suyo y devuelve un `PurgeReceipt` solo con IDs y SHA-256 | C24; components (EthicsGovernance); U4 BR19.3; U5 F6; U7 F9 y FD-U7-12 |
| Qué borra InterviewSession | Además de lo de U4, borra `TranscriptPaste` (U6), `ConductorObservation` con su historial (U8) y `TurnAudio`, el archivo antes de la fila, con `audio_id` y SHA-256 para el acta (U9) | FD-U6-22; FD-U8-07; FD-U9-09 |
| Qué sobrevive | Sobreviven `RetentionAct`, `AccessLogEntry` y `AnonymizationIncident`, sin clave foránea y solo con IDs. `AnalystAcknowledgement` no es purgable | C24; FD-U4-12; FD-U3-09 |
| Acta | Lleva los IDs borrados, el SHA-256 de cada reporte borrado, la hora y la regla aplicada | AC15.7.2; VE-12 |
| Bienestar | Al abrir M4, antes de la transcripción, aparece «Esta sesión contiene relatos de violencia. Puedes pausar cuando lo necesites» con «Continuar». Al cumplirse el intervalo del catálogo de límites, aparece un recordatorio no modal «Llevas un rato revisando. Considera una pausa», que se cierra sin perder el trabajo | AC15.9.1–AC15.9.2; VE-16; DD-05 |
| Frontera del clúster | Todo corre dentro del clúster, en `session-api` y en su Job, y nada sale. La nota de un reporte de problemas puede traer testimonio y se borra con la sesión | components (tabla de fronteras); AUTONOMIA-04 |
| Convenciones comunes | Las tablas de solo inserción siguen la convención de auditoría de U3. Cada pantalla y diálogo nuevo entra en la suite `axe` de U4 | US8.4; US5.6; unit-of-work-story-map |
| Reportes del investigador | La retención no toca las tablas de U12 | U12 BR1.4; ADR-014 |

## 2. Lo que el diseño resolverá sin preguntar

Las precisiones a artefactos aprobados irán a la tabla de precisiones de `functional-spec.md`. No se edita
ningún original.

1. **Texto versionado de las reglas.** El texto de los tres puntos vive en un archivo versionado de
   IntegrityPolicy (propuesta: `contracts/integrity/usage-rules.v1.yaml`, junto al aviso de VE-01 en C8).
   ConsoleApi lo sirve con su versión, y `AcknowledgementStatus` se calcula frente a esa versión. Es una
   precisión a C8 que va por PR de U1.
2. **Cifras al catálogo de límites.** Se añaden a C25 `retention_max_days` (90),
   `acknowledgement_validity_days` (90) y `wellness_reminder_interval_s`, cuya cifra fija NFR Requirements.
   El 90 ya lo fijan VE-04 y VE-12. Es una precisión a C25.
3. **Vigencia exacta.** El reconocimiento es vigente si `ahora − at ≤ 90 × 24 h` y su versión es la
   vigente. El diálogo aparece al entrar a la consola y también al abrir una sesión cuando el estado no es
   `valid` (AC15.1.3). Solo lo ven los usuarios `analista`, porque C1 da la ruta solo a ese rol.
4. **Adaptador de C23.** Inserta la fila dentro de la transacción de la petición, con *timeout* de E/S y
   sin clave foránea. La prueba de nivel 1 recorre las cuatro clases de recurso y la exportación.
   AC15.6.2 se cubre con la prueba común de U3 (el usuario de la aplicación no puede modificar ni borrar).
5. **Detección de testimonio en dos lados.** La consola avisa antes de enviar, con los turnos ya cargados
   en M4. El servidor es la autoridad que fija `testimony_warning`. Las dos implementaciones usan la misma
   especificación y los mismos ejemplos, como ya se hizo con la división de la transcripción. La
   comparación solo normaliza espacios, igual que la verificación de citas.
6. **Nota opcional.** AC15.3.1 dice «una nota opcional» y C1 la exige (`required: [category, note]`). Se
   sigue la historia y `note` pasa a opcional. Es una precisión a C1.
7. **Coherencia de IDs en el reporte.** Si llegan `session_id` y `suggestion_id` y no coinciden, la
   respuesta es `422`. Quien reporta sobre una sesión debe poder verla, sea el dueño o el `admin`; si no,
   recibe el mismo `403` o `404` que la ruta de la sesión. La verificación se hace en ConsoleApi, como en
   ADR-009.
8. **Campo del plazo en el contrato.** `retention_days` entra en `POST /sessions` y en
   `POST /sessions/import`, con un mínimo de 1 día y el máximo del catálogo. Hacen falta códigos nuevos:
   `retention.above_maximum`, `retention.cannot_extend` y `retention.below_minimum`. Todo va como
   precisión a C1.
9. **Mecánica del Job.** Hay una transacción y un acta por sesión, porque `RetentionAct` lleva un solo
   `deleted_session_id`. Los archivos se borran antes que las filas, con `file_missing` si ya no están. Si
   falla una sesión, se revierte esa sesión, el Job sigue con las demás y termina con código ≠ 0. La salida
   y los logs llevan solo IDs. Antes de borrar, se cancelan las corridas en cola con la clave de Redis que
   escribe InterviewSession (CD-06). El manifiesto es un `Job` en `deploy/`, nunca un `CronJob`, y monta
   los volúmenes de reportes y de audio.
10. **Bienestar sin entidad.** El aviso y el recordatorio son solo de AnalystConsole y no guardan nada. El
    aviso sale en cada apertura de M4. El reloj del recordatorio empieza al abrir la sesión y se reinicia
    al cerrar el aviso.
11. **Mensajes.** Los textos visibles nuevos (por ejemplo, el aviso de reconocimiento vencido y el plazo
    de retención en la cabecera) van a la tabla de precisiones como propuesta. No se citan como si los
    fijara un criterio aprobado.

---

## 3. Preguntas

### P1. Qué hace «Salir» en el diálogo de reconocimiento

**Contexto.** AC15.1.1 pide un diálogo modal con «Reconozco estas reglas» y «Salir». A la vez, DD-01, ADR-016
y el punto 4 de la definición de terminado de B13 dicen que ninguna demostración bloquea el uso de la
consola. Si «Salir» cierra la sesión web, un analista que no reconoce no puede usar la consola, aunque la
API nunca lo rechace. Las fuentes se contradicen en este punto.

- A. «Salir» cierra la sesión web. Se cumple la letra de AC15.1.1, y la API sigue sin compuerta (no hay
  `403`): se puede trabajar por API sin reconocer. Costo: en la interfaz, el reconocimiento funciona en la
  práctica como una compuerta.
- B. **(Recomendada)** El botón cierra el diálogo y la consola sigue usable. Queda una franja persistente
  bajo el aviso de VE-01: «No has reconocido las reglas de uso», con el botón «Reconocer». El botón pasa a
  llamarse «Más tarde» para que no se confunda con cerrar la sesión. Es una precisión al texto de AC15.1.1
  y cumple DD-01 y B13 sin ambigüedad.
- C. Igual que B, pero se conserva el rótulo «Salir». No cambia el texto de AC15.1.1, a cambio de un botón
  que no hace lo que dice.
- D. No hay diálogo modal, solo la franja con «Reconocer». Costo: contradice el «diálogo modal» de
  AC15.1.1.
- X. Other (please specify)

[Answer]: B **Mode:** guided

### P2. Plazo de retención por defecto y sesiones creadas sin plazo

**Contexto.** VE-12 dice «90 días como máximo por defecto», y AC15.7.1 prueba 30 y 120. No se fija si el
analista debe escribir el plazo o si viene puesto. Además, U4 (B3) y las unidades siguientes crean sesiones
con `retention_days` vacío hasta que llega U13 (FD-U4-22), y el Job tiene que decidir qué hacer con ellas.

- A. **(Recomendada)** El campo viene relleno con el máximo del catálogo (90) en M3 y M7, y es opcional
  en la API: si falta, se usa el máximo. Una sesión antigua con el plazo vacío se lee como «creada + máximo
  del catálogo», sin migración de datos, y el acta nombra esa regla («plazo por defecto»). Nada queda sin
  plazo.
- B. El campo es obligatorio en la consola y en la API, sin valor puesto: el analista lo elige siempre.
  Las sesiones antiguas reciben el máximo con un script de migración revisable que entra por su propio PR.
  Costo: un paso más al crear y una migración de datos.
- C. Igual que A para las sesiones nuevas, pero el Job no toca las sesiones con el plazo vacío y las
  lista como «sin plazo». Costo: esos testimonios pueden quedarse más de 90 días.
- D. El campo es opcional y no tiene valor por defecto: una sesión sin plazo nunca vence. Costo:
  contradice el «máximo por defecto» de VE-12.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P3. Desde cuándo cuenta el plazo y qué sesiones borra el Job

**Contexto.** Las fuentes no dicen desde cuándo cuenta el plazo. Si cuenta desde la creación, una sesión
puede vencer mientras sigue abierta, suspendida o con una corrida en curso. Si cuenta desde el cierre, una
sesión abandonada sin cerrar nunca vence. El consentimiento del TG dice «por cuánto tiempo» se guarda el
relato (VE-07).

- A. **(Recomendada)** Cuenta desde la creación: `retention_until` = creación + plazo, fijado al crear y
  recalculado al reducir. El Job borra toda sesión vencida, sea cual sea su estado. Antes cancela sus
  corridas en cola, y un resultado que llegue después se descarta porque la sesión ya no existe. Es
  determinista y coincide con lo que el consentimiento promete.
- B. Cuenta desde la creación, pero el Job salta las sesiones abiertas, suspendidas o con corridas en
  curso. Las anota en su salida como «vencida y activa» y las borra en la siguiente ejecución, cuando estén
  cerradas. Costo: el testimonio puede pasar el plazo mientras alguien trabaja.
- C. Cuenta desde el cierre (finalizada, terminada, consolidada o importada): `retention_until` se fija
  en esa transición. Costo: una sesión que nunca se cierra nunca vence, y U6 y U7 tendrían que escribir el
  campo.
- D. Cuenta desde la creación con dos plazos: el del analista para las sesiones cerradas y el máximo del
  catálogo para las abiertas. Costo: hay dos reglas que explicar en el acta y en el consentimiento.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P4. Quién reduce el plazo de una sesión y desde dónde (AC15.7.3)

**Contexto.** AC15.7.3 permite reducir y prohíbe ampliar, con registro de quién y cuándo. C1 no tiene una
ruta para eso, y las maquetas no le dan lugar. La persona de US15.7 es el administrador. ADR-009 reserva al
dueño los cambios de la sesión, aunque el plazo no está en esa lista.

- A. **(Recomendada)** Pueden reducirlo el analista dueño y el `admin`. Se hace en la cabecera de M4, con
  «Plazo de retención: N días (hasta DD/MM/AAAA)» y «Reducir plazo», que abre un diálogo con el número de
  días. La ruta es nueva, `PATCH /sessions/{id}/retention`, con `x-veridicus-demo: true`. El cambio queda
  en un historial de solo inserción de EthicsGovernance que guarda el valor anterior, el nuevo, el actor y
  la hora. Es una precisión a C1 y a M4.
- B. Solo el analista dueño, con la misma ubicación y la misma ruta. El `admin` ve el plazo, pero no lo
  cambia (sigue ADR-009).
- C. Solo el `admin`, desde la lista de sesiones (M1), porque US15.7 es suya. El dueño ve el plazo en M4,
  pero no lo cambia.
- D. Solo por API, sin interfaz: se demuestra con la prueba de nivel 1 de AC15.7.3. Costo: el analista no
  puede reducir el plazo cuando la persona entrevistada lo pide.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P5. Fecha de corte del Job en el clúster y cómo se demuestra

**Contexto.** AC15.7.2 se prueba con reloj simulado. La demo de B13 pide que «el Job de retención borra una
sesión vencida con su acta». Con el reloj real y un mínimo de 1 día, en el clúster solo vence una sesión
creada al menos un día antes. Si el Job aceptara una fecha simulada en el clúster, una fecha mal puesta
borraría sesiones antes de su plazo, y ese borrado no se puede deshacer.

- A. **(Recomendada)** El Job usa siempre el reloj real para borrar. El reloj simulado solo se inyecta en
  las pruebas. Hay un modo `--dry-run` que acepta `--as-of <fecha>` y lista lo que se borraría (IDs y
  conteos), sin borrar nada ni escribir el acta. La demo en vivo usa el `--dry-run` más una sesión
  sintética creada con plazo de 1 día el día anterior.
- B. El Job acepta `--as-of` también para borrar, y el acta guarda la fecha de corte usada. Es más fácil
  de demostrar, a costa de poder borrar antes de tiempo con un error de tipeo.
- C. Se permite un plazo de 0 días, que vence enseguida: la demo crea una sesión sintética con plazo 0 y
  lanza el Job con el reloj real. Costo: un plazo 0 en una sesión real borra el testimonio en la siguiente
  ejecución.
- D. Solo el reloj real, sin `--dry-run`. La demo en vivo se apoya en la sesión del día anterior y en la
  evidencia de la prueba de nivel 1.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P6. Reporte de problemas sin sesión

**Contexto.** El enlace «Reportar un problema» está en la cabecera de todas las pantallas, incluidas M1, M6
y M8, donde no hay sesión. C1 deja `session_id` opcional. UG-01 dice que `session_id` es obligatorio y se
deriva de la sugerencia. Un reporte sin sesión no se compara con ningún turno, y la retención, que borra
por sesión, nunca borraría su nota, que puede traer testimonio.

- A. **(Recomendada)** `session_id` es opcional (C1). Un reporte sin sesión se guarda con la nota, y la
  consola muestra el aviso fijo «No incluyas texto del testimonio» sin comparar con turnos. El Job de
  retención borra también los reportes sin sesión cuyo `reported_at` supera el máximo del catálogo, y lo
  anota en un acta con `deleted_session_id` vacío. Es una precisión a UG-01, a C24 y a `RetentionAct`.
- B. `session_id` es obligatorio (UG-01). Fuera de M4 y M5, el formulario pide elegir una de las sesiones
  que el usuario puede ver. Costo: el `admin` no puede reportar un «Uso indebido» que no tenga que ver con
  una sesión.
- C. `session_id` es opcional, pero sin sesión no se admite nota: solo la categoría. No hay testimonio que
  borrar, a costa de un reporte sin detalle.
- D. `session_id` es opcional y el reporte sin sesión no lo borra nadie, con el riesgo declarado en un
  escenario visible.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P7. Cómo se consulta lo que registra la demostración

**Contexto.** AC15.6.1 dice «When consulto el registro de acceso», pero mockups §11 lo deja «sin
interfaz». Tampoco hay una ruta que lea los reportes de problemas, aunque US15.3 los quiere «para que el
equipo lo corrija». La demo de B13 dice que «se ve quién abrió la sesión». Añadir una pantalla es alcance
nuevo en el Bolt que se recorta primero, y la demo es en 8 días.

- A. **(Recomendada)** Sin pantalla. Un comando de solo lectura en la imagen de `session-api`, que el
  humano ejecuta, lista los accesos por sesión o por usuario y los reportes de problemas, con su nota, en
  texto o en JSON. El registro de acceso solo tiene IDs; la nota se muestra porque está dentro del clúster
  y es la vía para corregir. La prueba de nivel 1 consulta lo mismo por el puerto.
- B. Se añade una pantalla de solo lectura para el `admin`, en M6 o en una pestaña nueva, con el registro
  de acceso y los reportes de problemas, nota incluida. Son rutas nuevas en C1, una pantalla que las
  maquetas no tienen y más trabajo en B13.
- C. Igual que B, pero la pantalla no muestra la nota, solo la categoría, los IDs, la fecha y
  `testimony_warning`. La nota se lee con el comando de A.
- D. Nada fuera de las pruebas. La demo se hace con una consulta SQL documentada que el humano corre con
  `psql`.
- X. Other (please specify)

[Answer]: A **Mode:** guided
