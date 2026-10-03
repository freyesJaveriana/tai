<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->


- 2026-10-03T02:56:01Z — Los valores que la revisión de NFR Requirements echó en falta (R-02) ya los fijaron U3, U4, U6 y U9; no se volvieron a preguntar y entraron al catálogo de límites y a la cookie de C1.
<!-- aidlc-wave-memory:contracts:21d7f13641c3d92bf207dcd0f24299ad01d668fb4b561106be0a5fb1c217a63b -->


- 2026-10-03T03:03:51Z — P1 = A (UPDATE de last_seen_at en cada petición) mantiene exactas las pruebas de 1 799 s y 1 801 s de NFR10.3; con ≤ 20 sesiones el costo es despreciable.
<!-- aidlc-wave-memory:identity-access:79af9875963524c518c3a41447227dbe517bf891140450fabffe53b94a9b16a3 -->


- 2026-10-03T03:03:51Z — La cookie Secure de U3 obliga a HTTPS en el ingress; P1 = A lo resuelve con una CA local de mkcert en la anfitriona y el certificado como Secret, sin certificados en el repositorio.
<!-- aidlc-wave-memory:platform:380760012ab1b368e3f24618fc84b3832d4b60ab43a7110f272f95a7e4f5211d -->


- 2026-10-03T03:34:42Z — P1 = A se implementó con una primitiva compartida `session_api/shared/change_cursor.bump` que la UnitOfWork memoriza por sesión; así U4, U5 y U7 toman la sesión antes que la ronda sin crear dependencias entre módulos.
<!-- aidlc-wave-memory:human-review:9a01810d2e6e17ed497a8403e34f8ea0ef585acaacb9fb3f1fef615d5efdeef3 -->


- 2026-10-03T03:36:12Z — La marca del lote de P1 = A se vigila con WATCH además de MULTI/EXEC; sin WATCH, dos reenvíos simultáneos podían ver la marca ausente y publicar ambos el lote.
<!-- aidlc-wave-memory:session-lifecycle:9e0c34c54346515696d4c3552a2e648e12efccedf06f829bab328cec1c1bd6ec -->


- 2026-10-03T03:34:45Z — La comprobación de plazo de la pregunta (P2 = A) suma también los 5 s de count_tokens: ahora + 5 + 60 + 15 s < deadline_at; la omisión usa reason timeout para no ampliar el enum de NFR15.4.
<!-- aidlc-wave-memory:assistant-extras:762027f2f073852e2a0c9f9b2d5d303a7eb967b7f987d395efc49be334a170aa -->


- 2026-10-03T03:31:30Z — La numeración estable de P1 = A se deriva de la lista que trae cada llamada (posición por categoría, detectados por reglas desde N + 1); así no rompe la ausencia de estado de NFR8.3 y escala sin afinidad.
<!-- aidlc-wave-memory:anonymizer:92d08bfd40d14315fe867e63b712f903e2a1fff57558a4aaa481455a3f25171d -->


- 2026-10-03T03:56:35Z — P1 = A se aplicó a la API y al trabajador de session-api con raíz de solo lectura y /tmp en memoria, no solo a la ruta de voz; la lectura en streaming evita el disco y el montaje en memoria es la red de seguridad si otra ruta usara UploadFile.
<!-- aidlc-wave-memory:voice:a9717e0154815fce981f413b93d76450833d7501c50b48488e1abee383a013f0 -->


- 2026-10-03T03:57:26Z — El cursor del diálogo se compara como decode(expected_cursor) = valor del bump − 1, después de BR2.2–BR2.4 y BR2.7; como el latido de U6 y cot-views no incrementan change_seq, solo un cambio visible deja la vista desactualizada y no hay falsos rechazos.
<!-- aidlc-wave-memory:forensic-report:fc34a15cccab11c34e7da29a4e1aa68fc255600aa2327a8944d3fd90f7c77b3e -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->


