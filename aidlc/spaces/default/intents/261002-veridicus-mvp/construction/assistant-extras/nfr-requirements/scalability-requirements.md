# Requisitos de escalado — U8 assistant-extras

**Insumos.** Flujos F1–F3 y §8 de `functional-design/functional-spec.md` (functional-spec); reglas
BR1.1, BR2.4 y BR2.6 de `functional-design/rules.md` (rules); NFR2 y NFR8 y los supuestos de
`inception/requirements-analysis/requirements.md` (requirements); C2, C3 y C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 de
`nfr-requirements-questions.md`.

## 1. Carga esperada

| Dimensión | Valor | Origen |
|---|---|---|
| Extras en la configuración por defecto | Los tres apagados | FR10, FR11; entities (`EvaluationOptions`) |
| Prueba de carga de NFR8 | 50 sesiones, tandas de 3, **extras apagados** | P1 = A |
| Corrida de nivel 2 con extras | 10 transcripciones (≤ 15 turnos cada una), una sesión a la vez | P1 = A |
| Llamadas al juez por turno con extras | ≤ 3, en serie, en la misma ranura | NFR3.3 |
| Preguntas sugeridas | ≤ 1 por intento de turno; ≤ 1 decisión por pregunta | entities |

## 2. Requisitos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.1 | La prueba de carga de NFR8 corre con los extras apagados (P1 = A). | `evaluation/load/run_batches.py` registra en su reporte las opciones de cada sesión creada y falla si alguna trae un extra en `true`; el umbral de ≥ 98 % (NFR8.5 de U4) se mide así. |
| NFR8.2 | Capacidad de la cola con los extras activos. | Con p95 de 150 s (NFR3.1) y el tope de plazo de 3 600 s de U4, caben **24 turnos** en cola sin vencer, frente a 60 con los extras apagados. La corrida de nivel 2 con extras usa una sesión a la vez (≤ 15 turnos en cola) y termina con 0 `turn.error.timeout`. Tres sesiones concurrentes con extras activos **no se soportan en el MVP**: es un límite declarado, no una meta. |
| NFR8.3 | Los extras no suben los picos de memoria. | Durante la corrida de nivel 2 con extras: `model-judge` ≤ 7 GiB, `semantic-agent` ≤ 512 MiB y trabajador de `session-api` ≤ 768 MiB (los topes de U4); el reporte registra el pico de cada pod. Superar un tope es un hallazgo que se corrige por PR. |
| NFR8.4 | U8 no impide más réplicas. | Ni `semantic-agent` ni `session-api` guardan estado de los extras en memoria: las opciones viajan en C2, el resultado de la permutación en C3 y la decisión se aplica con una actualización condicional en la base. Prueba de nivel 1: dos decisiones simultáneas sobre la misma pregunta dan exactamente un 200 y un 409, y una sola fila de `QuestionDecision`. |
| NFR8.5 | Las tablas de U8 crecen de forma acotada. | Como mucho 1 `SuggestedQuestion` por intento de turno, 1 `QuestionDecision` por pregunta y 1 resultado de permutación por afirmación releída; estimado < 5 MB en el MVP. Se conservan todas (historial de auditoría, NFR11). |

## 3. Efecto de los extras en el plazo y la cola de U4

- **Rendimiento del juez.** El juez atiende un turno a la vez (NFR8.7 de U4). Con los tres extras
  activos, cada turno ocupa la ranura hasta unas 2,5 veces más (p95 150 s frente a 60 s), así que el
  rendimiento cae de ≈ 1 turno por minuto a ≈ 1 cada 2,5 minutos.
- **Plazo.** La fórmula proporcional de U4 sigue igual; lo que cambia es la base (600 s con extras,
  NFR3.6) y el reclamo (480 s, NFR3.7), para que un turno con tres llamadas en serie no venza ni se
  reclame mientras sigue en curso.
- **Señal.** La profundidad de la cola de U4 (`veridicus_turn_queue_depth`) sigue siendo la señal; con
  los extras activos, más de 20 turnos en cola ya acercan el tope de 24 de NFR8.2
  (`observability-requirements.md` §4).
- **Qué hacer si no alcanza.** En este orden: dejar apagado el extra que más cuesta (la permutación),
  usar el perfil GPU para la demostración, o la segunda pareja juez + `semantic-agent` de U4. Cada
  cambio entra por PR con su medición; nunca se sube el tope de 3 600 s para que pase.
