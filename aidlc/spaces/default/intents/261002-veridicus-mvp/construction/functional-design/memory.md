<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->


- 2026-10-02T23:01:33Z — En una unidad de tipo spec, las «entidades» son los documentos de contrato y los datos que describen; U1 no tiene comportamiento en ejecución, así que functional-spec.md documenta los flujos de validación y de cambio de contrato (F1–F6) en lugar de casos de uso.
<!-- aidlc-wave-memory:contracts:1d2d99084b5f7063fee0550367061f29902b966a885d795dd2d10c3c7f0cecc0 -->


- 2026-10-02T23:08:41Z — La comprobación de «sesiones pendientes» del cambio de rol (P3) va en ConsoleApi y no en IdentityAccess, con el mismo criterio de ADR-009, para no crear dependencia de IdentityAccess hacia InterviewSession; hasta que U4 cree la tabla de sesiones, el puerto devuelve 0.
<!-- aidlc-wave-memory:identity-access:00c77cd8270985915081f85dc5c216cc4ac922dc2b124fbd0fc6e1ee11b47c01 -->


- 2026-10-02T23:28:41Z — El Paquete de Contexto de Traspaso es uno por intento de turno (C3 trae un solo handoff_package): su fragmento es el texto del turno, con la lista de afirmaciones no documentadas y los 3 pasajes distintos más cercanos de esas afirmaciones.
<!-- aidlc-wave-memory:text-flow:0a916484fdfc8e615a5a9fceae2614b04d81f51151e020653ea36cbafdf9f107 -->


- 2026-10-02T23:52:08Z — La herencia de decisiones entre rondas que ADR-007 dejó a esta etapa se fijó como «estado vigente»: la última decisión de la ronda o, si no hay, el estado vigente en la ronda bloqueada de la que parte la corrección.
<!-- aidlc-wave-memory:human-review:c29a8fc4e78b6151c226a8a290af5b52e64d7c309fafbb0101efde32f47f3488 -->


- 2026-10-02T23:52:08Z — Las líneas del entrevistador se guardan como turnos de contexto (role interviewer) que no se evalúan pero sí cuentan como turnos previos del paquete (P2 = A).
<!-- aidlc-wave-memory:session-lifecycle:fbac41d695ca9012be0d16461658be618180602d6959ecc77337431da8a7a207 -->


- 2026-10-02T23:52:08Z — Una afirmación cuyas dos lecturas no coinciden queda «no documentada» y va al paquete (P2 = A), así el analista ve la discrepancia en vez de perderla.
<!-- aidlc-wave-memory:assistant-extras:e31761fff254d142a9079713599e84cb529d0167d025d57dc2dca302435836d4 -->


- 2026-10-02T23:52:08Z — Los embeddings externos también se enmascaran (BR1.4); como los pasajes del escenario pasan por el mismo enmascarado, la comparación por similitud conserva sentido.
<!-- aidlc-wave-memory:anonymizer:da04c01a88730d9533dc743a8a1865602843c40ce499dc171304e6ba7b5e69d3 -->


- 2026-10-03T00:09:14Z — Finalizar desde `suspended` se permite (U6 lo dejó a U7): una sesión suspendida y abandonada se podría cerrar sin reanudarla.
<!-- aidlc-wave-memory:forensic-report:cd982d4c1345fb748bc2ebb6118644f0308f980dc9ed8dc4a3f50e4b7bbd36fe -->


- 2026-10-03T00:09:14Z — AC6.2.2 se cubre con un code nuevo `report.not_consolidated`, porque la descarga va por versión y no existe versión antes de consolidar.
<!-- aidlc-wave-memory:forensic-report:6d1310aa4fb28551444639ea0ec2201a381082c341d9c8551b96bc0c114210cd -->


- 2026-10-03T00:21:01Z — La consola codifica a WAV mono de 16 kHz porque el navegador graba en su formato nativo y el contrato solo admite WAV o MP3.
<!-- aidlc-wave-memory:voice:d90eaa1d8643277289d67b1f108e384af03dfcf5c4540b9527ab7be70752ce95 -->


- 2026-11-09T21:39:32Z — V-1 = A: el papel es texto con patrón en C13, C19 (registro) y C21; un perfil genérico (papeles, alias, un fallback) que el analizador especializa con exactamente judge y verifier; C6 no cambia y una tabla fija traduce los tres papeles del analizador.
<!-- aidlc-wave-memory:contracts:9b217c5ad8d8b17d00156c8432f032424e8434638ff1c7333f7d28601746d962 -->


- 2026-11-09T22:43:59Z — P9 = A: U1 publica tres funciones puras (profiles.validate, limits.load, registry) para que U10, U11 y sistema no reimplementen la validación; FD-U1-10 enmienda el «sin lógica» de unit-of-work.
<!-- aidlc-wave-memory:contracts:a609342ef41375884905af5d614aafdd2bc07f02dba4dec93eaaa517f7d6a346 -->


- 2026-11-21T22:15:00Z — Tercera pasada (revalidación): de las revisiones 3 de Inception solo tocan a U1 el `Protocol` `AnonymizingProvider` en `model_calls` (C13, R-14) y el código `session.blocked` (CD-11); se registró como revisión 3 con BR9.9, sin cambiar otras entidades, reglas ni flujos (pregunta 12 = A).
<!-- aidlc-wave-memory:contracts:91be35c4dc088b73447e530c0c2cff08a0e431c4513f5965d34c6b75e1af651d -->


- 2026-11-21T22:41:38Z — Segunda pasada (Modify) por el cambio 01, la adenda 02 y las revisiones 3. U10 pasa de adaptador COULD a módulo MUST (C20) más `anonymizer-proxy` (C21) con los adaptadores nativos y sus claves (C22, CD-04). Siguen P1 = A y las reglas en español de P2 = A. Salen la lista de nombres del escenario, `embed` (BR1.4), `turn.error.system` y BR3.2–BR3.4, que pasan a U11 y U2. Entran NER local, restauración con detección de marcas alteradas, lista de dominios (US11.5), resolución del perfil en el proxy, transporte *fake* y subpaquete de adaptadores. Las preguntas P3–P8 solo cubren lo que C13/C20–C22, FR11.3 y las historias no fijan: categorías y red de seguridad, identidad de la marca, coherencia entre llamadas (FR11.3 «por entrevista» frente a C20 «por llamada»), alcance de las marcas alteradas, registro de las llamadas fallidas con `InvalidOutput` en el proxy, y salida JSON por proveedor (pregunta abierta de C22).
<!-- aidlc-wave-memory:anonymizer:2a31cdd340fb3c24f6d89c2c34180204a0042461ed9d76b792a0e5cff466e22f -->


