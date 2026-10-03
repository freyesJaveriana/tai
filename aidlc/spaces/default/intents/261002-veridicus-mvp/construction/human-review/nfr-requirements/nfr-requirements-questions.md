# Preguntas de NFR Requirements — U5 human-review

**Unidad.** U5 `human-review`: decisiones humanas sobre las sugerencias, rondas de revisión y métricas
de la regla AIR (`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Máquina de estados, exigencias de CoT y nota,
herencia entre rondas (P1 de Functional Design), convención de auditoría de U3, sondeo de la consola de
U4 y las metas de NFR11. Los tiempos de respuesta de las rutas de decisión siguen los de U3 y U4 y no
necesitan pregunta. `contract-summary.md` (C15) dejó para esta etapa la ventana *W* de la razón AIR.

---

## P1 — Ventana *W* de la razón de descarte (regla AIR)

`veridicus_session_dismissal_ratio` es la fracción de alertas descartadas o sin decidir entre las
últimas *W* alertas de la sesión; U2 alerta con una **propuesta** de umbral cuando supera 0,25 (FR9.3).
Una ventana corta reacciona antes pero es ruidosa (con 2 alertas, 1 descarte ya es 50 %).

A. *W* = 8, y la métrica no se publica hasta que la sesión tenga 8 alertas (sin falsas alarmas al
   inicio). (Recomendada)
B. *W* = 12, con el mismo mínimo.
C. *W* = 4, publicada desde la primera alerta.
X. Other (please specify)

[Answer]: A **Mode:** guided
