# Historias de usuario — Veridicus (MVP académico)

**Insumos.** `inception/requirements-analysis/requirements.md` (FR1–FR12, NFR1–NFR15), las prácticas de
team-practices (`inception/practices-discovery/team-practices.md`), las personas de `personas.md` y las
respuestas de `user-stories-questions.md` (P1–P8 y Seguimientos 1–6).

**Formato.** «Como [persona], quiero [acción], para [beneficio]». Criterios Given/When/Then con ID
`ACx.y.z`. Prioridad MoSCoW heredada del requisito de origen; el límite final del MVP lo fija Delivery
Planning. Las épicas 1 a 6 forman el flujo de **texto** de punta a punta, que es la primera unidad del
plan de entrega (team-practices, Walking Skeleton).

**Personas.** P1 Analista de Verdad · P2 Administrador de plataforma · P3 Oficial de Cumplimiento Ético.

## Convenciones de los criterios

- **Nivel de prueba** al final de cada criterio (team-practices, Testing Posture): `[N0]` unitaria,
  contrato o política estática, con *fakes* deterministas del LLM y de los *embeddings*; `[N1]`
  integración con PostgreSQL + `pgvector` y Redis reales (LLM y *embeddings* aún *fake*); `[N2]` Golden
  Dataset con el modelo real, temperatura 0 y semilla fija; `[N3]` E2E con Playwright o humo;
  `[Manual]`. Un criterio que depende del LLM real se parte en una variante determinista y otra `[N2]`.
- **Rechazos.** Todo rechazo de la API nombra el estado HTTP y un `code` estable de Problem Details con
  `detail` en español, y verifica que **no cambió ninguna fila**. Reparto propuesto, que confirma
  Functional Design: `401` sin autenticación; `403` rol o propiedad; `409` conflicto de estado; `413`
  tamaño; `415` formato; `422` validación.
- **Textos visibles.** Los textos entre «» son la redacción visible propuesta; viven en un catálogo de
  mensajes en español que las pruebas leen.
- **Vocabulario prohibido.** La lista de etiquetas de veracidad (con variantes de género, número y
  tiempo) es un archivo versionado en `contracts/` que leen las pruebas y el escaneo.
- **Control negativo.** Toda política estática o escáner tiene un *fixture* que la viola y una prueba que
  verifica que el chequeo falla sobre él.

---

## Decisiones de esta etapa que precisan `requirements.md`

Estas respuestas cierran hallazgos de la revisión de Análisis de Requisitos y huecos que encontró la
revisión de diseño, desarrollo y calidad. Las historias las aplican. Que `requirements.md` se actualice
para recogerlas se decide en la aprobación.

| Decisión | Requisito que precisa | Origen |
|---|---|---|
| La evaluación es **por afirmación**. Similitud bajo el umbral → «no documentada», entra al Paquete de Traspaso del turno. «Incongruente» en o sobre el umbral → alerta. «Congruente» → nada visible. Si una afirmación del turno es «no documentada», no hay pregunta sugerida en ese turno. | FR4.3, FR5.2, FR5.3 | P4 (R-01) |
| La guardia del umbral decide **antes** que el juez. Si el juez califica «no documentada» con similitud en o sobre el umbral, se trata igual que «no documentada». | FR4.3, FR5.2 | Seguimiento 2 |
| El umbral vive en la **configuración del despliegue**; cambiarlo es un PR y la fusión registra quién, cuándo, antes y después. Cada sesión guarda el valor con que se creó. La consola no tiene acción de cambio de umbral. | FR1.2, FR1.3, FR9.2 | P5 (R-03) |
| «Editada» = el analista escribe **su propia reformulación**; fragmento, cita, ID de documento y CoT de la IA no cambian. | FR6.1, FR7.2 | P6 (R-05) |
| Antes de consolidar, una decisión se puede cambiar entre `aceptada`, `editada` y `descartada`, con las mismas exigencias; nunca vuelve a `pendiente`. | FR6.1 | Seguimiento 5 |
| La consolidación se bloquea con alertas `pendiente` o turnos `en cola`/`procesando`; los turnos en `error` no la bloquean y el reporte los rotula «turno no evaluado». | FR7.1, FR7.2 | Seguimiento 1 de RA, Seguimiento 1 |
| Un reporte consolidado se corrige con «Corregir reporte»: copia de trabajo donde solo cambian estados y notas; consolidarla crea la versión nueva. | FR7.5 | P7 (R-06) |
| Un escenario con el mismo SHA-256 que una versión existente se rechaza. | FR2.4 | Seguimiento 6 |
| El escaneo de vocabulario prohibido cubre la salida de la IA, la interfaz y el reporte; excluye las citas literales y el texto escrito por el analista. | FR6.4 | Seguimiento 4 |
| Accesibilidad SHOULD: WCAG 2.1 AA con axe, flujo de texto solo con teclado, estados no solo por color. | `requirements.md` §7 (pregunta abierta) | Seguimiento 3 |
| Éxito del pipeline: **50 sesiones en tandas de 3 concurrentes y 0 fallos**. | NFR8 | P8 (R-04) |

---

## Épica 1 — Escenario de control

### US1.1 — Cargar e indexar un escenario de control · MUST · P1, P2
Como Analista de Verdad (o Administrador de plataforma), quiero cargar un documento de hechos sintéticos y
verlo indexado, para tener el marco de verdad contra el que se contrastará el testimonio.
*Origen:* FR2.1, FR2.2, FR2.3.

- **AC1.1.1** Given un archivo Markdown UTF-8 de exactamente 1 048 576 bytes, When lo cargo, Then la API responde `202`, el escenario aparece «Indexando…» y termina «Listo para contrastación» con ≥ 1 pasaje guardado en `pgvector` dentro del clúster. `[N1]` (el tiempo < 3 min es NFR9, diferido)
- **AC1.1.2** Given (a) 1 048 577 bytes, (b) un archivo `.md` cuyo contenido empieza por `%PDF`, (c) un archivo con bytes no válidos en UTF-8 (p. ej. `0xE9`), (d) un archivo de 0 bytes, When lo cargo, Then responde `413`, `415`, `422` y `422` con los mensajes «El archivo supera 1 MB. Divide el escenario o reduce su tamaño», «Solo se admiten archivos Markdown o de texto plano», «El archivo debe estar codificado en UTF-8» y «El archivo está vacío», y hay 0 pasajes de ese intento. `[N0]` validación + `[N1]` conteo
- **AC1.1.3** Given un escenario indexado, When consulto sus pasajes por la API, Then cada uno tiene texto literal, posición e identificador de documento. `[N1]`
- **AC1.1.4** Given un *fake* de *embeddings* que falla en el pasaje *k* > 1, When termina la indexación, Then hay 0 pasajes de esa versión, la versión queda «Error» con su causa en español y no se puede elegir para una sesión. `[N1]`
- **AC1.1.5** Given un escenario «Indexando…», When uso el resto de la consola, Then responde y el escenario no se puede elegir para una sesión. `[N0]` Vitest

