# Preguntas de NFR Design — U5 human-review

**Unidad.** U5 `human-review` (revisión humana): consulta de la CoT (`cot-views`), decisiones del
analista dueño (aceptar, editar, descartar) como filas nuevas en una ronda de revisión, rondas para la
consolidación de U7 (C11), `propose` para U4 (C10) y métricas de descarte para la señal AIR (C15).

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D12 de
`nfr-requirements/`: máquina de estados como función pura, estado vigente calculado con una sola
consulta `DISTINCT ON` (nunca guardado), bloqueo `SELECT … FOR UPDATE` de la ronda abierta en `decide`,
`lock_round` y `open_correction_round`, `lock_timeout` y `statement_timeout` de 2 s con `503`,
`seq` como desempate, solo `INSERT`/`SELECT` en `ReviewDecision` y `CotView`, sin `UPDATE` sobre
`ReviewSuggestion`, decisiones sin reintento automático y `cot-views` idempotente, consola sin
actualización optimista, ventana AIR de 8 alertas calculada tras el *commit*, y
`open_round(for_update=True)` en la consolidación de U7. Queda un hueco de diseño, que aparece al
juntar U5 con el cursor de sondeo que aprobó U4.

---

## P1 — Cómo llega una decisión al sondeo de la consola sin crear un interbloqueo

El NFR Design de U4 (respuesta P2 = A) fijó que la consola consulta `GET /sessions/{id}?since=<cursor>`
y solo recibe lo que cambió: un contador `change_seq` en la fila de la sesión, que toda transacción que
cambia algo de la sesión bloquea e incrementa, y que marca sus filas (turnos, sugerencias, paquetes) con
el nuevo valor. Una decisión de U5 cambia el estado vigente de una sugerencia, pero no puede marcar la
fila de `ReviewSuggestion` (la aplicación no tiene `UPDATE` sobre ella), así que hoy el sondeo
incremental no la vería: una segunda pestaña o el siguiente sondeo de la misma pestaña se quedarían con
el estado viejo (U4 exige no perder ningún cambio). Además, U5 bloquea la fila de la **ronda** y U4 la
de la **sesión**; si una transacción toma ronda → sesión y otra sesión → ronda (la ingesta de U4 llama
`propose`, que lee o abre la ronda), pueden interbloquearse. `cot-views` no cambia el estado y
queda fuera de esta pregunta.

A. Un solo orden de bloqueo para todo `session-api`: **primero la fila de la sesión, después la de la
   ronda**. `decide` bloquea la sesión, incrementa
   `change_seq`, bloquea la ronda abierta e inserta `ReviewDecision` con ese `change_seq` (columna
   nueva, sin `UPDATE`). La consulta de sondeo incluye las sugerencias que tengan una decisión con
   `change_seq > cursor` y devuelve su estado vigente. U7 (`lock_round`, `open_correction_round`) sigue
   el mismo orden e incrementa `change_seq`. Una prueba de nivel 1 con decisiones e ingestas
   simultáneas (dos hilos, barrera, 50 repeticiones) no produce interbloqueos ni cambios perdidos.
   (Recomendada)
B. Las decisiones no tocan `change_seq` ni la sesión: tras el `201`, la consola pide la sesión
   **completa** (sin `since`) y reinicia el cursor. Sin riesgo de interbloqueo, pero otra pestaña u
   otro usuario en solo lectura no ve la decisión hasta recargar, y la vista completa cuesta más que el
   sondeo incremental.
C. Se mantiene el bloqueo de la ronda en la transacción de la decisión y el `change_seq` se incrementa
   en una segunda transacción corta después del *commit*. Evita cambiar el orden de bloqueo, pero si
   la segunda transacción falla, la decisión queda guardada y el sondeo no la ve nunca.
X. Other (please specify)

[Answer]: A **Mode:** guided