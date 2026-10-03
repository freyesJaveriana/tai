<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->


- 2026-10-03T01:27:54Z — U1 es de tipo spec: solo produce security-requirements, tech-stack-decisions y traceability; los NFR de rendimiento, escalado, fiabilidad y observabilidad en ejecución no aplican porque la unidad no corre. El tiempo de la suite (P6) se registró bajo NFR2 (CPU primero).
<!-- aidlc-wave-memory:contracts:272843b02c499f1870be1f6b834789b294c37b012fe23a9aad25ae5b5bc97eff -->


- 2026-10-03T01:27:54Z — Los servicios consumen contracts/ como dependencia de ruta de uv; se leyó la regla «solo libs/ se comparte» como referida a código de comportamiento, y contract-summary (regla 1) ya aprobó que los servicios importen contracts/.
<!-- aidlc-wave-memory:contracts:26a2b2835b1914ae50f1615b93a3bf63d6c24ff21d430f0a2f0989c4a8fb5f1b -->


- 2026-10-03T01:38:15Z — P2 se respondió con texto propio («8 con composición y lista común»); se leyó como mínimo 8 con mayúscula, minúscula, número y símbolo más la lista de contraseñas comunes, y se añadió un máximo de 128 caracteres para acotar el costo de Argon2id.
<!-- aidlc-wave-memory:identity-access:47a59c672360e917a2849568740cc464e7879084b52440a4a829788839d4fd76 -->


- 2026-10-03T01:38:15Z — U3 es el primer Bolt que construye session-api (B2), así que sus decisiones de pila fijan la base del proceso para U4–U7: FastAPI, Pydantic v2, SQLAlchemy 2 con psycopg 3, Alembic en un Job y redis-py.
<!-- aidlc-wave-memory:identity-access:f0887c764a524266de1bb3b787ab263c4ecec4324b832b2bf40d56d6636e78c2 -->


- 2026-10-03T01:38:15Z — U2 es de tipo packaging y no tuvo Functional Design: los requisitos se derivan de unit-of-work, requirements, contract-summary y team.md; solo aplican seguridad, pila y trazabilidad.
<!-- aidlc-wave-memory:platform:edf9a7891a0e682b1cec5d30fe533a0362fa20173c018a9896ca7ede9b7ba5fc -->


- 2026-10-03T02:00:43Z — S1 = A se leyó con la cola de todo el sistema (no solo la de la sesión), porque el juez atiende un turno a la vez para todas las sesiones; el tope de 3 600 s limita la capacidad a unos 60 turnos en cola.
<!-- aidlc-wave-memory:text-flow:bc3cf22470912c7d8d4dd8ca6103f1704b2b9c0bfe05cebc15fbb57a3f19f1b4 -->


- 2026-10-03T02:00:43Z — S3 = A usa turn.error.system para el prompt demasiado largo; para no crear un code nuevo, el mensaje de catálogo de ese code cubre los dos casos (dividir el turno o reintentar).
<!-- aidlc-wave-memory:text-flow:46cad5ef4cd76a1b3a2d3524fceaa6a6450612edfb70b61b53d29992264c215b -->


- 2026-10-03T02:19:51Z — P1 = A se leyó con «alertas elegibles»: decididas, o pendientes que el analista dejó atrás (ignoradas, FR9.3); las pendientes al final de la bandeja no cuentan, para que la razón no suba sola mientras llegan alertas nuevas.
<!-- aidlc-wave-memory:human-review:e1606b8b832b4811f4c526682b243595b9d2137d049baf202f96fb088d66bf53 -->


- 2026-10-03T02:19:51Z — La nota y la reformulación del analista son texto humano: no se censuran y el escaneo de vocabulario de nivel 3 las trata como citas literales; AUTONOMIA-03 prohíbe etiquetas automáticas, no el criterio del analista.
<!-- aidlc-wave-memory:human-review:9c2e250dd27c1bb92f15e8df4e71195ad322153481e9041ec432f474f04e1407 -->


- 2026-10-03T02:20:05Z — P2 = A dice que los turnos del entrevistador no cuentan para los 60; para acotar la transacción se fijó además un total de 200 turnos con el mismo transcript.too_large, y quedó en la tabla de precisiones para el humano.
<!-- aidlc-wave-memory:session-lifecycle:7bf2ba1b6821492c3c6d1478ad8be845d30f7d7bc38f25d7d0e51366d1531b0d -->


