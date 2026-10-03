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