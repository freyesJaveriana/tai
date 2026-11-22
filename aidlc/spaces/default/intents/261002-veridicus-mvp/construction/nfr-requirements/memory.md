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


- 2026-11-22T13:16:31Z — Segunda pasada: las cifras nuevas de C25 que piden U5, U10, U12 y U13 solo se nombran aquí; sus valores los fijan esas unidades en su NFR, y U1 valida la forma del catálogo y que cada maxLength coincida con su cifra.
<!-- aidlc-wave-memory:contracts:ebefe169deb95be71ee55b8fed1f62f157edab86f0a2167418ea341289f6bb51 -->


- 2026-11-22T13:16:31Z — Revisión 2 generada con P7 = A y P8 = A: el catálogo de errores declara un estado por code (limits.exceeded = 413) y U1 suma contracts/ts/; la sección clarifications de U8 (FD-U8-09) entra en C19 v2 como cambio mayor, porque C19 es estricto (BR1.4).
<!-- aidlc-wave-memory:contracts:6ee6f89cc91c109a25462f5ba4f8c3225b6f4941f19302cb823fac9863cf24db -->


- 2026-11-22T13:40:27Z — Segunda pasada sin preguntas: el tope de 128 de la contraseña pasa a ser cifra de C25 validada por el esquema (422 validation.invalid_request), y la política (8, composición, lista común) sigue con user.weak_password, para no chocar con BR8.4.
<!-- aidlc-wave-memory:identity-access:eb766e79afe36a94ec2e43a1d7766b38ae99715bda63046ee74a06f01526866f -->


- 2026-11-22T13:40:27Z — «El único con DELETE» de NFR11 se leyó como sobre historiales y tablas purgables, porque entities.md aprobado ya hace que session-api barra WebSession a los 7 días; quedó como NFR-U3-02.
<!-- aidlc-wave-memory:identity-access:231c13a83dac2c1d54cd3050a71d7a10baa7a80dba3d63be476e6c8e7582570a -->


- 2026-11-22T13:38:45Z — Segunda pasada: FR12.3 dice «todos los pods», así que la negación de salida se extiende a ingress-nginx, cnpg-system, monitoring y keda; semantic-agent ya no alcanza PostgreSQL (C9 Retirado, CD-06).
<!-- aidlc-wave-memory:platform:615445753854a2906b124b8eb3c0ee651c83849c95e41895d30985dada7b3309 -->


- 2026-11-22T13:38:45Z — Los Jobs de retención y create-admin van en un chart que Argo CD no sincroniza, porque VE-12 dice que el sistema no programa el borrado y U13 F7 pide que lo lance el humano.
<!-- aidlc-wave-memory:platform:cb29e910947bd769f1edf0cccbf341f877d7e0f560ef6edda6362784c6d2a794 -->


- 2026-11-22T13:37:41Z — Segunda pasada: el cambio 01 supera la parte de P1 = A que dejaba el proxy apagado y con un solo destino (FR11.3 MUST, FR14.1 y C13); se conserva el ADR del proveedor como condición para que un modelo entre a ProviderCapabilityTable, sin preguntar.
<!-- aidlc-wave-memory:anonymizer:bd933289da590e89a01b1c0240799449d0622b8fd9508217ffc5bcc9ae81a10c -->


- 2026-11-22T13:58:51Z — U11 es `library`: por el archivo de etapa le tocan security, tech-stack y traceability; se añadirán performance y reliability porque NFR3, NFR8 y los plazos de C25 recaen aquí.
<!-- aidlc-wave-memory:incoherence-analyzer:78a64f7a9d47d45ade5bfc71fa79b2afaad4eeadb415cf2668bcf876533cbba2 -->


- 2026-11-22T13:58:51Z — Las cinco cifras de C25 de la configuración efectiva (plazos por llamada y de corrida, ventana y solapamiento) se leen como de U11, porque C18 dice que U11 decide esos esquemas y B11 es su primer consumidor; el catálogo guarda el máximo (ZINE) y cada despliegue lo baja por entorno.
<!-- aidlc-wave-memory:incoherence-analyzer:0fd21d38a944880712c78a2a46eef25b4737b831009dccfe99987881fa43f39f -->


- 2026-11-22T14:22:49Z — Segunda pasada: S1 = A se conserva en su idea, pero ahora suma los plazos propios de las corridas que van por delante en la cola FIFO única, con un tope nuevo de C25 (run_queue_wait_max_s). Sin eso, una corrida incremental detrás de un modo final vencería sin fallar nada.
<!-- aidlc-wave-memory:text-flow:bb667932fb806ec6f63ae8302feee39e1f79bf153966f6af4bc9879dc1f59319 -->


