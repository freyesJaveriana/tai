# Diseño de escalado — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03. Las secciones conservan número y
tema; lo nuevo es §6 (cuota del audio conservado). Cambian: plazo base de 360 s, clave de entrega doble con
TTL `voice_key_ttl_s` (1 920 s), recorte por `MINID` y la meta de convivencia con el juez, que pasa al tramo
incremental de U11 (p95 ≤ 180 s).

**Insumos.** `nfr-requirements/scalability-requirements.md` (scalability-requirements, NFR8.5–NFR8.9 y
NFR8.12), `performance-requirements.md` (performance-requirements), `security-requirements.md`
(security-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; F1–F3 y F6 de `functional-design/functional-spec.md` (functional-spec)
y BR3.6, BR4.3 y BR8.2 de `functional-design/rules.md`; C2, C5 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); NFR Design de U2 (Redis) y U4 (colas).

## 1. Modelo de capacidad (NFR8.5, NFR8.6)

Un analista no graba más rápido que el tiempo real y el servicio es ≈ 2,5 veces más rápido (p95 de 12 s por
30 s): la cola de audio no crece. El cuello de botella del turno completo es el juez de U11.

| Elemento | Réplicas en el MVP | Concurrencia | Cómo escala |
|---|---|---|---|
| `audio-worker` (bucle de C5) | 1 | 1 audio (`XREADGROUP COUNT 1`, procesamiento síncrono) | Más consumidores en el grupo `audio-worker` (§2) |
| `audio-worker` (síntesis) | El mismo pod | 1: `threading.Semaphore(1)`; la segunda espera ≤ 2 s y luego `503` (NFRD-U9-13) | Igual que arriba |
| `model-whisper` | 1 | 1 transcripción | Una réplica por cada `audio-worker` |
| `model-tts` | 1 | 1 síntesis | Rara vez necesario |
| Ingesta de C5 | Trabajador de `session-api` | 1 hilo junto a los de U4 | Más réplicas del trabajador |

**Plazo proporcional.** `voice_deadline_at` crece con los turnos de voz en `transcribing` de todo el sistema
(`performance-design.md` §3). Verificación en la corrida de voz: 1 sesión de 15 turnos de 30 s al ritmo real →
0 `analysis.timeout` y `veridicus_audio_queue_depth` ≤ 2; 3 sesiones así a la vez → 0 `analysis.timeout`.

## 2. Colas e idempotencia (NFR8.9)

| *Stream* | Grupo | Consumidores | Idempotencia |
|---|---|---|---|
| `veridicus:audio` (C5) | `audio-worker` | 1 por pod | Clave `veridicus:transcribed:{turn_id}:{attempt}` con TTL `voice_key_ttl_s`, fijada en el `MULTI` de cierre; con la clave, el mensaje se confirma y se borra sin llamar a Whisper |
| `veridicus:transcripts` (C5) | `session-api-transcripts` | 1 hilo por trabajador | La ingesta solo escribe si `voice_status` sigue en `transcribing` para ese `attempt` (`UPDATE … WHERE … RETURNING`); un duplicado o tardío se confirma sin efectos |

`audio-worker` no guarda estado entre mensajes: el `AofRewriteRequester` solo guarda una marca y una hora,
que se rehacen al arrancar, y el latido de `reliability-design.md` §4 es local. `attempt` es siempre 1.
Verificación de nivel 1: dos consumidores en el grupo y el mismo mensaje entregado dos veces → 1 llamada al
Whisper *fake* y 1 texto guardado. El MVP corre 1 réplica.

## 3. Memoria de Redis (NFR8.7)

- En uso normal ≤ 2 mensajes de audio (≤ 16 MB); tras procesar, `XLEN` de los dos *streams* es 0.
- `maxmemory` con ≥ 128 MB para los *streams* y `maxmemory-policy noeviction` los fija U2; Redis rechaza en
  lugar de expulsar claves del limitador de U3 o de las colas.
- Un `XADD` rechazado por memoria: como la fila se confirma antes del `XADD`, el turno pasa a `error` con
  `analysis.system` y, con autorización, el archivo queda para la retención (`reliability-design.md` §13).
- **Cota de memoria sin consumidor.** El recorte por `MINID` del supervisor (`security-design.md` §2) impide
  que los mensajes de audio sigan en memoria más de `voice_key_ttl_s` + 15 s aunque `audio-worker` no exista.
- El AOF crece con cada audio y lo reducen el `AofRewriteRequester` y la reescritura automática; U2 dimensiona
  el PVC con el doble del AOF máximo.
- Verificación de nivel 1 de capacidad: 10 mensajes de 8 000 000 caracteres encolados se aceptan y se procesan
  todos sin `OOM command not allowed`, y al final `XLEN` = 0.

## 4. Convivencia con el juez (NFR8.8, NFR3.15)

Whisper (`cpu_threads = 4`) y el juez de U11 comparten la CPU. Infrastructure Design los separa por
`requests` y `limits.cpu`, con `model-whisper` limitado a 4 núcleos. Verificación en la corrida de voz mixta
(turnos escritos y de voz alternados en la misma sesión): el tramo incremental sigue en p95 ≤ 180 s mientras
Whisper transcribe (NFR8.8), y la transcripción sigue en p95 ≤ 12 s con un tramo en curso (NFR3.15). Si no, es
un hallazgo sobre `limits.cpu` o `cpu_threads` que se corrige por PR, nunca subiendo la meta.

## 5. Señales para escalar

| Señal | Umbral | Acción, en este orden, por PR con medición |
|---|---|---|
| `veridicus_audio_queue_depth` | > 3 durante 10 minutos | Ajustar `cpu_threads`; perfil GPU para la demostración; segunda pareja `audio-worker` + `model-whisper` (§2 lo permite) |
| p95 de `veridicus_transcription_seconds` en clips ≤ 30 s | > 12 s en la corrida de voz (sola o mixta) | Igual que arriba |
| Pico de memoria de un pod | Sobre su tope de `performance-design.md` §7 | Corregir por PR |
| Llenado del audio conservado | > 80 % de `audio_store_max_bytes` | §6 |

No hay autoescalado en el MVP. La carga de NFR8 de requirements (50 sesiones de texto) no incluye voz.

## 6. Cuota del audio conservado (NFR8.12) · nuevo

- `audio_store_max_bytes` (2 147 483 648) es la cuota del directorio de audio, medida por el propio proceso
  con un contador (`security-design.md` §12), no con `kubelet_volume_stats`, que Minikube no publica.
- Equivale a ≈ 550 grabaciones de 120 s o ≈ 2 200 de 30 s dentro de la retención de 90 días. El PVC de U2 es de
  ≥ 1,2 × la cuota (NFRD-U2-15).
- Una escritura que la pasaría da `503` `analysis.system` sin turno; el turno escrito sigue disponible.
- `veridicus_audio_store_bytes` en `/metrics` y una regla informativa al 80 %.
- Prueba de nivel 1 con la cuota bajada por `VERIDICUS_LIMIT_AUDIO_STORE_MAX_BYTES` (el entorno solo baja).
- Para crecer: subir la cuota junto con el PVC, por PR, o acortar la retención con la decisión de U13.
