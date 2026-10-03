# Decisiones de pila — U8 assistant-extras

**Insumos.** Flujos F1–F3 de `functional-design/functional-spec.md` (functional-spec) y reglas BR1–BR4
de `functional-design/rules.md` (rules); NFR2, NFR4, NFR13 y NFR14 de
`inception/requirements-analysis/requirements.md` (requirements); C2, C3, C6, C8, C13 y C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 de
`nfr-requirements-questions.md`; `security-requirements.md`; las decisiones de pila de U4 (juez,
servidor, semilla, bloque de datos, validación con `jsonschema`, `httpx`, TanStack Query) y de U3.

Lo que ya fijan `team.md`, U2, U3 y U4 no se repite. U8 **no añade dependencias nuevas**: usa las de
`semantic-agent`, `session-api`, `libs/model_gateway`, `libs/integrity_policy` y `frontend` de U4.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Modelo y servidor de los extras | El mismo juez de U4 (Qwen2.5-7B-Instruct Q4_K_M en `llama-server`, una ranura, ventana 12 288, temperatura 0, `VERIDICUS_JUDGE_SEED`) para la segunda lectura y la pregunta | Un modelo más pequeño para la pregunta (Qwen2.5-3B); una segunda ranura (`--parallel 2`) | Otro modelo suma memoria y un servidor; una segunda ranura rompe la repetibilidad (NFR4.2 de U4) y reparte la ventana | NFR3.4, NFR4.5, NFR5.2, NFR8.3 |
| D2 | Segunda lectura | Una sola llamada con todas las candidatas (functional-spec F1), armada con el constructor de *prompt* de U4 y su parámetro de orden (NFR4.5 de U4): pasajes por similitud ascendente y afirmación antes de los pasajes; mismo prompt del sistema; validada con C6 y el mismo validador de U4 | Una llamada por afirmación; reutilizar la primera salida reordenada | Menos latencia en CPU y un solo validador; una afirmación mal formada invalida el turno, como pide FR4.2 | NFR3.3, NFR3.4, NFR10.12 |
| D3 | Regla de permutación | Función pura en `services/semantic-agent/.../domain/permutation.py` que recibe guardia y calificaciones y devuelve `PermutationOutcome`; sin E/S | Lógica dentro del adaptador del juez | Código puro de AUTONOMIA-05 en `domain/` (team.md), probado por propiedades y con 100 % de ramas | NFR4.1, NFR13.2 |
| D4 | *Prompt* de la pregunta | Archivo propio `prompts/suggest-question.v1.md` (≤ 600 *tokens*, pide una sola pregunta en español, abierta, basada solo en los pasajes y sin juicios sobre la persona) en un `ConfigMap` montado `readOnly`, con `VERIDICUS_QUESTION_PROMPT_SHA256` | Añadir la pregunta a la salida de la primera lectura (cambiaría C6, que es estricto) | C6 no cambia; el *prompt* es configuración inmutable como el de U4 | NFR3.5, NFR10.3 |
| D5 | Salida de la pregunta | JSON con solo `text`, validado con `jsonschema` contra `suggested-question-output.v1.json`; se pide con `response_format` de esquema JSON al servidor, pero manda la validación propia; `max_tokens = 160`; *timeout* 60 s | Texto libre sin esquema; Pydantic a mano | Esquema estricto en `contracts/` y un solo origen con U1 (BR4.2) | NFR3.5, NFR10.4, NFR10.13 |
| D6 | Política de la pregunta | Función pura `domain/question_policy.py`: decide si se pide (BR2.1), valida longitud y esquema y aplica el escáner (BR2.3, BR4.1); devuelve la pregunta o el motivo de omisión | Decidir en la capa de aplicación | Guardia de AUTONOMIA-03 y 05 en `domain/` con 100 % de ramas | NFR10.3–NFR10.5, NFR13.2 |
| D7 | Indicio afectivo | Lista `contracts/integrity/affective-keywords.v1.yaml` cargada al arrancar y normalizada con las funciones de C8 de `libs/integrity_policy` (palabra completa, sin mayúsculas ni tildes); una expresión regular compilada con la alternancia de la lista; texto fijo en el catálogo de mensajes de U1 | Clasificador con LLM (P3 de Functional Design); lematizador (spaCy) | Determinista y auditable, sin modelo extra ni descarga en ejecución | NFR3.11, NFR10.10 |
| D8 | Activación | Tres banderas en los *values* de `session-api` (`false` en `values-cpu.yaml` y `values-gpu.yaml`); se copian a la sesión al crearla y viajan en `options` de C2 | Ajuste en la consola; banderas en `semantic-agent` | La consola no las cambia (entities) y cada sesión conserva sus opciones (NFR10.9) | NFR10.9, NFR11.4 |
| D9 | Decisión del analista | Transacción con `UPDATE … WHERE status = 'proposed'` + `INSERT` en `question_decision`; permiso por columna y disparador que rechaza cambios fuera de `proposed`; migración en su propio `Job` y PR (team.md) | Bloqueo optimista con versión; tabla de estado mutable sin historial | Atómico, sin estado en memoria y con historial de solo inserción | NFR8.4, NFR10.15, NFR11.1, NFR11.2 |
| D10 | Corrida de nivel 2 con extras | El arnés de U4 con `--extras all` levanta sus contenedores locales con las tres banderas en `true`; nunca toca el clúster | Activar los extras en el clúster para medir | P1 = A; AUTONOMIA-01 | NFR3.1, NFR4.3–NFR4.5 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `VERIDICUS_EXTRAS_PERMUTATION`, `VERIDICUS_EXTRAS_SUGGEST_QUESTION`, `VERIDICUS_EXTRAS_AFFECTIVE` | `false` (en los *values*, sin valor en el código) | Obligatorias; solo `true` o `false` | `session-api` |
| `VERIDICUS_QUESTION_PROMPT_SHA256` | — | Obligatorio; 64 hexadecimales; igual al del archivo montado | `semantic-agent` |
| `VERIDICUS_QUESTION_TIMEOUT_SECONDS` | 60 | Entero entre 10 y el *timeout* del juez | `semantic-agent`, `session-api` |
| `VERIDICUS_QUESTION_MAX_TOKENS` | 160 | Entero entre 100 y 400 | `semantic-agent` |
| `VERIDICUS_AFFECTIVE_KEYWORDS_PATH` | `/etc/veridicus/contracts/integrity/affective-keywords.v1.yaml` | Archivo legible, `schema_version` conocida, sin términos de C8 | `semantic-agent` |
| `VERIDICUS_TURN_DEADLINE_BASE_SECONDS`, `VERIDICUS_QUEUE_RECLAIM_IDLE_SECONDS` (de U4) | 300 y 240; **600 y 480** en los *values* que activan extras | Con extras: ambos > suma de NFR3.6 y reclamo < plazo base | `session-api` (y reclamo en ambos) |

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR2.1 | Todo U8 se prueba en CPU sin modelos reales en los niveles 0 y 1. | El juez *fake* de U4 se amplía para responder a la segunda lectura (con el orden recibido registrado, BR1.1) y a la pregunta; ninguna prueba de los niveles 0 y 1 descarga un modelo ni exige GPU. |
| NFR2.2 | Los extras funcionan en el perfil CPU. | NFR3.1, NFR4.3 y NFR4.4 se miden con `values-cpu.yaml` más las banderas de la corrida con extras; el perfil GPU es opcional. |
| NFR13.1 | Cobertura de líneas. | ≥ 80 % en `services/semantic-agent`, `services/session-api` y `frontend` con el código de U8 incluido, medido en la CI y bloqueante. |
| NFR13.2 | 100 % de ramas en los módulos guardia de U8. | `services/semantic-agent/.../domain/permutation.py` (BR1.1–BR1.6), `domain/question_policy.py` (BR2.1–BR2.3, BR4.1, BR4.2) y `services/session-api/.../domain/question_decision.py` (BR2.4, máquina de estados de la pregunta): `--cov-branch` con `fail_under = 100`, añadidos a `.coveragerc-guards`. |
| NFR14.1 | Textos visibles en español y del catálogo. | «Pregunta sugerida · requiere tu aprobación», «Aprobar», «Descartar», los mensajes de `question.already_decided` y `question.not_approved` y el texto fijo del indicio salen del catálogo de U1; la prueba de literales de U4 cubre los componentes de U8; identificadores del glosario (`suggested_question`, `affective_note`, `permutation_outcome`). |
| NFR14.2 | La pregunta está en español. | El *prompt* lo exige; el reporte de nivel 2 marca toda pregunta con menos de un 20 % de palabras vacías del español o sin signos «¿…?», y la meta es 0 marcadas. |

