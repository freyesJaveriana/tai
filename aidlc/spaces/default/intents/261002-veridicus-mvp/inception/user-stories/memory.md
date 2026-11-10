<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T19:18:58Z — Las objeciones de diseño, desarrollo y calidad eran conocimiento (no disputas entre ellos) y se integraron sin ronda 2; los seis puntos de criterio (turnos en error, juez «no documentada» sobre umbral, accesibilidad, escaneo del texto del analista, cambiar decisión, escenario duplicado) se preguntaron al humano.
- 2026-10-02T18:57:49Z — Los hallazgos R-01 y R-03 a R-06 de la revisión de requisitos, aceptados como riesgo al aprobar, se cerraron aquí como preguntas 4 a 8 porque sin ellos no se podían escribir criterios de aceptación.
- 2026-11-02T21:11:25Z — Segunda pasada por Modify: las historias que siguen conservan su ID, las que salen quedan «Retirada» sin renumerar y las nuevas toman épicas 12–14, para no romper referencias de las etapas siguientes.
- 2026-11-02T21:22:41Z — Las objeciones de diseño, desarrollo y calidad de la segunda pasada eran de conocimiento y se integraron sin ronda 2; solo el plazo de la medición de la 4L (pregunta 15) y la ubicación de los .sbatch de validación (pregunta 16) se preguntaron al humano.
- 2026-11-02T22:18:25Z — R-02/R-05 se cerraron con un reporte por secciones M1–M6 y una comprobación `comprobar_reporte.py` con control negativo; AC14.1.7 nombra las seis cifras que deciden el diseño y tres decisiones posibles.


## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T18:57:49Z — No se editó `requirements.md` (ya aprobado); las decisiones que lo precisan quedaron en una tabla al inicio de `stories.md` para que el humano decida en la aprobación si se actualiza.
- 2026-11-02T21:11:25Z — La validación de modelos locales en ZINE (respuesta 14) entró como historia MUST US14.1 con criterios `[ZINE]` que registran cifras sin umbral, y como FR16.3 propuesto en la tabla de decisiones, sin editar requirements.md aprobado.
- 2026-11-02T21:22:41Z — US14.1 se reescribió para no depender del código del producto: la instalación sin internet se mide con una wheelhouse mínima y la de la CLI real pasó a AC14.2.5, porque la CLI se construye después del alto de Domain Design que US14.1 libera.
- 2026-11-02T22:18:25Z — Reapertura tras una aprobación involuntaria: el humano llevó la tabla de decisiones y FR16.3 a requirements.md aprobado (commit a6b60c2) y corrigió el orden de entrega de team.md (commit ddb549f), cada uno en su propio commit, en vez de dejarlos en la tabla.
- 2026-11-10T01:33:55Z — Tercera pasada (revalidación): el desfase venía de precisiones ya aprobadas en Domain Design (A-1..A-4) y Contract Design (CD-02, CD-04); solo se preguntó cómo registrar la revisión 3 (preguntas 17–19).
- 2026-11-10T01:47:08Z — Además del código CD-02 (pregunta 17), se corrigieron los criterios AC3.2.5, AC11.3.3, AC11.3.7, AC11.6.2 y AC13.3.1 y se añadió AC11.6.4, por objeciones de conocimiento de diseño, desarrollo y calidad sobre CD-04 (integradas sin ronda 2); ninguna historia cambió de enunciado.


## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T19:18:58Z — Se partió US4.1 (umbral) de US4.2 (paquete) ya en esta etapa, como pidió desarrollo, porque Units Generation dimensiona con historias y no con criterios.
- 2026-10-02T19:18:58Z — La «CoT interrumpida» del Hecho No Documentado la produce el sistema de forma determinista, sin llamar al LLM, porque la guardia decide antes que el juez.
- 2026-10-02T18:57:49Z — Los NFR de calidad (IA, MTTV, latencia, cobertura) quedan diferidos a NFR Requirements y Build and Test en vez de forzarlos como historias sin persona real (respuesta 3).
- 2026-11-02T21:11:25Z — El anonimizador (US11.3) conservó su ID en la épica 11 aunque sube a MUST, en vez de moverlo a una épica nueva: se prefirió la estabilidad de los ID sobre el orden por prioridad.
- 2026-11-02T21:11:25Z — La verificación de citas (US3.4) se separó de la presentación del hallazgo (US3.1), y el verificador (US3.5) del incremental (US3.6), para que Units Generation dimensione con historias pequeñas.
- 2026-11-02T21:22:41Z — La inyección del Escenario A se mide con una salida reconocible y frente al desacuerdo entre 3 corridas, en vez de exigir el mismo conjunto de hallazgos, porque los modelos comerciales no son deterministas.
- 2026-11-10T01:33:55Z — Se ratificó en bloque como revisión 3 y solo se sustituyó el código `anonimizador_no_disponible` en cuatro criterios, en vez de reescribir historias: la adenda 02 sigue aparte y la trazabilidad no cambia de ID.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T19:18:58Z — Pendientes para NFR Requirements: plazo T del latido de reanudación, timeout de evaluación por turno, rango válido del umbral, ventana y definición de «ignorada» del AIR, duración de la sesión web.
- 2026-11-02T21:11:25Z — Corregir el orden de entrega de team.md (Walking Skeleton) por la respuesta 10: decide el humano en la aprobación y va en su propio commit.
