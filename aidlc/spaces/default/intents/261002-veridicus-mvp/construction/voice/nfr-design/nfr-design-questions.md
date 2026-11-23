# Preguntas de NFR Design — U9 voice

**Unidad.** U9 `voice` (SHOULD): grabación en la consola y envío por `POST /sessions/{id}/voice-turns`,
cola C5 con el audio en base64, transcripción con Whisper local en `audio-worker`, ingesta del texto
hacia el camino de U4 y síntesis con Piper de la pregunta aprobada por la ruta interna de
`audio-worker`.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D12 de
`nfr-requirements/`: Whisper `base` int8 voraz con VAD e idioma `es`, Piper `es_*` en `model-tts`,
base64 en C5 con máximo de 6 000 000 bytes (P1 = A), un audio a la vez, plazo de audio proporcional
(300 s, tope 1 800 s), *timeout* de Whisper de 90 s, reclamo a 120 s y 3 entregas, `XACK` + `XDEL` con
cualquier resultado, deduplicación con clave de Redis con TTL, sin reintento ante un Whisper caído,
síntesis por `POST /internal/v1/speech` con Bearer, un solo Redis con AOF `everysec` y `save ""` (D9),
y el audio nunca en disco por la aplicación ni en el navegador (NFR10.2, NFR10.5). Quedan dos huecos de
diseño, los dos sobre dónde puede quedar el audio crudo (AUTONOMIA-04).

---

## P1 — Cómo lee `session-api` la subida *multipart* sin que el audio toque el disco del pod

NFR10.2 exige que el audio de `POST /voice-turns` (C1, `multipart/form-data`) se lea solo en memoria.
Pero el analizador que FastAPI usa por defecto (`UploadFile` de Starlette) pasa a un archivo temporal
en disco toda parte de más de 1 MB, y una grabación de 30 s ya ocupa unos 0,96 MB en WAV; con 120 s
(3,84 MB) el audio crudo quedaría escrito en el disco del contenedor. Hay que fijar cómo se lee.

A. La ruta no usa `UploadFile` ni `request.form()`: lee `request.stream()` por trozos y lo pasa a un
   analizador *multipart* en *streaming* (`python-multipart` con sus *callbacks*), que acumula la parte
   `audio` en un `bytearray` y corta con `422` al pasar `VERIDICUS_VOICE_MAX_BYTES`; además el
   contenedor monta `/tmp` como `emptyDir` con `medium: Memory` y el sistema de archivos raíz es de solo
   lectura, como red de seguridad. Se verifica con la prueba de nivel 1 de NFR10.2 que hace fallar
   `tempfile`. (Recomendada)
B. Se mantiene `UploadFile` y se sube el umbral de paso a disco de Starlette por encima de 6 MB
   (atributo de clase `spool_max_size`), más el `/tmp` en memoria: menos código propio, pero depende de
   un detalle interno de Starlette que puede cambiar al actualizarla.
C. Se cambia el contrato C1 para enviar el audio como cuerpo `audio/wav` o `audio/mpeg` crudo, con
   `client_request_id` en una cabecera: lectura en memoria trivial, pero exige un PR de contrato a U1 y
   tocar la consola y el OpenAPI aprobados.
X. Other (please specify)

[Answer]: A **Mode:** guided
## P2 — Cuándo se borra del AOF de Redis el audio ya procesado

D9 acepta que el audio siga en el AOF del PVC de Redis después del `XDEL`, hasta la siguiente
reescritura, que hoy solo dispara el umbral `auto-aof-rewrite-min-size 16mb`. Ese umbral cuenta bytes,
no tiempo: con grabaciones típicas de 10–30 s (0,4–1,3 MB en base64) pueden hacer falta más de 12
turnos para llegar a él, y los audios de los últimos turnos de una sesión pueden quedarse en el disco
de Redis durante días si no hay más tráfico. El riesgo sigue dentro del clúster, pero no está acotado
en el tiempo.

A. `audio-worker` pide `BGREWRITEAOF` cuando la cola de audio queda vacía tras borrar un audio, como
   mucho una vez cada 60 s (y otra vez al final de esa espera si llegó otro audio); si Redis responde
   que ya hay una reescritura en curso, no es error. Así ningún audio queda en el AOF más de unos 2
   minutos después de procesarse. Se verifica con la prueba de nivel 1 de NFR10.4: tras procesar un
   audio centinela y esperar la reescritura, 0 apariciones en `appendonlydir` en ≤ 120 s, sin llamar a
   `BGREWRITEAOF` desde la prueba. (Recomendada)
B. Un proceso periódico (tarea de `audio-worker` cada 10 minutos) pide `BGREWRITEAOF` si hubo algún
   audio desde la última reescritura: más simple, pero el audio puede quedar hasta 10 minutos en disco.
C. Se mantiene lo aprobado: solo el umbral de 16 MB, y el riesgo de tiempo indefinido queda declarado
   como riesgo aceptado junto a T5.
