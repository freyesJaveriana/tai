# Componentes lógicos — U4 text-flow

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; `functional-design/functional-spec.md` (functional-spec);
C1–C4, C6–C9, C13 y C14 de `inception/contract-design/contract-summary.md` (contract-summary); los
demás documentos de diseño de esta carpeta.

## 1. Inventario

| Componente lógico | Proceso | Responsabilidad | Patrones de NFR |
|---|---|---|---|
| Rutas de escenarios, sesiones y turnos | API de `session-api` | C1 de U4 | Autorización de U3; corte de carga a 1 MB; 202 sin esperar |
| `TurnEnqueuer` | API de `session-api` | Numerar, guardar y publicar C2 | Bloqueo de la sesión; `change_seq` |
| `SessionPoll` | API de `session-api` | `GET /sessions/{id}?since` | Cursor por sesión (P2 = A) |
| `ResultIngestor` | Trabajador de `session-api` | Consumir C3, validar C7, guardar | Idempotencia por (`turn_id`, `attempt`) |
| `ScenarioIndexer` | Trabajador de `session-api` | Consumir C4, segmentar, *embeddings* | Todo o nada |
| `DeadlineSweeper` | Trabajador de `session-api` | Vencer turnos cada 15 s | Ningún turno en curso para siempre |
| `TurnEvaluator` | `semantic-agent` | Consumir C2 y orquestar la evaluación | Un turno a la vez; `XACK` tras publicar |
| `ThresholdGuard`, `JudgeOutputValidation`, `AlertAssembly` | `semantic-agent/domain/` | Reglas AUTONOMIA-03/05 | Código puro, 100 % de ramas |
| `PromptBuilder` | `semantic-agent` | Instrucciones y datos JSON | Aislamiento del *prompt* |
| `ModelGateway` | `libs/model_gateway` | Juez, *embeddings*, `count_tokens` | URL internas; *timeouts*; reintento acotado del juez (P1 = A) |
| `IntegrityPolicy.scan` | `libs/integrity_policy` | Escáner C8 | 100 % de ramas |
| M2–M4 | `frontend` | Consola de texto | Sondeo 2 s / 15 s con reintento creciente |

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue | Radio |
|---|---|---|---|
| `model-judge` | Evaluación de afirmaciones sobre el umbral | Consola, carga, envío de turnos; afirmaciones bajo el umbral | Turnos en curso (esperan o vencen) |
| `model-embeddings` | Indexación y evaluación | Consola y revisión de alertas ya emitidas | Turnos y escenarios nuevos |
| `semantic-agent` | Evaluación | Todo lo demás | Turnos en curso (vuelven por reclamo) |
| Trabajador de `session-api` | Ingesta, indexación, plazos | API y consola | Resultados llegan al reiniciar |
| Redis | Encolar y entregar | Consultas de la consola | Turnos nuevos |
| PostgreSQL | Todo | — | Todo el sistema |

## 3. Recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| Proceso API de `session-api` | U3, U5–U7 | Capas e import-linter; nada pesado en la API |
| Base PostgreSQL | Todas las unidades | Esquema `truthframe` de solo lectura para el evaluador; permisos de solo inserción en historiales |
| Redis | U3 (limitador), U8, U9 | Prefijos `veridicus:turns`, `veridicus:results`, `veridicus:indexing`; *streams* vacíos tras procesar |
| `model-embeddings` | Indexador y evaluador | Lotes acotados de 32 |

## 4. Entrega a Infrastructure Design

- Topes de memoria medidos (performance-design §7) y `limits` con ≥ 20 % de margen.
- Dos `Deployment` de la imagen de `session-api` (API y trabajador) y uno de `semantic-agent`.
- `ConfigMap` del *prompt* montado `readOnly` y `VERIDICUS_JUDGE_PROMPT_SHA256` en los *values*.
- Puertos internos de métricas en API, trabajador y `semantic-agent`.

## 5. Calidad, pruebas y textos (NFR2.1, NFR2.2, NFR13.1, NFR13.2, NFR14.1, NFR14.2)

- **Dobles de prueba.** `ModelGateway` es un `Protocol` (C13); en los niveles 0 y 1 se inyectan
  `FakeJudge`, `FakeEmbeddings` y `FakeTokenizer` deterministas (tabla de respuestas por entrada), y
  PostgreSQL + `pgvector` y Redis son reales en contenedor. Ninguna prueba de esos niveles descarga un
  modelo ni pide GPU; las metas de NFR3.1, NFR3.10, NFR9.1 y NFR8.5 se miden con `values-cpu.yaml`.
- **Cobertura.** ≥ 80 % de líneas en `session-api`, `semantic-agent`, `libs/model_gateway`,
  `libs/integrity_policy` y `frontend`; 100 % de ramas en `threshold_guard.py`,
  `judge_output_validation.py`, `alert_assembly.py`, la validación de C7 al ingerir y
  `libs/integrity_policy/scanner.py`, con `.coveragerc-guards`.
- **Textos.** M2–M4 solo usan cadenas del catálogo de U1; una prueba de nivel 0 falla ante un literal
  visible fuera del catálogo. El reporte de nivel 2 marca toda CoT con menos de un 20 % de palabras
  vacías del español (meta: 0 marcadas).
