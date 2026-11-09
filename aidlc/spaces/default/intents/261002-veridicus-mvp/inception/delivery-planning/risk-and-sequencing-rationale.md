# Razones del orden y riesgos — Veridicus (MVP)

**Revisión 2 (2026-11-09), segunda pasada por el cambio 01 (DT27) y la adenda 02.** Sustituye a la
revisión 1. Los riesgos R1–R9 conservan su número; los que el cambio vuelve obsoletos quedan «Retirado» y
los nuevos son R10–R13.

**Insumos.** Grafo de `inception/units-generation/unit-of-work-dependency.md`
(unit-of-work-dependency), unidades de `unit-of-work.md` (unit-of-work) y mapa de historias
`unit-of-work-story-map.md` (unit-of-work-story-map); requisitos y NFR de
`inception/requirements-analysis/requirements.md` (requirements); historias de
`inception/user-stories/stories.md` (stories); pantallas de `inception/refined-mockups/mockups.md`
(mockups); contratos de `inception/contract-design/contract-summary.md` (contract-summary); componentes
de `inception/domain-design/components.md` (components); prácticas de
`inception/practices-discovery/team-practices.md` y `team.md` (team-practices); cambio 01 en
`docs/iteracion2.md`; riesgos del PRD (S12); plan del curso (PRD S13); respuestas P1–P14 de
`delivery-planning-questions.md`.

## Heurística elegida

Un **Bolt** es una pasada de construcción sobre una unidad que termina en algo que corre y se puede
demostrar. El orden combina tres criterios, en este orden de prioridad, sin una tabla de puntos (P4 = A):

1. **Primera rebanada de valor para el TG** (`team.md`, DT27). Antes era «el flujo de texto primero»; el
   cambio 01 la superó (`project.md`). Ahora la primera rebanada es la biblioteca del analizador con su
   CLI, el anonimizador como módulo y un proveedor comercial: B1 → B10 → B11 (P10 = A). Se prueba sola,
   sin servicios ni clúster, y es lo primero que usa el Trabajo de Grado.
2. **Valor para la sustentación** (*value-first*). Después se completa lo que pide la demo de la sesión
   16 (PRD S13): acceso, flujo de texto, plataforma, revisión y reporte (B2 → B3 → B4 → B5 → B6). Siguen
   las MUST que no están en la demo: reportes del investigador (B12, sirve al TG), ciclo de vida (B7,
   robustez) y ética (B13, demostración) (P11 = A).
3. **Calendario del curso.** La plataforma (B4) sigue los módulos 6–7 (Redis, namespaces,
   `NetworkPolicy`, Secrets, anonimizador en el clúster) y deja Argo CD, la razón de descartes y KEDA para
   el módulo 8.

El **riesgo primero** (Boehm) queda cubierto por el primer criterio: los dos riesgos técnicos mayores
—que el analizador emita hallazgos sin evidencia y que un dato sin seudonimizar salga del clúster— se
prueban en B10 y B11, antes de construir servicios encima.

Se mantiene el descarte de **WSJF** (*Weighted Shortest Job First*: valor + urgencia + reducción de
riesgo, dividido por tamaño; Reinertsen, SAFe): con `team.md`, el grafo y la demo casi no quedan grados de
libertad.

## El orden respeta el grafo

Orden de unidades: U1 → U10 → U11 → U3 → U4 → U2 → U5 → U7 → U12 → U6 → U13 → (corte) → U8 → U9.

| Unidad | Depende de (`unit-of-work-dependency.md`) | ¿Llega después de todas? |
|---|---|---|
| U1 contracts | — | Sí (B1) |
| U10 anonymizer | U1 | Sí (B10, después de B1) |
| U11 incoherence-analyzer | U1, U10 | Sí (B11, después de B1 y B10) |
| U3 identity-access | U1 | Sí (B2) |
| U4 text-flow | U1, U3, U11 | Sí (B3, después de B1, B11 y B2) |
| U2 platform | U1 | Sí (B4) |
| U5 human-review | U4 | Sí (B5) |
| U7 forensic-report | U5 | Sí (B6) |
| U12 research-reports | U1, U3, U4 | Sí (B12) |
| U6 session-lifecycle | U4 | Sí (B7) |
| U13 ethics-governance | U4, U5, U7 | Sí (B13) |
| U8 assistant-extras | U4, U11 | Sí (B8) |
| U9 voice | U4, U8, U11 | Sí (B9) |

Es un orden topológico válido. **Desviaciones respecto del orden más temprano posible:**

