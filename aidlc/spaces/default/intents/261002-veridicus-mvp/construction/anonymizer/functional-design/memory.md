<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:52:08Z — Los embeddings externos también se enmascaran (BR1.4); como los pasajes del escenario pasan por el mismo enmascarado, la comparación por similitud conserva sentido.
- 2026-11-21T22:41:38Z — Segunda pasada (Modify) por el cambio 01, la adenda 02 y las revisiones 3. U10 pasa de adaptador COULD a módulo MUST (C20) más `anonymizer-proxy` (C21) con los adaptadores nativos y sus claves (C22, CD-04). Siguen P1 = A y las reglas en español de P2 = A. Salen la lista de nombres del escenario, `embed` (BR1.4), `turn.error.system` y BR3.2–BR3.4, que pasan a U11 y U2. Entran NER local, restauración con detección de marcas alteradas, lista de dominios (US11.5), resolución del perfil en el proxy, transporte *fake* y subpaquete de adaptadores. Las preguntas P3–P8 solo cubren lo que C13/C20–C22, FR11.3 y las historias no fijan: categorías y red de seguridad, identidad de la marca, coherencia entre llamadas (FR11.3 «por entrevista» frente a C20 «por llamada»), alcance de las marcas alteradas, registro de las llamadas fallidas con `InvalidOutput` en el proxy, y salida JSON por proveedor (pregunta abierta de C22).

- 2026-11-21T23:15:00Z — El mapa de historias cruza U10 con US13.3, US13.6, US9.1 y US11.6, así que el sensor exige sus 12 AC además de US11.3 y US11.5 (22 en total). Los que solo prueba otra unidad quedan Deferred con su dueño (U2, U4, U11) y el lado de U10 nombrado; AC11.3.8 queda Deferred porque detectar `anonymized: false` y bloquear la sesión es de U11 y U4 (ADR-013), aunque unit-of-work y B10 lo ponían en U10 (precisión FD-U10-16).
- 2026-11-21T23:15:00Z — El módulo es agnóstico de perfiles: en la CLI `req.destination` ya llega resuelto (C20) y en el proxy lo resuelve ProxyProfileCopy antes de llamar al mismo `generate`. Así la validación de perfiles queda en U11 para la CLI y en el proxy para el clúster, sin que U10 importe ExecutionProfiles.
- 2026-11-21T23:15:00Z — Si un mensaje es JSON, se seudonimizan sus valores de cadena ya decodificados: un nombre con su tilde serializada como secuencia de escape Unicode no lo vería el NER sobre el texto crudo y saldría del clúster (FD-U10-15).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:52:08Z — Ninguna desviación del texto de la etapa.
- 2026-11-21T23:15:00Z — La etapa pide diseño sin referencias de tecnología, pero P8 trata justo de la API de cada proveedor; se nombran operación y modo estructurado al nivel de la respuesta P8 y se deja a la prueba de contrato con respuestas grabadas fijar los nombres exactos de los parámetros.
- 2026-11-21T23:15:00Z — Se citaban reglas de U1 (BR9.4, BR9.8, BR9.9) y el sensor las tomó como reglas huérfanas de U10; se reemplazaron por descripciones (misma corrección aprendida en U4).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:52:08Z — Marcadores consistentes por llamada con restauración dentro del clúster (P1 = A): el juez externo puede razonar sobre quién y dónde, a costa de mantener una tabla en memoria que nunca debe registrarse.
- 2026-11-21T23:15:00Z — La red de seguridad no se aplica a los mensajes system: así los tipos de C6 («Fecha», «Persona») y el resto del prompt quedan legibles para el juez, a costa de confiar en que el prompt versionado no trae testimonio (FR4.6); el NER y las reglas sí lo recorren (FD-U10-02).
- 2026-11-21T23:15:00Z — Una forma de marca que el modelo escribe sin venir de la tabla invalida el hallazgo aunque fuera texto legítimo: se prefiere perder un hallazgo a restaurar mal una cita (P6 = A).
- 2026-11-21T23:15:00Z — Tabla versionada de capacidades por modelo en el subpaquete de adaptadores: el modo estructurado de Anthropic (esquema o herramienta forzada) se decide por datos revisables y no por prueba y error, a costa de un PR por cada modelo nuevo; además rechaza al arrancar herramienta forzada con esfuerzo, que el proveedor no admite (FD-U10-09).
- 2026-11-21T23:15:00Z — El adaptador nativo valida contra req.schema además del núcleo (FD-U10-10): cumple AC13.6.2 en el adaptador y deja la validación de C6 en U11, a costa de validar dos veces.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:52:08Z — Si un nombre propio sin patrón escapa del enmascarado, el riesgo residual queda para la decisión de usar o no un modelo externo.
- 2026-11-21T23:15:00Z — Riesgo residual de P3 = A: un nombre que abre oración, que el NER no reconoce y que no se repite a mitad de oración sale del clúster. La prueba de fuga cero (AC11.3.1) debe incluir nombres al inicio de turno; si el NER que elija NFR Requirements no los atrapa, la prueba falla y hay que decidir sin bajar el umbral.
- 2026-11-21T23:15:00Z — profile_sha256 lo calculan U11 y el proxy por separado con JCS; si divergen, todas las llamadas externas dan 409. Se propone que U1 publique la función (FD-U10-12); depende de la decisión del humano sobre las precisiones de U1.
- 2026-11-21T23:15:00Z — Las cifras nuevas de C25 (anonymizer_request_max_bytes y anonymizer_masking_budget_ratio, FD-U10-13) y el NER con su umbral quedan para NFR Requirements.
