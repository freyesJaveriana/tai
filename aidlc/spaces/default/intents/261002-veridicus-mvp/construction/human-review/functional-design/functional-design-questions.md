# Preguntas de Functional Design — U5 human-review

**Unidad.** U5 `human-review` (tipo `service`): aceptar con CoT consultada (US5.1), editar con
reformulación propia (US5.2), descartar con nota (US5.3), solo el dueño decide (US5.4); rondas y
decisiones de solo inserción (ADR-007).

**Lo que ya está decidido y no se vuelve a preguntar.** Toda sugerencia nace pendiente; nunca vuelve a
pendiente; dentro de una ronda abierta se cambia entre aceptada, editada y descartada con las mismas
exigencias; descartar exige nota; editar nunca toca fragmento, cita, documento ni CoT; una ronda
bloqueada no admite cambios; la autorización por dueño la aplica ConsoleApi (components, ADR-007,
ADR-009, AC5.1.1–AC5.4.3). La copia de trabajo de una corrección parte de las decisiones vigentes
(interaction-spec F4). Queda un solo hueco.

---

## P1 — Validez del evento «CoT consultada» en una ronda de corrección

Aceptar o editar exige que el mismo usuario haya desplegado la CoT de esa alerta (AC5.1.2). Cuando U7
abre una ronda de corrección del reporte, el analista vuelve a decidir sobre alertas que ya revisó.

A. El evento vale por usuario y alerta para siempre: si ya desplegó la CoT en la ronda 1, puede aceptar
   o editar en la corrección sin volver a desplegarla. (Recomendada)
B. El evento vale solo dentro de la ronda: en cada ronda de corrección hay que volver a desplegar la CoT
   antes de aceptar o editar.
X. Other (please specify)

[Answer]: A **Mode:** guided