- 2026-11-21T23:15:00Z — El mapa de historias cruza U10 con US13.3, US13.6, US9.1 y US11.6, así que el sensor exige sus 12 AC además de US11.3 y US11.5 (22 en total). Los que solo prueba otra unidad quedan Deferred con su dueño (U2, U4, U11) y el lado de U10 nombrado; AC11.3.8 queda Deferred porque detectar `anonymized: false` y bloquear la sesión es de U11 y U4 (ADR-013), aunque unit-of-work y B10 lo ponían en U10 (precisión FD-U10-16).
<!-- aidlc-wave-memory:anonymizer:2e046bd030908a6ea569c1cfad55fe6e21e2da28021a91d17229c0f852f4b2ba -->


- 2026-11-21T23:15:00Z — El módulo es agnóstico de perfiles: en la CLI `req.destination` ya llega resuelto (C20) y en el proxy lo resuelve ProxyProfileCopy antes de llamar al mismo `generate`. Así la validación de perfiles queda en U11 para la CLI y en el proxy para el clúster, sin que U10 importe ExecutionProfiles.
<!-- aidlc-wave-memory:anonymizer:7c5541599e787b2c2edecc42205814749323f252c583f72742ca2a602a11dfe4 -->


- 2026-11-21T23:15:00Z — Si un mensaje es JSON, se seudonimizan sus valores de cadena ya decodificados: un nombre con su tilde serializada como secuencia de escape Unicode no lo vería el NER sobre el texto crudo y saldría del clúster (FD-U10-15).
<!-- aidlc-wave-memory:anonymizer:0234a5458875122e1868fc2ae18cb7d747a7097743091029666390e7c81c4cdf -->


- 2026-11-21T22:45:12Z — Segunda pasada (Modify) de U3 por el cambio 01, la adenda 02 y las revisiones 3. Siguen BR1–BR4, BR6 y BR7 (autenticación, gestión de usuarios, primer admin, matriz, auditoría, accesibilidad) con P1–P3 = A. Cambian BR5 y F9, que pasan del umbral a la configuración por PR (perfiles, proveedores, prompts, precios y límites, AC8.3.x). Quedan «Retirado» las acciones upload_scenario y apply_threshold_change. Entran el rol investigador (destino M8), las extensiones owner-only-for-role y demo de C1, el manejador de Problem Details, el consumo de C23 y el usuario de retención de A-2 en la convención. Las precisiones user.* de la revisión 1 siguen pendientes, porque C1 v2 pone validation.invalid_request. Pregunté solo los cinco puntos de criterio (P4–P8): VE-09 frente a FR1.2, el registro de acceso y su fallo, el actor sistema (R-02), el usuario de retención y las sesiones pendientes con desactivación (R-03).
<!-- aidlc-wave-memory:identity-access:e1a8cb70fbc723b3e9f33611af945632c3deb86b69c97b0516e0c49fce6f4c51 -->


- 2026-11-21T23:10:30Z — Revisión 2 escrita con P4–P8 = A: 51 reglas (BR1.1–BR9.5, ninguna retirada) y 43 escenarios (E1–E43). La tabla de precisiones conserva el número §10 de la revisión 1 para no romper referencias, y va de FD-U3-01 a FD-U3-13.
<!-- aidlc-wave-memory:identity-access:d428ffe3b61b56c180307b40c47e5068a2a9f8f6783e6a740555054d3ae60c3e -->


- 2026-11-21T23:10:30Z — R-01: la marca de la convención es una sola, en el comentario de la tabla (`veridicus-audit`), y la llevan todas las tablas, no solo los historiales (kind history | mutable). Así la prueba común detecta una tabla sin registrar sin necesitar un sufijo ni una lista paralela.
<!-- aidlc-wave-memory:identity-access:5787b50f8e08245502ed28974ebaa0bcd45285c792dcab1ab3cd5f8001685028 -->


- 2026-11-21T23:10:30Z — R-08: en vez de renombrar las columnas de actor y hora de las otras unidades (consolidated_by, exported_at…), la marca declara cuáles son; ADR-003 «actor/at» se lee como columnas lógicas (FD-U3-07).
<!-- aidlc-wave-memory:identity-access:4bee20f53c235a6ba1197242689d11c1c3418dcca191079ff8abce2ae1a7cdb5 -->


- 2026-11-21T23:10:30Z — Registro de acceso: un sondeo con `since` no es una apertura y no se registra (BR9.4); la apertura de un hallazgo es el POST de observation-views. Ninguna de las dos cosas la decía P5; quedaron como propuesta en FD-U3-05.
<!-- aidlc-wave-memory:identity-access:1fd3d91cc758fa4b06f4e947c04819ed91c3e464ff1675952008e1e9eb1bdfe0 -->


- 2026-11-21T23:10:30Z — Los `code` `user.weak_password` y `auth.too_many_attempts` vienen de NFR Requirements de U3, y `system.internal` y `system.unavailable` del manejador; todos quedan como propuesta a C1 (FD-U3-02, FD-U3-03).
<!-- aidlc-wave-memory:identity-access:bf2eb8ddb3d08c04a088a80498c800df2305eae330e0618a66bb42c406ed02a6 -->


- 2026-11-21T23:42:00Z — Alcance de U11 leído como la biblioteca completa del analizador (núcleo C17, ModelGateway con adaptador local y cliente HTTP de C21, ExecutionProfiles, escáner y aviso de IntegrityPolicy), la CLI con `analyze` y `evaluate`, el conjunto sintético con su manifiesto y los `.sbatch` de ZINE. Quedan fuera las colas y sesiones (U4), la seudonimización y los adaptadores nativos (U10) y las aclaraciones neutras (U8). Solo se preguntan 8 decisiones de criterio que las fuentes no fijan o en las que se contradicen: orden de filtros, contexto del verificador, vocabulario prohibido (AC3.2.4 frente al motivo de C6), permutación en B11 frente a US10.5 en U8, alterno y familias, métricas de las 3 corridas, etiquetas de sesgo frente a `bias_table` de C19, y aviso de VE-01 en la CLI.
<!-- aidlc-wave-memory:incoherence-analyzer:2d1155811ee6cbe02485c0087687b61f6e5d6c8d6e0904ad29f8b0b6e4d272eb -->


- 2026-11-22T00:25:00Z — El archivo de entrada de la CLI se leyó como el objeto `transcripcion` de C6 (la CLI arma la entrada con modo y perfil) y el reporte identifica cada entrevista por `interview_sha256` y no por su id, porque C19 no admite texto libre (FD-U11-23).
<!-- aidlc-wave-memory:incoherence-analyzer:6cc72d5ed0c9fa5c989f06811e656d5e0c4749b6252fca14946ef77081cc2e30 -->