- 2026-10-03T02:19:30Z — P1 = A solo fija la humo con extras apagados; para un despliegue que active extras por PR se fijó N = 300 s (2 × p95 de 150 s), por analogía con 120 s ≈ 2 × 60 s de U4.
<!-- aidlc-wave-memory:assistant-extras:f3de672e77f44733674e33d0934a261a5a1eb444a8085183aa039c100052b756 -->


- 2026-10-03T02:19:28Z — Se interpretó que el patrón de expediente cubre toda secuencia de 6 o más dígitos (cédulas y radicados de U1) por «enmascarar ante la duda»; quedó como precisión a BR1.2.
<!-- aidlc-wave-memory:anonymizer:f10194866b28540230581bc0cbb309869c6a533648188f4f5c0b29f487a0efc4 -->


- 2026-10-03T02:37:07Z — Los turnos de la transcripción se tratan como cita literal (literal_testimony_quote de C8) en el escaneo del reporte, para que un compareciente que dice «falso» no bloquee la consolidación sin salida (hallazgo R-01 del Functional Design); quedó en la tabla de precisiones.
<!-- aidlc-wave-memory:forensic-report:fa9368d22840116dadaf3059de00c16ffe89ad7a7516f8ff8b0b46ac0ecffafe -->


- 2026-10-03T02:38:33Z — La síntesis de la pregunta va de session-api a una ruta interna de audio-worker y de ahí al TTS, para respetar que SpeechProcessing vive en audio-worker y que solo audio-worker habla con los servidores de voz (U2); queda como precisión de contrato y de red.
<!-- aidlc-wave-memory:voice:0db8cce825207dbae27245c6faf0ad4a6f28a9daca924f15f4089730524b043c -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->


- 2026-10-03T01:27:54Z — C1 aprobado tiene cuatro respuestas 409 descritas sin Problem Details, lo que la suite (BR7.2) rechazaría; no se editó contract-summary: se registró en la tabla de precisiones con el code de cada una y la falta de un code para la pregunta no aprobada.
<!-- aidlc-wave-memory:contracts:51f3cb2661b4d79e34261db002859129e957d633282de1ed9c5da48835a90763 -->


- 2026-10-03T01:38:15Z — Las métricas de autenticación, los code auth.too_many_attempts, user.weak_password y system.unavailable y la cabecera Retry-After no están en los contratos aprobados; se registraron en la tabla de precisiones en vez de editar contract-summary.
<!-- aidlc-wave-memory:identity-access:febc67ffca404d537cc6f2a432c08ae04d2d2457eb63140ebbef555f56b3dc23 -->


- 2026-10-03T02:00:43Z — BR8.2 usa turn.error.timeout para el juez que no responde, pero el enum error_code de C3 no lo incluye; se registró en la tabla de precisiones sin editar contract-summary, junto con count_tokens en C13 y el XDEL de C2/C3.
<!-- aidlc-wave-memory:text-flow:546dce5dcd396d61da83023809e7af267422394073678fe0eae8beb1f1fd3c4a -->


- 2026-10-03T02:19:51Z — C1 lista solo 201 y 409 para las decisiones aunque rules.md usa 422 y 403, C11 no permite bloquear la ronda al leerla y C15 no fija W; se registraron en la tabla de precisiones de security-requirements.md sin editar contract-summary.
<!-- aidlc-wave-memory:human-review:5871c11fb8cf6dfcfc58236c1b8cd1a4a98414825f5aa9622f297541a029ef93 -->


- 2026-10-03T02:20:05Z — InterviewerLabels y los límites del pegado no son variables de entorno sino un archivo versionado compartido por consola y servidor, para que la vista previa nunca discrepe de la división del servidor; registrado como precisión de entities.md.
<!-- aidlc-wave-memory:session-lifecycle:5b9e04f5727aff5d24334f2f0bf1aff3131afc4851c9b3bb94226efd91b70ee0 -->