*INVEST:* independiente; pequeña; comprobable en nivel 1 contra `pgvector` real.

### US1.2 — Corregir un escenario creando una versión nueva · MUST · P1
Como Analista de Verdad, quiero corregir un escenario sin alterar el que ya usé, para que cada sesión
pasada siga contrastada contra exactamente lo que vio.
*Origen:* FR2.4 (Seguimiento 6).

- **AC1.2.1** Given un escenario indexado, When cargo un documento corregido como nueva versión, Then se crea una versión con identificador y SHA-256 propios y la anterior conserva sus pasajes y su SHA-256. `[N1]`
- **AC1.2.2** Given cualquier versión, When envío `PUT`, `PATCH` o `DELETE` sobre un pasaje o una versión, Then responde `404` o `405` (la ruta no existe en el OpenAPI) `[N0]`, y el usuario de base de datos de la aplicación no tiene `UPDATE` ni `DELETE` sobre pasajes (una sentencia directa falla) `[N1]`.
- **AC1.2.3** Given un documento con el mismo SHA-256 que una versión existente, When lo cargo, Then responde `409` con «Este documento ya está cargado como <escenario> versión <n>» y no se crea ninguna versión. `[N1]`
- **AC1.2.4** Given dos versiones de un escenario, When las listo, Then veo cada una con su SHA-256 y su fecha de carga. `[N1]`

### US1.3 — Elegir escenario del catálogo · MUST · P1
Como Analista de Verdad, quiero ver el catálogo de escenarios y versiones, para elegir con cuál contrastar
una sesión.
*Origen:* FR2.5.

- **AC1.3.1** Given tres escenarios, uno con dos versiones, When abro el catálogo, Then veo los tres con sus versiones y su estado («Indexando…», «Listo», «Error»); la versión «Listo» más reciente aparece preseleccionada y las demás se rotulan «versión anterior». `[N0]` Vitest + `[N1]`
- **AC1.3.2** Given una versión «Indexando…» o «Error», When intento crear una sesión con ella (interfaz o `POST` a la API), Then no puedo elegirla y la API responde `409`. `[N1]`
- **AC1.3.3** Given que no hay escenarios listos, When abro el catálogo, Then veo «No hay escenarios de control listos» y la acción «Cargar escenario de control». `[N0]` Vitest

---

## Épica 2 — Sesión e ingreso del testimonio en texto

### US2.1 — Crear una sesión ligada a un escenario · MUST · P1
Como Analista de Verdad, quiero crear una sesión sobre una versión de escenario, para que todo lo que
evalúe quede atado a ese marco y a ese umbral.
*Origen:* FR3.1, FR9.2 (P5), FR1.2.

- **AC2.1.1** Given una versión lista, When creo una sesión, Then la sesión guarda el identificador y el SHA-256 de la versión y el umbral vigente, y su cabecera muestra escenario, versión, los primeros caracteres del SHA-256 y el umbral. `[N1]` + `[N0]` Vitest
- **AC2.1.2** Given una sesión S1 creada con umbral T1 y el servicio reiniciado con umbral T2 ≠ T1, When se evalúa en S1 una afirmación con similitud entre T1 y T2, Then el resultado corresponde a T1; y una sesión S2 creada después guarda T2. `[N1]`
- **AC2.1.3** Given un usuario `admin`, When intenta crear una sesión, enviar un turno, pegar una transcripción o finalizar una sesión, Then `403` y 0 filas nuevas; y en la interfaz no ve «Nueva sesión». `[N1]` + `[N0]` Vitest
- **AC2.1.4** Given una sesión de otro analista, When intento enviar un turno o finalizarla, Then `403`. `[N1]`

### US2.2 — Enviar el testimonio turno a turno · MUST · P1
Como Analista de Verdad, quiero enviar cada turno del testimonio y seguir trabajando mientras se procesa,
para no quedar bloqueado por la latencia de la IA en CPU.
*Origen:* FR3.2, FR3.4.

- **AC2.2.1** Given una sesión abierta, When envío un turno, Then queda numerado en orden y muestra su estado («En cola», «Procesando», «Evaluado», «Error»); con 10 envíos concurrentes los turnos quedan numerados 1..10 sin huecos ni duplicados. `[N1]`
- **AC2.2.2** Given un juez *fake* que bloquea el procesamiento hasta que la prueba lo libera, When envío un segundo turno y consulto una alerta existente, Then el `POST` responde `202` y el `GET` `200` antes de liberar el juez. `[N1]` (la latencia máxima por turno es NFR3, diferida)
- **AC2.2.3** Given un turno, When se encola, Then el mensaje cumple el contrato de la cola; un mensaje mal formado se rechaza sin crear filas. `[N0]`
- **AC2.2.4** Given un trabajador que muere mientras procesa un turno, When otro trabajador toma el mensaje pendiente, Then el turno produce exactamente un resultado (entrega al menos una vez, idempotente por ID de turno). `[N1]`
- **AC2.2.5** Given una sesión recién creada, When la abro, Then veo «Aún no hay turnos. Escribe el primer turno o pega una transcripción completa» y «Enviar turno» está deshabilitado mientras el texto esté vacío. `[N0]` Vitest

### US2.3 — Pegar una transcripción completa · MUST · P1
Como Analista de Verdad, quiero pegar una transcripción entera, para no enviar turno por turno un
testimonio ya transcrito.
*Origen:* FR3.3.

- **AC2.3.1** Given una transcripción con turnos separados por línea vacía o por marca de hablante, When la pego, Then veo cuántos turnos detectó y una vista previa de cada uno, y puedo cancelar sin que se cree ningún turno. `[N0]` Vitest
- **AC2.3.2** Given la vista previa confirmada, When se procesa, Then los turnos se crean y se procesan en orden. `[N1]`
- **AC2.3.3** Given una transcripción del Golden Dataset y el juez *fake*, When la proceso pegada y turno a turno, Then los resultados son iguales comparando (número de turno, fragmento, ID de documento, calificación, tipo de resultado) `[N1]`; la misma igualdad con el modelo real `[N2]`.

### US2.4 — Finalizar la sesión · MUST · P1
Como Analista de Verdad, quiero cerrar el ingreso de turnos, para empezar la revisión con el testimonio
completo.
*Origen:* FR3.5, NFR7.

- **AC2.4.1** Given una sesión abierta, When pulso «Finalizar sesión», Then un diálogo dice «Después de finalizar no podrás agregar turnos», indica cuántos turnos siguen en proceso y ofrece «Finalizar» y «Cancelar». `[N0]` Vitest
- **AC2.4.2** Given que confirmo, When la sesión se finaliza, Then guarda en UTC la hora de inicio de MTTV y un nuevo turno responde `409` sin crear filas. `[N1]`
- **AC2.4.3** Given una sesión finalizada con turnos aún en proceso, When terminan, Then sus resultados se guardan en la sesión. `[N1]`
- **AC2.4.4** Given una sesión finalizada, When la miro, Then veo cuántas sugerencias de revisión quedan pendientes y un acceso a la primera. `[N0]` Vitest

