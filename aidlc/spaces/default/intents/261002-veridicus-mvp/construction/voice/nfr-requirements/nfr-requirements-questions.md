# Preguntas de NFR Requirements — U9 voice

**Unidad.** U9 `voice` (SHOULD): grabación por demanda, transcripción con Whisper ligero en CPU y audio
de la pregunta aprobada (`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Máximo 120 s por grabación en WAV mono de
16 kHz (P1), audio borrado del *stream* tras confirmarlo, servidor de Whisper de U2 (`faster-whisper`
compatible con OpenAI), 8–12 s por turno de voz aceptados en CPU (NFR3 de requirements), y el camino del
turno de texto de U4 tras transcribir. Quedan para esta etapa el tamaño máximo del audio (pregunta
abierta de C5) y el modelo de Whisper.

---

## P1 — Tamaño máximo del audio y cómo viaja

120 s en WAV mono de 16 kHz ocupan unos 3,8 MB (unos 5,1 MB en base64 dentro del mensaje de Redis).
Functional Design propuso 6 MB y conservar el audio dentro del mensaje.

A. `VERIDICUS_VOICE_MAX_BYTES` = 6 MB y el audio viaja en base64 dentro del mensaje de C5, borrado con
   `XDEL` al confirmarlo; más grande → rechazo antes de encolar. (Recomendada)
B. 6 MB, pero el audio va a un volumen temporal y el mensaje lleva solo una referencia, con borrado
   tras transcribir.
C. 4 MB (unos 100 s), dentro del mensaje.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Modelo de Whisper

El PRD pide Whisper ligero (`tiny` o `base`) en CPU y acepta 8–12 s por turno de voz. Un modelo más
grande transcribe mejor el español pero tarda más.

A. `base` cuantizado int8 con `faster-whisper`, idioma fijo `es`: p95 ≤ 12 s por turno de hasta 30 s
   de audio y ≤ 40 s para una grabación de 120 s. (Recomendada)
B. `tiny` int8: unas dos veces más rápido, con más errores de transcripción en nombres y fechas.
C. `small` int8: mejor transcripción, fuera de «ligero» y con riesgo para los 8–12 s.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Unidad.** U9 `voice` (SHOULD; VE-08 y VE-09 son MUST cuando U9 se construye), con su Functional Design
revisión 2, aprobado hoy: espera en orden de las corridas (RunPublicationHold), audio conservado con
autorización (TurnAudio), voz de la aclaración aprobada con plantilla versionada, autorización de voz y
encaje con la pausa, la terminación y la retirada.

## Lo que ya está decidido

- P1 = A (6 000 000 bytes, base64 dentro de C5) y P2 = A (Whisper `base` int8, p95 ≤ 12 s para 30 s y
  ≤ 40 s para 120 s) de la primera pasada siguen.
- Functional Design revisión 2: P1 = A (120 s), P2 = A (sin reintento), P3 = A (sin corrección), P4 = A
  (audio conservado al recibirlo y sin uso), P5 = B (espera en orden), P6 = C (se transcribe tras terminar,
  no tras la retirada) y P7 = A (frase fija versionada con el tema).
- Lo fijado hoy por otras unidades: `limits.exceeded` siempre `413` y C25 sin nulos (U1); Redis con AOF,
  volumen de audio aparte de `session-api` con *prune* desactivado y el Job de retención que lo monta (U2);
  p95 incremental ≤ 180 s y *N* = 300 s (U11); liberación de una corrida en espera ≤ 1 s tras la ingesta
  (NFR-U4-10); el puerto `is_observation_approved` de U8 (NFR-U8-07).
- **Conflicto de NFR-U11-11 (`transcribe` y `synthesize`).** No es una contradicción entre fuentes
  aprobadas: C13 revisión 3 (`libs/model_gateway/port.py` v2.0.0) ya declara los dos métodos como SHOULD y
  solo locales; la tabla de contratos pone a U9 como consumidor de C13 y de C14 («adaptadores locales de
  ModelGateway»), y `unit-of-work-dependency.md` justifica la arista voice → incoherence-analyzer porque
  «SpeechProcessing llama a Whisper y TTS por ModelGateway, que es de U11». El Functional Design de U11 no
  los declara, pero no los excluye. Se resuelve sin preguntar en D13 y NFR-U9-01: los métodos se quedan en
  el puerto de U11 y los escribe U9 en B9; no hace falta un PR de U1.

## Cómo se registra la revisión

Revisión 2 de los seis documentos y de `traceability.json`, que sustituye a la revisión 1 del 2026-10-03.
Los IDs que siguen se conservan; lo que sale queda «Retirado» sin renumerar; lo nuevo toma el número
siguiente de su grupo. Las precisiones a artefactos aprobados van en la tabla NFR-U9 de
`security-requirements.md` §6; las filas de la revisión 1 quedan como «Superado».

## Lo que el diseño resolverá sin preguntar

1. Cifras de C25 de U9 (tamaño, duración, plazos, *timeouts*, entregas, TTL, texto de la voz, cuota del
   audio conservado), con los mínimos que exigen los flujos.
2. Base del plazo de audio a 360 s y 2 entregas como máximo, para que la segunda entrega quepa con margen
   (cierra R-03 de la revisión 1).
3. Cota comprobable del rastro del audio en el AOF de Redis (cierra R-01).
4. TTL de las claves de FD-U9-06: plazo máximo de la transcripción más un margen igual al reclamo de C5.
5. Almacenamiento del audio conservado: volumen propio, permisos, cuota y sin cifrado en reposo, con el
   mismo criterio que los reportes de U7.
6. Latencia del turno escrito que espera a uno de voz y de la síntesis con la plantilla.
7. Duración medida sobre el audio (recuento de muestras o de tramas), nunca sobre la cabecera.
8. Métricas solo con etiquetas permitidas por U1.

**Sin preguntas: todo lo fijan las fuentes.**