- 2026-11-22T00:25:00Z — La regla del corpus se leyó por la ubicación del directorio de salida: dentro de un árbol de Git debe estar ignorado (`git check-ignore`); fuera de todo repositorio, como en ZINE, se permite (FD-U11-16).
<!-- aidlc-wave-memory:incoherence-analyzer:9aae365f9c11cc5deaf7073e6823afc6b5252af26a009b270729e5489b2c0700 -->


- 2026-11-22T00:25:00Z — El sensor de trazabilidad sumó AC5.5.3, AC5.5.4 y AC8.3.1–AC8.3.3 por los cruces US5.5 y US8.3 del mapa; se cubrieron AC5.5.3 (BR3.4), AC8.3.2 (BR2.11) y AC8.3.3 (BR2.10), y se difirieron AC5.5.4 y AC8.3.1 a U4/U7.
<!-- aidlc-wave-memory:incoherence-analyzer:18e6fa779a08dd8f9131f3bf822ff792da399e100ca0852bb1301027832c6fe6 -->


- 2026-11-22T01:48:15Z — Segunda pasada (Modify por cambio 01, adenda 02 y revisiones 3): U4 deja de evaluar y pasa a orquestar. Conserva sesión, turnos, colas C2/C3, ingesta, creación de sugerencias por C10, escaneo de salida e interfaz con el escáner de U11, consola base y axe, y suma consentimiento, perfil, AnalysisWorker sobre C17, corridas con su registro de modelos, bloqueo por incidente e import-linter de semantic-agent. Lo que fijan C1–C3, C10, C17, C21, CD-01/06/11, U1 F3, FD-U3-04/08/10/13 y FD-U10-03/16 no se pregunta; solo quedan seis decisiones de criterio (P6–P11): efecto de anonimizador_no_disponible (UG-02), alcance y fin del bloqueo, incidente fuera de su sesión, quién marca processing, corrida de los turnos ENT y tramos cubiertos por el modo final.
<!-- aidlc-wave-memory:text-flow:080958dfe7a86e139322031ed131d69c6b9162360bf6e1fd8fd1cf42b9712ae6 -->


- 2026-11-22T03:13:39Z — El bloqueo por incidente se modela con blocked_code permanente además del estado blocked: blocked solo reemplaza a open, paused o suspended, y una sesión finalized o terminated conserva su estado con blocked_code fijo. Así P7 = A («se puede finalizar y consolidar») cabe en el enum único de SessionStatus de C1; pide precisiones a U6 (FD-U4-18) y a U7, que no puede exigir un modo final terminado en una sesión que ya no lo puede lanzar (FD-U4-19).
<!-- aidlc-wave-memory:text-flow:b20de8e01bbdb639501f67867a7ae2a495c0f13c955e8333b9ff7ba34e59f472 -->


- 2026-11-22T03:13:39Z — «Plegado» se explicó con D52 y D53 de la matriz del TG (pasajes poco relevantes reemplazados por «[pasaje plegado: N palabras]»), porque ni C6 ni requirements definen el término; queda como propuesta FD-U4-17.
<!-- aidlc-wave-memory:text-flow:9d0e7cf9e171b807a5e2011389624fa5cc26976f97df08a5fb819f7543a7f74d -->


- 2026-11-22T03:19:24Z — Segunda pasada. La lógica de la permutación ya es de U11 (F4, BR6.1–BR6.3, FD-U11-06), así que U8 solo decide su valor en los perfiles que no son de evaluación y la prueba por el camino del producto. La aclaración neutra (US10.3) es lo único que se diseña de nuevo: biblioteca, ingesta, ConductorObservation y consola. La pregunta por pasajes, la segunda lectura del juez y el indicio afectivo quedan «Retirado» sin renumerar. Solo se preguntan P4 (origen del tema), P5 (permutación fuera de evaluación) y P6 (aclaración en el reporte).
<!-- aidlc-wave-memory:assistant-extras:c92d4c6eb14cf6e13a2d09c04bb29302f3e5dc1f46d5e603918e1c6ec21ca0c8 -->


- 2026-11-22T03:44:00Z — AC10.3.4 «se registra como descartada» se leyó como evento de log con run_id, id del hallazgo y regla (no una fila), y «cita de cualquier turno» como la regla cites_turn de C8 más las citas de la salida; quedó como FD-U8-06 para decidir.
<!-- aidlc-wave-memory:assistant-extras:edbbb44964e0a8bfe0875a55ee1f771ac5a8c4476e2bb854d2d5a688b3202301 -->


- 2026-11-22T03:19:41Z — Segunda pasada (Modify) de U5 por el cambio 01, la adenda 02 y las revisiones 3: cambio menor. Siguen la máquina de estados, las rondas, la autorización y P1 = A (ahora sobre ObservationsView). Sale lo de la alerta (CoT, fragmento, cita del documento, CotView, review.cot_not_viewed, propuesta de umbral AIR) y las columnas de ronda que referenciaban ReviewReport (R-01 de Domain Design). Entran los campos protegidos de C7 v2, la retención (C24), el registro de acceso de las observaciones (FD-U3-05), change_seq y el orden usuario → sesión → ronda, y el cierre de R-01..R-05 de la revisión 1. U4 ya crea ReviewSuggestion, ReviewRound y propose; U5 no los reescribe. Solo se preguntan P2 (reformulación en una corrección) y P3 (decidir tras terminar o retirar el consentimiento).
<!-- aidlc-wave-memory:human-review:8f82690ec46b8e5efc3135786f4187741c537644a6b94c2b279b5738f739a97c -->


- 2026-11-22T03:44:09Z — Volver a `pending` responde 422 por el enum del cuerpo de C1, no el 409 que dice AC5.1.4; el 409 `review.invalid_transition` queda para la decisión repetida sin cambios y se propone la precisión FD-U5-09.
<!-- aidlc-wave-memory:human-review:a5464a98d7e52b3ab6d4831585d7b178e2a787a5768fdf5ab2e01d2ebe0ff2b9 -->


- 2026-11-22T03:18:59Z — Leo U12 como validación y guarda de cifras de C19 más lista, detalle y comparación en M8. AC12.6.1 se cierra con FD-U1-05: el canary da 422 y 0 apariciones en filas y logs, y por eso el detail nunca repite valores ni nombres de campos desconocidos. Solo pregunto tres cosas de criterio: el canary de una palabra en un campo con patrón (residuo de R-06), qué se guarda de runs[] y de dónde sale el «Origen». C19 v2 (FD-U11-09) sigue pendiente de aprobación, así que se acepta la versión vigente que publique U1.
<!-- aidlc-wave-memory:research-reports:2a2b5eb997216b8ec38d3b504e2a988abf600e51019e1a2ea14811e4fa1fd0dd -->


