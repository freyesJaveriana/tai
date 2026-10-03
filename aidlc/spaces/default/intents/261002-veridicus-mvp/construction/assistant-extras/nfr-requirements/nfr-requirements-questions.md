# Preguntas de NFR Requirements — U8 assistant-extras

**Unidad.** U8 `assistant-extras`: permutación del orden de lectura, pregunta sugerida e indicio
afectivo, apagados por defecto (`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Doble lectura solo de las candidatas a alerta
(P1), lo no sostenido va al paquete (P2), lista de palabras emocionales sin LLM (P3), el juez y su
ventana de U4, y la consistencia > 65 % de NFR4. Functional Design dejó para esta etapa medir el efecto
de la segunda lectura en la latencia y en NFR8.

---

## P1 — Latencia con los extras activos

Con la permutación activa, cada turno con candidatas a alerta llama dos veces al juez; con la pregunta
sugerida, una vez más. En CPU eso puede duplicar o triplicar el tiempo de esos turnos frente a la meta
de U4 (p95 ≤ 60 s con los extras apagados).

A. Con los extras activos, p95 ≤ 150 s por turno en CPU; la prueba de humo y la carga de NFR8 corren
   con los extras apagados (su configuración por defecto), y una corrida aparte de nivel 2 mide los
   extras activos. (Recomendada)
B. Los extras activos deben cumplir la misma meta de 60 s.
C. Sin meta de latencia para los extras: solo se mide y se reporta.
X. Other (please specify)

[Answer]: A **Mode:** guided
