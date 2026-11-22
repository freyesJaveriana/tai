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

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-22)

**Unidad.** U8 `assistant-extras` (tipo `service`, SHOULD, tamaño S; Bolt B8, después de la línea de
corte de las MUST). Según la revisión 3 de `unit-of-work.md`, entrega dos cosas: las **aclaraciones
neutras** (US10.3: la salida `observaciones_conductor` validada en la biblioteca, su guardado como
ConductorObservation y su presentación como «Aclaración sugerida · requiere tu decisión») y la
**confirmación en ambos órdenes** en producción (US10.5). **Salen** la pregunta sugerida que se apoyaba en
el Paquete de Contexto de Traspaso y el indicio afectivo (US11.1 Retirada; WON'T por DT15).

## Lo que ya está decidido y no se vuelve a preguntar

| Tema | Qué está decidido | Fuente |
|---|---|---|
| Forma de la aclaración | Solo `tipo: aclaracion_neutra`, un `tema` y los `turnos`; el esquema rechaza cualquier otro campo. Solo en modo incremental; con `estado: error`, `observaciones_conductor` va vacío | FR10.3 (DT23); AC10.3.1; C6 (`observaciones_conductor` y regla 7) |
| Neutralidad | El tema nunca menciona la contradicción, nunca dice «antes dijo» ni sus variantes y nunca cita un turno; nunca contiene el texto de ninguna de las dos citas (meta 0 %); la que no pasa no se muestra | VE-05; AC10.3.2; C8 `neutral-clarification.v1.yaml`; BR5.6 de U1 |
| Escaneo | `observaciones_conductor[].tema` entra en el escaneo de vocabulario prohibido | C8 `scanned`; US5.5 (mapa de historias: U8 aclaraciones) |
| Decisión humana | Se muestra como «Aclaración sugerida · requiere tu decisión» con «Aprobar» y «Descartar»; no se reproduce ni se registra como formulada sin la acción del analista; solo el dueño decide | AC10.3.3; mockups §6.11; C1 `/conductor-observations/{id}/decision` (`x-veridicus-owner-only`) |
| Audio | «Escuchar audio» solo tras aprobar y solo al pulsarlo; lo construye U9 (`409 conductor_observation.not_approved`) | AC10.4.1; C1 `/conductor-observations/{id}/audio`; unit-of-work U8 «Límites» |
| Dónde vive | La validación en la biblioteca de U11 sin cambiar su contrato; ConductorObservation es entidad de InterviewSession (`session-api`); U4 deja el punto de la ingesta para que U8 la añada | unit-of-work U8; components (InterviewSession, IncoherenceAnalyzer); FD de U4 §7; FD de U11 BR8.6 y FD-U11-03 |
| Qué se permuta | El verificador evalúa cada candidato con las dos citas en ambos órdenes y lo conserva solo si confirma en los dos | `docs/iteracion2.md` P12 = A; FR4.5; FR10.5 |
| Lógica de la permutación | Ya está diseñada en U11 y se construye en B11: llamada `verifier_permuted` después de la directa y siempre las dos, `rechazado_permutacion`, obligatoria en evaluación; «en producción, U8 decide sobre US10.5 sin cambiar esta lógica» | FD de U11 F4, BR6.1–BR6.3, BR2.9, FD-U11-06 |
| Interfaz de la permutación | US10.5 no tiene interfaz propia; el registro de llamadas de la corrida se ve en solo lectura (lo muestra U4) | mockups (tabla de historias: «US10.5 Sin interfaz propia»); AC12.5.3 |
| Casos de escaneo de aclaración | Los ejecuta la suite de U8, no la de U11 | FD de U11 BR9.4, FD-U11-20 |
| Auditoría y autorización | Convención de auditoría (tablas `history`) y mecanismo de dueño de F2 que entrega U3; la autorización se aplica en ConsoleApi | FD de U3 F2, F8 y §7; ADR-009 |
| Cifras | Latencia y costo de la segunda llamada frente a NFR3 y NFR8, umbrales de nivel 2 | NFR Requirements (project.md); bolt-plan B8 |
| Preguntas P1–P3 de la primera pasada | **Superadas.** P1 (qué se invierte) la sustituye P12 = A y F4 de U11; P2 («no documentada» al paquete) desaparece con el Hecho No Documentado; P3 (indicio afectivo) sale con US11.1 | Cambio 01; project.md § Corrections (el cambio 01 manda) |

## Cómo se registra la revisión 2

- Los cuatro artefactos (`entities.md`, `rules.md`, `functional-spec.md`, `traceability.json`) llevan una
  cabecera «Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02» que sustituye a la
  revisión 1 del 2026-10-02 y nombra qué sigue, qué sale y qué entra.
- **IDs estables** (regla de project.md): ningún ID se renumera. Lo que sale queda «Retirado» con su motivo:
  - Entidades: EvaluationOptions (sus banderas `suggest_question` y `affective`; la permutación es la del
    perfil de C18), ReadingOrder, PermutationOutcome, SuggestedQuestion, QuestionDecision y
    AffectiveKeywordList.
  - Reglas: BR1.1–BR1.6 (la segunda lectura del juez con pasajes; la sustituye F4 de U11), BR2.1–BR2.6
    (la pregunta sugerida), BR3.1–BR3.3 (el indicio afectivo) y BR4.3 en su texto actual.
  - Flujos F1–F3 y escenarios E1–E10.
- **Entra** lo nuevo con números nuevos: entidades ConductorObservation y ConductorObservationDecision;
  reglas desde **BR5.1** (aclaración) y **BR6.1** (permutación en producción); BR4.1, BR4.2 y BR4.4
  (vocabulario y accesibilidad) siguen y se reescriben para la aclaración; flujos desde **F4** y
  escenarios desde **E11**.
- `traceability.json`: los criterios asignados hoy son AC10.3.1–AC10.3.3, AC10.5.1 y los cruzados de
  US5.5 y US5.6. AC11.1.1 sale de `upstream_ids` (US11.1 Retirada) y las reglas retiradas van en
  `reverse` como `N/A` con «Retirado (cambio 01)», para que el sensor no las tome como huérfanas.
- Las precisiones a artefactos aprobados (contract-summary, components, FD de U4 y de U11) van a una tabla
  **FD-U8-01…** en `functional-spec.md`, sin editar los originales; decides en la aprobación.
- Los hallazgos R-01 a R-06 de `reviews/review-01.md`: R-01, R-02, R-03 y R-05 caducan (no hay segunda
  lectura del juez, ni pasajes, ni la pregunta con prompt propio); R-04 y R-06 se cierran con los puntos 6
  y 5 de la lista siguiente.

## Lo que el diseño resolverá sin preguntar

1. **US10.5 en producción.** U8 no toca la lógica de F4 de U11. Aporta: los valores de `permutation` en
   los perfiles que no son de evaluación (pregunta 5), la prueba de AC10.5.1 por el camino del producto
   (`semantic-agent` con un verificador *fake* que confirma en un solo orden: sin hallazgo, dos llamadas
   en el registro y `rechazado_permutacion`; sin permutación, una) y la medición del costo extra que pide
   B8, cuyas cifras fija NFR Requirements. Sin pantalla propia.
2. **Dónde se añade la aclaración.** Un módulo de dominio en `libs/incoherence_analyzer/`, después de la
   consolidación de los hallazgos (F5 de U11) y antes de validar la salida contra C6, solo en modo
   incremental y solo con `estado: ok`. Sustituye BR8.6 de U11 («la biblioteca no emite
   `observaciones_conductor`») por una precisión. Corre igual en la CLI y en el trabajador (AC2.2.7). No
   hace falta una bandera nueva en el perfil, porque C18 no la tiene y añadirla cambiaría el contrato.
3. **Validación, en este orden:** esquema (AC10.3.1), regla de VE-05 (BR5.6 de U1), ausencia del texto de
   las citas del hallazgo de origen (AC10.3.2: se compara con espacios normalizados y sin distinguir
   mayúsculas ni tildes; se rechaza también si el tema comparte 5 o más palabras seguidas con una de las
   citas; la cifra va a la tabla de precisiones) y escaneo de vocabulario. Es módulo guardia con 100 % de
   ramas y control negativo por regla. La que no pasa se quita de la salida sin afectar a los hallazgos, y
   se registra solo con `run_id` y el ID de la regla, nunca con el texto.
4. **Segunda línea en la ingesta (U4).** Si un `tema` llega inválido a `session-api`, se aplica la regla
   que ya existe (F3 de U1, R-09): la corrida entera queda en `analysis.invalid_output`. Así nada se quita
   en silencio y la ingesta no tiene una excepción. El atributo `discarded_by_rule` de ConductorObservation
   (components) no tiene uso: va como precisión retirarlo.
5. **Persistencia.** ConductorObservation (`observation_id`, `run_id`, `session_id`, `tema`, `turnos`,
   `status`) se guarda en la misma transacción de la ingesta. Se deduplica por (sesión, `turnos`, `tema`
   normalizado), y el reintento de una corrida no la duplica. El historial ConductorObservationDecision es
   una tabla `history` de la convención de U3; el estado y la fila del historial se escriben en la misma
   transacción, con prueba de nivel 1 (cierra R-06). `decided_by` y `decided_at` se derivan de la última
   fila del historial.
6. **Decisión y códigos.** `POST /conductor-observations/{id}/decision` exige ser el dueño (mecanismo de
   F2 de U3) y CSRF. Respuestas: `404 conductor_observation.not_found`,
   `409 conductor_observation.already_decided` y `409 conductor_observation.session_closed`. Van como
   precisión a C1, que hoy solo documenta 200 (cierra R-04).
7. **Estados.** `proposed → approved | discarded`, los dos finales. Aprobar exige que la sesión acepte
   turnos nuevos (no finalizada, ni terminada, ni con el consentimiento retirado, VE-10). Descartar se
   permite hasta finalizar. Las aclaraciones pendientes de una sesión cerrada quedan en solo lectura.
   Una sesión bloqueada por incidente sigue permitiendo decidir, igual que en U5.
8. **Consola.** Panel al pie de la columna derecha de M4 (mockups §6.11): rótulo, tema y turnos, nunca
   las citas; la aparición se anuncia en `aria-live="polite"` sin mover el foco; entra en la suite `axe`
   de U4 (US5.6), y sus cadenas pasan por el escaneo del catálogo de mensajes (US5.5). «Escuchar audio» es
   de U9.
9. **Frontera del clúster (AUTONOMIA-04).** Con la opción recomendada en la pregunta 4, la aclaración se
   arma dentro del proceso que ya tiene el hallazgo restaurado: no sale nada nuevo del clúster ni hay
   llamada nueva a un modelo. La tabla por componente queda en `functional-spec.md` §1.
10. **Casos de escaneo.** La suite de U8 ejecuta los casos de aclaración neutra de
    `scan-cases.v1.yaml` (E30 de U1 y los que publique U1), con control negativo (FD-U11-20).

---

## P4 — De dónde sale el tema de la aclaración

El contrato C6 ya fija la forma (`tipo`, `tema`, `turnos`), y el esquema del juez de U11 (BR3.4) no tiene
ningún campo para aclaraciones. Hay que decidir quién redacta el tema. Esto define si hay llamadas nuevas,
si cambia el prompt y si hay que repetir el nivel 2.

A. **Determinista, sin modelo.** Por cada hallazgo emitido en una corrida incremental, la biblioteca arma
   una aclaración con `tema` = el `hecho` del hallazgo y `turnos` = los turnos de sus dos citas. Pasa por
   la validación del punto 3, y si no pasa, se quita. Sin llamadas nuevas, sin cambio de prompt ni de
   contrato, y sin nada que restaurar del anonimizador. A cambio, el tema solo es tan neutro como el
   `hecho` que redacta el juez, y se pierden las aclaraciones de los hallazgos cuyo `hecho` describe la
   contradicción. (Recomendada)
B. **El juez en la misma llamada.** El esquema del juez suma un campo opcional `aclaracion {tema}` por
   candidato, que solo sale si su candidato sobrevive al filtro, al verificador y a la permutación. Los
   temas quedan mejor redactados, pero cambia el prompt único de juez y verificador (FD-U11-21): hay que
   repetir el nivel 2 y restaurar los marcadores del tema.
C. **Una llamada aparte con un papel nuevo** (p. ej. `conductor`) por hallazgo emitido. Aísla el prompt
   del juez, pero cambia el contrato (`papel` de C6, `role` de C13 y C21, validación del proxy) y suma
   llamadas y latencia.
D. **Sin aclaraciones generadas en el MVP.** Se construyen solo el esquema, la validación y la consola, y
   la biblioteca no emite ninguna.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Permutación en los perfiles que no son de evaluación

BR2.9 de U11 ya la exige en evaluación. En los perfiles `demonstration` y `production` (incluido
`todo-local`), el valor de `permutation` lo decide U8. Activarla duplica las llamadas al verificador, que
son cortas porque solo llevan `hecho`, `tipo` y las dos citas, a cambio de menos falsas alarmas. Las cifras
las mide NFR Requirements.

A. `permutation: true` en todos los perfiles del archivo, también en `todo-local`: el analista ve lo
   mismo que se mide en evaluación. Si NFR Requirements muestra que `todo-local` rompe la latencia en CPU,
   se apaga allí por PR. (Recomendada)
B. `true` en los perfiles con verificador comercial y `false` en `todo-local`, para no doblar la carga de
   la CPU.
C. Solo en evaluación. En demostración y producción queda apagada, y US10.5 se cumple como opción
   disponible y probada sin uso por defecto.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — Si la aclaración aprobada entra en el reporte consolidado

AC10.3.3 dice que la aclaración no se «registra como formulada» sin la acción del analista, pero ningún
insumo dice si el reporte de revisión (U7) la lista. Esta respuesta afecta a U7, que se diseña en
paralelo.

A. **No entra en el reporte.** Queda en la consola y en el historial auditado de la sesión (quién y
   cuándo). El reporte sigue siendo solo de las sugerencias de revisión, y U7 no cambia. (Recomendada)
B. **Entra la aprobada.** Una sección «Aclaraciones aprobadas» con tema, turnos, quién y cuándo, que pasa
   por el escaneo del reporte. Es una precisión a U7 y suma una prueba de su lado.
C. **Entran todas**, aprobadas y descartadas, con su decisión.
X. Other (please specify)

[Answer]: A **Mode:** guided
