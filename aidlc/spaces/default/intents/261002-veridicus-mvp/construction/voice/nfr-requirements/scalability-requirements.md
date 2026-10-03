# Requisitos de escalado — U9 voice

**Insumos.** Flujos F1–F3 de `functional-design/functional-spec.md` (functional-spec); reglas BR1.3,
BR2.4, BR3.5 y BR3.6 de `functional-design/rules.md` (rules); NFR2, NFR3, NFR8 y los supuestos de
`inception/requirements-analysis/requirements.md` (requirements); C2 y C5 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 (uso real y sustentación) | Supuestos de requirements |
| Duración de una grabación | ≤ 120 s; típica 10–30 s | BR1.3 |
| Tamaño de un mensaje de audio | ≤ 8 MB en base64 (≤ 6 MB de archivo); 120 s de WAV ocupan 3,84 MB (5,1 MB en base64) | P1 = A |
| Ritmo de llegada | Un analista no puede grabar más rápido que el tiempo real: como mucho 30 s de audio cada 30 s | BR1.3 |
| Ritmo de servicio | p95 de 12 s por 30 s de audio (NFR3.1): el trabajador procesa unas 2,5 veces más rápido que el tiempo real | P2 = A |

Con un analista la cola de audio no crece: cada grabación termina de transcribirse antes de que la
siguiente esté lista.

## 2. Requisitos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.5 | Un audio a la vez. | Una réplica de `audio-worker` toma un mensaje de C5 a la vez y una réplica de `model-whisper` atiende una transcripción a la vez; Redis absorbe la concurrencia. La síntesis de preguntas corre en un hilo aparte de `audio-worker` con concurrencia 1 (una petición más espera dentro de su *timeout*). |
| NFR8.6 | Una sesión de voz larga no vence plazos. | Corrida de voz: una sesión con 15 turnos de voz de 30 s enviados a ritmo de grabación real termina con 0 `turn.error.timeout`, y `veridicus_audio_queue_depth` nunca pasa de 2. Con 3 sesiones así a la vez (capacidad, no uso real), 0 `turn.error.timeout` gracias al plazo proporcional (NFR3.5). |
| NFR8.7 | Redis no acumula audio. | En uso normal, `veridicus:audio` tiene ≤ 2 mensajes (≤ 16 MB); tras procesar, `XLEN` de `veridicus:audio` y de `veridicus:transcripts` es 0 (NFR10.3). Con 10 mensajes de 8 MB encolados (prueba de nivel 1 de capacidad), Redis los acepta y los procesa todos sin `OOM command not allowed`; el `maxmemory` concreto lo fija Infrastructure Design con ≥ 128 MB para los *streams*. |
| NFR8.8 | La voz no rompe la meta del juez. | En una corrida de voz mixta (turnos escritos y de voz alternados en la misma sesión), los turnos escritos siguen en p95 ≤ 60 s (NFR3.1 de U4) mientras Whisper transcribe; si no, es un hallazgo sobre los `limits.cpu` de `model-whisper`, que se corrige por PR. |
| NFR8.9 | U9 no impide más réplicas en el futuro. | `audio-worker` no guarda estado en memoria entre mensajes (la deduplicación de BR3.6 se apoya en una clave de Redis `veridicus:transcribed:<turn_id>:<attempt>` con TTL de 1 800 s, no en memoria); la ingesta es idempotente por (`turn_id`, `attempt`) (BR4.3). Prueba de nivel 1 con dos consumidores en el grupo `audio-worker` y el mismo mensaje entregado dos veces: 1 llamada al Whisper *fake* y 1 texto guardado. El MVP corre 1 réplica. |

## 3. Señal para escalar

No hay autoescalado en el MVP. Si `veridicus_audio_queue_depth` pasa de 3 de forma sostenida o NFR3.1
no se cumple en CPU, las opciones, en este orden, son: ajustar `cpu_threads` de Whisper, usar el perfil
GPU para la demostración, o añadir una segunda réplica de `audio-worker` y `model-whisper` (NFR8.9 lo
permite). Cada cambio entra por PR con su medición. La carga de NFR8 de requirements (50 sesiones de
texto) no incluye voz: la voz es SHOULD y su capacidad se mide con NFR8.6.
