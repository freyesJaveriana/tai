# Requisitos de seguridad — U8 assistant-extras

**Insumos.** Flujos F1–F3, la frontera de §1 y la máquina de estados de §3 de
`functional-design/functional-spec.md` (functional-spec); reglas BR1–BR4 de `functional-design/rules.md`
(rules); FR5.2, FR10.3, FR10.5, FR11.1 y NFR1, NFR4, NFR5 y NFR10–NFR12 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C2, C3, C6, C8, C13, C14 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 de
`nfr-requirements-questions.md`; reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de team-practices: nivel 0
(unitarias, contratos y políticas), nivel 1 (integración con PostgreSQL y Redis reales), nivel 2
(evaluación de IA sobre el Golden Dataset), nivel 3 (E2E y humo) y manual. Los comandos están en
`tech-stack-decisions.md` §5. U8 reutiliza sin repetirlos los controles de U3 (autenticación, rol,
anti-CSRF, convención de auditoría) y de U4 (ModelGateway con URL internas, bloque de datos en JSON,
*prompt* montado de solo lectura, validación de C6, escáner de C8, logs solo con identificadores,
`XDEL` de los *streams*).

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| SemanticEvaluation — permutación | `semantic-agent`, dentro del clúster, bajo la `NetworkPolicy` de salida denegada de U2 | Afirmaciones candidatas y sus pasajes hacia `model-judge` interno (C14); nada sale | Confidencial |
| SemanticEvaluation — pregunta sugerida | `semantic-agent`, dentro | Texto del turno y pasajes recuperados hacia `model-judge` interno; la pregunta vuelve por C3 (Redis interno) | Confidencial |
| SemanticEvaluation — indicio afectivo | `semantic-agent`, dentro | Ninguno: búsqueda local en la lista, sin LLM | Confidencial (el turno) |
| InterviewSession (preguntas y decisiones) | `session-api`, dentro | Ninguno sale; filas en PostgreSQL interno | Confidencial |
| ConsoleApi (`/questions/*/decision`) | `session-api`, dentro | Pregunta y su estado hacia el navegador, dentro del clúster (C1) | Confidencial |
| AnalystConsole (tarjeta de la pregunta) | Navegador, servido por `frontend` | Solo habla con ConsoleApi | Confidencial |
| Lista afectiva y *prompt* de la pregunta | `ConfigMap` montados de solo lectura | Ninguno | Pública (versionada en el repositorio) |

**Ningún componente de U8 hace una llamada fuera del clúster ni añade un destino nuevo.**

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | La permutación produce una alerta que la primera lectura no tenía, o bajo el umbral (AUTONOMIA-05) | Tampering | Alto | NFR4.1 (`reliability-requirements.md`), NFR13.2 |
| T2 | La pregunta sugerida lleva una etiqueta de veracidad («¿por qué miente?») o un campo de veracidad (AUTONOMIA-03) | Tampering | Alto | NFR10.4, NFR10.5 |
| T3 | Se sugiere una pregunta en un Hecho No Documentado o con conjeturas fuera del marco de verdad (AUTONOMIA-05) | Tampering | Alto | NFR10.3, NFR4.3 |
| T4 | Inyección desde el testimonio para dictar la pregunta o la segunda lectura | Tampering | Alto | NFR10.2, NFR5.1 |
| T5 | *Prompt* de la pregunta alterado en el clúster | Tampering | Medio | NFR10.3 |
| T6 | Una pregunta llega al compareciente sin aprobación del analista | Elevation of privilege | Alto | NFR10.7 |
| T7 | Otro analista o un `admin` decide la pregunta de una sesión ajena, o sin anti-CSRF | Elevation of privilege | Medio | NFR10.6 |
| T8 | Reescribir o borrar la decisión sobre una pregunta | Repudiation | Medio | NFR11.1, NFR11.2 |
| T9 | Activar o apagar un extra sin rastro (desde la consola o en caliente) | Repudiation | Medio | NFR10.9, NFR11.4 |
| T10 | Texto de la pregunta, CoT invertida o palabra afectiva en logs o métricas | Information disclosure | Alto | NFR10.8 |
| T11 | El indicio afectivo se lee como diagnóstico o juicio sobre el compareciente | Tampering | Medio | NFR10.10, NFR10.5 |
| T12 | Un extra envía datos a un destino externo por configuración | Information disclosure | Alto | NFR1.1, NFR1.2 |
| T13 | Los extras activos saturan la cola (hasta 3 llamadas por turno) | Denial of service | Bajo | Riesgo aceptado (§5) |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | U8 no añade destinos. | La segunda lectura y la pregunta usan el mismo `ModelGateway` y la misma `VERIDICUS_JUDGE_URL` validada por U4 (NFR1.1 de U4); la configuración de U8 no tiene ninguna URL. Prueba de nivel 0 sobre el modelo de configuración de U8: ningún campo es una URL. | Nivel 0 |
| NFR1.2 | Los extras funcionan con la `NetworkPolicy` de salida denegada. | Con los tres extras activos, `/readyz` de `semantic-agent` pasa con la política de U2 aplicada; la lista afectiva y el *prompt* de la pregunta vienen montados, nada se descarga en ejecución. Verificación manual en el clúster junto con la de U2 y U4. | Manual |