- 2026-11-22T03:38:44Z — AC12.6.1 se cerró con CD-03 sin excepción: el canary da 422 en un hallazgo, como nombre de campo y en los campos con patrón (P1 = A); solo el nombre del archivo no rechaza, porque no se guarda ni se registra (FD-U12-01).
<!-- aidlc-wave-memory:research-reports:0a02f4d5d2e4fae811026b45875d96032dcde3704053d4701d38cf66b496d5b4 -->


- 2026-11-22T03:19:43Z — Segunda pasada: U6 pierde la versión de escenario (US1.2, F1 y BR1.x «Retirado») y gana importación (US2.6), modo final (US2.7) y pausa, terminación y retirada del consentimiento (US15.2, VE-10); P1–P3 de la primera pasada quedan superadas por el hablante ENT/TEST de C1 y el catálogo C25. Casi todo lo deciden C1, U4 (BR5.5, F12, FD-U4-01/07/18) y los AC, así que solo se pregunta lo que contradicen entre sí o lo que no fijan: marcas de hablante (P4), importación sintética sin consentimiento (P5), modo final tras la retirada (P6) y progreso del modo final (P7, SHOULD). Finalizar y consolidar siguen siendo de U7; U6 solo admite las transiciones en su máquina. La suspensión vale también para sesiones importadas porque la demo de B7 lo exige.
<!-- aidlc-wave-memory:session-lifecycle:c0b4a665c7c6f903b313354ab2d8e128fae2765dd2208fedfc745275747fb9df -->


- 2026-11-22T03:47:09Z — P7 = B: el progreso del modo final es etapa, cronómetro y total de ventanas que calcula session-api con la ventana y el solapamiento de effective_config (1 + techo((N − W)/(W − O))), con los ejemplos de U11; no hay «ventana N de M» y no cambian C3, C17 ni la biblioteca.
<!-- aidlc-wave-memory:session-lifecycle:3ade181c5a8d883781d56bb86f7dc10092fc1fe90d5c29bda3169c66f7400411 -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->


- 2026-10-02T23:01:33Z — Las decisiones P1 (delimitador «» de cita literal) y P3/P4 (catálogo de rótulos y formato de fecha nuevos) precisan contract-summary.md ya aprobado; se registraron en una tabla de functional-spec.md sin editar el original, para que el humano decida en la aprobación.
<!-- aidlc-wave-memory:contracts:5c6c4751c0244236f9cc7599e710dfa2c026927c8c45018d9351086def60b39b -->


- 2026-10-02T23:08:41Z — U3 es de tipo service y no produce frontend-components.md, pero toca M0 y M6; los estados y textos de esas pantallas quedaron en §6 de functional-spec.md, y la accesibilidad de US5.6 se cubrió con BR7.1–BR7.3 porque el mapa de historias la reparte entre unidades.
<!-- aidlc-wave-memory:identity-access:865b3cdc770a313991b3af97fc946ee023b02dd26d01501e4fcdcab4ff4c9249 -->


- 2026-10-02T23:28:41Z — El escáner de vocabulario prohibido se asignó a U4 en libs/integrity_policy con la firma scan(text, literal_sources), resolviendo el hallazgo R-01 de la revisión de U1 desde esta unidad y dejándolo en la tabla de precisiones para el humano.
<!-- aidlc-wave-memory:text-flow:af48a3db96f4d9b7ccfe82a6dbdd3afa2543bccfc207a13fd7b60241263b1356 -->


- 2026-10-02T23:52:08Z — Para cerrar el hallazgo R-02 de la revisión de U4, propose rechaza con review.round_locked cuando todas las rondas están bloqueadas, y se dejó en la tabla de precisiones que U4 limite el reintento en sesiones consolidadas.
<!-- aidlc-wave-memory:human-review:ed00e14b353fe91f6b093a746bd112f794541c8ea13fade94ce0d7519b81e3b5 -->


- 2026-10-02T23:52:08Z — Un rule source citaba un ID de regla de U4 y el chequeo de trazabilidad lo tomó como regla huérfana; se reemplazó por una descripción para no mezclar IDs entre unidades.
<!-- aidlc-wave-memory:session-lifecycle:44e5887f82e658f0677ae885593c111ded6f9bb56595035363e0709a796fdda1 -->


- 2026-10-02T23:52:08Z — El chequeo de trazabilidad pidió cubrir US5.5 y US5.6 porque el mapa de historias las cruza con U8; se añadieron BR4.1–BR4.4.
<!-- aidlc-wave-memory:assistant-extras:b2fc9e808c2a2205e3e6d391202bfcddd14a3c7cecc3cd92a807bb68dbd129b3 -->


- 2026-10-02T23:52:08Z — Ninguna desviación del texto de la etapa.
<!-- aidlc-wave-memory:anonymizer:c59b0abdd9c07b1d8fca25e862010c881790aba77248aefe244b46b2c9214bf5 -->


- 2026-10-03T00:09:14Z — Ninguna desviación del texto de la etapa; los huecos de contrato (X1–X6) quedan en una tabla del spec en vez de editar U5 o C11.
<!-- aidlc-wave-memory:forensic-report:86eefc8ee3a67fe02c657793ca69976d289755326e3ce65961a4603dc5c17600 -->


- 2026-10-03T00:21:01Z — Ninguna desviación del texto de la etapa; los huecos de contrato (X1–X5) quedan en una tabla del spec.
<!-- aidlc-wave-memory:voice:9a7f21f345e5a20283760a86db1adb0d8aa95e2a7c3d00926ce4944df7ff81b6 -->


- 2026-11-09T21:39:32Z — Las precisiones de la segunda pasada (papeles abiertos, perfil genérico, prefijo de api_key_ref, importaciones veridicus_contracts, rótulos de los 7 tipos, comparación por contenido de la copia de C6) se registraron como FD-U1-01..09 en functional-spec.md §9 sin editar contract-summary, components ni stories aprobados.
<!-- aidlc-wave-memory:contracts:84b8b561681625a1e93a6195d2fd748aa91a3066d4423f587434235dceda0b84 -->


- 2026-11-09T22:43:59Z — Tras la revisión asesora, y con review-freeze bajado por el humano (opción B), U1 se corrigió después de la revisión: R-01 a R-09 resueltos y FD-U1-10..14 añadidas, sin editar contract-summary ni unit-of-work aprobados.
<!-- aidlc-wave-memory:contracts:d048a1aa6edd04bc62b6f901511432d14563dfe2f4d87060bfc44b05e0b0b55e -->


- 2026-11-21T23:15:00Z — La etapa pide diseño sin referencias de tecnología, pero P8 trata justo de la API de cada proveedor; se nombran operación y modo estructurado al nivel de la respuesta P8 y se deja a la prueba de contrato con respuestas grabadas fijar los nombres exactos de los parámetros.
<!-- aidlc-wave-memory:anonymizer:d75e64b652ce935285cc321ffaffa863e7ae108d5eeaa50ffdf4f554af33e701 -->


