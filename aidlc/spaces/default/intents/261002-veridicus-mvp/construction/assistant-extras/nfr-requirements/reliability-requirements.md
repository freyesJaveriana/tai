# Requisitos de fiabilidad — U8 assistant-extras

**Insumos.** Flujos F1–F3, la máquina de estados de §3 y §8 «Errores y bordes» de
`functional-design/functional-spec.md` (functional-spec); reglas BR1.1–BR1.6, BR2.1, BR2.3–BR2.5 y BR3.1
de `functional-design/rules.md` (rules); NFR4, NFR6, NFR8 y NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C2, C3, C6 y C16 y las reglas de
propiedad de `inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 de
`nfr-requirements-questions.md`.

## 1. Objetivos

Ningún MUST depende de U8. Su objetivo de fiabilidad es **no romper el flujo de U4**: con los extras
apagados no ejecuta nada, y con ellos activos un fallo de la pregunta o del indicio nunca convierte el
turno en error.

| ID | Objetivo | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.6 | La prueba de humo no falla por U8. | 0 fallos atribuibles a U8 en cada corrida de `scripts/smoke.sh` con los extras apagados (NFR3.12). | Nivel 3 |
| NFR8.7 | Los extras activos terminan cada turno. | En la corrida de nivel 2 con extras, el 100 % de los turnos termina `evaluated` o `error` con un `code` del catálogo, con 0 `turn.error.timeout` (una sesión a la vez, NFR8.2). | Nivel 2 |

## 2. Requisitos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.11 | Toda E/S de U8 tiene *timeout* explícito, leído de la configuración validada al arrancar. | Segunda lectura: el *timeout* del juez de U4 (180 s). Pregunta: **60 s** (`VERIDICUS_QUESTION_TIMEOUT_SECONDS`). `count_tokens` 5 s, PostgreSQL ≤ 2 s y Redis ≤ 0,5 s, como U4 (NFR10.14 de U4). | Nivel 0 (configuración) y nivel 1 |
| NFR10.12 | Cada fallo de la segunda lectura tiene el tratamiento de la primera (BR1.5). | Salida que no cumple C6, cita pasajes no recuperados o tiene vocabulario prohibido fuera de citas → `turn.error.invalid_output` y 0 alertas (E4); *timeout* → `turn.error.timeout` sin reintento automático; conexión rechazada o 5xx → no se confirma el mensaje y el turno entero vuelve por `XAUTOCLAIM` (no se publicó nada, así que no hay efectos dobles). Una prueba de nivel 0 por caso con el juez *fake*. | Nivel 0 |
| NFR10.13 | Un fallo de la pregunta nunca rompe el turno (BR2.3). | Salida fuera de su esquema, texto vacío o de más de 300 caracteres, término de C8, *timeout* de 60 s, conexión rechazada o 5xx, o bloque de más de 6 000 *tokens* → C3 sin `suggested_question`, turno `evaluated` con sus alertas y su paquete, y el motivo en la métrica y en el log. Sin reintento de la pregunta. Una prueba de nivel 0 por motivo (E6 incluido). | Nivel 0 |
| NFR10.14 | La configuración de los extras se valida al arrancar. | `session-api`: `VERIDICUS_EXTRAS_PERMUTATION`, `VERIDICUS_EXTRAS_SUGGEST_QUESTION` y `VERIDICUS_EXTRAS_AFFECTIVE` obligatorias, solo `true` o `false`; la regla de plazo y reclamo de NFR3.6 y NFR3.7. `semantic-agent`: SHA-256 del *prompt* de la pregunta igual a `VERIDICUS_QUESTION_PROMPT_SHA256`, y la lista afectiva cargada, con `schema_version` conocida y sin términos de C8. Cualquier fallo → el proceso termina con código distinto de 0 y `/readyz` responde `503` mientras tanto (C16). | Nivel 0 y nivel 1 |
| NFR10.15 | La decisión sobre una pregunta es atómica (BR2.4). | Una transacción hace la actualización condicional (`WHERE status = 'proposed'`) y la inserción de `QuestionDecision`; si la actualización no afecta filas → `409` sin insertar nada. Un fallo a mitad deja la pregunta `proposed` sin decisión. Prueba de nivel 1 con dos decisiones simultáneas (NFR8.4) y otra que corta la conexión antes de confirmar. | Nivel 1 |
| NFR10.16 | La consola sobrevive a un fallo al decidir. | Si `POST /questions/{id}/decision` falla por red o 5xx, la tarjeta conserva «Pregunta sugerida · requiere tu aprobación», muestra el mensaje del catálogo y vuelve a habilitar «Aprobar» y «Descartar»; si un reintento recibe `409`, la tarjeta se actualiza con el estado del siguiente sondeo. | Vitest con un servidor *fake* |

## 3. Calidad de la IA con los extras

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR4.1 | La permutación solo quita alertas, nunca las añade (BR1.2, BR1.4, AUTONOMIA-05). | Prueba de propiedad de nivel 0 (Hypothesis) sobre todas las combinaciones de guardia y de calificaciones de las dos lecturas: el conjunto de alertas con permutación está contenido en el de sin permutación; una afirmación bajo el umbral nunca tiene segunda lectura ni alerta (E3); `sustained` es `true` solo con las dos lecturas «incongruente». El módulo tiene 100 % de ramas (NFR13.2). | Nivel 0 |
| NFR4.2 | La permutación queda registrada (BR1.6). | Con `options.permutation` en `true`, el 100 % de los resultados C3 lleva `permutation_applied: true` y cada afirmación releída guarda `forward_grade`, `reversed_grade` y `sustained`; con `false`, `permutation_applied` es `false` y no hay calificaciones invertidas. | Nivel 1 |
| NFR4.3 | Los extras no rompen las metas de NFR4. | La corrida de nivel 2 con extras cumple los umbrales de NFR4 sobre el Golden Dataset: ≥ 5 de 6 discrepancias detectadas, ≤ 1 alerta en las 4 transcripciones alineadas, 100 % de trazabilidad factual y 0 % de error de formato JSON **en las dos lecturas**, y en el caso de Hecho No Documentado 0 alertas, **0 preguntas** y 1 paquete. Si la permutación baja la detección de 5 de 6, es un hallazgo y el extra sigue apagado. | Nivel 2 |
| NFR4.4 | Consistencia de la permutación en línea frente a la *offline*. | La consistencia > 65 % al invertir el orden y la permutación en el 100 % de las consultas *offline* de NFR4 las mide el arnés de U4 (NFR4.5 de U4) con los extras apagados. La corrida con extras mide además la **tasa en línea**: afirmaciones con `sustained: true` / candidatas releídas; debe ser **> 65 %** para activar la permutación en un despliegue. El reporte JSON registra las dos cifras por separado. | Nivel 2 |
| NFR4.5 | Los extras son repetibles. | Dos corridas seguidas de nivel 2 con extras, con el mismo modelo, *prompts*, semilla, umbral y lista afectiva, dan el mismo `sustained` por afirmación, el mismo conjunto de turnos con pregunta y con indicio afectivo; el texto de la pregunta y la CoT pueden diferir solo si el reporte lo declara. | Nivel 2 |
| NFR6.1 | La CoT que ve el analista no cambia con la permutación. | Una alerta sostenida muestra la CoT de la **primera lectura** (orden directo); la CoT de la segunda lectura se valida (BR1.5) pero no se muestra ni se guarda (precisión en `security-requirements.md` §6). Así la calificación Likert de NFR6, hecha con los extras apagados, vale también con la permutación activa. | Nivel 0 |

## 4. Recuperación y degradación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `semantic-agent` entre la primera y la segunda lectura | Nada | No se publicó C3; el mensaje vuelve por `XAUTOCLAIM` tras 480 s (NFR3.7) y el turno se evalúa de nuevo entero |
| El juez no responde a la pregunta | La pregunta de ese turno | El turno sigue `evaluated` (NFR10.13); no hay reintento de la pregunta |
| La lista afectiva o el *prompt* de la pregunta no cargan | Nada; el servicio no arranca | `/readyz` en `503` hasta corregir por PR (NFR10.14) |
| Caída de PostgreSQL al decidir | La decisión no se registra | La pregunta sigue `proposed`; el analista decide de nuevo (NFR10.16) |

Si el analista no decide una pregunta, se queda `proposed`: no bloquea la consolidación y no aparece
como formulada en el reporte (BR2.5).
