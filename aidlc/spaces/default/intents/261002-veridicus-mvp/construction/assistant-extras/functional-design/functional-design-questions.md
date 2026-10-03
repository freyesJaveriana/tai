# Preguntas de Functional Design — U8 assistant-extras

**Unidad.** U8 `assistant-extras` (tipo `service`, SHOULD/COULD): pregunta sugerida con aprobación del
analista (US10.3), permutación del orden de lectura (US10.5) e indicio afectivo en el paquete (US11.1).

**Lo que ya está decidido y no se vuelve a preguntar.** Ninguna pregunta en un turno con una afirmación
«no documentada» (AC10.3.2); la pregunta se basa solo en pasajes del marco de verdad y no se reproduce
sin aprobación (AC10.3.1, AC10.3.3); la permutación nunca produce alerta bajo el umbral (AC10.5.1); el
texto del indicio está fijado (AC11.1.1) y pasa el escaneo de vocabulario prohibido. Quedan tres huecos.

---

## P1 — Qué es «invertir el orden de lectura»

FR10.5 pide evaluar cada alerta candidata «en ambos órdenes de lectura» y registrarla solo si la
discrepancia aparece en los dos; ningún insumo dice qué se invierte.

A. La segunda evaluación presenta al juez los pasajes en orden inverso y la afirmación antes de los
   pasajes (en la primera va después); mismo prompt del sistema, misma semilla. (Recomendada)
B. Solo se invierte el orden de los pasajes.
C. Solo se cambia la posición de la afirmación respecto de los pasajes.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué pasa con una afirmación en la que los dos órdenes no coinciden

AC10.5.1 dice que no se registra alerta, pero no dice cómo queda la afirmación.

A. Queda como «no documentada»: sin alerta, entra al Paquete de Contexto de Traspaso con el motivo «el
   juez no sostuvo la incongruencia al invertir el orden», y suprime la pregunta sugerida. (Recomendada)
B. Queda como «congruente»: sin alerta y sin paquete.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Cómo detecta el indicio afectivo

FR11.1 habla de un «clasificador afectivo ligero (palabras clave emocionales en el *prompt*)».

A. Una lista versionada de palabras clave emocionales en español que se busca en el fragmento con las
   mismas reglas del escaneo (palabra completa, sin tildes ni mayúsculas), sin llamar al LLM; si hay al
   menos una, el paquete lleva el texto fijo. (Recomendada)
B. Una pregunta adicional al juez para que diga si el fragmento muestra estrés.
X. Other (please specify)

[Answer]: A **Mode:** guided