- 2026-11-22T14:42:08Z — Segunda pasada sin preguntas: el costo de la permutación en todo-local se resolvió con la regla del 98 % que fijó U11 (NFR-U8-01), y el tope del tema con los topes de bytes ya existentes en C25 (NFR-U8-03).
<!-- aidlc-wave-memory:assistant-extras:ad90c8fa25ba0b2ee3560d27515efb2ae1dd084e405de675c170e6f421109d0e -->


- 2026-11-22T14:42:08Z — «Con y sin permutación» de BR6.5 se mide por papel en la misma corrida, porque BR6.1 prohíbe un perfil con permutation false y la CLI solo acepta perfiles aprobados (NFR-U8-09).
<!-- aidlc-wave-memory:assistant-extras:99458ab306bad0925747efc2c19fea4b851dafa15b9f4900cd68cd19a28a90b8 -->


- 2026-11-22T14:42:40Z — Sin preguntas: las cifras de C25, el volumen de la lista y las latencias salen de las fuentes; el costo de P1 = A (E18, E19) lo dejó el Functional Design para la aprobación, no para esta entrevista.
<!-- aidlc-wave-memory:research-reports:c1d5d401296ad2fc4724df62d99f767d7738e263233a1763b5ac80740255a555 -->


- 2026-11-22T14:42:40Z — Los topes se dimensionaron con un reporte sintético estimado de 240 corridas × 30 llamadas (~3,3 MB): 8 MiB y profundidad 8, frente a una profundidad natural de 5 en C19 v2.
<!-- aidlc-wave-memory:research-reports:b0a36eb58506cbc0c9bbe0dadbb7a2d15ee36608cac6ad61e9665196d4bab15a -->


- 2026-11-22T14:43:57Z — Segunda pasada sin preguntas: AC5.4.4 frente a AC5.4.2 ya lo resolvió P4 = A del Functional Design de U3 con la matriz de FR1.2, y se aplicó como NFR10.19 con la precisión NFR-U5-03.
<!-- aidlc-wave-memory:human-review:47284c2d4e149d6eb3063a805446725ba342e194870b289288235fd020fc0ded -->


- 2026-11-22T14:43:57Z — La ventana AIR se leyó como en C15 v2 (últimas 8 decididas, ordenadas por el change_seq de la decisión vigente, heredadas incluidas), lo que retira las «ignoradas» y cierra R-01.
<!-- aidlc-wave-memory:human-review:a12a9e9d10a8a33fdda75936151ce4508066260a4f8425b3395b1fe70cc88e6d -->


- 2026-11-22T14:43:24Z — Segunda pasada sin preguntas: import_file_max_bytes = 2 097 152 (archivo máximo ≈ 1,4 MB, margen ≥ 45 %), heartbeat_timeout_s = 180 y dos cifras nuevas de C25 (session_sweep_interval_s = 30, heartbeat_write_min_s = 15); la lista no se pagina en el servidor.
<!-- aidlc-wave-memory:session-lifecycle:75dbfc43c786635336dc4cb091a8b6c53a9c29a0e554909668d07f645920b233 -->


- 2026-11-22T14:43:24Z — C1 declara 200 en PATCH /analysis y la regla de U1 exige 202 en toda ruta que encola IA; se propuso 202 como NFR-U6-03 para decidir en la aprobación.
<!-- aidlc-wave-memory:session-lifecycle:c60bdb38dad9237401fe838acfa5ba7e1002b534ac9ef5bce9ae0c5b0d567e7e -->


- 2026-11-22T15:08:17Z — NFR-U11-11 no es una contradicción entre fuentes aprobadas: C13 revisión 3 ya declara transcribe y synthesize (SHOULD, solo locales), así que van en el puerto de U11 escritos por U9 en B9, sin PR de U1 (D13, NFR-U9-01).
<!-- aidlc-wave-memory:voice:7ac96be99d40b516342cece516b80fa181b8891aa67b6d73e04cd9c5dfffb9a9 -->


- 2026-11-22T15:13:34Z — Sin preguntas: las preguntas abiertas 1–5 del Functional Design las resuelven U1, U2, U3, U5 y U7; el intervalo de bienestar no tiene cifra del TG en el repositorio, pero es un aviso que no bloquea, así que va como propuesta (2 700 s) a NFR-U13-01.
<!-- aidlc-wave-memory:ethics-governance:820ee1db15bc8957dc36637753c96a95fecbf0a2ec1dfc411cbd63a93949efe4 -->


