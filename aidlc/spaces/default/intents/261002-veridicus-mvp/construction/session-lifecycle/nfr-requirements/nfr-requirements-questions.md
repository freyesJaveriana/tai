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
