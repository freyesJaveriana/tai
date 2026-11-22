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

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Sin preguntas: todo lo fijan las fuentes.**

## Lo que ya está decidido

- **P1 = A sigue:** *W* = 8 y la serie no se publica hasta tener 8 decididas. C15 v2 ya fija que la
  ventana son las **últimas *W* decididas** de la sesión, así que salen las «ignoradas» de la revisión 1
  (cierra R-01 de `reviews/review-01.md`).
- **`limits.exceeded` responde `413`** en toda ruta (decisión P7 = A de U1, NFR-U1-03). U5 cambia el `422`
  de FD-U5-02, BR2.7, E21 y NFR10.5.
- **Cifras de U5 en C25:** `review_text_max_chars` = 2 000 y `review_body_max_bytes` = 65 536. Son las que
  ya fijaba la revisión 1, ahora en el catálogo (FD-U5-02, NFR-U1-07). Más `dismissal_window_w` = 8.
- **AC5.4.4 frente a AC5.4.2 y FR1.2.** Lo resolvió la pregunta P4 = A del Functional Design de U3,
  ya aprobada: manda la matriz de FR1.2. El analista no dueño y el `admin` leen en solo lectura, el
  `investigador` recibe `403`, y no existe ningún rol para la persona entrevistada. U7 lo dejó en U5;
  aquí se prueba y AC5.4.4 se precisa (NFR-U5-03).
- **Lo que trae el Functional Design revisión 2:**
  - el estado `discarded` y `discard_correction_round` (FD-U5-04);
  - pedir `pending` responde `422` (FD-U5-09);
  - `404` `suggestion.not_found` (FD-U5-01);
  - el orden de bloqueo usuario → sesión → ronda y `change_seq` (BR3.8);
  - `purge_session` (C24).
- **Lo que ya está en los contratos:** `open_round(for_update=True)` ya está en C11 v2, lo que cierra
  R-02. La métrica `veridicus_review_rejections_total` no entra en C15 v2, porque su etiqueta `code` no
  está permitida.

## Cómo se registra la revisión

- Los seis artefactos y `traceability.json` pasan a **Revisión 2 (2026-11-22)**. Sustituyen a la revisión 1,
  que queda en el historial de Git.
- Los requisitos conservan su ID. Cada fila dice si **se mantiene**, **cambia**, es **nuevo** o queda
  **Retirado**. Lo nuevo toma el número siguiente de su grupo.
- Las precisiones a artefactos aprobados van en la tabla NFR-U5-01… de `security-requirements.md` §7.
- Los hallazgos R-01 a R-05 de la revisión 1 se cierran en las filas que los citan.

## Lo que el diseño resolverá sin preguntar

- **NFR Design** decidirá:
  - el candado en proceso y la guarda por `change_seq` que publica la razón en orden (D13);
  - la forma exacta del `DELETE … RETURNING` de `purge_session`;
  - el índice que cubre la consulta del estado vigente sin rondas `discarded`.
- **Infrastructure Design de U2** fija el respaldo de CloudNativePG (RPO y RTO), que U5 hereda.
