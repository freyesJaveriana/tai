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