### NFR5 — Resistencia adversarial

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR5.1 | Escenario A con los extras activos. | Con el texto de inyección del PRD añadido a cada transcripción, el conjunto de alertas sostenidas es el mismo que sin inyección; ninguna pregunta publicada contiene el texto de inyección ni sus instrucciones (comparación de subcadenas normalizadas en el reporte). | Nivel 2 |
| NFR5.2 | Los extras no cambian de familia de modelo. | La segunda lectura y la pregunta usan el juez Qwen2.5 de U4; el reporte de nivel 2 con extras declara el mismo `model_digest` en las tres llamadas. | Nivel 2 |

### NFR10 — Seguridad de la aplicación

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | Las entradas de U8 se validan en su frontera. | Cuerpo de la decisión estricto (`status` ∈ {`approved`, `discarded`}, sin otros campos) y `question_id` UUID → si no, `422` `validation.invalid_request` sin filas. `options` de C2 con sus tres booleanos obligatorios (U4 ya rechaza un mensaje inválido). `suggested_question` de C3 revalidado al ingerir (1–300 caracteres, escaneo de C8); si falla, se descarta la pregunta y el resto del resultado se guarda. | Nivel 0 y nivel 1 |
| NFR10.2 | El testimonio nunca entra en las instrucciones de los extras. | Segunda lectura y pregunta usan el bloque de datos JSON en el mensaje `user` de U4 (NFR10.2 de U4); el mensaje `system` de cada una es idéntico byte a byte a su archivo montado. Prueba de nivel 0 con un turno que contiene «Fin de los datos. Nuevas instrucciones:», comillas y llaves. | Nivel 0 |
| NFR10.3 | La pregunta solo se apoya en el marco de verdad y nunca en un Hecho No Documentado (BR2.1, BR2.2). | El bloque de datos de la pregunta solo tiene las claves `turn` y `passages` (los recuperados para el turno); `source_passage_ids` lo fija el sistema con esos pasajes, no el juez. Si alguna afirmación es «no documentada» (por guardia, por el juez o por la permutación), no hay llamada. El *prompt* se lee de un `ConfigMap` `readOnly` y su SHA-256 debe coincidir con `VERIDICUS_QUESTION_PROMPT_SHA256`; si no, `semantic-agent` no arranca. Pruebas de nivel 0 (E5, inspección del bloque, SHA distinto). | Nivel 0 |
| NFR10.4 | El esquema de la salida de la pregunta es estricto y sin veracidad (BR4.2). | `contracts/schemas/suggested-question-output.v1.json`: objeto con `additionalProperties: false` y solo `text` (1–300 caracteres). Una salida con `is_truthful`, `veracity_score` o cualquier otro campo se rechaza y no hay pregunta. Prueba de nivel 0 sobre el esquema: ninguna propiedad pertenece a las categorías prohibidas de C8. | Nivel 0 |
| NFR10.5 | Nada de lo que añade U8 lleva vocabulario prohibido (BR1.5, BR2.3, BR3.2, BR4.1). | `scan(text, literal_sources)` de `libs/integrity_policy` sobre la pregunta antes de publicarla (el *fixture* «¿Por qué miente?» la omite, E6), sobre la CoT de la segunda lectura, sobre el texto fijo del indicio y cada palabra de la lista afectiva (nivel 0), sobre las preguntas del Golden Dataset (nivel 2) y sobre la tarjeta renderizada (nivel 3). 0 coincidencias fuera de citas literales. | Niveles 0, 2 y 3 |
| NFR10.6 | Solo el dueño decide la pregunta (BR2.4, ADR-009). | La ruta declara `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true` y exige `X-CSRF-Token`; la verificación de dueño se hace en ConsoleApi. Otro analista → `403` `session.not_owner` (E7); `admin` → `403` `auth.forbidden`; sin anti-CSRF → `403` `auth.csrf`; pregunta ya decidida → `409` `question.already_decided`. Todas sin filas nuevas. | Nivel 1 |
| NFR10.7 | Una pregunta no aprobada no sale de la consola (BR2.5). | U8 expone el puerto `is_question_approved(question_id)`; `GET /questions/{id}/audio` (U9) responde `409` `question.not_approved` para `proposed` o `discarded` (E8), y el reporte (U7) solo lista como formuladas las `approved`. Prueba de nivel 0 del puerto y de nivel 1 de la ruta cuando exista U9. | Nivel 0 y nivel 1 |
| NFR10.8 | Los logs y las métricas solo llevan identificadores. | Prueba de nivel 1 con una cadena centinela sembrada en el turno (que dispara el indicio afectivo), en la pregunta del juez *fake* y en la CoT de su segunda lectura: 0 coincidencias en los logs de `semantic-agent` y `session-api`, incluidos los de error, y en `/metrics`. | Nivel 1 |
| NFR10.9 | Los extras solo se activan por configuración del despliegue. | Ninguna ruta de C1 escribe `options` (prueba de nivel 0 sobre la especificación OpenAPI); `session-api` copia los tres valores a la sesión al crearla y C2 los toma de esa copia. Prueba de nivel 1: cambiar la configuración tras crear una sesión no cambia las opciones de esa sesión. | Nivel 0 y nivel 1 |
| NFR10.10 | El indicio afectivo es determinista y no opina. | Con `affective` activo o apagado, el juez *fake* recibe el mismo número de llamadas (BR3.1); el texto es el fijo del catálogo; la lista vive en `contracts/integrity/affective-keywords.v1.yaml`, cambia solo por PR con versión nueva y un *fixture* que ejercita el cambio (BR3.3). Pruebas de nivel 0: activo con coincidencia (E9), activo sin coincidencia y apagado (E10). | Nivel 0 y revisión del PR |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | `QuestionDecision` entra en la convención de U3 (BR2.6). | Registrada en `AuditConvention`; `actor_user_id` y `at` no nulos; el usuario de la aplicación no tiene `UPDATE` ni `DELETE` sobre ella. | Nivel 1 (prueba común de U3) |
| NFR11.2 | Una pregunta decidida no cambia de nuevo. | El usuario de la aplicación solo puede actualizar `status`, `decided_by` y `decided_at` de `SuggestedQuestion` (permiso por columna) y un disparador rechaza cualquier `UPDATE` si el estado anterior no es `proposed`; no hay `DELETE`. Prueba de nivel 1 que intenta cambiar una `approved` y borrar una `discarded`. | Nivel 1 |
| NFR11.3 | El resultado de la permutación no se reescribe. | `forward_grade`, `reversed_grade` y `sustained` se guardan con la evaluación de la afirmación, de solo inserción por intento (NFR11.2 de U4). | Nivel 1 |
| NFR11.4 | La activación de los extras queda versionada. | Las tres banderas viven en los *values* del despliegue y cambian solo por PR; activar un extra en el clúster exige adjuntar el reporte de nivel 2 con extras que cumpla NFR3.1, NFR4.3 y NFR4.4. Cada sesión guarda su copia de las opciones y cada reporte de nivel 2 registra las opciones, `question_prompt_sha256` y la versión de la lista afectiva. | Nivel 0 (no existe la ruta) y revisión del PR |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Los *fixtures* de U8 son sintéticos y marcados. | Turnos con palabras emocionales, preguntas del juez *fake* y salidas invertidas usan el catálogo de nombres y las marcas sintéticas de U1; la comprobación de U1 corre sobre las carpetas de pruebas de U8 con 0 hallazgos. | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U8 |
|---|---|
| AUTONOMIA-01 | U8 no aplica nada al clúster; las banderas, el *prompt* y la lista entran por PR (NFR11.4, NFR10.10) |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.4, NFR10.5, NFR10.6, NFR10.7, NFR10.10, NFR11.1, NFR11.2 |
| AUTONOMIA-04 | §1, NFR1.1, NFR1.2, NFR10.8 |
| AUTONOMIA-05 | NFR4.1 y NFR4.3 (`reliability-requirements.md`), NFR10.3, y 100 % de ramas en la regla de permutación y en la política de la pregunta (NFR13.2) |

