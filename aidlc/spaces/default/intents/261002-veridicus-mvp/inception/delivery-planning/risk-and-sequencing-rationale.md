# Razones del orden y riesgos — Veridicus (MVP)

**Insumos.** Grafo de `inception/units-generation/unit-of-work-dependency.md`
(unit-of-work-dependency), unidades de `unit-of-work.md` (unit-of-work) y mapa de historias
`unit-of-work-story-map.md` (unit-of-work-story-map); requisitos y NFR de
`inception/requirements-analysis/requirements.md` (requirements); historias de
`inception/user-stories/stories.md` (stories); contratos y preguntas abiertas de
`inception/contract-design/contract-summary.md` (contract-summary); componentes de
`inception/domain-design/components.md` (components); prácticas de
`inception/practices-discovery/team-practices.md` (team-practices); riesgos del PRD (S12) y de
`docs/critica.md`; plan del curso (PRD S13); respuestas P1–P9 de `delivery-planning-questions.md`.

## Heurística elegida

Un **Bolt** es una pasada de construcción sobre una o varias unidades que termina en algo
demostrable. El orden de los Bolts combina tres criterios, en este orden de prioridad, sin una tabla
de puntos (P4 = A):

1. **Rebanada de punta a punta primero** (Cockburn, *walking skeleton first*, sin la ceremonia de
   esqueleto: `skeleton: off`). team-practices fija que la primera unidad del plan es el flujo de texto.
   Como el flujo depende de contratos y acceso, van antes en dos Bolts propios: un Bolt por unidad y un
   commit por Bolt (P1 = B, P9 = B; `org.md`). Contratos, acceso y flujo de texto forman la primera
   rebanada de punta a punta.
2. **Valor para la sustentación** (*value-first*). Tras la plataforma, se completa primero lo que pide
   la demo de la sesión 16 (PRD S13): revisar y consolidar (U5 → U7), y después lo que la hace
   robusta (U6) (P3).
3. **Calendario del curso.** La plataforma (U2) sigue los módulos 6–7 (Redis, namespaces,
   `NetworkPolicy`, Secrets) y deja sus partes SHOULD/COULD (Argo CD, AIR, KEDA) para el módulo 8
   (P2).

El **riesgo primero** (Boehm) queda cubierto por el primer criterio: el riesgo técnico mayor —que un
juez de ≤ 8B en CPU no alcance NFR4— se prueba en B3, antes de construir nada encima.

Se descartó **WSJF** (*Weighted Shortest Job First*: valor + urgencia + reducción de riesgo, dividido
por tamaño; Reinertsen, SAFe): con las reglas del equipo, el grafo y la demo, casi no quedan grados de
libertad, y una tabla de puntos añadiría precisión falsa.

## El orden respeta el grafo

Orden de unidades del plan: U1 → U3 → U4 → U2 → U5 → U7 → U6 → (corte) → U8 → U9 → (U10 condicional).

| Unidad | Depende de (`unit-of-work-dependency.md`) | ¿Llega después de todas? |
|---|---|---|
| U1 contracts | — | Sí (B1) |
| U3 identity-access | U1 | Sí (B2, después de B1) |
| U4 text-flow | U1, U3 | Sí (B3, después de B1 y B2) |
| U2 platform | U1 | Sí (B4) |
| U5 human-review | U4 | Sí (B5) |
| U7 forensic-report | U5 | Sí (B6) |
| U6 session-lifecycle | U4 | Sí (B7) |
| U8 assistant-extras | U4 | Sí (B8) |
| U9 voice | U4, U8 | Sí (B9) |
| U10 anonymizer | U4 | Sí (B10, condicional) |

Es un orden topológico válido. **Desviación respecto del orden más temprano posible:** U2 podría ir
justo después de U1 (solo depende de contratos). Se pone después de U4 a propósito: las pruebas de
niveles 0–2 de B3 corren en contenedores sin clúster, y así el flujo de texto prueba la hipótesis más
arriesgada sin esperar a la plataforma. U6 también podría ir antes de U5 y U7; va después porque la
demo no la necesita.

**Cómo lo recorre Construction.** Construction recorre las unidades **etapa por etapa** (P8) y en serie,
según el grafo; el plan de Bolts no cambia ese grafo. Si el flujo propone una unidad en un orden
distinto dentro de una etapa de diseño, no afecta al orden de construcción de este plan, que es el que
sigue el autor al implementar.

## Por qué cada Bolt va donde va

