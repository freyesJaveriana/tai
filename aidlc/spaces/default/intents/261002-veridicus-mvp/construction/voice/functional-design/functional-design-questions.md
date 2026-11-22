# Preguntas de Functional Design — U9 voice

**Unidad.** U9 `voice` (tipo `service`, SHOULD): grabar un turno por voz y transcribirlo con Whisper en
CPU dentro del clúster (US10.2), y escuchar la pregunta aprobada (US10.4). El turno transcrito sigue el
mismo camino que un turno de texto (U4).

**Lo que ya está decidido y no se vuelve a preguntar.** La grabación es *push-to-talk* en WAV o MP3 y va
por `POST /sessions/{id}/voice-turns` asíncrono. La respuesta es `202` con el turno numerado en la etapa
`transcribing`, y la consola acepta otro envío antes de que termine (FR10.2, AC10.2.2, C1). El audio viaja
en base64 por el *stream* `veridicus:audio`. El `audio-worker` llama a Whisper con `language: es` por
ModelGateway y publica el texto en `veridicus:transcripts`. Con el texto, InterviewSession publica el
mismo turno en la cola de evaluación (C5, C13, C14). El audio crudo nunca sale del clúster y se borra del
*stream* tras confirmarlo (SpeechProcessing, AUTONOMIA-04). Si el navegador niega el micrófono, aparece
«No hay acceso al micrófono. Puedes seguir escribiendo el turno» (AC10.2.3). La voz de la pregunta se
sintetiza en CPU solo al pulsar «Escuchar audio» y solo para una pregunta aprobada (AC10.4.1, C1). Quedan
tres huecos.

---

## P1 — Duración máxima de una grabación

El audio viaja dentro del mensaje de Redis, y el contrato deja abierto su tamaño máximo (C5, pregunta
abierta de U9). Un turno muy largo hace pesado el mensaje y lento a Whisper en CPU. Sin un límite, una
grabación olvidada encendida podría bloquear al trabajador.

A. Máximo 120 segundos por turno. La consola muestra el tiempo que queda y detiene la grabación sola a los
   120 s con el aviso «Se alcanzó el máximo de 2 minutos; envía este turno y graba el siguiente». La API
   rechaza un audio más largo o más pesado que el límite con `422 validation.invalid_request` sin crear
   el turno. El límite en bytes y su valor por configuración los fija NFR Requirements. (Recomendada)
B. Máximo 60 segundos, con el mismo comportamiento.
C. Sin límite en la consola; solo la API rechaza por tamaño.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué pasa si la transcripción falla

Whisper puede fallar por *timeout* o error del sistema, o devolver un texto vacío (silencio, ruido). Hoy
«Reintentar» reprocesa el mismo turno, pero el audio se borra del *stream* tras confirmarlo, así que no
habría nada que volver a transcribir.

A. El turno pasa a «Error» con su `code` (`turn.error.timeout`, `turn.error.system`, o
   `turn.error.invalid_output` si el texto sale vacío) y el audio se borra igual. Un turno de voz con
   error en la transcripción no ofrece «Reintentar», sino «Grabar de nuevo» o escribir el turno, que
   crean un turno nuevo. El turno fallido queda en el reporte como «turno no evaluado». Nunca se guarda
   audio para reintentar. (Recomendada)
B. El audio se conserva cifrado en el *stream* hasta que el turno se transcribe bien o la sesión se
   finaliza, para permitir «Reintentar» sobre el mismo turno; después se borra.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — ¿El analista ve o corrige la transcripción antes de evaluarla?

Whisper puede transcribir mal un nombre o una fecha, y el juez evaluaría ese texto. Pero corregirlo
también es cambiar el testimonio, y el criterio pide que el turno de voz siga el mismo camino que el de
texto (AC10.2.1).

A. No hay paso de corrección. El texto transcrito se evalúa tal cual y se muestra rotulado «Turno por voz
   (transcripción automática)». Si la transcripción está mal, el analista escribe un turno nuevo con la
   aclaración, y los dos quedan en el reporte. (Recomendada)