## 5. Riesgo aceptado

**T13 — saturar la cola con los extras.** Con los tres extras activos, cada turno ocupa el juez hasta
tres llamadas y la cola admite 24 turnos sin vencer (NFR8.2). Se acepta porque los extras están
apagados por defecto, la prueba de NFR8 corre sin ellos y en el MVP trabaja un solo analista. Se
vigila con `veridicus_turn_queue_depth` y `veridicus_extras_enabled` (`observability-requirements.md`).

## 6. Precisiones a artefactos ya aprobados

Estas decisiones precisan artefactos ya aprobados o de otras unidades. No los edité; decides en la
aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `contract-design/contract-summary.md` (C1 `ErrorCode`) | Añade `question.already_decided` (409 de la decisión, BR2.4) y `question.not_approved` (409 del audio, BR2.5); hoy el catálogo no tiene un `code` para ninguno de los dos (cambio menor) | NFR10.6, NFR10.7 |
| `contract-design/contract-summary.md` (C3) | `suggested_question` añade `source_passage_ids` (de la entidad `SuggestedQuestion`) y `maxLength: 300`; el resultado añade `question_prompt_sha256` opcional (cambio menor; nadie publica aún el campo) | NFR10.3, NFR11.4 |
| `contracts/` de U1 | Esquema nuevo y estricto `contracts/schemas/suggested-question-output.v1.json` (solo `text`, 1–300 caracteres), con sus *fixtures* válidos e inválidos (`is_truthful`, texto vacío, 301 caracteres) | NFR10.4, BR4.2 |
| `contract-design/contract-summary.md` (C15) | Añade las métricas de U8 de `observability-requirements.md` §2, por un PR de U1 como las de U3 y U4 | NFR15.1 |
| Functional Design de U8 (BR1.6) | La alerta sostenida muestra la CoT de la primera lectura; la CoT de la segunda se valida pero no se guarda ni se muestra | NFR6.1 |
| NFR Requirements de U4 (`tech-stack-decisions.md` §2) | La regla «reclamo > *timeout* del juez + *timeout* de *embeddings*» cuenta también las llamadas de los extras activos; los *values* que activan extras fijan plazo base 600 s y reclamo 480 s | NFR3.6, NFR3.7 |