- 2026-11-21T23:15:00Z — Se citaban reglas de U1 (BR9.4, BR9.8, BR9.9) y el sensor las tomó como reglas huérfanas de U10; se reemplazaron por descripciones (misma corrección aprendida en U4).
<!-- aidlc-wave-memory:anonymizer:8c3820f4b6538758d929cc67b4b20f6fc215701d596aed97e0aa98913420bf9b -->


- 2026-11-21T23:10:30Z — R-04: la revisión 1 pedía anotar la carrera entre el cambio de rol y U4 como riesgo aceptado. En su lugar la cerré dentro de U3 (BR2.12): toda petición que cambia estado bloquea en modo compartido la fila del usuario, y el PATCH en exclusivo. El orden de bloqueo pasa a usuario → sesión → ronda (FD-U3-13).
<!-- aidlc-wave-memory:identity-access:232d1cca6fb93ebfd653699a300f280ab25b273fec4fb6cb76538291d8ebc0c9 -->


- 2026-11-21T23:10:30Z — P7 = A daba al usuario de retención SELECT y DELETE; le añadí INSERT solo en RetentionAct, porque el Job escribe el acta con su propio usuario (FD-U3-09).
<!-- aidlc-wave-memory:identity-access:f9d8f8dfe933d513385d8284694ac7eaa5f771e6249ceef5c45ab7cb42b12b67 -->


- 2026-11-21T23:10:30Z — AC8.4.2 incluye «las corridas», pero AnalysisRun tiene estado mutable; no lo resolví desde U3 y lo dejé como FD-U3-10 para U4.
<!-- aidlc-wave-memory:identity-access:57197631bf2c7b333a5fbfdb1d91e33fa410417117be4ba3125fe280fc8cdf74 -->


- 2026-11-22T00:25:00Z — Las métricas de P6 (valores por corrida, umbrales, `passes`, `permutation_coverage`, `type_agreement`, `completed_runs`, sensibilidad por distancia, sección adversarial) no caben en C19 v1: se propone C19 v2 como cambio mayor por un PR de U1 antes del código de B11 (FD-U11-09) y un código de salida 6 (FD-U11-10).
<!-- aidlc-wave-memory:incoherence-analyzer:eb6e49a930b17ff3f5445e000ac4f95978fa79aa2bf95b760b14cfcbf0575a5e -->


- 2026-11-22T03:13:39Z — AnalysisRun se partió en tres tablas de solo inserción (AnalysisRun con la petición, RunStatusChange con cada estado y su actor, RunAttempt con el resultado de cada intento) en lugar de la fila con status, error_code y finished_at de components: responde a FD-U3-10 sin precisar AC8.4.2, a costa de derivar el estado vigente de la última fila (FD-U4-03).
<!-- aidlc-wave-memory:text-flow:eb1ab8ef461bbfb8df92c35e4ffbbc7e6de096c2b3ffbbf0b15679bfce8029f0 -->


- 2026-11-22T03:13:39Z — Se añadieron sin pregunta los code session.suspended y session.consolidated a C1 y el actor run-supervisor a la lista ActorSystem; los tres quedan en la tabla FD-U4 para decidir en la aprobación.
<!-- aidlc-wave-memory:text-flow:ad307329f412cacfb4dfe0ac5b2b0f45bf167242162c1dc2f1bbe20216f122b4 -->


- 2026-11-22T03:44:00Z — Además de lo previsto en las preguntas, entraron BR4.5–BR4.7 (AC5.5.4, AC5.6.4 y AC5.6.5, nuevos o sin regla tras retirar BR4.3) y se retiró también AffectiveNote, que la lista de retiros no nombraba pero sale con US11.1.
<!-- aidlc-wave-memory:assistant-extras:91b4f229891751414a6b6df5f99e270bf806325d2383713f6e4d922f8de20480 -->


- 2026-11-22T03:44:09Z — Se añadió el estado `discarded` de la ronda y `discard_correction_round` (BR3.9, FD-U5-04), que la lista acordada no nombraba: AC6.3.2 lo necesita, U7 ya lo había propuesto (X1) y C11 v2 no lo trae.
<!-- aidlc-wave-memory:human-review:b2683b4d3d4303f4ed2bb852a679039f33078545daa149b241f2da73b878e738 -->


- 2026-11-22T03:46:40Z — El version comercial que informa el proveedor (U10) no lo declara el perfil, así que P1 = A literal rechazaría todo reporte comercial; se admite «modelo» más segmentos que empiezan por dígito (BR3.3, FD-U12-11).
<!-- aidlc-wave-memory:research-reports:ee1c866cd8976ef4f4bde7e5b6c34a24ba37c3b23f31575baf7dfbb478077b74 -->


- 2026-11-22T03:47:09Z — «Reanudar análisis» (punto 6 de la lista) excluye los tramos en error: solo encola desde el primer TEST cuya última corrida está cancelled o que no tiene ninguna, para no pisar el «Reintentar tramo» que esos tramos ya ofrecen (FD-U6-15).
<!-- aidlc-wave-memory:session-lifecycle:3dca3ce774fd51426d034bf853a130382b445e7b95e312ca2291d83eacd7b474 -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->


- 2026-10-02T23:01:33Z — La lista de vocabulario prohibido 1.0.0 se queda en 9 términos (P2 = A) aunque deja sin detectar flexiones como «mienten» o «falsedad»; la limitación quedó visible como escenario E14 y cada ampliación entra por su PR con control negativo.
<!-- aidlc-wave-memory:contracts:ebd914fd3a30a9c130aa7e6279af072105885ec86bbaa8e11eeecf66b2b0d1f4 -->


- 2026-10-02T23:08:41Z — El primer admin nace con un comando ejecutado como Job revisable que lee un Secret (P1 = A), en vez de crearse al arrancar o por migración: respeta la prohibición de migraciones al arrancar y de versionar Secrets, a costa de un paso manual en la instalación.
<!-- aidlc-wave-memory:identity-access:ac5467dd5c3fa59eb8af1bc83a60f446ff1cddcf2ebf09a7c0f49a6ce7317a80 -->


- 2026-10-02T23:28:41Z — Un solo llamado al juez por turno con solo las afirmaciones que pasan la guardia, en vez de uno por afirmación: menos latencia en CPU y coherente con el arreglo claims de C6, a cambio de que una afirmación mal formada invalide el turno entero (que es lo que pide FR4.2).
<!-- aidlc-wave-memory:text-flow:f2ebad8220ecdb39d462477ee1cee9ceb00499210222969a0f98bb4c0a95a2fd -->