- U3 y U2 podrían ir justo después de U1. U3 va después de U11 para que la primera rebanada de valor
  llegue antes; U2 va después de U4 porque los niveles 0–2 corren en contenedores sin clúster (regla
  aprendida «Plataforma justo después del flujo de texto», vigente).
- U12 podría ir justo después de U4; va después de U7 para no retrasar la demo (P11 = A).
- U6 podría ir antes de U5; va después porque la demo no la necesita.

**Cómo lo recorre Construction.** Construction recorre las unidades **etapa por etapa** (P8) y en serie,
según el grafo; este plan no cambia ese grafo. Si el flujo propone otro orden dentro de una etapa de
diseño, no afecta al orden de construcción, que es el que sigue el autor al implementar.

## Por qué cada Bolt va donde va

| Bolt | Argumento |
|---|---|
| B1 Contratos | Lo exige el grafo: todas las unidades consumen sus esquemas. Fija desde el principio el contrato común sin campos de veracidad y con los 5 campos obligatorios del hallazgo (AUTONOMIA-03, AUTONOMIA-05). |
| B10 Anonimizador | Lo exige el grafo antes de U11: ModelGateway no admite un destino externo sin él. Es MUST desde el cambio 01 (DT18) y contiene el módulo guardia del fallo cerrado (AUTONOMIA-04). |
| B11 Analizador | Primera rebanada de valor (`team.md`). Prueba la hipótesis central del producto —contradicciones internas con dos citas verificadas— con la propia CLI, sin infraestructura, antes de construir servicios. |
| B2 Acceso | Lo exige el grafo antes de U4 y U12: toda ruta exige token y rol. Deja la convención de auditoría que verifican las demás unidades. |
| B3 Flujo de texto | Envuelve la biblioteca en el trabajador de cola y la consola; es la base de la demo y de todas las unidades de pantalla. |
| B4 Plataforma | Sin ella no hay despliegue, prueba de humo, `NetworkPolicy` ni anonimizador en el clúster (AUTONOMIA-04). Encaja con los módulos 6–7. |
| B5 Revisión humana | Convierte los hallazgos en decisiones humanas (AUTONOMIA-03) y ataca el sesgo de automatización (PRD S12). Es requisito de B6. |
| B6 Reporte de revisión | Cierra la demo de la sustentación (consolidar y descargar) y la segunda guardia de AUTONOMIA-03. |
| B12 Reportes del investigador | MUST que sirve al TG: compara corridas de la CLI en la consola sin guardar testimonio. Va después de la demo (P11 = A). |
| B7 Ciclo de vida | Robustez (reanudar, importar, pegar, modo final, pausa y retirada del consentimiento) y la medición de NFR8; la demo no lo necesita. |
| B13 Ética | Demostración de la adenda 02 sin compuertas; cierra las MUST y es lo primero que se recorta (P13 = A). Sustituye el doble del puerto `AccessLog` de B6. |
| B8 Extras del asistente | SHOULD; la permutación duplica inferencias, así que se mide frente a NFR3 y NFR8 cuando las MUST ya son estables. |
| B9 Voz | SHOULD; depende de la aclaración aprobada (US10.4 → US10.3) y de que el texto ya funcione. |

## Riesgos y cómo los ataca el orden

