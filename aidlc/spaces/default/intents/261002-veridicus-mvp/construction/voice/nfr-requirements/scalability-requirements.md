# Requisitos de escalado — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03. Los IDs se conservan; lo nuevo
es NFR8.12. Cada fila dice si **se mantiene**, **cambia** o es **nuevo**.

**Insumos.**
- Flujos F1–F8 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR1.3, BR2.4, BR3.5, BR3.6, BR8.2 y BR9.1 de `functional-design/rules.md` (rules).
- NFR2, NFR3, NFR8 y los supuestos de `inception/requirements-analysis/requirements.md` (requirements,
  revisión 3).
- C2, C5 y C25 de `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- P1 = A y P2 = A de `nfr-requirements-questions.md`.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 en uso real y en la sustentación; 3 sesiones concurrentes como prueba de capacidad | Supuestos de requirements; NFR8 |
| Duración de una grabación | ≤ `audio_max_seconds` (120 s); típica 10–30 s | BR1.3 |
| Tamaño de un mensaje de audio | ≤ `audio_base64_max_chars` (8 000 000) en base64, para un archivo de ≤ `audio_max_bytes` (6 000 000). 120 s de WAV ocupan 3,84 MB (5,1 MB en base64) | P1 = A |
| Ritmo de llegada | Un analista no puede grabar más rápido que el tiempo real: como mucho 30 s de audio cada 30 s | BR1.3 |
| Ritmo de servicio | p95 de 12 s por 30 s de audio (NFR3.1): el trabajador procesa unas 2,5 veces más rápido que el tiempo real | P2 = A |
| Audio conservado | Solo con `autoriza_conservar_audio`; 3,84 MB por grabación de 120 s, unos 0,96 MB por una de 30 s | BR8.2 |

Con un analista, la cola de audio no crece: cada grabación termina de transcribirse antes de que la
siguiente esté lista.

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.5 | cambia | Un audio a la vez. | Una réplica de `audio-worker` toma un mensaje de C5 a la vez, y una réplica de `model-whisper` atiende una transcripción a la vez; Redis absorbe la concurrencia. La síntesis de aclaraciones corre en un hilo aparte de `audio-worker` con concurrencia 1. Una segunda petición espera dentro de su *timeout*; si no le alcanza, recibe `503` `speech.unavailable`. |
| NFR8.6 | cambia | Una sesión de voz larga no vence plazos. | En la corrida de voz, una sesión con 15 turnos de voz de 30 s, enviados al ritmo de una grabación real, termina con 0 `analysis.timeout`, y `veridicus_audio_queue_depth` nunca pasa de 2. Con 3 sesiones así a la vez (capacidad, no uso real), también hay 0 `analysis.timeout`, gracias al plazo proporcional (NFR3.5). |
| NFR8.7 | se mantiene | Redis no acumula audio. | En uso normal, `veridicus:audio` tiene ≤ 2 mensajes (≤ 16 MB). Tras procesar, `XLEN` de `veridicus:audio` y de `veridicus:transcripts` es 0 (NFR10.3). En la prueba de capacidad de nivel 1 se encolan 10 mensajes de 8 000 000 caracteres: Redis los acepta y los procesa todos sin `OOM command not allowed`. El `maxmemory` concreto lo fija Infrastructure Design, con ≥ 128 MB para los *streams*. |
| NFR8.8 | cambia | La voz no rompe la meta del analizador. | En una corrida de voz mixta, con turnos escritos y de voz alternados en la misma sesión, el tramo incremental sigue en p95 ≤ 180 s (meta de U11) mientras Whisper transcribe. Si no, es un hallazgo sobre los `limits.cpu` de `model-whisper` que se corrige por PR. El efecto inverso, sobre la transcripción, es NFR3.15. |
| NFR8.9 | cambia | U9 no impide más réplicas en el futuro. | `audio-worker` no guarda estado en memoria entre mensajes. La deduplicación de BR3.6 se apoya en la clave `veridicus:transcribed:{turn_id}:{attempt}`, con TTL `voice_key_ttl_s` (1 920 s, mayor que `voice_deadline_max_s`), y la cancelación en la clave de NFR10.25. La ingesta es idempotente por (`turn_id`, `attempt`) (BR4.3), y `attempt` es siempre 1. Prueba de nivel 1 con dos consumidores en el grupo `audio-worker` y el mismo mensaje entregado dos veces: 1 llamada al Whisper *fake* y 1 texto guardado. El MVP corre 1 réplica. |
| NFR8.12 | nuevo | El audio conservado no llena el volumen sin aviso (BR8.2, BR8.6). | `audio_store_max_bytes` (2 147 483 648) es la cuota del directorio de audio, medida por el propio proceso, como la cuota de reportes de U7 en Minikube. Equivale a unas 550 grabaciones de 120 s o a unas 2 200 de 30 s dentro de la retención de 90 días (VE-12). Una escritura que pasaría la cuota da `503` `analysis.system`, sin turno; el turno escrito sigue disponible. `veridicus_audio_store_bytes` se publica en `/metrics`, con una regla informativa al 80 %. Prueba de nivel 1 con una cuota reducida por variable de entorno. |

## 3. Señal para escalar

No hay autoescalado en el MVP. Las señales son tres:
- `veridicus_audio_queue_depth` pasa de 3 de forma sostenida;
- NFR3.1 o NFR3.15 no se cumplen en CPU;
- el audio conservado pasa del 80 % de su cuota.

Las opciones, en este orden, son:
1. Ajustar `cpu_threads` de Whisper.
2. Usar el perfil GPU para la demostración.
3. Añadir una segunda réplica de `audio-worker` y `model-whisper`, que NFR8.9 permite.

Para la cuota, se sube `audio_store_max_bytes` junto con el PVC, por PR, o se acorta la retención con la
decisión de U13. Cada cambio entra por PR con su medición. La carga de NFR8 de requirements (50 sesiones
de texto) no incluye voz: la voz es SHOULD y su capacidad se mide con NFR8.6.