- 2026-10-02T23:52:08Z — El evento «CoT consultada» vale por usuario y alerta en todas las rondas (P1 = A): menos fricción en la corrección, a costa de no exigir una relectura en cada ronda.
<!-- aidlc-wave-memory:human-review:66bfbe4912043a03a9deaa6a3d7e3e7f0f246ef6d05721017e091318b158db38 -->


- 2026-10-02T23:52:08Z — La división de la transcripción se repite en la consola (vista previa) y en el servidor (autoridad) con la misma especificación y los mismos ejemplos, en vez de pedir la vista previa al servidor: respuesta inmediata a cambio de mantener dos implementaciones probadas igual.
<!-- aidlc-wave-memory:session-lifecycle:c4989c054651d959e0ff87d26ffcea8a231592cdf3eda5829f9f6db7483ad9ce -->


- 2026-10-02T23:52:08Z — El indicio afectivo usa una lista versionada sin LLM (P3 = A): determinista y auditable, a costa de no captar emociones expresadas sin palabras clave.
<!-- aidlc-wave-memory:assistant-extras:d1bccc958587859835141e1d2f21c17e7d6652ca26343998bdbe51b24f59c771 -->


- 2026-10-02T23:52:08Z — Marcadores consistentes por llamada con restauración dentro del clúster (P1 = A): el juez externo puede razonar sobre quién y dónde, a costa de mantener una tabla en memoria que nunca debe registrarse.
<!-- aidlc-wave-memory:anonymizer:e59cc4a1ce45b2253f64d56f1c8475575ec8322d56ecd82761fe5350f5a6bcff -->


- 2026-10-03T00:09:14Z — Archivo antes que fila (P2 = A): nunca hay versión sin archivo, a cambio de un barrido de huérfanos al arrancar.
<!-- aidlc-wave-memory:forensic-report:3a208f8dd39b004c543f7a47f8365fa3491300a1ee0a9293b9d9c2dc43d518d1 -->


- 2026-10-03T00:09:14Z — La sugerencia editada muestra IA y analista (P3 = A): más largo, pero separa lo que dijo la máquina de lo que decidió la persona.
<!-- aidlc-wave-memory:forensic-report:4f272d98d24479fdb699878e4b7a0b85ec1f36ae8466b4819f6765dc2a29d19b -->


- 2026-10-03T00:21:01Z — Sin audio guardado para reintentar (P2 = A): se pierde el reintento sobre el mismo turno a cambio de no conservar nunca audio crudo.
<!-- aidlc-wave-memory:voice:5b31c38f2052ea2be97c8520b3176b07a94738efdb694ac0b3af904fe80f6920 -->


- 2026-11-09T21:39:32Z — El prefijo VERIDICUS_ de api_key_ref pasa del esquema a un argumento de la función de validación: sistema reutiliza el mismo esquema con su prefijo, a costa de que el esquema solo ya no impida una clave de otro producto.
<!-- aidlc-wave-memory:contracts:46f8a4ab15f2b577441a89b953aec056bb6f14c8289b359155a2396f28134cb2 -->


- 2026-11-09T22:43:59Z — P10 = A: los escenarios de vocabulario pasan a casos de escaneo que ejecuta U11 en B11; U1 queda sin lógica de escaneo a cambio de que esas pruebas no corran hasta B11.
<!-- aidlc-wave-memory:contracts:c96f86d2aab72ac786ab30d20c86cc7e1a44028cabf5352f978150fbc0a2b321 -->


- 2026-11-21T23:15:00Z — La red de seguridad no se aplica a los mensajes system: así los tipos de C6 («Fecha», «Persona») y el resto del prompt quedan legibles para el juez, a costa de confiar en que el prompt versionado no trae testimonio (FR4.6); el NER y las reglas sí lo recorren (FD-U10-02).
<!-- aidlc-wave-memory:anonymizer:6adc6b57f5a4a93152b3ec3d357eaba84525b88a5a9f429440de365cd3d0d2bd -->


- 2026-11-21T23:15:00Z — Una forma de marca que el modelo escribe sin venir de la tabla invalida el hallazgo aunque fuera texto legítimo: se prefiere perder un hallazgo a restaurar mal una cita (P6 = A).
<!-- aidlc-wave-memory:anonymizer:3cb4f150145b06d3d8408dff6b6de8fe3de31454cee67b4e47a1c175001211b4 -->


- 2026-11-21T23:15:00Z — Tabla versionada de capacidades por modelo en el subpaquete de adaptadores: el modo estructurado de Anthropic (esquema o herramienta forzada) se decide por datos revisables y no por prueba y error, a costa de un PR por cada modelo nuevo; además rechaza al arrancar herramienta forzada con esfuerzo, que el proveedor no admite (FD-U10-09).
<!-- aidlc-wave-memory:anonymizer:ee3a6b02359bb08d4b0d4a2ef4b34d3498377a1155bccd182851adf7fcc63a44 -->


- 2026-11-21T23:15:00Z — El adaptador nativo valida contra req.schema además del núcleo (FD-U10-10): cumple AC13.6.2 en el adaptador y deja la validación de C6 en U11, a costa de validar dos veces.
<!-- aidlc-wave-memory:anonymizer:2c1fb03e84718a2fa53eb154ac2c8141ec637d20e56fe8263248b1e5f3927abd -->


- 2026-11-21T23:10:30Z — Registro de acceso por marca declarativa en el pipeline (P5 = A), en vez de que cada unidad llame al puerto: una sola prueba de nivel 0 lo vigila, a costa de una extensión nueva en C1 y de que la exportación siga siendo la excepción que llama al puerto ella misma.
<!-- aidlc-wave-memory:identity-access:52bcf2b0079120b0d30c258631091608260d8351d7691890284bd1c847a48309 -->


- 2026-11-21T23:10:30Z — Desactivar se permite con sesiones pendientes (P8 = A): prima el control de seguridad, a costa de sesiones en solo lectura hasta reactivar; M6 muestra su número con un campo `pending_sessions` nuevo en C1 (FD-U3-04).
<!-- aidlc-wave-memory:identity-access:59cb0834b38b69a92cca2147fbc520b8c1741d53f728aecc5c4bc48f4ff32922 -->


- 2026-11-22T00:25:00Z — Con permutación se hacen siempre las dos llamadas del verificador, aunque la directa rechace: el doble de llamadas a cambio de medir sin sesgo la consistencia al invertir el orden (BR6.1, BR12.4).
<!-- aidlc-wave-memory:incoherence-analyzer:8f12eeac35cd781464fd8df63975caf85313b5460df7c0c9935143ae28846804 -->


- 2026-11-22T00:25:00Z — Los veredictos se capturan con un envoltorio del gateway que solo guarda booleanos, en vez de añadirlos a la salida de C6: el contrato no cambia, a costa de que la métrica solo exista dentro de `evaluate` (BR12.4).
<!-- aidlc-wave-memory:incoherence-analyzer:4834e8d8f5b5633667cfbf59e01ae261f3802da430fa03b07217f9c7fca1360b -->


- 2026-11-22T00:25:00Z — En `estado: error`, `registro.descartes` va vacío igual que `hallazgos`: nada de una corrida fallida se interpreta como resultado, a costa de perder el diagnóstico de los descartes previos al fallo (BR7.1, FD-U11-13).
<!-- aidlc-wave-memory:incoherence-analyzer:774914eebfda80971c1e9ac2146b26a2a994d2f5dd325ec4e2ee3e78aae13b1f -->


- 2026-11-22T03:13:39Z — Un resultado que se va a descartar (intento viejo, corrida cancelada o vencida) se revisa igual en busca de un incidente antes de descartarlo: cuesta una lectura del registro por mensaje descartado, pero no se pierde una llamada externa sin anonimizar que ya ocurrió (FD-U4-11, AUTONOMIA-04).
<!-- aidlc-wave-memory:text-flow:400aca5e931d8307e8a5d647496dbe1b04612cf81fde09f07b88ffbece14e1be -->


- 2026-11-22T03:13:39Z — AnonymizationIncident sobrevive a la retención sin clave foránea, solo con IDs, en vez de borrarse con la sesión como pide el orden de C24: conserva la evidencia de VE-14 a cambio de una excepción más al borrado (FD-U4-12).
<!-- aidlc-wave-memory:text-flow:0e0553ac2e7ae3c389e287ea95b0abfedd784532fcbf4a40ab667d013fd96d5e -->


- 2026-11-22T03:13:39Z — En la ingesta, el vocabulario prohibido en un hallazgo invalida la corrida entera (regla de U1, F3) aunque U11 descarte solo el candidato (FD-U11-02): son dos líneas distintas, y en la segunda no se quita nada en silencio.
<!-- aidlc-wave-memory:text-flow:2a3753c5ec923e05e9ebaef139ca763043f257d6ba5ab0ff26a4c313306595ff -->


- 2026-11-22T03:44:00Z — BR5.5 compara el tema con las citas de todos los hallazgos de la salida y no solo con el de origen: la biblioteca y la ingesta aplican la misma regla, a costa de quitar algunas aclaraciones más.
<!-- aidlc-wave-memory:assistant-extras:5a7c0710700c488744548483c059f4cd6c90cde24d120c616b7c1b9bb2d2a665 -->


- 2026-11-22T03:44:00Z — La llegada de aclaraciones se anuncia como contador agregado y no una por una (FD-U8-10), para cumplir AC5.6.5 sin perder el anuncio del punto 8.
<!-- aidlc-wave-memory:assistant-extras:6f478d2b4c1331631dd59c6ad304e81ef8c65287f7c679babe890a101b37f5a8 -->


- 2026-11-22T03:44:09Z — `open_round(for_update=True)` abre la ronda 1 si la sesión no tiene ninguna (BR3.7): U7 siempre bloquea una ronda, a costa de que una lectura con bloqueo pueda crear una fila.
<!-- aidlc-wave-memory:human-review:507887e696a0815eabc09f567555a14b83720b831a9ea1fec4beb69f0916b705 -->


- 2026-11-22T03:46:40Z — El costo de M8 va solo en la fila Total (FD-U12-09): recalcularlo por papel duplicaría la fórmula de U11 en session-api, a cambio de perder el desglose que dibujaba §10.2.
<!-- aidlc-wave-memory:research-reports:ef2fb720d64f2d459fb33f1239c5df9c44a3df801cd14c8db4ff3204a622e216 -->


- 2026-11-22T03:47:09Z — El hasta_turno de un bloque pegado es su último turno TEST y no n+k−1 (FD-U6-07): respeta la restricción de U4 de que una incremental termina en TEST y la semántica del turno ENT sin corrida, a costa de una precisión a AC2.3.3.
<!-- aidlc-wave-memory:session-lifecycle:014defda73b8187fb811f52133a8fdf97971cce8790641d28575dfa69e14cb2e -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

- 2026-10-02T23:01:33Z — El sensor de trazabilidad marca que ninguna historia del mapa se asigna a la unidad contracts; es estructural (U1 respalda criterios de US2.2, US3.2, US5.5 y US8.3 sin historias propias) y no se editó el mapa aprobado.
<!-- aidlc-wave-memory:contracts:54e3508fd8535cbe6e4b8fde38dbecb3c7df049aba750e0d9983df888d56b29e -->

- 2026-10-02T23:08:41Z — Política de contraseñas, duración de la sesión web y bloqueo por intentos fallidos quedan para NFR Requirements.
<!-- aidlc-wave-memory:identity-access:281b906f5bcf15251c0ce3089e0a8599bf40cdb94c37b18589af3acfdd8253ce -->

- 2026-10-02T23:28:41Z — Máximo de caracteres por pasaje, dimensión del vector, intervalo de sondeo y plazo por turno quedan para NFR Requirements.
<!-- aidlc-wave-memory:text-flow:df0ea5f508326220de9cca68d932776d203c615709063f96bb5de6856fadbd37 -->

- 2026-10-02T23:52:08Z — La ventana W de la razón AIR (C15) queda para NFR Requirements.
<!-- aidlc-wave-memory:human-review:16366fa4910cf0cae4214d899188109bf3883412114d9494f39680237e7ef616 -->

- 2026-10-02T23:52:08Z — T del latido, intervalo de revisión y sondeo lento quedan para NFR Requirements.
<!-- aidlc-wave-memory:session-lifecycle:a9fd4392629134006c568aa0be0fd8a99c5653456d6659f55191f4a0c9e92f10 -->

- 2026-10-02T23:52:08Z — El efecto de la segunda lectura sobre la latencia y NFR8 lo mide NFR Requirements.
<!-- aidlc-wave-memory:assistant-extras:673bbc42c55724f4d1a3a9b83062aa2df88a3368c221ffa4e61d3f30c7ddfc0d -->

- 2026-10-02T23:52:08Z — Si un nombre propio sin patrón escapa del enmascarado, el riesgo residual queda para la decisión de usar o no un modelo externo.
<!-- aidlc-wave-memory:anonymizer:3687fe0f41736fbfe9ec591b55e4e5998f12009c53f7543b997a32a4e6414422 -->

- 2026-10-03T00:09:14Z — Los cambios X1–X6 a U5, C1 y C11 necesitan la decisión del humano en la aprobación antes de Code Generation.
<!-- aidlc-wave-memory:forensic-report:e417a09eef27f193b90ea8ee797efed7b17e29a4d04fa8ed1e77d7ef52077a1e -->

