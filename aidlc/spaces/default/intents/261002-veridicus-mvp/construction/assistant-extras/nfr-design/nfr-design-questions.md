# Preguntas de NFR Design — U8 assistant-extras

**Unidad.** U8 `assistant-extras` (extras del asistente, apagados por defecto): permutación del orden
de lectura (segunda lectura del juez solo para las afirmaciones candidatas a alerta), pregunta sugerida
que el analista aprueba o descarta, e indicio afectivo con una lista versionada de palabras sin LLM.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D10 de
`nfr-requirements/`: el mismo juez de U4 con una sola ranura para la segunda lectura y la pregunta,
p95 ≤ 150 s por turno con los tres extras activos (humo y carga de NFR8 con los extras apagados), una
sola llamada para todas las candidatas, la CoT visible es la de la primera lectura, salida de la
pregunta con solo `text` (1–300 caracteres) y esquema estricto, *timeout* de la pregunta 60 s, plazo
base 600 s y reclamo de pendientes 480 s cuando hay extras activos, banderas solo en los *values* del
despliegue copiadas a cada sesión, decisión del analista con actualización condicional y disparador,
módulos guardia puros en `domain/` con 100 % de ramas. De U4 ya está diseñado el reintento acotado del
juez ante fallos pasajeros (P1 = A de su NFR Design). Quedan dos huecos de diseño en cómo se cruzan los
extras con ese reintento y con el plazo del turno.

---

## P1 — Si el reintento acotado del juez de U4 cubre también las llamadas de los extras

El NFR Design de U4 añadió, solo para la primera lectura, hasta 2 reintentos dentro del mismo
procesamiento (esperas de 2 s y 6 s con variación aleatoria) ante conexión rechazada o `502`, `503` y
`504`, y solo si el plazo del turno lo permite. Los requisitos aprobados de U8 dicen lo contrario para
sus llamadas: si la segunda lectura encuentra el juez caído, no se confirma el mensaje y el turno entero
vuelve por `XAUTOCLAIM` (reclamo de mensajes pendientes de Redis) a los 480 s, repitiendo también la
primera lectura (NFR10.12); y la pregunta sugerida se omite sin reintento (NFR10.13). Un reinicio breve
del juez justo entre las dos lecturas le suma así 8 minutos al turno, y el reintento vive en una pieza
común (`ModelGateway`, `libs/model_gateway`), así que hay que decidir a qué llamadas se aplica.

A. El mismo reintento acotado de U4 se aplica a la segunda lectura, con la misma comprobación del
   plazo; la pregunta sugerida sigue sin reintento: ante un fallo pasajero se omite con motivo
   `unavailable` y el turno se publica con sus alertas y su paquete. El reintento se activa por llamada,
   no para todo el `ModelGateway`. (Recomendada)
B. Una sola política para todas las llamadas al juez: el reintento acotado cubre la primera lectura,
   la segunda y la pregunta, siempre que el plazo lo permita.
C. Se mantiene lo aprobado: ningún reintento en las llamadas de U8; la segunda lectura cae al reclamo
   de 480 s y la pregunta se omite.
X. Other (please specify)

[Answer]: A **Mode:** guided
## P2 — Qué hace el evaluador si al turno no le queda plazo para la pregunta sugerida

La pregunta es la última llamada del turno y es opcional, pero el plazo (`deadline_at`) es del turno
entero: si vence mientras `semantic-agent` espera la pregunta, el barrido de plazos de U4 (cada 15 s)
marca el turno `turn.error.timeout` y se pierden también las alertas y el paquete ya válidos. Pasa sobre
todo tras un reclamo de pendientes (a los 480 s solo quedan 120 s de los 600 s del plazo base de un turno
sin cola) o cuando los reintentos ya consumieron tiempo.

A. Antes de pedir la pregunta, el evaluador comprueba que `ahora + 60 s` (su *timeout*) `+ 15 s` (un
   ciclo del barrido) `< deadline_at`; si no alcanza, no llama al juez y omite la pregunta con motivo
   `timeout`, y el turno se publica sin ella. La segunda lectura no lleva esta comprobación porque no es
   opcional cuando está activa. (Recomendada)
B. Sin comprobación: el plazo base de 600 s ya cubre la suma de 450 s de NFR3.6 (*embeddings* 30 s +
   juez 180 s × 2 + pregunta 60 s) y se acepta perder el turno en el caso raro.
C. El *timeout* de la pregunta se acorta al tiempo que queda (`deadline_at − ahora − 15 s`, con un
   mínimo de 10 s por debajo del cual se omite con motivo `timeout`), en vez de omitirla de entrada.
X. Other (please specify)

[Answer]: A **Mode:** guided