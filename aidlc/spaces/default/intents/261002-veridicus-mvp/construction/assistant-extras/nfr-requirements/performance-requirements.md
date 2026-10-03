# Requisitos de rendimiento — U8 assistant-extras

**Insumos.** Flujos F1–F3 y §8 «Errores y bordes» de `functional-design/functional-spec.md`
(functional-spec); reglas BR1.1, BR1.5, BR2.2, BR2.3, BR2.4 y BR3.1 de `functional-design/rules.md`
(rules); FR10.3, FR10.5, FR11.1 y NFR2, NFR3 y NFR8 de `inception/requirements-analysis/requirements.md`
(requirements); C1, C2, C3 y C14 de `inception/contract-design/contract-summary.md` (contract-summary);
respuesta P1 de `nfr-requirements-questions.md`.

Las metas se miden en la **máquina de desarrollo con el perfil CPU** (NFR2) y con el mismo juez de U4
(Qwen2.5-7B-Instruct Q4_K_M en `llama-server` con una sola ranura). U8 no cambia las metas de U4: con
los extras apagados —su configuración por defecto— rigen el p95 ≤ 60 s por turno (NFR3.1 de U4) y la
*N* = 120 s de la prueba de humo (NFR3.10 de U4). Este documento fija lo que cuesta **encender** los
extras. Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*; nunca se
reintenta ni se baja su umbral (team-practices).

## 1. Latencia del turno con los extras

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | Tiempo de un turno de texto (`evaluated_at − submitted_at`) con **los tres extras activos** (`permutation`, `suggest_question`, `affective`) | **p95 ≤ 150 s** (P1 = A) | Todos los turnos de texto de las 10 transcripciones del Golden Dataset, una sola sesión a la vez | Corrida aparte de nivel 2 con extras activos; el reporte JSON registra p50, p95 y máximo, y las opciones de cada sesión |
| NFR3.2 | Coste de U8 con los extras apagados | **0 llamadas adicionales** al juez: exactamente 1 llamada por turno evaluado y ninguna búsqueda en la lista afectiva | Turnos con afirmaciones incongruentes sobre el umbral y con opciones en `false` | Prueba de nivel 0 con el juez *fake*, que cuenta las llamadas recibidas |
| NFR3.3 | Número de llamadas al juez por turno con los extras activos | Primera lectura: 1. Segunda lectura: 1 si hay al menos una candidata (BR1.1), 0 si no. Pregunta: 1 si no hay ninguna afirmación «no documentada» (BR2.1), 0 si no. Indicio afectivo: 0 siempre (BR3.1). Máximo 3 por turno | Las combinaciones de E1–E10 | Prueba de nivel 0 con el juez *fake* |

**Presupuesto orientativo de NFR3.1** (lo confirma la medición, no la reemplaza): flujo de U4 ≤ 60 s;
segunda lectura ≤ 50 s (solo las candidatas, sin volver a calcular *embeddings* ni recuperar pasajes);
pregunta ≤ 30 s (salida corta, pero sus instrucciones no están en la caché del servidor, ver
`tech-stack-decisions.md` §6); indicio afectivo < 0,01 s. El reporte de nivel 2 registra el p95 de
cada llamada por separado (`veridicus_extra_judge_duration_seconds`, `observability-requirements.md`).

## 2. Tamaño de los *prompts* de los extras

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.4 | La segunda lectura usa los mismos límites que la primera (BR1.1, BR1.5). | Misma ventana de 12 288 *tokens*, mismo prompt del sistema, misma semilla (`VERIDICUS_JUDGE_SEED`) y temperatura 0. Su bloque de datos solo lleva las afirmaciones candidatas y sus pasajes —un subconjunto del bloque de la primera lectura en otro orden—, así que cabe por construcción en los 6 000 *tokens* de U4 y no se vuelve a llamar a `count_tokens`. Salida `max_tokens = min(4 096, 200 × candidatas)`. Prueba de propiedad de nivel 0 (Hypothesis): el bloque de la segunda lectura nunca tiene más elementos ni más caracteres que el de la primera. |
| NFR3.5 | La pregunta sugerida tiene su propio límite (BR2.2). | Bloque de datos (el texto del turno y sus pasajes recuperados, cada pasaje una vez) ≤ 6 000 *tokens* contados con `count_tokens` del servidor del juez antes de llamarlo; si se supera, **no hay llamada** y la pregunta se omite con motivo `too_long`, sin afectar al turno (BR2.3). Instrucciones de la pregunta ≤ 600 *tokens* (prueba de nivel 0 sobre el archivo del *prompt*). Salida `max_tokens = 160` (300 caracteres en español más el envoltorio JSON). Pruebas de nivel 0 con un contador de *tokens* falso por debajo y por encima del límite. |