- 2026-10-03T02:19:30Z — El catálogo de C1 no tiene code para los 409 de la pregunta (ya decidida, no aprobada) ni C3 lleva source_passage_ids; se registraron question.already_decided, question.not_approved y los campos de C3 en la tabla de precisiones sin editar contract-summary.
<!-- aidlc-wave-memory:assistant-extras:9fcfc63c88465044418b7a1c2bc7de52c4d115fd47054ba2b1bf2c43be68d546 -->


- 2026-10-03T02:19:28Z — El proxy recibe la lista de nombres del cliente en vez de cargarla de la base (F1 paso 2): el único pod con salida no tiene credencial de base de datos; registrado en la tabla de precisiones.
<!-- aidlc-wave-memory:anonymizer:9267ab557085891d3b7744b1c44a18372cf466d8cc6f4b5af4604165d4e0611f -->


- 2026-10-03T02:37:07Z — La atomicidad depende de open_round(for_update=True), que no está en C11 ni en el Functional Design aprobado de U7; se registró como precisión junto con report.storage_failed, el margen de 300 s del barrido y la réplica única con Recreate.
<!-- aidlc-wave-memory:forensic-report:cd5f93ae8003665184dd961d7a641835c570f1fbd2ff124ad40708a747933873 -->


- 2026-10-03T02:38:33Z — U2 no tiene subchart model-tts ni las reglas de red session-api → audio-worker y audio-worker → model-tts, y Redis no desactiva RDB; se registraron en la tabla de precisiones sin editar U2.
<!-- aidlc-wave-memory:voice:b3031d0ea6073858b299d8ec94f459e5032784a2ff0baa3954c0061a54544b5f -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->


- 2026-10-03T01:27:54Z — Meta-esquemas oficiales de OpenAPI 3.1 y AsyncAPI 3.0 copiados y fijados por SHA-256 (P2 = A) en vez de la CLI de AsyncAPI en Node: una sola pila y sin red, a costa de actualizar a mano la copia cuando cambie la especificación.
<!-- aidlc-wave-memory:contracts:c0e7a86333224f8a83d128606e23b6f5155ea235950f6676530ba702e2171785 -->


- 2026-10-03T01:27:54Z — Datos sintéticos con marca, catálogo cerrado de nombres y patrones de cédula y radicado (P4 = A): no detecta un nombre real que el autor no declare; ese riesgo residual queda en la revisión del PR.
<!-- aidlc-wave-memory:contracts:e733b0b02c9f52c39e15a994bcdd63c50ebdb97cc13a3ec409c4f498704269ec -->


- 2026-10-03T01:27:54Z — ruamel.yaml en modo seguro con claves duplicadas prohibidas, en vez de PyYAML: YAML 1.2 evita que valores como «no» se lean como booleanos y una clave repetida no sobrescribe en silencio la lista de C8.
<!-- aidlc-wave-memory:contracts:1cd1c76cf6c12a02c902d58cac698ca09eadedaa7755d85b4f3c1e9fdbfb12ba -->


- 2026-10-03T01:38:15Z — El limitador de intentos falla cerrado (503) si Redis no responde: se prefiere no dejar entrar a nadie antes que permitir probar contraseñas sin límite, a costa de que una caída de Redis bloquee el inicio de sesión.
<!-- aidlc-wave-memory:identity-access:bbc387788279ca3068b93b63c2e613eca75c9a5f0477c09c3cbabe1376438ece -->


- 2026-10-03T01:38:15Z — last_seen_at se escribe como máximo una vez por minuto aunque la consola sondee más seguido: evita una escritura por sondeo a costa de que la caducidad por inactividad tenga hasta 60 s de holgura.
<!-- aidlc-wave-memory:identity-access:3222fc55e93aff2d0f0bf2f71b40d52f849d13c74311cff5a6657f8fc5cd8ff7 -->


- 2026-10-03T01:38:15Z — llama.cpp sirve juez y embeddings con una sola tecnología GGUF en CPU, a costa de que el esquema JSON se cumpla por gramática y no por un modo nativo; la validación contra C6 en U4 sigue siendo la que manda.
<!-- aidlc-wave-memory:platform:9e4e0156aa7937a351bb89615d1755afc005bb8cc70c72618a539f31820681ed -->