B. Antes de evaluar, el analista ve la transcripción y puede corregirla y confirmarla. El turno espera en
   un estado nuevo «por confirmar», y el reporte guarda el texto de Whisper y el corregido.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-22)

**Unidad.** U9 `voice` (tipo `service`, SHOULD, tamaño M; Bolt B9, después de la línea de corte de las
MUST). Según la revisión 3 de `unit-of-work.md`, entrega dos cosas: grabar un turno por voz y
transcribirlo con Whisper en CPU dentro del clúster (US10.2), y **escuchar la aclaración aprobada**
(US10.4), que sustituye a la pregunta sugerida. Restricciones nuevas: exige la autorización de voz del
consentimiento (A-4, VE-06) y el audio crudo solo se conserva con autorización expresa (VE-08). **Sale**
la voz de la pregunta sugerida (SuggestedQuestion, retirada con el Paquete de Contexto de Traspaso).
**Entran** la guardia de autorización de voz (AC15.4.3), el ciclo de vida del audio conservado
(AC10.2.4), el rechazo del TTS a todo texto que no sea una aclaración aprobada y validada (AC10.4.2,
VE-09) y el encaje con la pausa, la terminación y la retirada del consentimiento de U6 (VE-10).

## Lo que ya está decidido y no se vuelve a preguntar

| Tema | Qué está decidido | Fuente |
|---|---|---|
| Preguntas P1–P3 de la primera pasada | **Siguen.** 120 s por grabación; sin reintento de la transcripción ni audio guardado para reintentar; sin paso de corrección y con el rótulo de transcripción automática | P1–P3 = A; project.md § Corrections («sin audio guardado para reintentar», «ante Whisper caído no hay reintento») |
| Ruta y forma del envío | `POST /sessions/{id}/voice-turns` multipart con `audio` (WAV mono de 16 kHz o MP3), `hablante` (`ENT` o `TEST`) y `client_request_id`; `202` con el turno; `409 session.voice_not_authorized` sin `autoriza_voz` | C1; AC15.4.3; VE-06 |
| Consentimiento | Sin `ConsentRecord`, `409 session.consent_missing` con la guardia común de U4; los estados que no admiten turnos responden con los mismos codes y el mismo orden que un turno escrito | BR14.3 de U4; AC15.4.2; FD de U6 (rechazo de turnos por estado) |
| Colas | C5 1.1.0: `AudioToTranscribe` lleva `retain_audio` (copia de `autoriza_conservar_audio`); el trabajador nunca guarda audio y borra el mensaje (`XDEL`) tras confirmarlo; con `retain_audio`, lo guarda InterviewSession (TurnAudio), nunca el trabajador | C5; VE-08; components (TurnAudio en el volumen de InterviewSession) |
| Estado del turno | Ya no se guarda en el turno: se deriva de su corrida incremental (U4). El turno de voz lleva `voice_status` (`transcribing`, `transcribed`, `error`), y la etapa «Procesando audio…» la muestra el progreso de U6 | C1 `Turn.voice_status`; BR de estado derivado de U4 (FD-U4-04); FD de U6 BR5.1 |
| Turno ENT y pausa | Un turno de voz ENT se guarda sin corrida, como uno escrito; en pausa, el turno transcrito se guarda sin corrida y «Reanudar análisis» lo cubre | FD-U4-01; FD de U6 BR9.2 y tabla de integración («Su turno de voz entra en pausa sin corrida igual que uno escrito») |
| Audio de la aclaración | `GET /conductor-observations/{id}/audio`, solo el dueño; `409 conductor_observation.not_approved` si no está aprobada; solo al pulsar «Escuchar audio» | C1; AC10.4.1; FD de U8 BR5.14 y E36 |
| Neutralidad | La aclaración que llega a «Aprobada» ya pasó la regla de DT23 y el escaneo (U8); la aclaración no entra en el reporte | FD de U8 punto 3 y P6 = A; C8 |
| Camino de la síntesis | ConsoleApi comprueba dueño y aprobación y llama a la ruta interna `POST /internal/v1/speech` de `audio-worker`, que llama a `ModelGateway.synthesize` contra `model-tts` (Piper) | NFR Requirements de U9, D3 y D4 (cierra R-01) |
| Plazos | Plazo de la transcripción al encolar (`300 s × (1 + m)`, tope 1 800 s) y plazo de evaluación de U4 recalculado al ingerir el texto; el supervisor de plazos de U4 cubre `transcribing` | NFR3.5–NFR3.8 de U9 (cierra R-03) |
| Redis y disco | AOF con reescritura que pide `audio-worker`; lectura del cuerpo sin *spool* a disco | NFR Design de U9 (security-design §2, scalability-design); D7 (cierra R-04) |
| Cifras | Límites de audio en `contracts/limits.v1.yaml` (`audio_max_bytes`, `audio_max_seconds`); un exceso responde `413 limits.exceeded` | C25; project.md (catálogo único de límites) |
| Frontera del clúster | Ningún componente de U9 llama a un servicio externo; solo `anonymizer-proxy` tiene salida | AUTONOMIA-04; mapa de historias (US9.1 y US11.6) |