## 3. Plazo y cola con los extras

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.6 | El plazo base cubre el peor caso de un turno con extras. | Con algún extra que llame al juez activo, la validación al arrancar de `session-api` exige `VERIDICUS_TURN_DEADLINE_BASE_SECONDS` > *timeout* de *embeddings* (30 s) + *timeout* del juez (180 s) × (1 + `permutation`) + *timeout* de la pregunta (60 s) × `suggest_question` = 450 s con los tres activos; los *values* que activan los extras fijan **600 s**. La fórmula proporcional a la cola y el tope de 3 600 s de U4 (NFR3.5 de U4) no cambian. Pruebas de nivel 0: 450 s se rechaza y 600 s se acepta con los tres extras; 300 s se acepta con todos apagados. |
| NFR3.7 | El reclamo de pendientes no roba un turno que sigue en curso. | Con extras activos, `VERIDICUS_QUEUE_RECLAIM_IDLE_SECONDS` debe superar la misma suma (450 s con los tres) y quedar por debajo del plazo base; los *values* de extras fijan **480 s**. Prueba de nivel 0 de la validación. |

## 4. Consola

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.8 | Responder a la decisión sobre una pregunta es inmediato. | `POST /questions/{id}/decision` p95 ≤ 300 ms con 100 decisiones sobre preguntas distintas. Prueba `perf` de nivel 1 en proceso con PostgreSQL real. |
| NFR3.9 | Las preguntas no frenan el sondeo de la sesión. | `GET /sessions/{id}?since=<cursor>` sigue en p95 ≤ 200 ms (NFR3.3 de U4) con 50 turnos, 20 sugerencias, 5 paquetes y **15 preguntas sugeridas** (con sus decisiones). Prueba `perf` de nivel 1. |
| NFR3.10 | La tarjeta de la pregunta aparece con el resultado del turno. | Desde `evaluated_at` hasta que «Pregunta sugerida · requiere tu aprobación» aparece en M4: ≤ 3 s con turnos en curso (el mismo ciclo de sondeo de 2 s de U4). Tras «Aprobar» o «Descartar», la tarjeta muestra el nuevo estado con la respuesta 200, sin esperar al siguiente sondeo. Playwright de nivel 3 con el juez *fake* y los extras activos, y Vitest. |
| NFR3.11 | El indicio afectivo no añade latencia apreciable. | Búsqueda de la lista sobre un turno de 2 000 caracteres: p95 ≤ 10 ms con la lista completa. Prueba `perf` de `semantic-agent` (1 000 repeticiones). |

## 5. Prueba de humo

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.12 | La humo de team-practices corre con los extras apagados (P1 = A). | `scripts/smoke.sh <url-base>` usa *N* = 120 s (NFR3.10 de U4) contra la configuración por defecto; antes de los casos, `frontend/e2e/smoke.spec.ts` comprueba que la sesión creada trae las tres opciones en `false` y falla si no. Si un despliegue activa algún extra por PR, ese despliegue corre la humo con `SMOKE_TIMEOUT_SECONDS=300` (2 × el p95 de NFR3.1) y el caso de Hecho No Documentado comprueba además 0 preguntas sugeridas. |

## 6. Recursos

Los extras no cambian los topes de memoria de U4 (NFR8.1–NFR8.4 de U4): la segunda lectura y la
pregunta usan la misma ventana del mismo servidor, y la lista afectiva pesa unos KB. Se comprueba en
`scalability-requirements.md` (NFR8.3) midiendo los picos durante la corrida de nivel 2 con extras.
