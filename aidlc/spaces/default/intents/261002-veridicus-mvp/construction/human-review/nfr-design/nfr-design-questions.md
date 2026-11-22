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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Sin preguntas: todo lo fijan las fuentes.**

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) diseñó la CoT consultada (`cot-views`), las
rondas sin descarte, una métrica de rechazos y el orden sesión → ronda. El cambio 01 y la adenda 02 traen
las observaciones en lugar de la CoT, el estado `discarded` y `discard_correction_round`, el `404`
`suggestion.not_found`, la matriz de roles con AC5.4.4, el borrado por retención (C24), las cifras de C25 y
`limits.exceeded` siempre `413`. El Functional Design revisión 2 (FD-U5-01 a FD-U5-10) y el NFR Requirements
revisión 2 (NFR-U5-01 a NFR-U5-06) ya están aprobados.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| P1 de la revisión 1 | P1 = A sigue: orden único de bloqueo, ahora usuario → sesión → ronda, con `change_cursor.bump` y `change_seq` en decisiones y rondas | Revisión 1; BR3.8; NFRD-U3-01 |
| Requisitos | NFR1.1, NFR2.1, NFR3.1–NFR3.9, NFR7.1, NFR8.1–NFR8.7, NFR10.1–NFR10.22, NFR11.1–NFR11.6, NFR12.1, NFR13.1–NFR13.3, NFR14.1, NFR15.1–NFR15.5; decisiones D1–D15 | `nfr-requirements/`, revisión 2 |
| *W* y ventana | *W* = 8 de C25, últimas 8 decididas por `change_seq`, sin serie hasta 8 | P1 = A de NFR Requirements; NFR-U5-04 |
| Límites | `review_text_max_chars` = 2 000, `review_body_max_bytes` = 65 536, `413` `limits.exceeded`; el catálogo empaquetado es el techo | NFR-U5-01, NFR-U5-02; NFRD-U1-09 |
| Sondeo de U4 | Lectura en una instantánea `REPEATABLE READ READ ONLY` que devuelve el `change_cursor` leído (cierra R-01 de la revisión 1 de esta etapa) | NFRD-U4-05 |
| Supervisor de U4 | Recorre por sesión, con `bump` primero (cierra R-02 de la revisión 1) | NFRD-U4-06 |
| Autorización | `GuardedRoute` de U3: sesión → CSRF → `FOR SHARE` del usuario → rol → resolvedor → cuerpo; registro de acceso en un punto de guardado de 500 ms | NFR Design de U3 §2 |
| Fixtures AIR | U2 usa los suyos y el archivo de U5 a la vez | NFRD-U2-12 |
| Respaldo | El RPO es el último volcado manual y el RTO el de una restauración manual | NFRD-U2-13 |

## Cómo se registra la revisión

- Los seis documentos y `traceability.json` pasan a la revisión 2 en el mismo archivo, con una nota de
  cabecera que dice qué cambia y por qué. La revisión 1 queda en el historial de Git.
- Las secciones conservan su número cuando siguen; lo que sale queda «Retirado» sin renumerar y lo nuevo
  toma números nuevos.
- Las precisiones a artefactos aprobados y las peticiones a otras unidades van en la tabla NFRD-U5-xx de
  `security-design.md` §11. La tabla §7 de `reliability-design.md` de la revisión 1 queda superada.
- Los hallazgos R-01 a R-04 de `reviews/review-01.md` se cierran en las filas que los citan.

## Lo que el diseño resolverá sin preguntar

1. **Publicación en orden de la razón (D13, R-03).** Toda escritura en el *gauge* (fijar o retirar) lleva el
   `change_seq` con que se calculó; una más vieja se descarta.
2. **Retirada al purgar.** El `Job` de retención corre en otro proceso; la API reconcilia sus series cada
   60 s (NFRD-U5-01).
3. **Barrera de «en blanco» (R-04).** El `CHECK` usa `btrim` con la lista exacta de espacios de
   `str.isspace()` (NFRD-U5-02).
4. **Nombres de las variables de C25** según NFRD-U1-09 (NFRD-U5-03) y tope del cuerpo por `GuardedRoute`
   de U3 (NFRD-U5-04, NFRD-U5-05).
5. **Índices y forma de `purge_session`**, incluida la respuesta a «índice para saltar las rondas
   `discarded`»: no hace falta (NFRD-U5-06).
6. **Sondeo tras descartar una copia**, que revierte estados sin decisión nueva (NFRD-U5-07).
7. **Redis caído** deja sin servicio la consola aunque U5 no use Redis (NFRD-U5-08).

Ningún punto cambia el alcance ni deja salir del clúster algo que hoy no sale.