## Cómo se registra la revisión 2

- Los cuatro artefactos (`entities.md`, `rules.md`, `functional-spec.md`, `traceability.json`) llevan una
  cabecera «Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02» que sustituye a la
  revisión 1 del 2026-10-03 y nombra qué sigue, qué sale y qué entra.
- **IDs estables** (regla de project.md): ningún ID se renumera. Lo que sale queda «Retirado» con su motivo:
  - Entidades: QuestionAudio (la sustituye una entidad nueva para la voz de la aclaración) y la referencia
    a SuggestedQuestion.
  - Flujo F4 (escuchar la pregunta) y, en la tabla de precisiones, X2 (reintento sin audio: en el cambio 01
    el reintento es de corridas y un turno con la transcripción fallida no tiene corrida), X4 (C1 ya marca
    la ruta como solo del dueño) y X5 (lo fijaron NFR Requirements y C25), como «Superado».
- **Siguen y se reescriben**: BR2.3 (límites de C25 y `413`), BR2.5 y BR4.1 (sin `status` ni
  `processing_stage` en el turno; la corrida se crea al ingerir el texto), BR4.3, BR3.3 y BR3.4 (los codes
  de C5), y BR5.1–BR5.4 (solo aprobada, solo al pulsar, sin guardar, solo el dueño) para la aclaración.
- **Entra** lo nuevo con números nuevos: entidades ConductorObservationAudio (la voz de la aclaración) y el
  uso de TurnAudio; reglas desde **BR8.1** (consentimiento y audio conservado) y **BR9.1** (orden de los
  turnos y ciclo de vida de la sesión); flujos desde **F5**; los escenarios de la revisión 1 toman E1–E12 en
  su orden y lo nuevo empieza en **E13**.
- `traceability.json`: suma AC10.2.4, AC10.4.2 y AC15.4.3 (lado de U9), y AC10.4.1 se reescribe para la
  aclaración. Las reglas retiradas van en `reverse` como `N/A` con «Retirado (cambio 01)».
- Las precisiones a artefactos aprobados (contract-summary, components, FD de U4, U6, U8 y U13) van a una
  tabla **FD-U9-01…** en `functional-spec.md`, sin editar los originales; decides en la aprobación. X1 y X3
  pasan a esa tabla con la ruta y los codes nuevos.
- Los hallazgos R-01 a R-07 de `reviews/review-01.md`: R-01, R-03 y R-04 los cerraron NFR Requirements y NFR
  Design (tabla de arriba); R-05, R-06 y R-07 se cierran con los puntos 6, 5 y 2 de la lista siguiente; R-02
  sigue abierto en el modelo del cambio 01 y es la pregunta 5.

## Lo que el diseño resolverá sin preguntar