### US2.5 — Ver la lista de sesiones · MUST · P1
Como Analista de Verdad, quiero ver las sesiones con su estado, para retomar las mías y consultar las de
otros.
*Origen:* FR1.2 (leer todas), FR7.4, FR8.3. No sustituye al historial lateral (US11.2).

- **AC2.5.1** Given sesiones de dos analistas, When entro como `analista`, Then veo escenario y versión, dueño, fecha y estado («Abierta», «Suspendida», «Finalizada», «Consolidada») de cada una, y puedo filtrar las mías. `[N1]` + `[N0]` Vitest
- **AC2.5.2** Given que no hay sesiones, When abro la lista, Then veo «Aún no hay sesiones» y la acción «Nueva sesión». `[N0]` Vitest
- **AC2.5.3** Given una sesión «Suspendida» mía, When abro la lista, Then lo muestra con texto e icono, no solo con color. `[N0]` Vitest

---

## Épica 3 — Validación semántica y alertas

### US3.1 — Ver una alerta de incongruencia con su justificación · MUST · P1
Como Analista de Verdad, quiero ver cada incongruencia con el fragmento, la cita, el documento y la
CoT, para juzgarla con la evidencia delante.
*Origen:* FR4.1, FR4.3, FR4.4, FR4.5.

- **AC3.1.1** Given una afirmación «incongruente» con similitud en o sobre el umbral (similitud = `1 −` distancia coseno), When se evalúa, Then aparece una alerta `pendiente` con fragmento literal, cita literal, identificador de documento y CoT. `[N0]` dominio con recuperador y juez *fake* + `[N1]` vectores sembrados en `pgvector`
- **AC3.1.2** Given una alerta con cualquiera de esos cuatro campos ausente, `null`, vacío o solo espacios, o con un ID de documento que no pertenece a la versión de la sesión, When se intenta guardar, Then se rechaza (al menos una prueba por campo y caso). `[N0]` contrato + `[N1]` restricciones de base de datos
- **AC3.1.3** Given un turno con todas sus afirmaciones «congruente», When termina, Then no hay alertas y el turno muestra «Evaluado · sin sugerencias de revisión», distinto de «Procesando» y de un Hecho No Documentado. `[N0]`
- **AC3.1.4** Given una CoT cuyo esquema exige referencias a pasajes, When una referencia apunta a un pasaje que no está entre los recuperados para esa afirmación, Then la salida se rechaza y no hay alerta `[N0]`; 100 % de trazabilidad factual sobre el Golden Dataset `[N2]`.
- **AC3.1.5** Given un turno, When el sistema lo divide en afirmaciones, Then aplica una regla determinista (la fija Functional Design): el mismo texto produce siempre las mismas afirmaciones, cada una subcadena literal del turno. `[N0]` prueba de propiedad con Hypothesis
- **AC3.1.6** Given un turno evaluado, When consulto su registro de evaluación por la API, Then cada afirmación guarda su texto, su similitud máxima, los 3 pasajes más cercanos y su calificación. No es visible en la interfaz. `[N1]`
- **AC3.1.7** Given una alerta nueva, When aparece, Then se agrega al panel sin ventana modal, sin sonido y sin mover el foco; el contador de pendientes se actualiza, una región `aria-live="polite"` lo anuncia, y su rótulo es «Sugerencia de revisión · Incongruencia semántica», sin grados de severidad. `[N0]` Vitest
- **AC3.1.8** Given una alerta, When la selecciono, Then su fragmento queda resaltado en el turno de la transcripción. `[N0]` Vitest

### US3.2 — Nunca recibir una alerta parcial · MUST · P1
Como Analista de Verdad, quiero que una respuesta mal formada de la IA no se convierta en alerta, para no
revisar hallazgos incompletos.
*Origen:* FR4.2.

- **AC3.2.1** Given un juez *fake* que devuelve (a) texto no JSON, (b) JSON sin un campo obligatorio, (c) una calificación fuera del enum, (d) tres afirmaciones con una mal formada, (e) *timeout*, When se procesa el turno, Then 0 alertas para todo el turno, turno «Error» y `code` estable, distinto para formato inválido y para *timeout*. `[N0]`
- **AC3.2.2** Given un turno «Error», When lo veo, Then leo la causa sin jerga («No se pudo evaluar este turno: la respuesta de la IA no tenía el formato esperado. Puedes reintentar») y el `code` como referencia secundaria. `[N0]` Vitest
- **AC3.2.3** Given un turno «Error», también en una sesión finalizada, When pulso «Reintentar evaluación», Then se reprocesa el mismo turno con su mismo número; reintentado dos veces, no hay alertas duplicadas. `[N1]`
- **AC3.2.4** Given una CoT que contiene vocabulario prohibido fuera de las citas literales, When se valida la salida del juez, Then se trata como salida inválida (sin alerta, turno «Error», `code` estable). `[N0]`

### US3.3 — Que el testimonio no cambie las reglas del juez · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que las instrucciones escritas dentro de un testimonio se traten
como datos, para que nadie pueda torcer el análisis desde la entrada.
*Origen:* FR4.6, NFR10.

- **AC3.3.1** Given un turno, When se construye el *prompt*, Then el testimonio va solo dentro del bloque delimitado de datos, nunca en la sección de instrucciones, y el *prompt* del sistema se lee del archivo montado cuyo SHA-256 coincide con el del repositorio `[N0]`; añadir el texto de inyección del Escenario A a cada transcripción del Golden Dataset no cambia el conjunto de alertas `[N2]`.
- **AC3.3.2** Given los manifiestos, When corre la política, Then falla si el *prompt* del sistema no está montado `readOnly: true` desde un `ConfigMap` `[N0]`; con el usuario de base de datos del juez, `INSERT`, `UPDATE` y `DELETE` sobre cualquier tabla, y `SELECT` fuera del marco de verdad, fallan `[N1]`.

---

## Épica 4 — Silencio Fáctico

### US4.1 — Calificar como «no documentada» por umbral · MUST · P1
Como Analista de Verdad, quiero que la IA calle cuando una afirmación no está documentada, para no recibir
una conjetura como hallazgo.
*Origen:* FR4.3, FR5.2 (P4, Seguimiento 2), AUTONOMIA-05.

- **AC4.1.1** Given similitudes `umbral − δ`, `umbral` y `umbral + δ` (δ = 10⁻⁶ en `[N0]` con recuperador *fake*; δ = 0,01 en `[N1]` con vectores sembrados) y un juez que califica «incongruente», When se evalúa, Then hay «no documentada» sin alerta, alerta y alerta, respectivamente. `[N0]` + `[N1]`
- **AC4.1.2** Given un juez *fake* forzado a calificar toda afirmación «incongruente» y similitud `umbral − δ`, When se evalúa el turno, Then 0 alertas, 0 preguntas sugeridas y 1 Paquete de Contexto de Traspaso: la guardia decide antes que el juez. `[N0]` + `[N1]`
- **AC4.1.3** Given similitud en o sobre el umbral y un juez que califica «no documentada», When se evalúa, Then se trata como «no documentada»: entra al paquete, sin alerta, y suprime la pregunta sugerida del turno. `[N0]`
- **AC4.1.4** Given similitud `umbral + δ` y calificación «congruente», When se evalúa, Then 0 alertas y 0 paquetes. `[N0]`
- **AC4.1.5** Given un turno con una afirmación «no documentada» y otra «incongruente» sobre el umbral, When se evalúa, Then hay una alerta para la segunda y un paquete para la primera. `[N0]`

### US4.2 — Recibir el Paquete de Contexto de Traspaso · MUST · P1
Como Analista de Verdad, quiero recibir el contexto de lo que la IA no pudo validar, para intervenir yo
con la evidencia delante.
*Origen:* FR5.3, FR5.4. Depende de US4.1.

- **AC4.2.1** Given un turno con al menos una afirmación «no documentada», When termina, Then el paquete trae el fragmento literal, los turnos previos (0, 1 y 2 para los turnos 1, 2 y 3; exactamente 3 desde el turno 4, con «Turnos previos disponibles: N de 3»), los 3 pasajes más cercanos ordenados por coeficiente descendente (todos si el escenario tiene menos) y una CoT interrumpida que produce el sistema de forma determinista (pasajes, similitud máxima, umbral de la sesión y motivo «similitud X < umbral Y»), sin llamar al LLM. `[N0]`
- **AC4.2.2** Given un paquete, When se muestra, Then aparece el aviso «La IA no puede validar este fragmento de forma autónoma. Control manual requerido» (comparado carácter por carácter), distinguible de una alerta por texto e icono y no solo por el color, sin estilo de error del sistema, y no cuenta como sugerencia pendiente. `[N0]` Vitest + `[N3]`
- **AC4.2.3** Given el aviso, When lo pulso, Then el panel lateral se abre sin tapar el turno y se cierra con Escape o con «Cerrar». `[N0]` Vitest
- **AC4.2.4** Given el caso de Hecho No Documentado configurado en los dobles, When se procesa, Then 0 alertas, 0 preguntas y 1 paquete `[N1]`; el mismo resultado con el Golden Dataset real `[N2]` y en `frontend/e2e/smoke.spec.ts` `[N3]`.

### US4.3 — Impedir que el agente arranque sin umbral · MUST · P2
Como Administrador de plataforma, quiero que el agente semántico no arranque sin un umbral válido, para
que nunca evalúe con un valor implícito.
*Origen:* FR5.1.

- **AC4.3.1** Given la variable del umbral (nombre del glosario, p. ej. `VERIDICUS_SIMILARITY_THRESHOLD`) ausente, vacía, `abc`, `NaN`, por debajo del mínimo o por encima del máximo, When arranca el servicio, Then el cargador de configuración falla `[N0]`, el proceso termina con código ≠ 0 y no pasa la sonda de salud, y el log nombra el ajuste sin su valor ni datos sensibles `[N1]`.
- **AC4.3.2** Given el umbral en el mínimo y en el máximo del rango válido, When arranca, Then se acepta. `[N0]` (el rango lo fija NFR Requirements)

---

## Épica 5 — Revisión humana de alertas

### US5.1 — Aceptar una alerta después de leer su CoT · MUST · P1
Como Analista de Verdad, quiero aceptar una alerta solo después de desplegar su justificación, para no
validar nada a ciegas.
*Origen:* FR6.1, FR6.2, FR6.5, NFR11.

- **AC5.1.1** Given una alerta con la CoT plegada, When la miro, Then «Aceptar» y «Editar» aparecen deshabilitados con el texto visible «Despliega y lee la justificación (CoT) para habilitar esta acción». `[N0]` Vitest
- **AC5.1.2** Given que despliego la CoT, When ocurre, Then se registra un evento «CoT consultada» con mi usuario y la hora; la API responde `409` (`code` p. ej. `cot_not_viewed`) a `aceptada` o `editada` si no existe ese evento del mismo usuario para esa alerta, y `200` después. «Descartada» no lo exige. `[N1]` (el evento prueba que se desplegó, no que se leyó)
- **AC5.1.3** Given la CoT desplegada, When acepto con o sin nota, Then pasa a `aceptada` (en la lista: «Aceptada · con nota» y la nota visible, si la hay) y el historial guarda usuario, hora, estado anterior y nuevo. `[N1]` + `[N0]` Vitest
- **AC5.1.4** Given la tabla de transiciones que fije Functional Design, When pido una transición fuera de ella (p. ej. volver a `pendiente`), Then `409`. Antes de consolidar, se permite cambiar entre `aceptada`, `editada` y `descartada` con las mismas exigencias, y cada cambio queda en el historial. `[N0]` + `[N1]`
- **AC5.1.5** Given cualquier alerta, When la veo, Then junto a los botones de decisión, sin *hover*, está «La IA es un asistente de soporte. Su criterio como analista prevalece». `[N0]` Vitest

### US5.2 — Editar una alerta con mi propia reformulación · MUST · P1
Como Analista de Verdad, quiero reformular un hallazgo con mis palabras sin tocar lo que dijo la IA, para
que el reporte muestre ambas cosas.
*Origen:* FR6.1, FR6.2, FR7.2 (P6).

- **AC5.2.1** Given una alerta con la CoT desplegada, When guardo mi reformulación, Then pasa a `editada` con mi texto, mi usuario y la hora; una reformulación vacía o solo de espacios responde `422` y «Guardar» está deshabilitado con su motivo visible. `[N1]` + `[N0]` Vitest
- **AC5.2.2** Given una alerta `editada`, When comparo, Then el SHA-256 de (fragmento, cita, ID de documento, CoT) es idéntico antes y después; una petición que intenta cambiar alguno responde `422` sin cambiar nada. `[N1]`
- **AC5.2.3** Given el editor, When escribo, Then el hallazgo original de la IA se ve a un lado en solo lectura. `[N0]` Vitest
- **AC5.2.4** Given una alerta `editada`, When se consolida, Then el reporte muestra el hallazgo original y mi reformulación con quién y cuándo. `[N1]`

### US5.3 — Descartar una alerta con una nota · MUST · P1
Como Analista de Verdad, quiero descartar una alerta explicando por qué, para que quede constancia de mi
criterio.
*Origen:* FR6.3.

- **AC5.3.1** Given una alerta, When intento descartarla con la nota ausente, vacía o solo de espacios, Then `422`, la alerta no cambia, y junto al campo aparece «Escribe por qué descartas esta sugerencia». `[N0]` + `[N1]`
- **AC5.3.2** Given una nota no vacía, When la descarto, Then pasa a `descartada` con la nota, mi usuario y la hora. `[N1]`

### US5.4 — Solo el dueño de la sesión cambia sus alertas · MUST · P1
Como Analista de Verdad, quiero que solo yo pueda cambiar las alertas de mis sesiones, para que nadie
valide hallazgos en mi nombre.
*Origen:* FR1.2, FR6.1.

- **AC5.4.1** Given una sesión de otro analista, When intento cambiar el estado de una alerta, Then `403` y 0 filas nuevas. `[N1]`
- **AC5.4.2** Given una sesión de otro analista, When la abro, Then veo «Sesión de <usuario>. Solo lectura», puedo leer alertas y reporte, y no hay botones de decisión ni de consolidación. `[N1]` + `[N0]` Vitest
- **AC5.4.3** Given un usuario `admin` o una identidad de servicio, When intenta cambiar el estado de cualquier alerta, Then `403`. `[N1]`

### US5.5 — Ningún juicio de veracidad sobre el compareciente · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que ni la IA ni la interfaz califiquen al compareciente como
mentiroso o veraz, para evitar la revictimización.
*Origen:* FR6.4, AUTONOMIA-03 (Seguimiento 4).

- **AC5.5.1** Given la lista versionada de vocabulario prohibido, When corre el escaneo (por palabra completa, sin distinguir mayúsculas ni tildes), Then hay 0 coincidencias en la salida del juez sobre *fixtures* `[N0]` y sobre el Golden Dataset `[N2]`, en las cadenas de la interfaz `[N0]`, en el reporte generado `[N1]` y en la interfaz renderizada `[N3]`. Se excluyen las citas literales (fragmento y cita) y el texto escrito por el analista.
- **AC5.5.2** Given el escaneo, When corre sobre su control negativo, Then una CoT *fixture* que dice «el compareciente miente» lo hace fallar, y «falso» dentro de una cita literal no. `[N0]`
- **AC5.5.3** Given el esquema de la alerta, When lo valido, Then tiene `additionalProperties: false`, ningún campo de veracidad, y un JSON con un campo extra (p. ej. `is_truthful`) se rechaza. `[N0]`
- **AC5.5.4** Given el enum de calificación, When lo valido, Then tiene exactamente «congruente», «incongruente» y «no documentada»; los únicos rótulos de resultado en pantalla son «Sugerencia de revisión», «Incongruencia semántica» y «Hecho No Documentado». `[N0]`

### US5.6 — Revisar alertas con teclado y lector de pantalla · SHOULD · P1
Como Analista de Verdad, quiero recorrer el flujo sin ratón y con lector de pantalla, para trabajar con
la atención repartida o con una discapacidad.
*Origen:* `requirements.md` §7 (pregunta abierta asignada a esta etapa), S12-R2 (Seguimiento 3).

- **AC5.6.1** Given login, lista de sesiones, sesión, panel de alertas, paquete de traspaso y consolidación, When corre `@axe-core/playwright` con WCAG 2.1 AA, Then hay 0 violaciones de impacto `serious` o `critical`. `[N3]`
- **AC5.6.2** Given el flujo de texto de punta a punta, When lo recorro solo con teclado (Tab, Enter, Espacio, Escape), Then puedo enviar un turno, desplegar la CoT, aceptar, editar, descartar y consolidar, con el foco siempre visible. `[N3]`
- **AC5.6.3** Given cualquier estado de turno, alerta o sesión, When lo veo, Then se identifica por texto o icono además del color. `[N0]` Vitest

---

## Épica 6 — Consolidación y reporte

### US6.1 — Consolidar la sesión cuando todo está revisado · MUST · P1
Como Analista de Verdad, quiero consolidar el reporte solo cuando revisé cada alerta, para que ningún
hallazgo de la IA llegue al reporte sin validación humana.
*Origen:* FR7.1, FR7.2, FR7.3 (Seguimiento 1 de RA, Seguimiento 1).

- **AC6.1.1** Given una sesión no finalizada, con alguna alerta `pendiente` o con algún turno «En cola» o «Procesando», When intento consolidar, Then el botón está deshabilitado con su motivo visible («Finaliza la sesión para consolidar», «Quedan N sugerencias pendientes» con enlace a la primera, «Hay turnos en proceso») y la API responde `409` sin crear reporte. `[N1]` + `[N0]` Vitest
- **AC6.1.2** Given todas las alertas revisadas, When pulso «Finalizar y Consolidar», Then un diálogo resume cuántas sugerencias quedaron aceptadas, editadas y descartadas, cuántos Hechos No Documentados hay y qué turnos están en «Error», y avisa «Después de consolidar, la sesión queda bloqueada; una corrección creará una versión nueva», con «Consolidar» y «Cancelar». `[N0]` Vitest
- **AC6.1.3** Given que confirmo, When se consolida, Then el reporte Markdown contiene la transcripción por turnos, cada alerta con su estado y notas, los Hechos No Documentados con su paquete, los turnos en «Error» rotulados «turno no evaluado» con su `code`, la versión del escenario, el umbral de la sesión y quién consolidó y cuándo; y se guarda en el volumen persistente con su SHA-256 registrado, recalculable. `[N1]`
- **AC6.1.4** Given un reporte recién consolidado, When termina, Then veo quién y cuándo, el SHA-256 completo con acción para copiarlo y «Descargar reporte». `[N0]` Vitest
- **AC6.1.5** Given una sesión consolidada, When intento cambiar una alerta directamente, Then `409` sin cambios. `[N1]`
- **AC6.1.6** Given dos peticiones de consolidación simultáneas, When terminan, Then exactamente una responde `200` y la otra `409`, con un solo reporte y un solo SHA-256. `[N1]`
- **AC6.1.7** Given una sesión de otro analista, un usuario `admin` o una identidad de servicio, When intenta consolidar, Then `403`. `[N1]`

### US6.2 — Descargar el reporte y comprobar su integridad · MUST · P1
Como Analista de Verdad, quiero descargar el reporte consolidado, para entregarlo y que cualquiera pueda
comprobar que no cambió.
*Origen:* FR7.3, FR7.4.

- **AC6.2.1** Given un reporte consolidado, When lo descargo, Then el SHA-256 del archivo coincide con el registrado y visible junto a la descarga. `[N1]` + `[N3]`
- **AC6.2.2** Given una sesión sin consolidar, When pido la descarga, Then `409` con `code` estable y la interfaz no ofrece la acción. `[N1]`

### US6.3 — Corregir un reporte consolidado con una versión nueva · MUST · P1
Como Analista de Verdad, quiero corregir un reporte ya consolidado sin borrar el anterior, para enmendar
un error dejando el rastro completo.
*Origen:* FR7.5 (P7).

- **AC6.3.1** Given mi sesión consolidada, When pulso «Corregir reporte», Then se abre una copia de trabajo rotulada «Copia de trabajo de la versión N. Solo puedes cambiar estados y notas»; cambiar la transcripción o la salida de la IA responde `422`. `[N1]` + `[N0]` Vitest
- **AC6.3.2** Given una copia de trabajo abierta, When pulso otra vez «Corregir reporte», Then vuelvo a la misma copia: nunca hay dos abiertas por sesión; y «Descartar copia» la elimina sin crear versión. `[N1]`
- **AC6.3.3** Given la copia sin alertas `pendiente`, When consolido, Then se crea una versión nueva con su SHA-256, quién y cuándo, que referencia a la anterior; los bytes de la anterior recalculan el mismo SHA-256. `[N1]`
- **AC6.3.4** Given dos versiones de reporte, When consulto los estados de alertas de cada una, Then cada versión conserva los suyos (la revisión pertenece a la versión de reporte), y la lista de versiones muestra SHA-256, quién y cuándo, con la vigente marcada. `[N1]` + `[N0]` Vitest
- **AC6.3.5** Given una sesión de otro analista o un usuario `admin`, When intenta «Corregir reporte», Then `403`. `[N1]`

---

## Épica 7 — Reanudación

### US7.1 — Reanudar una sesión interrumpida · MUST · P1
Como Analista de Verdad, quiero retomar una sesión tras perder la conexión, para no repetir la entrevista
ni perder lo ya procesado.
*Origen:* FR8.1, FR8.2, FR8.3.

- **AC7.1.1** Given una sesión abierta, When el servidor no recibe el latido de la consola durante *T* segundos (configurable; *T* lo fija NFR Requirements), Then la sesión pasa a «Suspendida» en ≤ *T* + el intervalo de revisión y el cambio guarda la hora. `[N1]`
- **AC7.1.2** Given una sesión «Suspendida» mía, When vuelvo a entrar, Then veo «Se detectó una interrupción inesperada en la sesión. ¿Desea reanudar desde el último turno registrado?» con «Reanudar» y «Más tarde»; con «Más tarde» sigue suspendida y se reanuda desde la lista. `[N0]` Vitest
- **AC7.1.3** Given una transcripción cortada a mitad de su procesamiento, When reanudo, Then los conteos de turnos, alertas y filas de historial son iguales antes del corte y después de reanudar, sin duplicados. `[N1]`
- **AC7.1.4** Given una sesión «Suspendida» con turnos en cola, When pasa el tiempo, Then el trabajador los termina y al reanudar se ven «Evaluado» o «Error» con sus alertas. `[N1]`
- **AC7.1.5** Given una sesión de otro analista, When intento reanudarla, Then `403`. `[N1]`

---

## Épica 8 — Acceso, administración y auditoría

### US8.1 — Iniciar sesión en la consola · MUST · P1, P2
Como usuario de Veridicus, quiero entrar con usuario y contraseña, para que cada acción quede a mi nombre.
*Origen:* FR1.1, FR1.3.

- **AC8.1.1** Given credenciales válidas, When inicio sesión, Then el `analista` llega a la lista de sesiones y el `admin` a la gestión de usuarios. `[N1]` + `[N0]` Vitest
- **AC8.1.2** Given un usuario inexistente o una contraseña errónea, When intento entrar, Then ambos casos producen el mismo estado y el mismo cuerpo byte a byte, con un mensaje en español. `[N1]`
- **AC8.1.3** Given una contraseña única sembrada, When busco en todas las columnas de texto y en los logs capturados, Then hay 0 coincidencias y el hash tiene el prefijo de un algoritmo adaptativo con sal. `[N1]`
- **AC8.1.4** Given cada ruta del OpenAPI salvo inicio de sesión y salud, When la llamo sin token, Then `401`. `[N1]`
- **AC8.1.5** Given que mi sesión web expira con una sesión de entrevista abierta, When vuelvo a entrar, Then regreso a esa sesión sin pérdida. `[N1]` (la duración la fija NFR Requirements)

### US8.2 — Gestionar usuarios · MUST · P2
Como Administrador de plataforma, quiero crear y desactivar usuarios con su rol, para controlar quién
usa la consola.
*Origen:* FR1.2.

- **AC8.2.1** Given que soy `admin`, When creo un usuario `analista`, Then puede iniciar sesión con ese rol. `[N1]`
- **AC8.2.2** Given un usuario `analista`, When intenta gestionar usuarios, Then `403`. `[N1]`
- **AC8.2.3** Given un usuario desactivado, When usa su token vigente o intenta entrar, Then `401`, y sus acciones pasadas conservan su autoría. `[N1]`

### US8.3 — Cambiar el umbral con un PR revisable · MUST · P2
Como Administrador de plataforma, quiero cambiar el umbral de similitud solo mediante un PR, para que
el cambio quede aprobado y registrado y el sistema nunca se recalibre solo.
*Origen:* FR9.1, FR9.2 (P5), AUTONOMIA-01.

- **AC8.3.1** Given el OpenAPI, When lo enumero, Then no hay ninguna ruta que escriba el umbral `[N0]`; y Playwright recorre la consola con ambos roles sin encontrar ese control `[N3]`.
- **AC8.3.2** Given el código de los servicios, When corre la regla estática, Then falla si un módulo fuera del cargador de configuración escribe el ajuste; con control negativo. `[N0]`
- **AC8.3.3** Given un PR que cambia el umbral, When se fusiona en `main`, Then el historial de git muestra quién, cuándo, el valor anterior y el nuevo. `[Manual]`, con el `git log` adjunto como evidencia

### US8.4 — Que el rastro de auditoría no se pueda reescribir · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que cada decisión quede registrada de forma permanente, para
poder auditar quién hizo qué y cuándo.
*Origen:* FR1.3, NFR11, AUTONOMIA-03.

- **AC8.4.1** Given cada tabla de cambios de estado (alertas, consolidaciones, versiones de reporte, umbral de sesión, «CoT consultada»), When intento un `INSERT` con actor u hora nulos, Then falla. `[N1]`
- **AC8.4.2** Given una fila de esos historiales, When intento `UPDATE` o `DELETE` con el usuario de la aplicación, Then falla. `[N1]`

---

## Épica 9 — Plataforma en el clúster

### US9.1 — Aislar de internet los pods con datos sin anonimizar · MUST · P2
Como Administrador de plataforma, quiero una `NetworkPolicy` que niegue la salida a internet a esos pods,
para demostrar que ningún testimonio sale del clúster.
*Origen:* FR12.3, NFR1, AUTONOMIA-04.

- **AC9.1.1** Given los manifiestos, When corre la política, Then falla si un pod no tiene la etiqueta de clasificación de datos o si un pod con datos sin anonimizar no está cubierto por una `NetworkPolicy` de salida denegada; con control negativo. `[N0]`
- **AC9.1.2** Given el clúster desplegado, When desde cada pod sensible ejecuto `curl -m 5` a un *host* público, Then termina con código ≠ 0, y el mismo pod sí alcanza PostgreSQL y Redis (control positivo). `[Manual]`, solo lectura, sin `apply`
- **AC9.1.3** Given el diseño, When se revisa en Infrastructure Design, Then cada componente de `deploy/` aparece en la tabla de fronteras (dentro o fuera del clúster, datos que cruzan). `[Manual]`
- **AC9.1.4** Given que no existe el anonimizador, When la configuración trae una URL de LLM o de *embeddings* que no es interna del clúster, Then el servicio no arranca. `[N0]`
- **AC9.1.5** Given un turno con un *canary* único sembrado, When termina su procesamiento, Then el *canary* no aparece en ningún log capturado de ningún servicio. `[N1]`

### US9.2 — Saber que cada servicio está listo · MUST · P2
Como Administrador de plataforma, quiero que cada servicio exponga su salud, para que la prueba de humo
diga si el despliegue sirve.
*Origen:* FR12.5.

- **AC9.2.1** Given un servicio listo, When consulto su *endpoint* de salud, Then responde `200`; con PostgreSQL caído, no responde `200`. `[N1]`
- **AC9.2.2** Given el despliegue completo (requiere US3.1 y US4.2), When corro `scripts/smoke.sh <url-base>`, Then termina con código 0 solo si todos los servicios responden `200` y el *spec* de humo pasa en ≤ *N* s (*N* lo fija NFR Requirements). `[N3]`

### US9.3 — Declarar recursos y credenciales de cada pod · MUST · P2
Como Administrador de plataforma, quiero que cada pod declare sus recursos y tome sus credenciales de
Secrets, para evitar caídas por memoria y credenciales en el repositorio.
*Origen:* FR12.2, FR12.4, NFR10.

- **AC9.3.1** Given los manifiestos, When corre la política de Kyverno CLI, Then falla si algún pod no tiene `resources.requests` y `resources.limits`; con control negativo. `[N0]`
- **AC9.3.2** Given los manifiestos, When corre la política, Then falla si una variable cuyo nombre contiene `PASSWORD`, `TOKEN`, `KEY` o `SECRET` usa `value` literal en vez de `secretKeyRef` o `envFrom`, y `gitleaks` termina con código 0; ambos con control negativo. `[N0]`

### US9.4 — Base de datos y cola dentro del clúster · MUST · P2
Como Administrador de plataforma, quiero PostgreSQL + `pgvector` con CloudNativePG y Redis como artefactos
revisables, para que todo el estado viva en el clúster local.
*Origen:* FR12.1.

- **AC9.4.1** Given el chart, When corren `helm template` y `kubeconform`, Then aparecen un `Cluster` de CloudNativePG con la extensión `pgvector` y Redis `[N0]`; y cuando el humano lo aplica tras la fusión de su PR, ambos quedan dentro del clúster `[Manual]`.
- **AC9.4.2** Given los manifiestos, When corre la política, Then falla si un `Deployment` o un `initContainer` ejecuta las migraciones; solo existen como `Job`. `[N0]`

### US9.5 — Ningún *workflow* aplica cambios al clúster · MUST · P2
Como Administrador de plataforma, quiero que la CI y los *scripts* nunca apliquen cambios al clúster, para
que todo cambio pase por una aprobación humana registrada.
*Origen:* AUTONOMIA-01, team-practices (mapa AUTONOMIA).

- **AC9.5.1** Given `.github/workflows/` y `scripts/`, When corre la comprobación estática, Then ninguno contiene `kubectl apply`, `helm install`, `helm upgrade`, `terraform apply` ni migraciones contra el clúster, y ningún *workflow* referencia un `kubeconfig`; con control negativo. `[N0]`

---

## Épica 10 — Funciones SHOULD

### US10.1 — Ver el progreso del procesamiento · SHOULD · P1
*Origen:* FR10.1. Como Analista de Verdad, quiero ver qué hace el sistema y cuánto lleva, para no dudar si se colgó.
- **AC10.1.1** Given un turno en proceso, When lo miro, Then veo su etapa («Procesando audio…», «Consultando marco de verdad…») y un cronómetro; cada cambio se anuncia en `aria-live="polite"`. `[N0]` Vitest
- **AC10.1.2** Given un turno que supera el *timeout* de evaluación (lo fija NFR Requirements), When vence, Then pasa a «Error» con la opción de reintentar; nunca queda en «Procesando» indefinidamente. `[N1]`

### US10.2 — Grabar un turno por voz · SHOULD · P1
*Origen:* FR10.2. Como Analista de Verdad, quiero grabar un turno con un botón, para usar la voz cuando el flujo de texto ya funciona.
- **AC10.2.1** Given el flujo de texto funcionando, When grabo y envío un turno, Then se transcribe con Whisper en CPU dentro del clúster y sigue el mismo camino que un turno de texto. `[N1]` con transcriptor *fake*
- **AC10.2.2** Given un transcriptor *fake* que tarda 12 s, When envío el audio, Then el `POST` responde `202` y la interfaz acepta otro envío antes de que termine. `[N1]` + `[N0]` Vitest
- **AC10.2.3** Given que el navegador niega el micrófono, When pulso grabar, Then veo «No hay acceso al micrófono. Puedes seguir escribiendo el turno» y la entrada de texto sigue disponible; mientras graba hay un indicador visible y anunciado. `[N0]` Vitest

### US10.3 — Recibir una sugerencia de pregunta · SHOULD · P1
*Origen:* FR10.3. Como Analista de Verdad, quiero que la IA me sugiera la siguiente pregunta, para decidir yo si la formulo.
- **AC10.3.1** Given un turno evaluado sin afirmaciones «no documentada», When termina, Then veo «Pregunta sugerida · requiere tu aprobación» con «Aprobar» y «Descartar», y el constructor del *prompt* recibe solo pasajes del marco de verdad. `[N0]`
- **AC10.3.2** Given un turno con alguna afirmación «no documentada», When termina, Then no hay pregunta sugerida (vale aunque FR10.3 no se construya). `[N0]`
- **AC10.3.3** Given una pregunta sugerida, When no la apruebo, Then no se reproduce ni se registra como formulada. `[N0]`

### US10.4 — Escuchar la pregunta · SHOULD · P1
*Origen:* FR10.4. Como Analista de Verdad, quiero reproducir en voz la pregunta que apruebo, para leerla al compareciente.
- **AC10.4.1** Given una pregunta aprobada, When pulso «Escuchar audio», Then se sintetiza en CPU dentro del clúster y se reproduce; sin pulsarlo, el TTS *fake* registra 0 llamadas. `[N0]`

### US10.5 — Confirmar cada alerta en ambos órdenes · SHOULD · P1
*Origen:* FR10.5. Como Analista de Verdad, quiero que una alerta solo se registre si la IA la sostiene al invertir el orden de lectura, para recibir menos falsas alarmas.
- **AC10.5.1** Given un juez *fake* que discrepa solo en un orden, When se evalúa en ambos órdenes de forma asíncrona, Then no se registra alerta; la permutación nunca produce alerta bajo el umbral `[N0]`; consistencia > 65 % `[N2]` (NFR4).

### US10.6 — Recibir una propuesta de umbral cuando hay ruido · SHOULD · P2
*Origen:* FR9.3, NFR15. Como Administrador de plataforma, quiero que Grafana me avise cuando una sesión supere el AIR, para proponer un nuevo umbral sin que el sistema lo cambie solo.
- **AC10.6.1** Given la ventana y la definición de alerta «ignorada» que fije NFR Requirements, When `promtool test rules` corre con 25 % exacto y con 25 % + 1 alerta, Then no alerta y alerta, respectivamente, con una propuesta de umbral. `[N0]`
- **AC10.6.2** Given una propuesta, When nadie hace nada, Then el umbral no cambia; aplicarla sigue US8.3. `[N0]`

### US10.7 — Sincronizar el clúster con GitOps · SHOULD · P2
*Origen:* FR12.6. Como Administrador de plataforma, quiero que Argo CD aplique lo fusionado en `main`, para que el clúster refleje solo cambios aprobados.
- **AC10.7.1** Given la `Application` de Argo CD, When corre la política, Then usa una *deploy key* de solo lectura y no tiene *prune* sobre CloudNativePG y sus PVC `[N0]`; la sincronización real se verifica `[Manual]`.

---

## Épica 11 — Funciones COULD

### US11.1 — Ver indicios afectivos en el paquete de traspaso · COULD · P1
*Origen:* FR11.1. Como Analista de Verdad, quiero ver palabras clave emocionales del fragmento, para moderar el ritmo de la entrevista.
- **AC11.1.1** Given el clasificador afectivo ligero activo, When se genera un paquete, Then incluye «Fluctuación afectiva por posible estrés/trauma en este fragmento. Se recomienda moderar el ritmo»; desactivado, no lo incluye; el texto entra al escaneo de AC5.5.1. `[N0]`

### US11.2 — Volver a una sesión desde el historial lateral · COULD · P1
*Origen:* FR11.2. Como Analista de Verdad, quiero un panel lateral con mis sesiones anteriores, para retomarlas sin salir de la sesión actual.
- **AC11.2.1** Given sesiones previas, When abro el panel lateral, Then las veo ordenadas por fecha con su estado. `[N0]` Vitest

### US11.3 — Anonimizar antes de cualquier llamada externa · COULD · P2
*Origen:* FR11.3, AUTONOMIA-04. Como Administrador de plataforma, quiero que todo lo que salga hacia un LLM externo pase por el anonimizador, para cumplir la soberanía de datos.
- **AC11.3.1** Given el proxy construido, When el agente llama a un LLM externo, Then el *payload* saliente no contiene los nombres, ubicaciones ni números de expediente sembrados; si el anonimizador falla, no se hace la llamada (falla cerrado). `[N0]` con 100 % de ramas
- **AC11.3.2** Given la `NetworkPolicy`, When corre la política, Then solo el proxy tiene salida fuera del clúster. `[N0]`

### US11.4 — Escalar los trabajadores según la cola · COULD · P2
*Origen:* FR12.7. Como Administrador de plataforma, quiero que KEDA escale los pods de IA con la longitud de la cola, para liberar CPU cuando no hay entrevistas.
- **AC11.4.1** Given la cola vacía durante el periodo configurado, When se evalúa el escalado, Then los pods de inferencia escalan a 0; con mensajes en cola, a 1 o más. `[Manual]` en el clúster

---

## Dependencias

| Historia | Depende de |
|---|---|
| US1.2, US1.3 | US1.1 |
| US2.1 | US1.3, US8.1 |
| US2.2, US2.3 | US2.1 |
| US2.4 | US2.2 |
| US2.5, US8.2 | US8.1 |
| US3.1, US3.2, US4.1 | US2.2 |
| US4.2 | US4.1 |
| US5.1–US5.4 | US3.1 |
| US6.1 | US2.4, US4.2, US5.1–US5.3 |
| US6.2, US6.3 | US6.1 |
| US7.1 | US2.2, US5.1 |
| US9.2 (AC9.2.2) | US3.1, US4.2 |
| US10.2–US10.5 | US2.2 y US3.1 (flujo de texto funcionando); US10.3 también US4.1 |
| US10.6 | US5.3 y FR12.6 (Prometheus/Grafana) |

**Ruta crítica del flujo de texto:** US8.1 → US1.1 → US1.3 → US2.1 → US2.2 → US3.1 → US4.1 → US5.1 →
US2.4 → US6.1 → US6.2.

## Cobertura AUTONOMIA

| Regla | Prueba del mapa de team-practices | Criterios |
|---|---|---|
| 01 | Ningún *workflow* ni *script* aplica cambios | AC9.5.1, AC9.4.1, AC8.3.3 |
| 02 | Cada tarea nombra su verificación | Todos los criterios llevan nivel y comando o prueba |
| 03 | Máquina de estados con actor y hora | AC5.1.2–AC5.1.4, AC5.2.1, AC5.3.2, AC8.4.1, AC8.4.2 |
| 03 | Consolidación explícita con SHA-256 | AC6.1.1–AC6.1.7, AC6.3.3 |
| 03 | Esquema sin campos de veracidad y escaneo de vocabulario | AC5.5.1–AC5.5.4, AC3.2.4 |
| 04 | `NetworkPolicy` estática y manual; *payload* del anonimizador | AC9.1.1–AC9.1.5, AC11.3.1 |
| 05 | Alerta rechazada sin cada campo; umbral de configuración; prueba bajo el umbral | AC3.1.2, AC2.1.2, AC4.3.1, AC4.1.1–AC4.1.3, AC4.2.4 |

## Notas INVEST

- Cada historia MUST se puede probar por sí misma con datos sembrados y dobles deterministas; las
  dependencias de la tabla son de datos de prueba, no de código compartido.
- El Silencio Fáctico se partió en US4.1 (decisión por umbral) y US4.2 (paquete), y la corrección del
  reporte dejó en US6.1 la poscondición de bloqueo; así Units Generation dimensiona con historias pequeñas.
- La protección de rastros se separó en US8.4 para que AUTONOMIA-03 tenga su propia historia comprobable.
- Los NFR de calidad (NFR2–NFR9, NFR13–NFR14) y los datos sintéticos (NFR12) no son historias: quedan
  diferidos a NFR Requirements y Build and Test (respuesta 3).
- US10.5 duplica las inferencias por alerta candidata en CPU; Delivery Planning debe contarlo frente a
  NFR3 y NFR8.