- 2026-10-03T00:21:01Z — El tamaño máximo en bytes (propuesto 6 MB) lo confirma NFR Requirements.
<!-- aidlc-wave-memory:voice:80bd535350bdfa50b0767c9b824286ec95693fcf93faf328dfcdbb3ee94a1338 -->

- 2026-11-09T21:39:32Z — AC12.6.1 espera 201 con el texto descartado y CD-03 rechaza con 422; BR10.1 cubre ambos y la diferencia (FD-U1-05, misma que DP-01) se cierra en el Functional Design de U12.
<!-- aidlc-wave-memory:contracts:a3a4e9e0f87c70cec727e4a528e642cd91b532a95d4302f874d30d04c2e8c4ea -->

- 2026-11-09T22:43:59Z — FD-U1-14: si un tramo «…» que es solo un término de la lista debe seguir excluido del escaneo (R-05), queda para que el humano decida en la aprobación.
<!-- aidlc-wave-memory:contracts:02f570e4daa768fb5fddee3e0b1b3ef2ff637a17486a01ce5e08437b083fac6c -->

- 2026-11-21T23:15:00Z — Riesgo residual de P3 = A: un nombre que abre oración, que el NER no reconoce y que no se repite a mitad de oración sale del clúster. La prueba de fuga cero (AC11.3.1) debe incluir nombres al inicio de turno; si el NER que elija NFR Requirements no los atrapa, la prueba falla y hay que decidir sin bajar el umbral.
<!-- aidlc-wave-memory:anonymizer:5b0e69f46896ef4197aad76c86452bb056eb746c97374117ca306c50d1af4054 -->

- 2026-11-21T23:15:00Z — profile_sha256 lo calculan U11 y el proxy por separado con JCS; si divergen, todas las llamadas externas dan 409. Se propone que U1 publique la función (FD-U10-12); depende de la decisión del humano sobre las precisiones de U1.
<!-- aidlc-wave-memory:anonymizer:dc7acca2edaac9b013befa767707cd8ec704c92b4e701d8fb68fed1bd5d26346 -->

- 2026-11-21T23:15:00Z — Las cifras nuevas de C25 (anonymizer_request_max_bytes y anonymizer_masking_budget_ratio, FD-U10-13) y el NER con su umbral quedan para NFR Requirements.
<!-- aidlc-wave-memory:anonymizer:828e154411030039fbb3bf125d3ec23874945f2769880cc6439baeb26ec6a7cf -->

- 2026-11-21T23:10:30Z — NFR11.1 y NFR11.2 de NFR Requirements de U3 (revisión 1) quedan superados por BR6.1 y BR5.2; hay que actualizarlos en la segunda pasada de esa etapa (FD-U3-12).
<!-- aidlc-wave-memory:identity-access:9e5e17ee1fdbc9d70a66c1afb79c80d9870227fd7b3605be4337025ea08b9b28 -->

- 2026-11-21T23:10:30Z — Los textos de M6 (Reactivar, Cambiar rol, confirmación con número, mensajes de 409 y 422), M0 (429) y M8 (403) son propuestas de esta etapa (FD-U3-11); los decide el humano en la aprobación.
<!-- aidlc-wave-memory:identity-access:2c45b0d008782454fadb686ea293ce020260a2b0caf66aedd5dfd7dc5414cd2c -->

- 2026-11-22T00:25:00Z — Listas iniciales de `tipo_hecho` y `perfil_persona` (BR13.3) propuestas por el diseño; las aprueba el autor.
<!-- aidlc-wave-memory:incoherence-analyzer:99f1bcf29f549a00b6967516fea38c7532fbe3c71bbd157a94001b3603014d48 -->

- 2026-11-22T00:25:00Z — Umbrales de las métricas estadísticas y composición mínima del conjunto: los fija NFR Requirements en `evaluation/thresholds.v1.yaml`.
<!-- aidlc-wave-memory:incoherence-analyzer:1b70f623f86e6ea2de707d62ba078c7417ab8bbe58db0cd95b90378c3896e1c6 -->

- 2026-11-22T00:25:00Z — Tramos de distancia para la sensibilidad (hasta el solapamiento, hasta la ventana, más de la ventana) por confirmar en NFR Requirements (BR12.5).
<!-- aidlc-wave-memory:incoherence-analyzer:5321dbfba231038c9f7afa66ba2f6cf880660954d3ec70e2286b0145118de2fd -->

- 2026-11-22T00:25:00Z — El riesgo de una sola palabra citada en el escáner depende de FD-U1-14, aún pendiente en U1 (BR9.2).
<!-- aidlc-wave-memory:incoherence-analyzer:c4a3f41ab3114f752542db35e38a53e95a04e14a398e018da3cf4112b91c82f7 -->

- 2026-11-22T03:13:39Z — La interacción entre la pausa de U6 y la ruta de turnos (202 sin corrida en pausa) y el code para turnos sobre una sesión suspendida dependen de la segunda pasada de U6, que aún no se hace.
<!-- aidlc-wave-memory:text-flow:bd671c315f15be8986c2e17d328c593b1ed168dfd9ac65abc327f667f38b1491 -->

- 2026-11-22T03:44:00Z — Para NFR Requirements: el costo de verifier_permuted en todo-local frente a NFR3 y NFR8, la tasa aceptable de aclaraciones descartadas por regla y si hace falta un tope de aclaraciones o de largo del tema en C25.
<!-- aidlc-wave-memory:assistant-extras:84656469a01527cbada161073179e207ce0707e3ed056bc766e2c13f694f1552 -->

- 2026-11-22T03:44:09Z — NFR Requirements (segunda pasada) fija las cifras de `review_text_max_chars` y `review_body_max_bytes` en C25 y pasa el código de longitud a `limits.exceeded`.
<!-- aidlc-wave-memory:human-review:54391f623533533bbd5a35c8c4764499160d523dd9545c77cdebe749b713ae3e -->

- 2026-11-22T03:46:40Z — Con P1 = A, un reporte hecho antes de cambiar un perfil o la tabla de precios por PR ya no se puede subir (E18, E19); queda para decidir en la aprobación si basta con subir antes del cambio o hace falta guardar versiones anteriores en C18.
<!-- aidlc-wave-memory:research-reports:4e3d4ecb9e00f76d2acc161793ca94d1f1301a85ec0089c1758dbe90baa2c3c7 -->

- 2026-11-22T03:47:09Z — Para NFR Requirements: cifras de C25 del pegado y la importación con margen sobre la entrevista más larga del piloto, run_deadline_final_s en CPU, si el latido escribe en cada sondeo y si NFR8 exige paginar la lista en el servidor (functional-spec §11).
<!-- aidlc-wave-memory:session-lifecycle:07e0c344ca1b5a1e1974248d337500cd21a9982f0760e5bfa6d329de0b8e3b35 -->
