# Preguntas de NFR Requirements — U6 session-lifecycle

**Unidad.** U6 `session-lifecycle`: versiones nuevas de escenarios, transcripción pegada, lista de
sesiones, latido, suspensión y reanudación, y progreso del turno (`functional-design/functional-spec.md`,
`rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Regla de división (P1), turnos del entrevistador
como contexto (P2), límites de 100 turnos y 100 000 caracteres (P3), sondeo de la consola cada 2 s con
turnos en curso y cada 15 s sin ellos, y el plazo proporcional a la cola con tope de 3 600 s (U4, P5 y
S1). `contract-summary.md` dejó para esta etapa el *T* del latido.

---

## P1 — Tiempo sin latido para suspender (*T*) e intervalo de revisión

Cada sondeo del dueño cuenta como latido (cada 15 s sin turnos en curso). Los navegadores ralentizan las
pestañas en segundo plano hasta un temporizador por minuto, así que un *T* corto suspendería sesiones
abiertas en otra pestaña.

A. *T* = 180 s y revisión cada 30 s: una sesión se suspende entre 180 y 210 s después del último
   latido; tolera la pestaña en segundo plano. (Recomendada)
B. *T* = 60 s y revisión cada 15 s: detecta antes el corte, pero suspende pestañas en segundo plano.
C. *T* = 600 s y revisión cada 60 s.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Transcripción pegada más larga que la cola que cabe en el plazo

El juez evalúa un turno a la vez (≈ 45–60 s cada uno en CPU) y el plazo de un turno tiene un tope de
3 600 s (U4). Una transcripción pegada de 100 turnos de testimonio tardaría unos 75 minutos y sus últimos
turnos vencerían por plazo aunque nada falle. El Golden Dataset usa transcripciones de unos 15 turnos.

A. Bajar el límite de una transcripción pegada a 60 turnos de testimonio (los del entrevistador no
   cuentan); más se rechaza con `transcript.too_large`. Precisa BR2.3 de Functional Design, que se
   registra en la tabla de precisiones. (Recomendada)
B. Mantener 100 turnos y aceptar que, en CPU, los turnos que pasen de unos 60 en cola pueden terminar en
   «Error» por plazo y se reintentan a mano; la vista previa lo advierte.
C. Mantener 100 turnos y subir el tope del plazo a 7 200 s para todo el sistema (precisa el valor de U4).
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Unidad.** U6 `session-lifecycle`, revisión 2 del Functional Design (aprobada hoy): pegado, importación,
lista, latido y suspensión, reanudación, modo final con progreso, pausa, terminación y retirada del
consentimiento. Sale la versión nueva de un escenario (cambio 01).

## Lo que ya está decidido

- **Cifras de U4 (C25):** `transcript_max_chars` = 250 000, `turn_max_chars` = 20 000,
  `transcript_max_turns` = 2 000, `poll_interval_s` = 15, `poll_interval_active_s` = 2,
  `run_queue_wait_max_s` = 10 800 y `cancel_key_margin_s` = 120. U4 deja a U6 `import_file_max_bytes` y
  `heartbeat_timeout_s`.
- **Cifras de U11 (C25):** `run_deadline_final_s` = 3 600 en la máquina de desarrollo y 43 200 como tope
  del catálogo; `run_deadline_incremental_s` = 900 en desarrollo.
- **U1:** `limits.exceeded` siempre `413`; C25 sin nulos; las rutas que encolan IA declaran `202` como
  única respuesta 2xx, «Reanudar análisis» incluida.
- **U3:** `ActorSystem` suma `session-supervisor`. **U10 y U2:** sin cambios para U6.
- **Primera pasada:** P1 = A (*T* = 180 s y revisión cada 30 s) sigue vigente; P2 = A (60 turnos de
  testimonio) queda superada por el cambio 01: un bloque crea una sola corrida y los límites son los de C25.
- **Functional Design revisión 2:** las respuestas P4–P7 y las precisiones FD-U6-01 a FD-U6-24.

## Cómo se registra la revisión

Revisión 2 de los seis documentos y de `traceability.json`, que sustituye a la revisión 1 del 2026-10-03.
Los requisitos que siguen conservan su ID; lo que sale queda «Retirado» sin renumerar; lo nuevo toma el
número siguiente de su grupo. Las precisiones nuevas van en la tabla NFR-U6 de `security-requirements.md`
§6, y las de la revisión 1 quedan marcadas «Superado».

## Lo que el diseño resolverá sin preguntar

- `import_file_max_bytes` = 2 097 152: una transcripción en el límite (2 000 turnos y 250 000 caracteres)
  ocupa como mucho ≈ 1,4 MB en UTF-8 con el sobre de cada turno; queda un margen ≥ 45 % y coincide con
  `run_message_max_bytes`.
- `heartbeat_timeout_s` = 180 (P1 = A); dos cifras nuevas de C25: `session_sweep_interval_s` = 30 y
  `heartbeat_write_min_s` = 15.
- El latido **no** escribe en cada sondeo: a lo sumo una vez cada 15 s y sin esperar bloqueos.
- NFR8 **no** exige paginar la lista en el servidor: ≤ 500 sesiones, una consulta agregada y
  paginación de 25 en la consola.
- Un bloque que llevaría la sesión por encima de los totales de C25 responde `413`, como un turno en U4.
- `PATCH /sessions/{id}/analysis` responde `202` (regla de U1) en vez de `200` (C1); va a la tabla.
- `run_deadline_final_s` no lo fija U6; una medición sin umbral lo informa (NFR3.17).
- El Ingress de U2 no debe escribir en disco los cuerpos del pegado ni de la importación.

**Sin preguntas: todo lo fijan las fuentes.**
