# Preguntas — Diseño de contratos (Veridicus)

Esta etapa fija los **contratos** entre unidades y hacia afuera del sistema: qué datos cruzan cada
frontera, con qué forma, por qué mecanismo y qué pasa cuando algo falla. Sale un solo documento,
`contract-summary.md`, con un bloque de especificación por contrato (OpenAPI, AsyncAPI o esquema
compartido).

Ya están decididos y no se vuelven a preguntar:

- La consola solo habla con ConsoleApi por REST, y ConsoleApi es la única superficie expuesta al
  navegador (ADR-004). Los errores son Problem Details (RFC 9457) con `code` estable y `detail` en
  español (NFR10).
- El turno va a SemanticEvaluation por una cola Redis y el resultado vuelve por una cola de
  resultados que InterviewSession consume de forma idempotente por turno e intento (ADR-002). El
  mensaje de turno lleva la instantánea del umbral y de la versión del escenario (ADR-006).
- Toda llamada a un modelo pasa por el puerto ModelGateway, con destino interno verificado al
  arrancar (ADR-005).
- Los contratos viven en la unidad `contracts` (U1, tipo `spec`), y cada cambio entra por su propio
  PR (Units Generation, P3). Los esquemas de la salida del juez y de la alerta usan
  `additionalProperties: false`, sin campos de veracidad (AC5.5.3).
- Los valores numéricos (plazo de evaluación, *T* del latido, umbral) los fija NFR Requirements; aquí
  solo se nombran como parámetros.

## Cómo responder

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es mi propuesta; no está aplicada todavía.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

### Pregunta 1 — ¿Qué estructura de Redis usan las colas?

Las colas de turnos, resultados, indexación, audio y transcripción necesitan entrega al menos una vez:
si un trabajador muere a mitad de un turno, el turno no se puede perder (AC2.2.4).

A. **Redis Streams con grupos de consumidores**: cada mensaje se confirma (`XACK`) solo después de
procesarlo; los pendientes de un trabajador caído se reclaman tras un plazo (`XAUTOCLAIM`), y lo que
agota sus intentos pasa a un *stream* de mensajes fallidos por cola **(Recomendada)**
B. Listas de Redis con movimiento atómico a una lista de «en proceso» (`BLMOVE`) y un barrido propio de
huérfanos.
C. Pub/Sub de Redis (más simple, pero un mensaje se pierde si no hay consumidor conectado).
X. Other (please specify)

[Answer]: A

### Pregunta 2 — ¿Cómo se versionan los contratos y cómo entra un cambio incompatible?

El monorepo despliega productor y consumidor desde el mismo commit, pero un mensaje puede quedar en la
cola durante un despliegue.

A. **Versión semántica por contrato y campo `schema_version` en cada mensaje.** Un cambio aditivo sube
la versión menor y los consumidores ignoran los campos que no conocen. Un cambio incompatible sube la
versión mayor y entra en **un solo PR** que actualiza productor y consumidores; un consumidor que recibe
una versión mayor que no conoce manda el mensaje a fallidos sin crear filas. Los esquemas del juez y de
la alerta siguen siendo estrictos (`additionalProperties: false`) **(Recomendada)**
B. Igual que A, pero con convivencia: durante un cambio mayor el productor publica las dos versiones y
el consumidor acepta ambas hasta un PR posterior que retira la vieja.
C. Sin versión explícita: el contrato es el que está en `main`.
X. Other (please specify)

[Answer]: A

### Pregunta 3 — ¿Qué pasa cuando una evaluación falla o tarda demasiado?

AC10.1.2 pide que un turno que supera el plazo pase a «Error» con opción de reintentar y nunca quede
«Procesando» para siempre. AC3.2.3 pide que el reintento conserve el número del turno.

A. **InterviewSession vigila el plazo de cada turno** (valor de NFR Requirements): al vencer, el turno
pasa a «Error» con `turn.error.timeout`. La reentrega automática de la cola (hasta 3 intentos) solo
cubre fallos recuperables, como un trabajador que murió. Una salida inválida del juez **no** se reintenta
sola (con temperatura 0 daría lo mismo): el turno pasa a «Error» y el analista decide «Reintentar
evaluación», que publica el mismo turno con `attempt + 1`. Un resultado que llega de un intento viejo se
descarta por (`turn_id`, `attempt`) **(Recomendada)**
B. Reintento automático de todo error, incluida la salida inválida, hasta 3 veces antes de «Error».
C. Sin reintentos automáticos: todo fallo pasa a «Error» de inmediato.
X. Other (please specify)

[Answer]: A

### Pregunta 4 — ¿Cómo se formalizan las fronteras que no cruzan la red?

Dentro de `session-api` viven InterviewSession, HumanReview, ForensicReport, TruthFrame e
IdentityAccess (Units Generation, P2), y ModelGateway e IntegrityPolicy son bibliotecas en `libs/`. Sus
llamadas son en proceso, pero varias cruzan de una unidad a otra (por ejemplo, U4 entrega sugerencias
que U5 decide y U7 consolida).

A. **Interfaces Python tipadas** (`Protocol` con modelos de datos) descritas aquí en un bloque de
esquema compartido por frontera, verificadas con mypy estricto y con import-linter para que cada módulo
solo use la interfaz pública del otro **(Recomendada)**
B. No se formalizan aquí: cada unidad las define en su Functional Design.
C. Se exponen como API REST internas entre módulos.
X. Other (please specify)

[Answer]: A

### Pregunta 5 — ¿Cómo se autentica la consola ante ConsoleApi?

Un usuario desactivado debe recibir `401` aunque su sesión siga vigente (AC8.2.3), y toda ruta salvo
inicio de sesión y salud exige autenticación (AC8.1.4).

A. **Sesión del servidor con cookie** `HttpOnly`, `Secure` y `SameSite=Strict`, revocable al
desactivar al usuario, más una cabecera anti-CSRF en toda petición que cambia estado **(Recomendada)**
B. Token JWT firmado en la cabecera `Authorization: Bearer`, guardado en memoria del navegador, con una
lista de revocación para usuarios desactivados.
C. Token opaco en `Authorization: Bearer`, verificado contra la base en cada petición.
X. Other (please specify)

[Answer]: A

### Pregunta 6 — ¿Cómo se entera la consola de que un turno cambió de estado?

Refined Mockups dejó el mecanismo abierto (sondeo frente a eventos del servidor) y pidió que el mismo
canal sirva de latido para la suspensión (AC7.1.1).

A. **Sondeo**: `GET` del estado de la sesión cada pocos segundos mientras haya turnos «En cola» o
«Procesando», con un cursor de cambios para traer solo lo nuevo; cada consulta cuenta como latido, y sin
turnos en proceso la consola manda solo el latido **(Recomendada)**
B. Eventos del servidor (*Server-Sent Events*) con un flujo por sesión, y el latido como petición
aparte.
X. Other (please specify)

[Answer]: A

### Pregunta 7 — ¿Qué protocolo usa ModelGateway para hablar con los servidores de modelos?

El PRD menciona Ollama o llama.cpp para el juez, *embeddings* locales y Whisper; el anonimizador (COULD)
se pondría delante como otro adaptador.

A. **API compatible con OpenAI dentro del clúster** donde el servidor la ofrezca (`/v1/chat/completions`
para el juez, `/v1/embeddings` y `/v1/audio/transcriptions`), con un adaptador propio para el TTS. Un
solo formato de petición facilita los *fakes* de prueba y que el anonimizador tenga la misma forma
**(Recomendada)**
B. La API nativa de cada servidor (por ejemplo la de Ollama) con un adaptador distinto por modelo.
C. gRPC propio delante de cada modelo.
X. Other (please specify)

[Answer]: A

---

## Segunda pasada — cambio 01 (DT27) y adenda 02 (2026-11-09)

Las respuestas 1 a 7 de la primera pasada siguen vigentes. La 3 ahora se aplica a la **corrida** y no
al turno, y la 7 solo al servidor local, porque los proveedores comerciales tienen su propia API
(FR15.1). Tampoco se vuelve a preguntar lo que ya fijan los artefactos aprobados:

- Entrada y salida del contrato común (propuesta v0.1 del cambio 01 §4) con el bloque `consentimiento`
  (A-4), que se copia versionado a `contracts/` (ADR-017). `origen: sintetico` queda exento del bloque.
- El mensaje de corrida lleva la transcripción hasta `hasta_turno`, la configuración efectiva del perfil y
  el consentimiento. El trabajador no tiene base de datos (ADR-006), y el resultado vuelve por la cola de
  resultados (ADR-002).
- El anonimizador seudonimiza, envía al proveedor de la lista y restaura (ADR-011). Es el único pod con
  salida a internet, y la lista de dominios la impone él mismo (P10 = A).
- Salen C4 (indexación) y C9 (pasajes). C15 pasa a ser la métrica de descartes (P13 = A, US10.8).
- Toda cifra de límite vive en `contracts/limits.v1.yaml` (regla de `project.md`).

### Pregunta 8 — ¿Cómo se nombran los códigos de error del contrato común?

La propuesta v0.1 usa códigos en español (`salida_invalida`, `bloqueo_contenido`, `tiempo_agotado`,
`proveedor`), pero los artefactos aprobados ya escriben `codigo: anonymizer.incident` para el incidente de
anonimización (components, R-04). Además, el fallo cerrado del anonimizador necesita su propio código, que
FR4.2 propone como `anonimizador` y Units Generation como `anonymizer.unavailable` (UG-02). El contrato lo
comparten Veridicus y el TG, y la consola traduce esos códigos al catálogo de Problem Details.

A. **Español y `snake_case` en el contrato común**, como la propuesta del TG: `salida_invalida`,
`bloqueo_contenido`, `tiempo_agotado`, `proveedor`, `anonimizador_no_disponible` (fallo cerrado: no salió
ninguna llamada) e `incidente_anonimizacion` (una respuesta llegó con `anonimizado: false`). El catálogo
de Problem Details de Veridicus sigue en inglés con puntos y los traduce uno a uno
(`analysis.anonymizer_unavailable`, `anonymizer.incident`…). El cambio de nombre de `anonymizer.incident`
dentro del contrato queda en la tabla de precisiones **(Recomendada)**
B. Inglés con puntos en todas partes, también en el contrato común (`analysis.invalid_output`,
`anonymizer.incident`…). Hay que proponérselo al TG como cambio a su v0.1.
C. Mezcla: se conservan los cuatro de la v0.1 y los dos nuevos se escriben en inglés con puntos.
X. Other (please specify)

[Answer]:

### Pregunta 9 — ¿Dónde viajan el ID de corrida y la versión del mensaje en las colas?

InterviewSession consume los resultados de forma idempotente por ID de corrida (ADR-002), y cada mensaje
lleva `schema_version` (respuesta 2). La salida del contrato común no tiene `run_id`, y el TG no lo
necesita.

A. **Sobre propio de Veridicus** alrededor del contrato: el mensaje de corrida es
`{schema_version, run_id, attempt, session_id, effective_config, entrada}` y el de resultado
`{schema_version, run_id, attempt, salida}`, donde `entrada` y `salida` son exactamente el contrato
común. Así el contrato queda igual al del TG y la CLI escribe la misma `salida` en sus archivos
**(Recomendada)**
B. Se añaden `run_id` e `intento` como campos opcionales del contrato común.
X. Other (please specify)

[Answer]:

### Pregunta 10 — ¿Dónde queda el registro de la corrida (llamadas, descartes, modo fragmentado, tokens y costo)?

FR15.3 pide registrar cada llamada (papel, proveedor, modelo, versión, esfuerzo o cuantización, motor,
semilla, tokens, fecha, proveedor alterno y `anonimizado`). FR4.5 pide guardar cada candidato descartado
con su motivo, FR4.8 declarar el modo fragmentado con su ventana y FR15.4 sumar tokens y costo. La v0.1
solo trae un campo `modelo`. Lo necesitan la consola (registro de modelos de la corrida), el reporte
consolidado y la CLI (reporte y US12.5).

A. **Dentro de la salida del contrato común**, en un bloque `registro` con `llamadas[]`, `descartes[]`
(motivo y turnos, sin texto de citas), `fragmentado {activo, ventana, solapamiento}`, `tokens_entrada`,
`tokens_salida` y `costo_estimado`. Reemplaza al campo `modelo` de la v0.1, y el TG recibe lo mismo
**(Recomendada)**
B. En el sobre de Veridicus (pregunta 9): el contrato común solo lleva `modelo`, y la CLI escribe el
registro en un archivo aparte.
X. Other (please specify)

[Answer]:

### Pregunta 11 — ¿Qué lleva el bloque `consentimiento` de la entrada?

A-4 fija lo mínimo: si lo dio la persona o una autoridad que lo exime, la versión del texto, y si
autoriza la transferencia a un proveedor comercial y grabar la voz. Components añade la conservación del
audio (VE-08) y la constancia de la autoridad. El bloque viaja con la transcripción por la cola y por los
archivos de la CLI, pero nunca a un proveedor externo.

A. **Mínimo y sin datos personales**: `tipo` (`persona` | `autoridad`), `version_texto`,
`autoriza_transferencia`, `autoriza_voz`, `autoriza_conservar_audio`, `constancia` (solo un identificador
de la constancia, nunca un nombre) y `registrado_en`. La retirada del consentimiento **no** va en el
contrato: la registra InterviewSession, que deja de encolar corridas (VE-10 (a)), y la CLI no la necesita
**(Recomendada)**
B. Como A, más un campo `retirado_en`, para que la biblioteca rechace por sí misma una corrida que llega
después de la retirada.
X. Other (please specify)

[Answer]:

### Pregunta 12 — ¿El reporte JSON de la CLI puede traer texto?

FR13.5 y NFR12 piden que la consola del investigador guarde solo metadatos y cifras. Pero components dice
que ResearchReports «descarta» el texto antes de guardar, y U12 dice que «rechaza» un reporte que traiga
texto. Hay que elegir una de las dos.

A. **El esquema del reporte no tiene ningún campo de texto libre** (`additionalProperties: false`): las
salidas por entrevista, con los hallazgos y las citas, van en archivos aparte y nunca dentro del reporte.
La consola **rechaza** con `422` un reporte que no cumple el esquema o que trae una cadena fuera de los
campos permitidos, sin guardar nada. La prueba del *canary* de FR13.5 queda igual **(Recomendada)**
B. El reporte puede incluir los hallazgos, y la consola quita el texto antes de guardar las cifras.
X. Other (please specify)

[Answer]:

### Pregunta 13 — ¿Qué recibe `anonymizer-proxy` por la red y dónde viven las claves de API?

En el clúster, la biblioteca corre en `semantic-agent`, sin salida a internet. La llamada a un proveedor
comercial tiene que salir desde `anonymizer-proxy`, que seudonimiza, llama y restaura (ADR-011). En la
CLI, el mismo módulo corre en el mismo proceso.

A. **El proxy expone la misma operación del puerto** por HTTP dentro del clúster:
`POST /v1/generate` con `{papel, proveedor, modelo, parametros, mensajes, esquema}`. Seudonimiza los
mensajes en su forma común, llama con el adaptador nativo del proveedor, restaura y responde con la
salida y el registro de la llamada (`anonimizado: true`). Los adaptadores nativos y las claves de API
viven **solo** en el proxy (el `Secret` se monta solo en ese pod). `semantic-agent` solo tiene el
adaptador local y el cliente del proxy **(Recomendada)**
B. Proxy transparente: los adaptadores nativos viven en `semantic-agent` y el proxy reenvía la petición
HTTP de cada proveedor, buscando el texto en el formato de cada API para seudonimizarlo. Las claves se
montan en `semantic-agent`.
X. Other (please specify)

[Answer]:

### Pregunta 14 — ¿En qué idioma van los nombres de campo?

El contrato común del TG nombra sus campos en español (`hallazgos`, `cita_a`, `observaciones`), y
AUTONOMIA-05 los cita así. `team.md` pide identificadores en inglés con un glosario único, y que
«ningún término se traduzca de dos formas».

A. **Los campos del contrato común conservan su nombre en español** en JSON y en los modelos de Python,
sin alias, y el glosario los registra como excepción. Todo lo que es propio de Veridicus (sobres de cola,
OpenAPI de la consola, perfiles, catálogo de límites, reporte de la CLI) va en inglés **(Recomendada)**
B. Modelos de Python en inglés con alias al español solo en la serialización JSON.
C. Todo en español, también lo propio de Veridicus.
X. Other (please specify)

[Answer]:
