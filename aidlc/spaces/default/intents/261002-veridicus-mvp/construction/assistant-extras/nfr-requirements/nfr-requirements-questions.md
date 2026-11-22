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

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Situación.** U8 pasa de «permutación del juez, pregunta sugerida e indicio afectivo, apagados por
defecto» a **aclaraciones neutras deterministas** (US10.3) y **permutación del verificador activa en todos
los perfiles** (US10.5, P5 = A), según el Functional Design revisión 2 de hoy (F4–F9, BR4.1–BR6.5,
FD-U8-01 a FD-U8-11). P1 = A de la revisión 1 queda **Superada**: ya no hay extras que encender, ni pregunta
ni segunda lectura del juez.

## Lo que ya está decidido

| Tema | Decisión | Fuente |
|---|---|---|
| Aclaración sin modelo | La biblioteca la arma del `hecho` sin ninguna llamada nueva | P4 = A; BR5.1 |
| Permutación | `permutation: true` en todos los perfiles, también `todo-local`; se apaga solo por PR que cambie el perfil y la prueba de BR6.1 | P5 = A; BR6.1; FD-U8-08 |
| Regla para apagarla | Solo si la permutación impide el 98 % de corridas completas de NFR8; el umbral no se baja | Decisión de U11 de hoy (permutación en todos los perfiles y su costo dentro de los plazos) |
| Verificador | Local (gpt-oss-20b) en todos los perfiles actuales: `verifier_permuted` no sale del clúster ni cuesta *tokens* comerciales | P1 = A de U11 |
| Latencia y humo | p95 incremental ≤ 180 s con `comercial-piloto`; *N* = 300 s; U4 dispone de ≤ 10 s; plazo incremental de 900 s en desarrollo | NFR de U11 y U4 de hoy |
| Aclaraciones fuera del reporte | Ninguna entra en el reporte | P6 = A |
| Umbrales | Nunca se bajan para que una compuerta pase | `team.md` |
| Límites | Toda cifra de límite vive en C25 y entra cuando su unidad dueña fija el valor | `project.md`; decisión de U1 de hoy |

## Cómo se registra la revisión

Como revisión 2 de cada artefacto, con los IDs de la revisión 1: lo que sigue conserva su número y dice
**se mantiene** o **cambia**; lo que sale queda **Retirado** sin renumerar; lo nuevo toma el número siguiente
de su grupo. Las precisiones a artefactos aprobados van a la tabla NFR-U8-xx de `security-requirements.md`.

## Lo que el diseño resolverá sin preguntar

Las tres preguntas abiertas del Functional Design (§12) se resuelven con las fuentes; quedan en la tabla
NFR-U8-xx para que las corrijas en la aprobación:

1. **Costo de `verifier_permuted` en `todo-local` (NFR-U8-01).** La permutación sigue activa. Se apaga en
   `todo-local`, por PR, solo si la medición de BR6.5 con ese perfil en la máquina de desarrollo da menos
   del 98 % de corridas incrementales terminadas sin `tiempo_agotado` dentro de `run_deadline_incremental_s`,
   o si la prueba de NFR8 no alcanza el 98 % por la llamada permutada. Es la misma regla que fijó U11.
2. **Tasa de aclaraciones descartadas (NFR-U8-02).** Se reporta sin bloquear, con una señal de revisión por
   encima de 0,50. No bloquea porque U8 es SHOULD y no tiene una palanca propia: las reglas que descartan
   (BR5.4, BR5.5) protegen VE-05 y no se relajan, y un umbral fijado sin línea base ya no se podría bajar.
   El 0 % de citas en los temas emitidos sí bloquea (FR10.3).
3. **Tope de aclaraciones y largo del tema en C25 (NFR-U8-03).** No se añade ninguna cifra: el tema sale del
   `hecho`, que ya acotan `model_response_max_bytes` y `run_message_max_bytes`, y las aclaraciones de una
   sesión no superan sus hallazgos, porque se deduplican. El rendimiento se prueba con 100 aclaraciones.

**Sin preguntas: todo lo fijan las fuentes.** Es una segunda pasada sin conflicto real entre fuentes
aprobadas, y ninguna decisión cambia el alcance, el riesgo ni lo que sale del clúster (regla de
`project.md`).