## 4. Trabajo en otras unidades que U8 necesita

- U1: el esquema `suggested-question-output.v1.json`, la lista afectiva, los `code` nuevos y las
  métricas en C15 (`security-requirements.md` §6).
- U4: el parámetro de orden del constructor de *prompt* (NFR4.5 de U4) y el juez *fake* ampliable.
- U2: montar el `ConfigMap` del *prompt* de la pregunta y el de la lista afectiva en `semantic-agent`.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y guardias (nivel 0) | `uv run --directory services/semantic-agent pytest -m "not integration and not perf"` y lo mismo en `services/session-api` | Verde |
| Ramas de los módulos guardia | `uv run --directory services/semantic-agent pytest --cov-branch --cov-config=.coveragerc-guards` y lo mismo en `services/session-api` | 100 % (NFR13.2) |
| Integración (nivel 1) | `uv run --directory services/session-api pytest -m integration -k "question or extras"` y `uv run --directory services/semantic-agent pytest -m integration -k extras` | Verde |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf -k question` y `uv run --directory services/semantic-agent pytest -m perf -k affective` | NFR3.8, NFR3.9, NFR3.11 |
| Consola | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas |
| Evaluación con extras (nivel 2, fuera de la CI) | `uv run --directory evaluation python -m golden.run --profile cpu --extras all --report out/level2-extras.json` | NFR3.1, NFR4.3–NFR4.5, NFR5.1, NFR5.2, NFR8.3, NFR8.7, NFR14.2 |
| Carga con extras apagados (a demanda) | `uv run --directory evaluation python -m load.run_batches --sessions 50 --concurrency 3 --report out/nfr8.json` | NFR8.1 y NFR8.5 de U4 |
| Humo (nivel 3) | `scripts/smoke.sh <url-base>` | Código 0 en ≤ 120 s por caso con extras apagados (NFR3.12) |
| E2E de la tarjeta (nivel 3) | `npx --prefix frontend playwright test e2e/suggested-question.spec.ts` | NFR3.10, BR4.4, NFR10.5 |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en cada servicio | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El *prompt* de la pregunta desplaza de la caché de la única ranura las instrucciones del juez, y el siguiente turno vuelve a procesarlas | La pregunta es la última llamada del turno y su coste está dentro del p95 de 150 s medido; si no alcanza, es un hallazgo que se resuelve por PR (p. ej. guardar y restaurar la ranura), nunca subiendo la meta |
| La permutación baja la detección por debajo de 5 de 6 | NFR4.3 lo detecta en la corrida con extras; el extra sigue apagado y la detección por defecto no cambia |
| El juez sigue generando preguntas con vocabulario prohibido | Se omiten (BR2.3); la métrica por motivo lo hace visible y el *prompt* se corrige por PR |
| La lista afectiva marca demasiado o muy poco | Es COULD y sin meta numérica (FR11.1); cada cambio entra por PR con su *fixture* |