X. Other (please specify)

[Answer]: A **Mode:** guided

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) diseñó la voz con la pregunta sugerida del
Paquete de Contexto de Traspaso, el `DeadlineSweeper` de U4 ampliado, 3 entregas y cifras en variables
de entorno. El cambio 01 y la adenda 02 cambian el objeto de la síntesis (la aclaración aprobada de U8 con
plantilla versionada), añaden la autorización de voz, el audio conservado, la espera en orden de las
corridas y la retirada del consentimiento. El Functional Design revisión 2 (F1–F8, FD-U9-01 a FD-U9-14) y el
NFR Requirements revisión 2 (tabla NFR-U9-01 a NFR-U9-09) ya están aprobados.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| P1 y P2 de la revisión 1 | P1 = A sigue, ahora con el lector `multipart` en memoria compartido de `session_api/shared/` (U6). P2 = A sigue: `audio-worker` pide `BGREWRITEAOF` con la cola vacía, como mucho cada 60 s; NFR10.4 revisión 2 fija además la cota por tamaño, que sigue valiendo como cota superior | Revisión 1; NFR10.4 |
| Requisitos | NFR1.1–NFR1.4, NFR2.1–NFR2.2, NFR3.1–NFR3.16, NFR4.1–NFR4.4, NFR5.1, NFR8.1–NFR8.12, NFR10.1–NFR10.27, NFR11.1–NFR11.2, NFR12.1, NFR13.1–NFR13.3, NFR14.1–NFR14.3, NFR15.1–NFR15.4; decisiones D1–D16 | `nfr-requirements/`, revisión 2 |
| Métodos de voz | `transcribe` y `synthesize` en el puerto de U11, escritos por U9 en B9 | NFR-U9-01; NFRD-U11-01 |
| Supervisor | El `run-supervisor` de U4 vence los turnos de voz y libera las esperas; el código lo escribe U9 en B9 | NFR-U9-07; NFRD-U4-06 |
| Cifras de C25 | Las de NFR-U9-02, por PR de U1; el entorno solo baja | NFRD-U1-09 |
| Métricas | En `contracts/metrics/voice.v1.yaml`, con la lista cerrada de etiquetas de U1 | NFRD-U1-05 |
| Red, Secret, volúmenes e Ingress | `NetworkPolicy`, `veridicus-speech-token`, PVC `veridicus-audio` y Ingress `veridicus-voice` son de U2 | NFRD-U2-03, NFRD-U2-06, NFRD-U2-15 |
| Hardware | Todo en CPU; ninguna meta depende del perfil GPU | NFR2.2; `team.md` |

## Cómo se registra la revisión

- Los seis documentos y `traceability.json` pasan a la revisión 2 en el mismo archivo, con una nota de
  cabecera que dice qué cambia. La revisión 1 queda en el historial de Git.
- Las secciones conservan su número cuando siguen; las que salen quedan «Retirado» sin renumerar y lo
  nuevo toma números nuevos.
- Las precisiones a artefactos aprobados van en la tabla NFRD-U9-xx de `security-design.md`. Ningún
  original se edita.

## Lo que el diseño resolverá sin preguntar

1. **Hallazgos de la revisión 1 de esta etapa.** R-01 (latido independiente de la duración de la
   transcripción), R-02 (recorte por `MINID` desde el supervisor para que el audio no dependa del
   consumidor), R-03 (lo cierran NFR-U9-07 y NFRD-U4-06), R-04 (centinela buscado en base64 en sus tres
   alineaciones) y R-05 (memoria contada con el cliente de Redis y un solo *timeout* de Redis).
2. **Orden de la clave de entrega doble.** BR3.6 dice «justo antes de publicar» y NFR10.14 dice «publicar y
   luego `MULTI`». Se sigue NFR10.14: un corte entre los dos pasos produce, como mucho, una segunda llamada
   a Whisper dentro del clúster, que la ingesta descarta (BR4.3); al revés, el turno perdería su resultado.
   No sale ningún dato.
3. **Quién libera las esperas.** BR9.2 y NFR10.26 liberan en la transacción que resuelve el turno de voz;
   el `HoldReleaser` de U4 sondea cada 500 ms. Se combinan: la liberación es de la transacción que resuelve
   el turno, con un módulo único; el `HoldReleaser` queda como red de seguridad con el mismo módulo.
4. **Cifra del cuerpo de la subida.** `voice_body_max_bytes` (`audio_max_bytes` + 16 384) entra en C25,
   como `import_body_max_bytes` de U6, porque toda operación con tope declara su nombre de C25.
5. **Transiciones de la sesión.** Pausar, terminar y retirar cancelan las esperas y, con la retirada, cierran
   los turnos de voz, dentro de la función de cancelación de InterviewSession que ya usan U4 y U6; así no
   aparece una arista voice → session-lifecycle.

Ningún punto cambia el alcance ni deja salir del clúster algo que hoy no sale.

Sin preguntas: todo lo fijan las fuentes.