- 2026-11-22T15:13:34Z — El comando de consulta sigue a verify_store de U7 (kubectl exec, READ ONLY, sin Job ni rol propio), con 1 000 filas por defecto y 10 000 como máximo.
<!-- aidlc-wave-memory:ethics-governance:65e0cbe4a4fd9e1b11a46afe1c7b5cde49c4e2a2d7e240b2a4394261ab52d01d -->

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


- 2026-11-22T13:44:22Z — F9 de U10 exige igualdad exacta con el Corefile; con P5 = A, U2 le pasa el Corefile sin la lista cerrada de infraestructura (github.com) y comprueba esa lista aparte (NFR-U2-03).
<!-- aidlc-wave-memory:platform:71f64c3d681f327649a54cd5726edbd9638e4e9c5a86792316f41a404d3567d5 -->


- 2026-11-22T14:36:18Z — P6 = A (250 000) contradice el 186 000 que ya aprobaron U10 y U11. No se editaron sus artefactos: NFR-U4-02 les pide repetir sus comprobaciones con 250 000 y fija model_call_timeout_s ≥ 270 s para todo despliegue con perfil comercial.
<!-- aidlc-wave-memory:text-flow:3486deb61c285f1502ef9942072101b47e55cf58e476d177ac3678e699272caa -->


- 2026-11-22T14:42:40Z — BR5.1 dice «ni en disco», pero `request.form()` de Starlette escribe en un archivo temporal por encima de 1 MiB y el Ingress guarda en disco los cuerpos de más de 16 KiB: se fijó un análisis del multipart en memoria (D2) y se pasó el Ingress a Infrastructure Design (NFR-U12-05).
<!-- aidlc-wave-memory:research-reports:cedfbddc21a9e8ffbdfb2c08cbce14820485d20b55a7e95529644d0989d2fc4f -->


- 2026-11-22T14:58:28Z — Segunda pasada: se retiró report.storage_failed (500 system.internal, NFR10.17 de U3), las métricas salen de C15 (NFR-U3-03), verify_store pasa a kubectl exec en el contenedor api sin Job ni rol propio (cierra R-01) y el barrido corre también cada 60 s (cierra R-02, NFR-U7-13).
<!-- aidlc-wave-memory:forensic-report:f9a9de02b431ca89a12ed9a1502b469c7d99f0f062647ef182c1b4f8312b72c9 -->


- 2026-11-22T15:08:17Z — La duración del MP3 se mide con un lector de tramas propio en vez de mutagen, porque mutagen estima la tasa variable desde la cabecera Xing, que se puede falsear (BR2.3, E31).
<!-- aidlc-wave-memory:voice:818b900f6f339118273b06f2ea74b5b14582b1f7a8c4477427c9ff004b507b26 -->

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


- 2026-11-22T13:40:27Z — AccessLog.record en un SAVEPOINT de 500 ms: un fallo del registro no revierte las escrituras del manejador (BR9.3), a costa de un punto de guardado por lectura marcada.
<!-- aidlc-wave-memory:identity-access:a7288ba7fcd2d74d68e0d960f19d009c564a34e69fcf243835ead3c3d14fb587 -->


- 2026-11-22T13:40:27Z — Las métricas de U3 quedan internas de session-api y no en C15 (R-05); la etiqueta code pasa a error_code para seguir la lista de U1 sin pedirle un cambio.
<!-- aidlc-wave-memory:identity-access:51409cca30c073936fd48dc3ea32e7634c1801c803daf9590617c28db9bfb1b3 -->


- 2026-11-22T13:44:22Z — P5 = A: Argo CD conserva la sincronización desde GitHub a cambio de una segunda salida sin datos, y queda como riesgo residual una conexión por IP literal desde el proxy o desde argocd-repo-server.
<!-- aidlc-wave-memory:platform:e596adab8b97fd20b6ba7944975dd768b275de93d3d2a4ecf8a577407c04c5a4 -->


- 2026-11-22T13:37:41Z — Las cifras de C25 de U10 (2 MiB y 0,15) se atan con comprobaciones de nivel 0 a transcript_max_chars y model_call_timeout_s de otras unidades, en vez de esperar a que U11 fije su plazo.
<!-- aidlc-wave-memory:anonymizer:f2f9cd8d3ff917848091d2d26b0c568854053ceff0bcee83609c7f814e2228fc -->


- 2026-11-22T13:51:20Z — La prueba de 0 fugas corre en nivel 1 con el NER real montado sin red, y el nivel 0 usa un NER diminuto de prueba: el nivel 0 no carga modelos, a costa de que la fuga por el NER solo se detecte en nivel 1 (también bloqueante).
<!-- aidlc-wave-memory:anonymizer:ef31dd5ed4e13a5508dae8ecce1e13f7238cc638c07e1481f42eb6e7390315e3 -->