| # | Riesgo | Probabilidad | Impacto | Bolt que lo ataca | Mitigación |
|---|---|---|---|---|---|
| R1 | El analizador no alcanza NFR4 sobre el conjunto sintético (precisión, sensibilidad o acuerdo entre 3 corridas) con el perfil de la primera rebanada | Media | Crítico | B11 | Evaluación de nivel 2 en la definición de terminado de B11; si falla, se ajustan *prompt*, perfil o modelo (con su PR y su reporte) antes de seguir. Los umbrales nunca se bajan. |
| R2 | Latencia por análisis o carga de CPU (PRD S12): la consola se bloquea o hay `OOMKilled` | Media | Alto | B3 (NFR3), B4 (`requests`/`limits`), B7 (NFR8), B8 (permutación) | Interfaz no bloqueante desde B3; límites desde B4; NFR8 medido en B7; costo de la permutación medido en B8 antes de activarla. |
| R3 | Juicio de veracidad o revictimización (PRD S12) | Alta | Crítico | B1 (esquema y vocabulario), B11 (escáner), B3, B5, B6 | Esquema sin campos de veracidad, escáner de vocabulario prohibido y máquinas de estado con 100 % de ramas desde los primeros Bolts (AUTONOMIA-03). |
| R4 | Alucinación: hallazgos sin evidencia o con citas inventadas | Media | Crítico | B11 | Verificación determinista de las dos citas en su turno con 100 % de ramas; `estado: error` con hallazgos vacíos; verificador de otra familia (AUTONOMIA-05). Sustituye a la guardia del umbral, retirada con el cambio 01. |
| R5 | Inyección de instrucciones en el testimonio (PRD S12) | Baja | Alto | B11 | NFR5 Escenario A en la evaluación de nivel 2 de B11, medido con una salida reconocible frente al desacuerdo entre 3 corridas (`project.md`); el bloque de datos va como JSON. |
| R6 | Fuga de datos fuera del clúster (PRD S12) | Media | Crítico | B10, B11, B4, B9 | Fallo cerrado y prueba del *payload* en B10 y desde ModelGateway en B11; `NetworkPolicy` con salida solo para `anonymizer-proxy` en B4; `audio-worker` entra en ella en B9. |
| R7 | Fuga de preferencias del juez (PRD S11 §3) | Media | Alto | B11 | Conjunto sintético generado por una familia distinta a la del juez y a la del verificador, declarado en su manifiesto y en el reporte (NFR5 Escenario B). Antes lo atacaba la tarea previa P0.2, ahora retirada. |
| R8 | B11 (U11, XL) es un solo PR grande que supera los 2 días de rama y retrasa todo | Alta | Alto | B11 | Aceptado a conciencia (P9 = B: un commit por Bolt, `org.md`). B1 y B10 van antes como PR más pequeños; el plan de tareas de U11 ordena el trabajo por capas para revisar por partes, y la rama se actualiza desde `main` a diario. B3 (U4) queda como segundo PR más grande. |
| R9 | El calendario del curso se queda corto para todas las MUST | Media | Alto | Corte de las MUST | Orden de recorte de P13 = A: B13 → partes SHOULD/COULD de B4 y B7 → alcance de B7; la demo queda completa en B6. Nunca se recortan pruebas. |
| R10 | Los datos reales del piloto acaban en el repositorio o en un reporte versionado | Baja | Crítico | B11, B12 | Los resultados sobre el piloto se escriben fuera de Git; el reporte de la CLI no admite texto (`pattern`, CD-03) y U12 lo rechaza con `422`; NFR12 y `project.md` (Forbidden). |
| R11 | Falta la clave de API o el costo del proveedor comercial se dispara | Media | Medio | B10, B11 | Niveles 0 y 1 con respuestas grabadas sin red; costo estimado por corrida en el registro de US12.5; dependencia D6 con seguimiento. |
| R12 | La seudonimización deja pasar un nombre o identificador que el NER no reconoce | Media | Crítico | B10 | Prueba del *payload* sobre el conjunto sintético con nombres sembrados; marcas consistentes y detección de marcas alteradas; 100 % de ramas. |
| R13 | La cola de ZINE no tiene cupo para las mediciones de modelos locales grandes | Media | Bajo | B11 | No bloquea: B11 entrega los `sbatch` como artefactos y mide en la máquina local; ZINE completa las cifras cuando haya cupo (D7). |

Retirado de la revisión 1: la versión de R1 sobre un juez de ≤ 8B con escenario y umbral, y la versión de
R4 sobre el Paquete de Contexto de Traspaso; ambas quedan sustituidas por las filas actuales con el mismo
número.

## Preguntas abiertas que afectan al orden

Ninguna cambia el orden, pero sí la definición de terminado de algún Bolt:

| Pregunta | Etapa que la cierra | Bolt afectado |
|---|---|---|
| Umbrales de precisión, sensibilidad y acuerdo; composición del conjunto sintético | NFR Requirements (segunda pasada) | B11 |
| Latencia por turno y por modo final, y *N* de la prueba de humo, con juez, verificador, anonimizador y red | NFR Requirements | B3, B4 |
| Si el fallo cerrado del anonimizador solo falla la corrida o también bloquea la sesión (UG-02) | Functional Design de U4 | B3 |
| Texto visible de `analysis.system` y `anonymizer.incident` (CD-08) | Functional Design | B3 |
| Proveedor comercial de la primera rebanada (US13.6) | Functional Design o NFR Requirements de U11 | B10, B11 |
| Servidor de cada modelo local; distribución de Kubernetes, CNI y namespaces | Infrastructure Design (segunda pasada) | B4, B9 |
| Tamaño máximo del audio en el mensaje (C5) | NFR Requirements | B9 |