1. **Orden de las guardias del envío.** Rol y dueño (ConsoleApi), luego `session.consent_missing`, luego el
   orden de estados de U4 y U6 (`blocked`, `consent_withdrawn`, `terminated`, `finalized`, `suspended`),
   luego `session.voice_not_authorized` y por último los límites y el formato. Cada rechazo, 0 filas y 0
   mensajes; una prueba de nivel 1 por guardia.
2. **Formato.** El contrato admite MP3 y se respeta, pero la duración se verifica por el audio decodificado y
   no por la cabecera (D7 de NFR Requirements); el MP3 entra solo por la API y tiene su caso de prueba. Las
   entidades de mensaje suman `schema_version` (cierra R-07).
3. **Codes de la transcripción.** Se alinean con C5 (`analysis.timeout`, `analysis.system`); el texto vacío
   necesita un valor más en el enum de C5 (`analysis.invalid_output`, versión menor), que va como
   precisión FD-U9 en lugar de los `turn.error.*` de la revisión 1.
4. **Turno fallido al transcribir.** Queda con `voice_status: error` y su code, sin corrida; la consola
   ofrece «Grabar de nuevo» y «Escribir el turno» (P2 = A). Ninguna entrada de C6 lo incluye: el contrato ya
   admite huecos en la numeración (FD-U6-06). El reporte lo declara como turno no transcrito (precisión a
   U7).
5. **TTS (VE-09, AC10.4.2).** `audio-worker` vuelve a aplicar la regla de DT23 y el escaneo de C8 al texto
   antes de sintetizar y rechaza cualquier otro texto con `422`, sin llamar al TTS (control negativo por
   caso). Un TTS caído responde `503 speech.unavailable` (antes X3). La concurrencia es la de NFR8.5: un
   audio a la vez por réplica; una segunda petición espera hasta el *timeout* de 10 s (cierra R-06). El
   audio sintetizado no se guarda.
6. **Entrega doble.** El trabajador marca `turn_id` y `attempt` en una clave de Redis con TTL antes de
   publicar; un mensaje repetido se confirma y se borra sin llamar a Whisper (cierra R-05). El valor del TTL
   ya está en NFR Design.
7. **Retención.** TurnAudio cae bajo `purge_session` del Job de retención de U13 y entra en su acta de
   borrado (VE-12); va como precisión a U13 y a la lista de borrado de C24.
8. **Consola.** «Grabar» se deshabilita con `aria-disabled` y su motivo cuando el consentimiento no
   autoriza la voz, igual que los botones de U6; la grabación entra en la suite `axe` de U4 (US5.6) y sus
   cadenas en el escaneo del catálogo de mensajes (US5.5).
9. **Frontera del clúster (AUTONOMIA-04).** La tabla por componente de §1 suma el volumen de
   InterviewSession (audio conservado, dentro del clúster) y la ruta interna `session-api` → `audio-worker`.

---

## P4 — Cuándo y para qué se conserva el audio autorizado

VE-08 y AC10.2.4 permiten conservar el audio con `autoriza_conservar_audio` hasta que venza la retención, y
C5 dice que lo guarda InterviewSession. Ningún insumo dice en qué momento se escribe, qué pasa si la
transcripción falla ni si el audio conservado se usa para algo. project.md dice que no hay audio guardado
para reintentar.

A. **Se escribe al recibirlo y no se usa.** `session-api` escribe el archivo en su volumen con su SHA-256
   (archivo antes que fila) en la misma operación que numera el turno, sea cual sea el resultado de la
   transcripción. No habilita «Reintentar» ni ninguna ruta para escucharlo o descargarlo en el MVP. Solo lo
   borra el Job de retención. Sin la autorización, nada llega al volumen. (Recomendada)
B. **Solo si la transcripción sale bien.** Se escribe al recibirlo y se borra si el turno termina en
   `error`, para conservar solo el audio de un turno que existe como texto.
C. **Como A, y además permite reintentar.** Un turno con audio conservado que falló al transcribir ofrece
   «Reintentar» sobre ese audio. Contradice la regla de project.md para este caso.
D. **Como A, y además el dueño lo puede descargar.** Una ruta nueva de C1, solo del dueño, que queda en el
   registro de acceso (VE-11).