- 2026-11-22T13:51:20Z — Los adaptadores usan httpx directo y no los SDK de los proveedores: los SDK reintentan, fijan su URL base y añaden cabeceras propias, y eso contradice NFR1.8 y NFR10.4.
<!-- aidlc-wave-memory:anonymizer:5e3b754d9ef36ee9772881a9f78e1d6f8aab5edef1fe21ca8a2456c84648b417 -->


- 2026-11-22T14:15:13Z — Con el verificador local de P1 = A y la permutación activa en todos los perfiles (FD-U8-08 manda sobre el punto 3 de la sección 2), el N del humo sube de 240 a 300 s y el tope incremental de C25 de 900 a 1200 s, a cambio de que solo Anthropic reciba datos.
<!-- aidlc-wave-memory:incoherence-analyzer:6671b64abf902dad0b4aed79e4396e1f2ce399e861706d311098315580738cea -->


- 2026-11-22T14:22:49Z — El trabajador renueva cada 15 s el reclamo del mensaje en curso, y por eso claim_idle_ms baja a 60 s aunque un modo final dure una hora. El precio es un hilo más en semantic-agent y una precisión a C2. A cambio, un trabajador caído se reemplaza en un minuto y no en lo que dura el plazo más largo.
<!-- aidlc-wave-memory:text-flow:934deb711b342fef6f2cc923dce3e0ea2cc944d01e8267d577fa6f0fc381aee9 -->


- 2026-11-22T14:42:08Z — La tasa de aclaraciones descartadas se reporta sin bloquear, con señal en 0,50, porque U8 no tiene palanca propia sin relajar las reglas de VE-05 y un umbral sin línea base ya no se podría bajar; el 0 % de citas en los temas sí bloquea (NFR-U8-02).
<!-- aidlc-wave-memory:assistant-extras:8e67aeee578760466e94b5c656ac048edea3196c5ab4b4f8cf7212e950e1ca58 -->


- 2026-11-22T14:43:57Z — Se retiró veridicus_review_rejections_total porque C15 v2 no admite la etiqueta code; los rechazos se cuentan con el log review.decision_rejected, a costa de no tener una serie en Grafana.
<!-- aidlc-wave-memory:human-review:d45df24b624cab8a452000b678dbfe7f68864bd411dec1b0347ee37f5fb0153a -->


- 2026-11-22T14:43:57Z — purge_session borra con DELETE … RETURNING en orden explícito y no con ON DELETE CASCADE: el recibo sale de lo que de verdad se borró, a costa de mantener el orden en código.
<!-- aidlc-wave-memory:human-review:a9b270a0a9f515f92bf6299fa0f14089dfe73a9534043153e4b9a34944503bb9 -->


- 2026-11-22T14:58:28Z — report_max_bytes = 8 MiB con 413 limits.exceeded (NFR-U7-01): cubre el caso máximo de C25 con margen y acota la memoria, a costa de que el peor caso teórico de 2,4 GiB no quepa en la cuota de 2 GiB (riesgo aceptado en NFR8.5).
<!-- aidlc-wave-memory:forensic-report:a57ea40aabe10f5513660757f1193032830658e8cb4b439d517aecfd123b37ac -->


- 2026-11-22T14:58:28Z — La exportación revierte toda la transacción si AccessLog falla en 500 ms (503 report.export_not_recorded), a diferencia de la lectura de U3 en punto de guardado: ninguna copia sale sin registro (A-3), a costa de que un adaptador caído impida exportar.
<!-- aidlc-wave-memory:forensic-report:6916e1c7102b73ecfb5081a56c3197a576cc72a2ee9e42d05cac893242cb613b -->


- 2026-11-22T15:08:17Z — Base del plazo de audio a 360 s con 2 entregas en vez de 300 s con 3: la segunda entrega cabe con 60 s de margen (cierra R-03), a costa de esperar más un turno cuyo trabajador se cae.
<!-- aidlc-wave-memory:voice:8abda0e5f9849764fffac99e1d68973a012def5beec7f1fa25c13ba173b4bf15 -->


- 2026-11-22T15:13:34Z — Con Redis caído, el Job no borra la sesión (failed, system.unavailable) en vez de borrarla sin cancelar sus corridas: el borrado se retrasa a cambio de que ninguna llamada salga para una sesión ya borrada (NFR-U13-05).
<!-- aidlc-wave-memory:ethics-governance:1f15b4cf865aba2069195a3b0ea8173ba141bc98b13ab3bfaf888f9ef82dafe9 -->