| Bolt | Argumento |
|---|---|
| B1 Contratos | Lo exige el grafo: todas las demás unidades consumen sus esquemas, colas y OpenAPI. Fija desde el principio las formas sin campos de veracidad y la alerta de 4 campos (AUTONOMIA-03, AUTONOMIA-05). |
| B2 Acceso | Lo exige el grafo: toda ruta exige token y rol. Deja la convención de auditoría que verifican las demás unidades. |
| B3 Flujo de texto | Regla del equipo; prueba la arquitectura completa (consola → API → cola → juez → `pgvector` → alerta con CoT) y la hipótesis de calidad de IA en CPU (NFR4, NFR5) antes de invertir en lo demás. Contiene las guardias de AUTONOMIA-05. |
| B4 Plataforma | Sin ella no hay despliegue, prueba de humo ni `NetworkPolicy` (AUTONOMIA-04, MUST). Encaja con los módulos 6–7 y valida que lo de B3 corre en el clúster dentro de sus límites. |
| B5 Revisión humana | Convierte las sugerencias en decisiones humanas (AUTONOMIA-03) y ataca el riesgo de sesgo de automatización (PRD S12, riesgo 2). Es requisito de B6. |
| B6 Reporte forense | Cierra la demo de la sustentación (consolidar y descargar) y la segunda guardia de AUTONOMIA-03. |
| B7 Ciclo de vida | Robustez (reanudar, pegar transcripciones, versiones de escenario) y la medición de NFR8; la demo no lo necesita, por eso va al final de las MUST. |
| B8 Extras del asistente | SHOULD; la permutación duplica inferencias en CPU, así que se mide frente a NFR3 y NFR8 cuando las MUST ya son estables. |
| B9 Voz | SHOULD; depende de la pregunta sugerida (US10.4 → US10.3) y de que el texto ya funcione (team-practices). |
| B10 Anonimizador | COULD condicional; no hay modelo externo decidido. |

## Riesgos y cómo los ataca el orden

| # | Riesgo | Probabilidad | Impacto | Bolt que lo ataca | Mitigación |
|---|---|---|---|---|---|
| R1 | El juez cuantizado en CPU no alcanza NFR4 (detección de 5 de 6 discrepancias, ≤ 1 alerta en las alineadas, 0 % de error de JSON) | Media | Crítico | B3 | Evaluación de nivel 2 en la definición de terminado de B3; si falla, se ajustan umbral, recuperación o modelo (NFR Requirements) antes de seguir. El perfil GPU queda como respaldo de evaluación, nunca como requisito (NFR2). |
| R2 | Latencia por turno o carga de CPU (PRD S12, riesgo 4): la consola se bloquea o hay `OOMKilled` | Media | Alto | B3 (NFR3), B4 (`requests`/`limits`), B7 (NFR8), B8 (permutación) | Interfaz no bloqueante desde B3; límites desde B4; NFR8 medido en B7; costo de la permutación medido en B8 antes de activarla. |
| R3 | Juicio de veracidad o revictimización (PRD S12, riesgo 6; `docs/critica.md` riesgo 1) | Alta | Crítico | B1 (esquema y vocabulario), B3 (escaneo), B5, B6 | Esquema sin campos de veracidad, escaneo de vocabulario prohibido y máquinas de estado con 100 % de ramas desde el primer Bolt (AUTONOMIA-03). |
| R4 | Alucinación cuando hay vacíos (`docs/critica.md` riesgo 4) | Media | Crítico | B3 | La guardia del umbral decide antes del juez y produce el Paquete de Contexto de Traspaso de forma determinista (AUTONOMIA-05). |
| R5 | Inyección de instrucciones en el testimonio (PRD S12, riesgo 7; `docs/critica.md` riesgo 2) | Baja | Alto | B3 | NFR5 Escenario A en la evaluación de nivel 2 de B3; *prompts* del sistema de solo lectura. |
| R6 | Fuga de datos fuera del clúster (PRD S12, riesgo 5) | Media | Crítico | B4, B9 | `NetworkPolicy` de salida denegada en B4 (estática y verificada a mano); `audio-worker` entra en ella en B9; sin modelo externo no hay U10. |
| R7 | Fuga de preferencias del juez (PRD S11 §3) | Media | Alto | Tareas previas, B3 | Golden Dataset generado por otra familia de modelos (P6) y declarado en el reporte (NFR5 Escenario B). |
| R8 | B3 (U4, XL) es un solo PR grande que supera los 2 días de rama y retrasa todo | Media | Alto | B3 | Aceptado a conciencia (P9 = B: un commit por Bolt, `org.md`). B1 y B2 van antes como PR pequeños; el plan de tareas de U4 ordena el trabajo por capas para que la revisión sea por partes, y la rama se actualiza desde `main` a diario. |
| R9 | El calendario del curso se queda corto para todas las MUST | Media | Alto | Corte de las MUST | Línea de corte antes de las SHOULD (P5); la demo queda completa en B6, así que B7 es lo primero que se recorta en alcance si falta tiempo, nunca sus pruebas. |

## Preguntas abiertas que afectan al orden

Vienen de `contract-summary.md` y `requirements.md`; ninguna cambia el orden, pero sí la definición
de terminado de algún Bolt:

| Pregunta | Etapa que la cierra | Bolt afectado |
|---|---|---|
| Umbral de similitud, modelo del juez y de *embeddings*, latencia por turno y *N* de la prueba de humo | NFR Requirements | B3, B4 |
| Plazo de evaluación por turno, *T* del latido, intervalo de sondeo y duración de la sesión web | NFR Requirements | B3, B5, B7 |
| Dimensión del vector y `top_k`; tamaño máximo de turno y de transcripción pegada | NFR Requirements, Functional Design | B3, B7 |
| Ventana *W* del AIR | NFR Requirements | B4 (parte SHOULD), B5 |
| Servidor de cada modelo y adaptador del TTS; distribución de Kubernetes, CNI y namespaces | Infrastructure Design | B4, B9 |
| Tamaño máximo del audio en el mensaje (C5) | NFR Requirements | B9 |