- 2026-10-03T01:38:15Z — NetworkPolicy de negar todo y abrir lo declarado (P4 = A): más reglas que mantener, pero ningún pod nuevo sale a internet por omisión.
<!-- aidlc-wave-memory:platform:be2af0a10d2c4cda12b75852cf932b8ec26acb6644f131f9ad8d892c242d4043 -->


- 2026-10-03T02:00:43Z — Búsqueda exacta por versión en vez de un índice HNSW: con unos 1 100 pasajes por versión cumple 100 ms y no pierde pasajes al filtrar por versión, a costa de recorrer toda la versión en cada consulta.
<!-- aidlc-wave-memory:text-flow:00d08db64882139720cfb7f481eb6ed958cb3fb57ab586f2ab2a9ea99f464af5 -->


- 2026-10-03T02:00:43Z — Una sola ranura en el servidor del juez y un turno a la vez en semantic-agent: resultados repetibles con semilla fija, a costa de que la prueba de carga de NFR8 dure horas.
<!-- aidlc-wave-memory:text-flow:0432ea3d9d6cf424f81dd3f5a67bc5d6dfbc91cda2c65c19fa1372d4ea3fd6e1 -->


- 2026-10-03T02:00:43Z — El bloque de datos del prompt va como JSON en el mensaje user en vez de delimitadores de texto: el testimonio no puede cerrar el bloque, a costa de unos tokens más.
<!-- aidlc-wave-memory:text-flow:47d66d3c08397169c90acc32b3a856f634aacbf6185e41d75639e66de378f150 -->


- 2026-10-03T02:19:51Z — Bloqueo de la fila de la ronda (FOR UPDATE) en vez de SERIALIZABLE: serializa las decisiones de una sesión sin reintentar operaciones que no son idempotentes, a costa de que U7 deba tomar el mismo bloqueo al consolidar.
<!-- aidlc-wave-memory:human-review:ea174961c8e5ac00076bf6979bba7a808ee3ed40f84508a3cfa04027b6c66609 -->


- 2026-10-03T02:19:51Z — La razón AIR se calcula al decidir y vive en memoria del proceso: /metrics no depende de la base, a costa de tener que cambiarlo si session-api pasa a varias réplicas.
<!-- aidlc-wave-memory:human-review:4c2ccdad090adb3a4cbeb087253732baea84e17bf2b3e98fec1ef73635181720 -->


- 2026-10-03T02:20:05Z — Latido escrito como máximo cada 15 s con la hora de la base: ≤ 4 escrituras por minuto y sesión en vez de 30, a costa de que la suspensión pueda llegar desde 165 s tras el último sondeo real en vez de 180 s.
<!-- aidlc-wave-memory:session-lifecycle:b7ba1bc15e98ab34fa980657c8eff38c0aa433bb6b1791af34d4c2f86966f3ac -->


- 2026-10-03T02:20:05Z — Republicar en el reenvío idempotente en vez de una tabla outbox: sin piezas nuevas, a costa de depender de que el navegador reenvíe tras un 503 (si no, el plazo de U4 cierra los turnos en error).
<!-- aidlc-wave-memory:session-lifecycle:4001a735d1e3b626efa94ce7b520138831ae5dbe3910ac1d5c457daf7abcab01 -->


- 2026-10-03T02:19:30Z — Con extras activos el plazo base sube a 600 s y el reclamo a 480 s para cubrir hasta 3 llamadas en serie al juez, a costa de que la cola solo admita 24 turnos sin vencer; por eso tres sesiones concurrentes con extras quedan fuera del MVP.
<!-- aidlc-wave-memory:assistant-extras:43c00689958d532d515ea30907689b6fe3080c50c365c7d69ae21ee478890b55 -->


- 2026-10-03T02:19:28Z — 502/504 del proxy son finales y no vuelven por XAUTOCLAIM (precisión a NFR10.16 de U4), a costa de reintentos manuales, para que nada se reenvíe fuera del clúster.
<!-- aidlc-wave-memory:anonymizer:2927ea2c5dad94b7c4d401920d963e71a51b54c09861d0c72662036b867f8ee4 -->


- 2026-10-03T02:37:07Z — El archivo se escribe dentro de la transacción con la ronda bloqueada (P2 = A): nunca hay versión sin archivo, a costa de que una decisión simultánea espere hasta 2 s; se acota con p95 ≤ 1,5 s de la consolidación.
<!-- aidlc-wave-memory:forensic-report:89ef136154c19a7b0b430f7e40f527ccf303a7a8d962e9362254cb78308232d0 -->


- 2026-10-03T02:37:07Z — Una sola réplica de la API por el PVC ReadWriteOnce y el barrido al arrancar: cierra la carrera del barrido sin bloqueos distribuidos, a costa de no poder escalar la API sin cambiar el almacenamiento.
<!-- aidlc-wave-memory:forensic-report:0c9c80b48d966dabae2261e6bf6ccf64cddfe7520100cfb556a72288f662bb4a -->


- 2026-10-03T02:38:33Z — Un solo Redis con AOF en vez de un Redis sin persistencia para el audio: menos piezas, a costa de que el audio quede en el AOF del PVC hasta la reescritura (declarado y probado en NFR10.4).
<!-- aidlc-wave-memory:voice:859ff78959d11b1858352f8797367821d1a49f6dbfbc22e9617acc1743222ca3 -->


- 2026-10-03T02:38:33Z — Un Whisper caído deja el turno de voz en error en segundos en vez de devolver el mensaje a la cola como el juez de U4: respeta BR3.4 y da respuesta inmediata, a costa de perder el audio y grabar de nuevo.
<!-- aidlc-wave-memory:voice:35403d74880254ae6748c76e99305b51099c0dedd8dae7143dfa574bba4e35ca -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

- 2026-10-03T01:38:15Z — Confirmar en Infrastructure Design que el CNI elegido hace cumplir políticas de salida y que la imagen de CloudNativePG trae pgvector.
<!-- aidlc-wave-memory:platform:249cf5142fc90b9a2757384194c3651db8adb33d3208163d4031bfd5947178c5 -->

- 2026-10-03T02:00:43Z — Confirmar al construir el Golden Dataset que ninguna transcripción pasa de 15 turnos; si pasa, la prueba de NFR8 con transcripciones pegadas puede vencer plazos.
<!-- aidlc-wave-memory:text-flow:e6cf9647bb7ef6ca1753171a292eba1c0c7ad269340d073a2b2d3052789ea2ec -->

- 2026-10-03T02:20:05Z — El pegado de 60 turnos llega al tope de 3 600 s sin margen si el juez va al p95 de 60 s; la corrida NFR3.11 dirá si hay que bajar el límite.
<!-- aidlc-wave-memory:session-lifecycle:cae07c47b0a1dc213df9531758ab6b07433b3ff02520bb7b13ce527ea82514f9 -->

- 2026-10-03T02:19:30Z — Falta decidir si una pregunta aún proposed puede decidirse tras finalizar la sesión; Functional Design no lo fija y aquí no se inventó un code para ello.
<!-- aidlc-wave-memory:assistant-extras:63dd49b9df9ff302d37ad3908021e3600564eeb171dac3af734f5c01081201b4 -->

- 2026-10-03T02:19:28Z — Confirmar en Infrastructure Design si el CNI admite políticas por FQDN y cómo limitar la resolución DNS externa (T15) antes de cualquier PR que habilite el proxy.
<!-- aidlc-wave-memory:anonymizer:61b0590c1ecaa50cfefd5f3340336c6647b82601af1e4e5137e187213c663e8f -->

- 2026-10-03T02:37:07Z — El RPO/RTO de los reportes depende del respaldo conjunto de CloudNativePG y del PVC, que fija Infrastructure Design; NFR10.20 solo verifica la restauración.
<!-- aidlc-wave-memory:forensic-report:0024397b2c79fcd927b969cbdf22d7f7e18d33058864b0dd8c811dfac70ad4ee -->

- 2026-10-03T02:38:33Z — Una transcripción de más de 2 000 caracteres (habla rápida de 120 s) se trata como turn.error.invalid_output; confirmar en la aprobación si se prefiere admitir turnos de voz más largos.
<!-- aidlc-wave-memory:voice:e0ac751940d0dd1641fa4f91f0b1668f120239024b1c99f40748d176d615c7eb -->
