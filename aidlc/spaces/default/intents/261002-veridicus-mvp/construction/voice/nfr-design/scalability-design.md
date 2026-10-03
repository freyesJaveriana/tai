# Diseño de escalado — U9 voice

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; flujos F1–F3 de `functional-design/functional-spec.md`
(functional-spec); C2 y C5 de `inception/contract-design/contract-summary.md` (contract-summary);
respuestas P1 = A y P2 = A de `nfr-design-questions.md`; diseño de escalado de U4.

## 1. Modelo de capacidad (NFR8.5, NFR8.6)

Con un analista que no graba más rápido que el tiempo real y un servicio ≈ 2,5 veces más rápido que el
tiempo real (p95 de 12 s por 30 s), la cola de audio no crece. El cuello de botella del turno completo
sigue siendo el juez de U4.

| Elemento | Réplicas en el MVP | Concurrencia | Cómo escala si hace falta |
|---|---|---|---|
| `audio-worker` (bucle de C5) | 1 | 1 audio (`XREADGROUP COUNT 1`, procesamiento síncrono) | Más réplicas en el grupo `audio-worker` (§2) |
| `audio-worker` (síntesis) | El mismo pod | 1 petición: un `threading.Semaphore(1)`; la segunda espera dentro de su *timeout* de 12 s | Igual que arriba |
| `model-whisper` | 1 | 1 transcripción | Una réplica más por cada `audio-worker` |
| `model-tts` | 1 | 1 síntesis | Rara vez necesario |
| Ingesta de C5 | Trabajador de `session-api` | 1 hilo nuevo junto a los de U4 | Más réplicas del trabajador |

**Plazo proporcional.** El plazo de cada audio crece con los turnos de voz en `transcribing` de todo el
sistema (performance-design §3), así que 3 sesiones de 15 turnos de 30 s a la vez no vencen plazos aunque
esperen. Verificación: corrida de voz con 1 sesión (0 `turn.error.timeout`, `veridicus_audio_queue_depth`
≤ 2) y con 3 sesiones a la vez (0 `turn.error.timeout`).

## 2. Colas e idempotencia (NFR8.9)

| *Stream* | Grupo | Consumidores | Idempotencia |
|---|---|---|---|
| `veridicus:audio` (C5) | `audio-worker` | 1 por pod | Clave `veridicus:transcribed:<turn_id>:<attempt>` con TTL de 1 800 s fijada en el mismo `MULTI` que `XACK` + `XDEL`; un mensaje cuya clave existe se confirma y se borra sin llamar a Whisper |
| `veridicus:transcripts` (C5) | `session-api-transcripts` | 1 hilo por trabajador | La ingesta solo escribe si el turno sigue en `transcribing` para ese `attempt` (`UPDATE … WHERE … RETURNING`); un duplicado se confirma sin efectos |

`audio-worker` no guarda estado entre mensajes (el `AofRewriteRequester` solo guarda una marca y una
hora, que se rehacen al arrancar). Verificación de nivel 1: dos consumidores en el grupo y el mismo
mensaje entregado dos veces → 1 llamada al Whisper *fake* y 1 texto guardado. El MVP corre 1 réplica.

## 3. Memoria de Redis (NFR8.7)

- En uso normal hay ≤ 2 mensajes de audio (≤ 16 MB); tras procesar, `XLEN` de ambos *streams* es 0.
- Infrastructure Design fija `maxmemory` con ≥ 128 MB reservados para los *streams* (10 mensajes de
  8 MB más los de U4) y `maxmemory-policy noeviction`, para que Redis rechace en lugar de expulsar
  claves del limitador de U3 o de las colas.
- Un `XADD` rechazado por memoria hace que la ruta responda `503` `system.unavailable`; como en U4 la
  fila se confirma antes del `XADD`, el turno ya numerado pasa a `error` con `turn.error.system` y nunca
  queda en curso.
- El AOF crece con cada audio y lo reduce la reescritura que pide `audio-worker` (security-design §2); la
  reescritura necesita en disco el doble del AOF vigente, que Infrastructure Design tiene en cuenta al
  dimensionar el PVC.
- Verificación de nivel 1 de capacidad: 10 mensajes de 8 MB encolados se aceptan y se procesan todos sin
  `OOM command not allowed`, y al final `XLEN` = 0.

## 4. Convivencia con el juez (NFR8.8)

Whisper (`cpu_threads = 4`) y el juez de U4 comparten la CPU de la máquina de desarrollo. El diseño los
separa por `requests`/`limits.cpu` en Infrastructure Design, con `model-whisper` limitado a 4 núcleos.
Verificación: corrida de voz mixta (turnos escritos y de voz alternados en la misma sesión) con los
turnos escritos en p95 ≤ 60 s; si no se cumple, es un hallazgo sobre `limits.cpu` de `model-whisper`
que se corrige por PR, nunca subiendo la meta.

## 5. Señales para escalar

| Señal | Umbral | Acción, en este orden, por PR con medición |
|---|---|---|
| `veridicus_audio_queue_depth` | > 3 durante 10 minutos | Ajustar `cpu_threads` de Whisper; perfil GPU para la demostración; segunda pareja `audio-worker` + `model-whisper` |
| p95 de `veridicus_transcription_seconds{audio_length="le30"}` | > 12 s en la corrida de voz | Igual que arriba; nunca subir la meta |
| Pico de memoria de un pod | Sobre su tope de performance-design §7 | Corregir por PR |

No hay autoescalado en el MVP.