- 2026-10-03T02:56:01Z — El diseño cambia el criterio aprobado de NFR10.6 (de 50 ms a análisis estático) y amplía NFR10.12 a toda operación de C1; no se editó security-requirements.md y quedó en la tabla de precisiones.
<!-- aidlc-wave-memory:contracts:56090c6274e927bef9472d66f4ea02c086de831ce721474ae5f03e64a05c47d5 -->


- 2026-10-03T03:14:53Z — P1 = A cambia NFR10.16 aprobado (ahora hay hasta 2 reintentos en el proceso ante fallos pasajeros del juez) y P2 = A añade change_seq a entidades aprobadas; quedaron en la tabla de precisiones de reliability-design sin editar los originales.
<!-- aidlc-wave-memory:text-flow:55300d27861d11aebb1f88294f05844ee25c22da645dd2288aa663d015620f1d -->


- 2026-10-03T03:34:42Z — El diseño cambia D3 aprobado (sesión antes que ronda), añade `change_seq` a `ReviewDecision` y `ReviewRound` y precisa C10, C11 y los diseños de U1, U3 y U4; todo quedó en la tabla de precisiones de reliability-design §7 sin editar los originales.
<!-- aidlc-wave-memory:human-review:7321edab85e309d6d5948cdb324c1e5825ecd0cdce4e675b6710b335522f555f -->


- 2026-10-03T03:36:12Z — El conteo de pendientes de la lista pasa a una vista de solo lectura de U5 (human_review.session_pending_suggestions) en vez del LEFT JOIN a sus tablas de D9; quedó en la tabla de precisiones de reliability-design; los límites nuevos del catálogo de U1 están en la de security-design.
<!-- aidlc-wave-memory:session-lifecycle:365024e9e31c04f4a09d31aa856b9c3c9d389759c18210b7be80ed8bbe66ac6f -->


- 2026-10-03T03:34:45Z — Con el reintento de P1 = A el peor caso de un turno con tres extras es 482,2 s y supera el reclamo aprobado de 480 s; el diseño fija 510 s en los values con extras. Quedó en la tabla de precisiones de performance-design sin editar NFR3.6 ni NFR3.7.
<!-- aidlc-wave-memory:assistant-extras:f51400ebf0fa98f2127977baa8f7958bb7a5c0109eb3ca1fa85501bc2fedd015 -->


- 2026-10-03T03:31:30Z — Con el adaptador anonimizador, 502 y 504 del proxy quedan fuera del reintento acotado de U4 (P1 = A de U4); reintentar reenviaría datos al destino externo. Solo 503 anonymizer.busy y la conexión rechazada son recuperables; registrado en la tabla de precisiones.
<!-- aidlc-wave-memory:anonymizer:1cb5d87eee59167313da4e7a94e6c5b38a7691ffb57805cba07b357f4276484f -->


- 2026-10-03T03:56:35Z — P2 = A acota en el tiempo el riesgo T5 que NFR10.4 aprobado solo acotaba por bytes (AofRewriteRequester con BGREWRITEAOF y prueba de 0 apariciones en ≤ 120 s); quedó en la tabla de precisiones de security-design junto con no renombrar BGREWRITEAOF en Redis de U2.
<!-- aidlc-wave-memory:voice:2ed87ceb1f71c566a22652d5b816493838d8bccae9f36fb5828f0cc8190f3d33 -->


- 2026-10-03T03:57:26Z — Con P2 = A el barrido del arranque deja de ser el camino normal de limpieza y pasa a ser respaldo de report.cleanup_failed; se registró como precisión a D5/D6, NFR10.16 y NFR10.17, sin editar los originales.
<!-- aidlc-wave-memory:forensic-report:e2250f8c6f0bf8a6d2c1602109153a35d4bfefb506033ef1cfee9a5dccaba6d8 -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->


- 2026-10-03T02:56:01Z — Catálogo único de límites (P1 = A): contrato y servicio no pueden divergir, a costa de que U9 pierda el margen de VERIDICUS_VOICE_MAX_BYTES hasta 8 000 000 bytes, porque el entorno solo puede bajar el límite.
<!-- aidlc-wave-memory:contracts:86293e4c630d45fe3a4975df28931f335c01fb22cc251ee73534e34ed8109927 -->


- 2026-10-03T03:03:51Z — Semáforo de Argon2id con espera de 5 s (P2 = A): picos de hasta 10 inicios terminan sin error, a cambio de un 503 con Retry-After si la cola dura más; un intento que no llegó a verificar no cuenta como fallo del limitador.
<!-- aidlc-wave-memory:identity-access:582c18b0ddfc54ee9a6c6c7df88da1c9c2f1a7543749b965e275818a10f29df5 -->


- 2026-10-03T03:03:51Z — Kyverno solo como CLI (P2 = A): se evita un controlador más en la máquina, a costa de que un manifiesto aplicado a mano fuera del chart solo lo frene Pod Security restricted.
<!-- aidlc-wave-memory:platform:60504c3b0e27045a24c004572eec7a1343e518c53a908e8560756dba1478ceec -->


- 2026-10-03T03:14:53Z — Calentar el juez al arrancar retrasa el readyz de semantic-agent unos segundos, a cambio de que el primer turno real no pague las instrucciones sin caché.
<!-- aidlc-wave-memory:text-flow:04823f5b9ec69fcf370944160de0dda70647ead5617cdcde74616e721e90e3c3 -->


- 2026-10-03T03:34:42Z — Las decisiones y los turnos de una misma sesión comparten ahora un bloqueo; se acepta porque hay un solo analista por sesión y las transacciones bajo ese bloqueo no hacen E/S de red, a cambio de un sondeo sin huecos y sin interbloqueos.
<!-- aidlc-wave-memory:human-review:430502b6ceecc5627aae69046f09aba61776804bf246b306d87c644eadd7c364 -->


- 2026-10-03T03:36:12Z — El latido se omite si la fila de la sesión está bloqueada (SKIP LOCKED) y no incrementa change_seq; el sondeo nunca espera un pegado, a cambio de que una escritura en curso retrase el latido hasta el siguiente sondeo.
<!-- aidlc-wave-memory:session-lifecycle:e62ea994b42813233ba5ef560acc418b78369cbd2bd9a747b66a120286fab830 -->


- 2026-10-03T03:34:45Z — La lista afectiva y el prompt de la pregunta se validan al arrancar aunque los extras estén apagados; un archivo roto impide arrancar semantic-agent, a cambio de que activar un extra por PR nunca descubra el fallo en el clúster.
<!-- aidlc-wave-memory:assistant-extras:70117caea88e743d91aa4de73f4466e60e6f98ac5a3c38684ee4a823bfcb41e6 -->


- 2026-10-03T03:31:30Z — La lista de nombres se compila por llamada en vez de cachearla; cuesta parte del presupuesto de 250 ms, a cambio de no retener nombres propios en memoria entre llamadas.
<!-- aidlc-wave-memory:anonymizer:e0435feb51650d993dfbf78216856593532f4b7d42ef50467467e49fbabeebac -->


- 2026-10-03T03:56:35Z — Sin reintento ante Whisper caído, a diferencia del juez de U4: el turno falla en segundos y el audio se borra, a cambio de que el analista grabe de nuevo; reintentar obligaría a conservar audio crudo más tiempo.
<!-- aidlc-wave-memory:voice:1e91c9898acb660c249e75905b4fba9864c4f6d2edcbbc9a2851b7d819acd6c3 -->


- 2026-10-03T03:57:26Z — La consolidación retiene la fila de la sesión y la ronda desde el bump hasta el commit (≤ 2 s, con E/S local del volumen) para que el reporte sea exactamente el estado bloqueado; a cambio, una decisión simultánea de otra pestaña espera o recibe 503 a los 2 s.
<!-- aidlc-wave-memory:forensic-report:b49cfd69488b706e4962a3026f5d2b980de95ed1dd953a2cc1cad2fb88ca0253 -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