- 2026-11-22T15:13:34Z — Una sola ejecución del Job a la vez con pg_try_advisory_lock y código de salida 3, en vez de confiar en que el humano no lance dos (NFR8.6 de U7, NFR-U13-04).
<!-- aidlc-wave-memory:ethics-governance:834e40b8288ba8cbb04be6366a9e5b36a5f0a4255754279f7c460c8ac76855c8 -->

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

- 2026-11-22T13:16:31Z — P7: limits.exceeded responde 413 en U4, U6 y U12 y 422 en U5 y U13; con una clase por code (BR7.4) no caben dos estados, así que se pregunta y no se generan artefactos.
<!-- aidlc-wave-memory:contracts:83b2238c20ccd74e5c1a3820e4340f339ae02f59cf27cc11807c892cc20d5f0c -->

- 2026-11-22T13:16:31Z — P8: la revisión 1 dejó la suite sin Node, pero la regla 1 de contract-summary y BR1.9, BR9.7 y BR12.3 piden ajv strict y JCS en TypeScript en nivel 0; dónde corre esa mitad cambia el alcance de B1.
<!-- aidlc-wave-memory:contracts:5f3e1c4e9366f35c84206ef97b6cdaa564e3801444ffe36dd0b5ee7deb11ff27 -->

- 2026-11-22T13:38:45Z — P5: Argo CD necesita github.com, lo que contradice FR12.3 y la igualdad de AC11.5.2; se pregunta al humano antes de generar la revisión 2 (recomendada A, excepción declarada solo para argocd-repo-server).
<!-- aidlc-wave-memory:platform:04cb8310c7f7577d77f03baeeeb74f76cfcc5ad765ce24f3247308c605872324 -->

- 2026-11-22T13:37:41Z — Se preguntó solo el proveedor comercial de la primera rebanada (P2): ninguna fuente aprobada lo fija y decide qué tercero recibe primero el testimonio seudonimizado, incluido el piloto; no se generaron artefactos.
<!-- aidlc-wave-memory:anonymizer:35162a2146b1f131b153addc23e212b5d2b268ced79a27e03581d05221e556e5 -->

- 2026-11-22T13:51:20Z — P2 = A (Anthropic primero) obliga a que el generador del conjunto sintético sea de Google u OpenAI y distinto del verificador (NFR5.2, NFR-U10-07); lo decide U11 al fijar sus perfiles de evaluación.
<!-- aidlc-wave-memory:anonymizer:492da4d14682f31f5a86422534e68088f494449bb829bc6208ab5f6e6d16aa7e -->

- 2026-11-22T13:58:51Z — Tres preguntas legítimas: verificador de `comercial-piloto` y familia del generador (cambia qué proveedor recibe datos y el alcance de B10; gpt-oss cuenta como línea de OpenAI), umbrales estadísticos del nivel 2 (riesgo de la compuerta) y composición mínima del conjunto (alcance de B11, R8).
<!-- aidlc-wave-memory:incoherence-analyzer:d6b8120ca9f191f5970f0d233fe38375d223b743ac6594f670ad5d6ef17ffe9f -->

- 2026-11-22T14:22:49Z — FR3.7 pide margen sobre la entrevista más larga del piloto (unos 186 000 caracteres), pero los NFR de U10 y U11 usan 186 000 como el máximo de C25. Se pregunta como P6, porque la cifra decide cuánto testimonio seudonimizado sale en una llamada. El turno más largo y el número de turnos del piloto no están en Git, así que se pregunta como P7 y no se generan artefactos.
<!-- aidlc-wave-memory:text-flow:bf5c3978c3608b9d7dc87ac239340bd8ad76d5d505209808997b047114a5cb2a -->

- 2026-11-22T14:43:24Z — El modo final de 2 000 turnos con todo-local puede pasar de run_deadline_final_s de desarrollo (3 600 s, de U11); NFR3.17 lo mide sin umbral y el Ingress de U2 no debe escribir en disco el cuerpo del pegado ni del archivo (NFR-U6-06).
<!-- aidlc-wave-memory:session-lifecycle:0b4588ef2ec0e932b09f5c80ab9cdce0e0dfdf20f292f707b552646e341f95e6 -->

- 2026-11-22T15:08:17Z — El audio conservado queda sin cifrado en reposo (mismo criterio que los reportes de U7 y A-2); se presenta como riesgo aceptado en la aprobación.
<!-- aidlc-wave-memory:voice:88b53ebba1e33714e70ccb08d08d9b73a27f90359c09b1dc9831fd64dfffa9ae -->