X. Other (please specify)

[Answer]:

## P5 — Turnos enviados mientras uno de voz se transcribe (R-02)

La consola acepta otro turno antes de que termine la transcripción (AC10.2.2). En el cambio 01, la
corrida del turno *n* lleva los turnos 1..*n* (F4 de U4). Si el turno de voz *n* todavía no tiene texto
cuando llega el turno escrito *n+1*, la corrida de *n+1* se arma sin *n*, y la de *n*, cuando llegue el
texto, no ve *n+1*. Así, una contradicción entre *n* y *n+1* solo la encontraría el modo final.

A. **Sin esperar.** Cada corrida lleva solo los turnos que tienen texto al encolarla, y el registro de la
   corrida dice qué turnos llevó. Las contradicciones entre un turno de voz y los que llegaron mientras se
   transcribía quedan para el modo final, como limitación declarada.
B. **Se espera en orden.** La corrida de un turno no se publica hasta que todos los turnos anteriores de voz
   tengan texto o estén en `error`; mientras tanto el turno se ve «En cola · esperando la transcripción del
   turno *n*». Las corridas ven lo mismo que si el relato se hubiera escrito en orden (AC10.2.1), a cambio
   de que *n+1* espere la transcripción (hasta unos 2 min en CPU). (Recomendada)
C. **La corrida del turno de voz mira hacia adelante.** Al llegar el texto de *n*, su corrida lleva todos
   los turnos con texto hasta el último, con el tramo *n*. Encuentra la contradicción con *n+1* sin esperar,
   pero cambia la regla de U4 «turnos 1..*n*» (precisión a U4 y a la regla 2 de C6).
X. Other (please specify)

[Answer]:

## P6 — Turno de voz en transcripción cuando se termina la sesión o se retira el consentimiento

La pausa ya está resuelta (U6: el texto se guarda sin corrida). Para la terminación y la retirada, VE-10
dice que no se encola ninguna corrida nueva, pero el audio ya aceptado puede estar en la cola de
`audio-worker`. Whisper es local, así que transcribir no saca datos del clúster.

A. **Se transcribe siempre.** El texto se guarda en el turno (se dijo antes), sin corrida, y la consola lo
   muestra «Transcrito · sin análisis». Sin código nuevo en `audio-worker`.
B. **No se transcribe en ningún caso.** `audio-worker` lee una clave de cancelación por sesión (el patrón de
   CD-06: la escribe InterviewSession y el trabajador solo la lee), borra el audio sin llamar a Whisper, y
   el turno queda en `error` con `session.terminated` o `session.consent_withdrawn`.
C. **Depende del motivo.** Con la terminación se transcribe como en A, porque la decide el analista y la
   transcripción queda completa. Con la retirada no se transcribe, como en B, porque la persona pidió
   parar y su audio no se procesa más. (Recomendada)
X. Other (please specify)

[Answer]:

## P7 — Qué texto se convierte en voz

La aclaración tiene `tipo`, `tema` y `turnos` (C6). El `tema` es una frase corta («el lugar de la
reunión»), y VE-09 dice que la voz es el único canal hacia la persona entrevistada. Ningún insumo dice qué
frase se pronuncia.

A. **Una frase fija y versionada con el tema.** Un archivo nuevo de U1 en `contracts/integrity/` con la
   plantilla, p. ej. «¿Podría contarnos un poco más sobre {tema}?». El texto completo pasa la regla de DT23
   y el escaneo antes de sintetizarse, y la plantilla solo cambia por PR, con su prueba. Precisión a C8 y a
   U1. (Recomendada)
B. **Solo el tema, tal cual.** No hay archivo nuevo, pero la persona oye un fragmento sin forma de pregunta.
C. **El analista redacta la frase.** Al aprobar, escribe la pregunta, que se valida con la regla de DT23
   antes de sintetizarse. Cambia la entidad de U8 y la ruta de decisión, y VE-09 se cumple solo si esa
   validación es la misma.
X. Other (please specify)

[Answer]:
