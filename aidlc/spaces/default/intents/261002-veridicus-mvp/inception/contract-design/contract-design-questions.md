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
