<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->


- 2026-10-03T10:20:04Z — U3 fija la forma del despliegue de session-api (réplica, sondas, base de recursos) porque es el primer Bolt que lo construye; U4–U7 solo añaden configuración, salida de red y memoria.
<!-- aidlc-wave-memory:identity-access:ee13dad0f1733700564ca6da7f9c12e4c5e87b1fbe9036337da2d8829f5adc88 -->


- 2026-10-03T10:20:04Z — P3 («una cifra intermedia, como 24 gb», partición Ubuntu con Docker) se leyó como Ubuntu nativo con 24 GB; con P5 = B se dieron 18 GiB y 10 CPU a Minikube y 6 GiB al sistema.
<!-- aidlc-wave-memory:platform:a181482362a05343c7a28663a4bae60ba99de05547f116895ef7f3347e981163 -->


- 2026-10-03T10:41:31Z — P1 («la máquina demo tiene 32 gb… deja 4 gb al sistema») se aplicó como Minikube de 28 GiB en la máquina de demostración, y P2 = A extendió la misma regla a la de desarrollo (20 GiB); los límites con ≥ 20 % de margen quedaron como valores de U4 y precisan los de U2.
<!-- aidlc-wave-memory:text-flow:23c2871a596a41bfcb78c0640eaec59b66411116ad98ce198d00e5596597e63c -->


- 2026-10-03T11:00:11Z — U6 no añade procesos ni reglas de red; lo propio son tres ajustes en el bloque común de los values, un cuarto hilo del trabajador y una migración aditiva.
<!-- aidlc-wave-memory:session-lifecycle:7aa15d70f3c6835455533678f19d306096b9d32001ae1bfe8f472103c068a7d5 -->


- 2026-10-03T11:00:42Z — La réplica única de session-api se trató como requisito de U5 (D7 calcula la razón AIR en el proceso) y no solo como valor por defecto de U3; pasar a más réplicas exige antes cambiar D7.
<!-- aidlc-wave-memory:human-review:d8743e8473928475721e0e9deef5a23a441312888435f5bde019c49ccc1830d8 -->


- 2026-10-03T11:00:43Z — P1 = A se materializó como dos Application (veridicus-dev sin values-extras.yaml, veridicus-demo con values-gpu.yaml + values-extras.yaml) y una comprobación offline que impide incluirlo en desarrollo.
<!-- aidlc-wave-memory:assistant-extras:b3bfe15d9ac75933762ec13639982ac76d425511852db14bd709d0219a1df01a -->


- 2026-10-03T11:01:37Z — P1 = A se aplicó como un Corefile versionado en deploy/cluster/coredns.yaml con zonas cluster.local, github.com y, solo con el proxy habilitado, exactamente upstreamHost; el resto responde NXDOMAIN y check-coredns.sh detecta la deriva que Minikube introduce al arrancar.
<!-- aidlc-wave-memory:anonymizer:ea17a97d7c846d581d5b6b71530f2ea050c034c2dcf6370d9e7bcdb9136a5dce -->


- 2026-10-03T11:50:55Z — P1 = A se aplicó como campo `format` en `models.lock` con lista cerrada por servidor (gguf, ctranslate2 solo Whisper, onnx solo la voz); los pesos de Systran son float16 y el int8 se hace al cargar, sin archivo aparte.
<!-- aidlc-wave-memory:voice:09f78156e50370043b9e937fb655cc8d0cb723cc1ea75050de46b6d2234bcd09 -->


- 2026-10-03T11:51:00Z — El aprovisionador hostPath de Minikube ignora fsGroup y no publica kubelet_volume_stats: VERIDICUS_REPORTS_DIR pasa a ser un subdirectorio reports/ 0700 que crea el proceso, y el llenado se mide con la cuota propia de P3 = A.
<!-- aidlc-wave-memory:forensic-report:5e0548fae1af4d166053aff1ed58a02c1b2582a2e6387ab6a9875b93b39066d8 -->


- 2026-11-23T00:47:00Z — Segunda pasada sin preguntas: la red, CoreDNS, el Secret, el endurecimiento y los requests/limits pasan a U2, así que U10 solo fija lo que necesita del pod y del anfitrión de la CLI y lo propone a U2 (IDS-U10-02 a IDS-U10-06); máquina supuesta de 64 GB solo CPU.
<!-- aidlc-wave-memory:anonymizer:605a345e7e572a2dec9593263587bcb20188f72f6211bb379bfe9cde71e34370 -->


- 2026-11-23T00:43:37Z — Segunda pasada sin preguntas: la sonda de disponibilidad pasa al /readyz completo porque NFR10.13 revisión 2, C16 v2 y el NFR Design revisión 2 lo fijan después de P1 = B, que queda Retirado (IDS-U3-01).
<!-- aidlc-wave-memory:identity-access:23223549f5481b64e9cac2d9830ccc8ae81db0d22e020116a639556dd99bd8aa -->


- 2026-11-23T00:43:37Z — Se usa el supuesto de una sola máquina de 64 GB solo CPU con Minikube por decidir en U2; la parte de U3 en session-api no cambia (384/768 MiB).
<!-- aidlc-wave-memory:identity-access:141f75b9d0edec3bf883cc31780f1b2b2b1c9a3a1336d504c076268eded561a4 -->


- 2026-11-23T00:41:02Z — Segunda pasada: el cambio de máquinas (sin GPU, un solo equipo de 64 GB con WSL2) cambia los recursos, así que se preguntó (P6–P8) y no se generaron artefactos; el juez de todo-local entró como pregunta porque NFR-U11-07 deja su archivo a U2 y fija casi la mitad de la memoria.
<!-- aidlc-wave-memory:platform:16e60c2d50e0784c439cce07b89a7a02a8dbe2c9ac4aa4d075fae0f7b6d35c3d -->


- 2026-11-23T00:57:53Z — «Reporte adjunto al PR» se lee como un par versionado (C19 v2 y una evidencia con el commit evaluado) en evaluation/reports/level2/, porque C19 no tiene campo de commit y la CI no puede leer adjuntos (IDS-U11-04).
<!-- aidlc-wave-memory:incoherence-analyzer:46eeeb6ab83e7c302a623d29bcfcb67e717a3561091fe92d1683009056b22345 -->


- 2026-11-23T01:10:01Z — Segunda pasada sin preguntas: U4 adopta los recursos que ya fijó U2 para el trabajador y semantic-agent (caben con el /tmp en memoria de 16 MiB) y solo pide a U2 lo que falta, sin darlo por aplicado (IDS-U4-01, -02, -03, -07, -10, -14).
<!-- aidlc-wave-memory:text-flow:2c60cb25b061fed80c5abc5e6ba51c2f274eebb0864eea0a7c781a796ca410b4 -->


- 2026-11-23T01:26:02Z — La memoria de la API que fijó U2 (1 152 MiB = 1,2 × 944) no incluye las subidas de U12: con dos subidas no cabe ni sin margen (1 404 MiB); se pide a U2 1 792 MiB (IDS-U12-01), sin tocar `requests`.
<!-- aidlc-wave-memory:research-reports:53431723caed19d55ccbba04244710a864437acfa6a035242c397108a7d98d5e -->


- 2026-11-23T01:26:02Z — NFR-U12-06 deja abierto imagen o ConfigMap: perfiles y precios desde `veridicus-profiles` (lo mismo que corre `semantic-agent`) y etiquetas en la imagen, para no ampliar `check-no-data.sh` (IDS-U12-03).
<!-- aidlc-wave-memory:research-reports:d5e57735708a07e916fff7f55609896beb2785eb11f43e253a885e4f538c22b4 -->


- 2026-11-23T01:30:59Z — Segunda pasada sin preguntas: P1 = A pierde su objeto con el cambio 01 (no hay extras que encender) y U8 no añade nada al despliegue salvo la migración, dos contadores y dos paneles (IDS-U8-01).
<!-- aidlc-wave-memory:assistant-extras:cc37ecf85be4fee5903d2e6858b539bdd6a2043345e125bab12cf9b695a5216f -->


- 2026-11-23T01:27:06Z — Segunda pasada sin preguntas: U6 no cambia ninguna cifra de pod; con sus +100 MiB la API queda en ≈ 826 MiB frente a 1,125 GiB, aun con tres consolidaciones de U7 a la vez.
<!-- aidlc-wave-memory:session-lifecycle:2145c011d94a346a9ac9995eb5e792be62ed4cfbba22c7fe2c6d0a70f679e030 -->


- 2026-11-23T01:31:23Z — Segunda pasada sin preguntas: U5 no añade procesos, memoria fuera del límite de 1,125 GiB de U2, red ni Secrets; su código corre en la API, el trabajador (propose) y el Job de retención (purge_session), y solo pide a U2 VERIDICUS_DB_LOCK_TIMEOUT_MS en cada contenedor de session-api que abre conexiones (IDS-U5-02).
<!-- aidlc-wave-memory:human-review:d7b85d333c8e0ca30c71c25afe3a4479133e25b10309a1278ab3d9ee7fc06744 -->


- 2026-11-23T01:41:06Z — U2 revisión 2 dejó la API en RollingUpdate, pero NFR8.6 y P1 = A siguen pidiendo Recreate: no es una contradicción nueva (la resolvió el humano en la revisión 1), así que va como petición a U2 (IDS-U7-03) sin pregunta.
<!-- aidlc-wave-memory:forensic-report:326c92c6659d02c91bbbe71448f10ffeecf7e2b3eb98cea7dfa8093590ca80ea -->


- 2026-11-23T01:45:49Z — Segunda pasada sin preguntas: U9 no cambia ninguna cifra de pod del presupuesto de U2; P3 = A se lee como voice.enabled en true en values-cpu.yaml de la única máquina.
<!-- aidlc-wave-memory:voice:864d3de47a98b740a83ea46853772c7d0a4fa19434bd2c056f750d3251f25c40 -->


- 2026-11-23T01:56:42Z — «La forma exacta de los dos manifiestos» que U13 dejó a esta etapa se fijó como dos plantillas de `deploy/jobs/` con el mismo pod; `--as-of` solo en la de simulación, para que un valor mal pasado nunca convierta una simulación en un borrado (IDS-U13-01).
<!-- aidlc-wave-memory:ethics-governance:81ad61ec825690be6395b8a1bb3dd27040798bbfe2b2efa4cb08e65aaad284ab -->


- 2026-11-23T01:56:42Z — El `Job` lee el `ConfigMap` de la API con `configMapKeyRef` clave por clave y no con `envFrom`: así una clave que falte impide arrancar y la comprobación de IDS-U5-02 la ve en el render (IDS-U13-03).
<!-- aidlc-wave-memory:ethics-governance:00dc58267aaf4e011e3615610f0e82f8d6ff73f3846683ab98e7f3c0fa1a9be7 -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->


- 2026-10-03T10:20:04Z — P1 = B cambia C16 y NFR10.13 aprobados (la sonda de Kubernetes usa /readyz?probe=kubernetes sin Redis); quedó en la tabla de precisiones sin editar los originales.
<!-- aidlc-wave-memory:identity-access:7d0861bbdd14edf3839d4f6302b99d96b7173e11cba99392b37f73c34ee743b5 -->


- 2026-10-03T10:20:04Z — Pod Security restricted prohíbe hostPath en el pod, así que los modelos se montan con un PersistentVolume estático de solo lectura y su PVC; se añadió un rol veridicus_owner para que el REVOKE de las tablas de historial sea efectivo; ambos quedaron en la tabla de precisiones.
<!-- aidlc-wave-memory:platform:fc3953a74015e2bda6d02f89035bd2b658b7f0d7540536b5a08dca161bebc5b5 -->


- 2026-10-03T10:41:31Z — El archivo del prompt vive en el chart (charts/semantic-agent/files/) porque Helm no lee fuera del chart; las pruebas de semantic-agent lo leen desde ahí para no tener dos copias.
<!-- aidlc-wave-memory:text-flow:4549ebcf88aab50f749cc56d38b04994876b7c19a8b62c43ac29b9ce604d8b92 -->


- 2026-10-03T11:00:11Z — veridicus_now() del clúster devuelve solo now(); la variante con hora inyectada la instala el fixture de nivel 1, para que ningún rol pueda adelantar la suspensión (precisión a D3).
<!-- aidlc-wave-memory:session-lifecycle:6dfeb6773b974f432b72cbfccbdc238c4cf03cb8678e7264a7e46c51fd0700e6 -->


- 2026-10-03T11:00:42Z — NFR10.20 (de U4) apareció citado en reliability-design y se añadió a traceability.json como N/A justificado para que el sensor pasara.
<!-- aidlc-wave-memory:human-review:8e6679bf2cc1c34a34592b06d6c2ab4f1fff3424f831961994f6ec823c7d0ad9 -->


- 2026-10-03T11:00:43Z — La lista afectiva y el prompt de la pregunta pasan al directorio files/ del chart de semantic-agent (frente a D7 y D4) porque Helm no lee contracts/; quedó en la tabla de precisiones.
<!-- aidlc-wave-memory:assistant-extras:2727758d18136a8763df9a22d9692b4b6ae56400482d68d213280456af6aa6be -->


- 2026-10-03T11:01:37Z — Un rango publicado más ancho que /24 se parte en sus /24 en upstreamCidrs en lugar de relajar la política de NFR Design; solo se renderizan CIDR IPv4 porque el clúster Calico es IPv4. Quedó en la tabla de precisiones.
<!-- aidlc-wave-memory:anonymizer:b2188c8a51200775ed589ff4ac9ec44ed62e7c197a7721d782af9caadbd0850d -->


- 2026-10-03T11:50:55Z — Se añadió un Ingress `veridicus-voice` sin buffering de petición ni de respuesta, no pedido por NFR Design: ingress-nginx escribe en disco los cuerpos de más de 16 KiB y eso contradecía NFR10.2.
<!-- aidlc-wave-memory:voice:423a4edce1c4e47a053b696364eafbd30c7ebbf7b5ff859d1c8733cf2e005230 -->


- 2026-10-03T11:51:00Z — El PVC queda en 2 GiB (reserva de U2) en lugar del 1 GiB de NFR8.5, y la API pasa a Recreate frente al RollingUpdate de U2/U3/U5/U6; ambas quedaron en la tabla de precisiones sin editar los originales.
<!-- aidlc-wave-memory:forensic-report:81fc409341616282e139ee6b6df4cbbcaa8064f4450664488271a59c2cb19bb1 -->


- 2026-11-23T00:47:00Z — El mamparo de 4 se limita a POST /v1/generate (IDS-U10-04), porque con 4 llamadas en curso una sonda sin cupo haría que la livenessProbe reiniciara el pod a mitad de una llamada.
<!-- aidlc-wave-memory:anonymizer:c08f56d8e430ea1b179767e8e873b47de46ab0f6fd5ef5c58cc4cde055cfad1c -->


- 2026-11-23T00:57:53Z — U11 es library: solo cicd-pipeline.md y traceability.json (produces_kinds), aunque el brief nombraba los cuatro artefactos; máquina de la CLI, ZINE y frontera van en §5–§7 (IDS-U11-01).
<!-- aidlc-wave-memory:incoherence-analyzer:eb1639c526e17c07afd32d29f5194433bf50e608ec219aababe3ea66ddd74b8c -->


- 2026-11-23T01:10:01Z — semantic-agent y el trabajador van con Recreate en vez del RollingUpdate de U2 §5: con maxSurge 1 convivirían dos consumidores de C2 (contra NFR8.7) y el trabajador abriría 8 conexiones; cierra R-01 de la revisión 1.
<!-- aidlc-wave-memory:text-flow:b32172c1fcd6ed74f727238cccdac77d0c16bcf61db3205223234472e20b3548 -->


- 2026-11-23T01:30:59Z — La medición de todo-local de B8 detiene Minikube (sin delete) mientras el juez y el verificador corren en la anfitriona: el procedimiento de U11 solo levanta el verificador, y con Minikube encendido los 38 GiB de modelos no caben en WSL2 (IDS-U8-08).
<!-- aidlc-wave-memory:assistant-extras:883e29baeec4acb9ab3c5f19fe437d2eeee4bfd260b28d613f65cad25599d667 -->


- 2026-11-23T01:27:06Z — El plazo de inactividad de la revisión 1 («5 s» sin alcance en veridicus-pg) pasa a SET LOCAL por transacción en shared/db.py, que acepta idle_timeout_s para U7 (NFRD-U7-01, NFRD-U7-03; IDS-U6-02).
<!-- aidlc-wave-memory:session-lifecycle:da078335394eb977d044eace7ae2e38887d1b9cdf0fc48d889e5c24df286b5d8 -->


- 2026-11-23T01:31:23Z — El sensor de trazabilidad tomó NFR3.13 de reliability-design §3, que cita la consolidación de U7; entró como N/A justificado.
<!-- aidlc-wave-memory:human-review:ff3b3be4b4fb619e9ae3700d82189088df170fd785031e2fd5b18bdeb21737a2 -->


- 2026-11-23T01:41:06Z — export_store sale de backup-db.sh y pasa al runbook, justo después del volcado, porque la lista cerrada de exec de U2 solo admite pg_dump, la consulta de U13 y verify_store; se conservan el orden base → volumen y el SHA256SUMS de P2 = A (IDS-U7-07).
<!-- aidlc-wave-memory:forensic-report:c94c6d956db2f0def5c1298bf31b388dd555b13a2e4e173915b78beb56427a60 -->


- 2026-11-23T01:45:49Z — El /tmp en memoria de model-tts baja de 64 a 16 MiB: con 64 MiB, 1,2 × (512 + 64) superaba su límite de 640 MiB de U2 (IDS-U9-06).
<!-- aidlc-wave-memory:voice:3d14bfcad6b89398f410397562b46124139f5e8eb63ec8f1f635d6c33df08d99 -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->


- 2026-10-03T10:20:04Z — VERIDICUS_TRUSTED_PROXY toma todo el pod CIDR porque solo ingress-nginx alcanza el puerto 8080; detrás de Minikube todos los navegadores comparten dirección, así que el contador por dirección es común (aceptable con un analista en la sustentación).
<!-- aidlc-wave-memory:identity-access:0068bd70a4e17396e6dbc9a25bbc11a9392856f46cff76a2d2b445ee341d5bab -->


- 2026-10-03T10:20:04Z — La suma de los limits (≈ 19 GiB) supera los 18 GiB de Minikube y la de los requests (≈ 13,7 GiB) cabe; se aceptó porque solo el juez se acerca a su pico, y el primer recorte ante presión es apagar el monitoreo durante NFR8.
<!-- aidlc-wave-memory:platform:4122d22ceeddc9d8e0b8082ec4b47b2602ce25c2494a8f3af9976c4f5cd311ca -->


- 2026-10-03T10:20:04Z — Sin Alertmanager, Loki ni redis_exporter: el MVP no notifica a nadie y cada pieza cuesta memoria en una sola máquina; las alertas se ven en el panel.
<!-- aidlc-wave-memory:platform:e3967d5f6379e87534f0ec1d5ef9ec2070a9af4acfa27ecd5bd5e2ba681bf7bd -->


- 2026-10-03T10:41:31Z — La evaluación de nivel 2 corre desde la anfitriona con kubectl port-forward al juez del clúster en vez de un Job: usa el mismo modelo y digest sin otra imagen, a cambio de depender de un script revisable que el humano ejecuta.
<!-- aidlc-wave-memory:text-flow:0d9c307285f4b028a17851c58148a68e94360613695b02e94f42832f39c82eb8 -->


- 2026-10-03T10:41:31Z — El juez pide 3 CPU y limita en 6: la suma de requests cabe en 10 CPU y el juez sigue usando sus 6 hilos cuando el resto está quieto.
<!-- aidlc-wave-memory:text-flow:d64a7a75efb311ff19ddf32ec6c3e799f8514b4908a0798df063d20de7872dce -->


- 2026-10-03T11:00:11Z — Tras minikube stop o la API caída > 180 s las sesiones abiertas se suspenden en la primera revisión; se acepta porque reanudar es un clic sin pérdida, en vez de complicar la revisión.
<!-- aidlc-wave-memory:session-lifecycle:5e1abab73475cccff59abe446be62d963dc55d4787331c521f34744a5f75c626 -->


- 2026-10-03T11:00:42Z — Se mantuvieron los 768 MiB de la API: la suma de picos con U5 (≈ 392 MiB) deja margen holgado, a cambio de que U6 y U7 vuelvan a sumar sobre esa tabla.
<!-- aidlc-wave-memory:human-review:570b12319c610019250aec61e1a266ed6a657a694a05ff7679e133f6a7d43574 -->


- 2026-10-03T11:00:42Z — Durante el RollingUpdate la serie AIR puede publicarse desde dos pods; se resolvió con max by (session_id) en la regla de U2 (precisión) en lugar de cambiar la estrategia a Recreate, que cortaría la API.
<!-- aidlc-wave-memory:human-review:fb06596acc589d7d0736396a5d60f7d70917a27a0414f1bd6791dd2a548d6454 -->


- 2026-10-03T11:00:43Z — La lista afectiva entra en el filtro de ai-eval-gate.yml aunque es determinista: más reportes de nivel 2, a cambio de medir la repetibilidad de lo que ve el analista.
<!-- aidlc-wave-memory:assistant-extras:37fbabbdcd645db35ed5f1a6c6e62807a447d39606647e577b2c2c480fc2d6e3 -->


- 2026-10-03T11:01:37Z — Los volcados de memoria se desactivan en el proceso (RLIMIT_CORE = 0 y no volcable) y no en el kernel de la anfitriona: no toca un ajuste compartido, a costa de depender de que el arranque lo haga antes de cargar nada (prueba de nivel 0).
<!-- aidlc-wave-memory:anonymizer:aaf6e8e07eda251437fa576cb923035cf6fee64512f741a944f51c0c424dd2c1 -->


- 2026-10-03T11:50:55Z — Con la voz encendida en desarrollo (P3 = A) los limits suman ≈ 21,9 GiB frente a 20 GiB; se aceptó porque los requests (≈ 16,1 GiB) caben y solo el juez y Whisper pueden coincidir en su pico (≈ 8 GiB). Redis sube a 768 MiB por el fork de BGREWRITEAOF.
<!-- aidlc-wave-memory:voice:72d496f20706cee664394fb90f7eb0e07379c7b75146f23ffc04bd9ace078640 -->


- 2026-10-03T11:51:00Z — verify_store usa un rol nuevo veridicus_report_ro de solo SELECT (un Secret más) en vez de reutilizar veridicus_app, por mínimo privilegio; el respaldo usa export_store en Python para no exigir tar en la imagen mínima.
<!-- aidlc-wave-memory:forensic-report:d559307b1bfe64b4390bf06009222a91c8c7a0657fbd6cf2ded16ec8b37f9609 -->


- 2026-11-23T00:47:00Z — La prueba de 0 fugas con el NER real corre en la CI con el NER aprovisionado y verificado por sha256 antes de las pruebas (IDS-U10-07), y el rendimiento se mide en la máquina de desarrollo con una puerta que exige el reporte, porque los runners no son comparables.
<!-- aidlc-wave-memory:anonymizer:f2144d96bdfe77603c513663d853013cb74239356c7b20e97f4117d94bf6144b -->


- 2026-11-23T00:47:00Z — El modelo NER no se fija por nombre y hash en esta etapa sino por criterios y orden de candidatos (IDS-U10-01); su revisión y sha256 se fijan en B10 con la prueba de 0 fugas como compuerta.
<!-- aidlc-wave-memory:anonymizer:6ab770f668091f139ecab4f53eec9eaa7d98ea9bab1ea8cfa04f6d93308686e1 -->


- 2026-11-23T00:41:02Z — El humano delegó P6–P8 («ahora tengo 64, así que puedes ajustar lo que sea necesario»): Minikube 50 GiB y 16 CPU, WSL2 56 GB y 20 procesadores, juez Qwen3.6-35B-A3B Q4_K_M; los limits (≈ 51,8 GiB) superan a Minikube porque los pesos de llama-server son memoria recuperable y juez y verificador no generan a la vez.
<!-- aidlc-wave-memory:platform:7e83e3301fb5d00c36becaec84a9f29795e40a21479e60be1e6a20b8df6213e6 -->


- 2026-11-23T00:57:53Z — La wheelhouse de ZINE va sin el extra cli (sin torch ni libs-anonymizer) a cambio de que composition importe el anonimizador de forma diferida y un perfil comercial sin él dé código 3 (IDS-U11-02).
<!-- aidlc-wave-memory:incoherence-analyzer:eb9f54432ba8a7f507ae5b725851abcec7219d8ed97afc94c747efade4a8e72e -->


- 2026-11-23T00:57:53Z — El verificador del nivel 2 en la anfitriona reutiliza la imagen de llama-server de U2 por digest solo en loopback; conserva la salida de la red puente de Docker, riesgo residual igual al de la propia CLI (IDS-U11-05).
<!-- aidlc-wave-memory:incoherence-analyzer:64f9533ea232f59ae2ef51c5f7d0406e954245c779859a193f484b75e00be0bb -->


- 2026-11-23T01:10:01Z — Con el cuarto hilo del trabajador el pico de veridicus_app iguala el connectionLimit de 25 (API 20 en rodadura, trabajador 4, create-admin 1); se pide 30 a U2 en vez de bajar el pool de la API de U3, a costa de 5 conexiones más dentro de max_connections 50.
<!-- aidlc-wave-memory:text-flow:ccd496941f793e82a73439425d4aa567c54eef05bd117b48a88b0abc250ba373 -->


- 2026-11-23T01:10:01Z — Un despliegue de semantic-agent a mitad de corrida reenvía el mismo cuerpo seudonimizado dentro del tope de 3 entregas; se acepta con un paso del runbook (desplegar sin corridas en processing) en vez de un periodo de gracia de horas.
<!-- aidlc-wave-memory:text-flow:aee22c5003becec5540a7fe68d5e4e298055c8aa69215bd4afc2866cca9c6701 -->


- 2026-11-23T01:26:02Z — Los `limits` de Minikube suben a ≈ 52,4 GiB (2,4 GiB sobre 50) a cambio de no subir `requests` por un pico raro; se apoya en el sobrecompromiso que U2 ya aceptó y en sus recortes.
<!-- aidlc-wave-memory:research-reports:f33b2c63ccd240bc3f8f174b59c553d6f1f6c009c45501308bd18f947e11b726 -->


- 2026-11-23T01:26:02Z — T3 fija `idle_in_transaction_session_timeout` de 5 s con `SET LOCAL` (respuesta a la nota NFRD-U7-02): no tiene huecos sin sentencias, así que no corta escrituras legítimas (IDS-U12-06).
<!-- aidlc-wave-memory:research-reports:66da2e807f5e05b20ca30f2e863025c71d88fe55e64da3d21c1cd13758cc0e44 -->


- 2026-11-23T01:30:59Z — session-api pasa a depender de libs-incoherence-analyzer para la segunda línea; se pide un job lock-boundary sin libs-anonymizer en vez de copiar el validador, a costa de una dependencia más en la imagen con la base (IDS-U8-03).
<!-- aidlc-wave-memory:assistant-extras:5ad4f65b5c194bf3d98a04b6f4c1733b09f585cdb7372cbeb320bddc50ed5651 -->


- 2026-11-23T01:30:59Z — El margen de semantic-agent queda en 13 MiB (947 de 960 MiB) con el módulo; se acepta sin pedir más memoria a U2 y cualquier pico mayor medido en B8 sube el límite por PR (IDS-U8-02).
<!-- aidlc-wave-memory:assistant-extras:14b5a44b95082f1c9f53a555e36c73a5165d5ed7a9f2369a0a6f278df1b06803 -->


- 2026-11-23T01:27:06Z — El tope del Ingress iguala import_body_max_bytes, así que un cuerpo mayor recibe el 413 de nginx sin Problem Details; se acepta porque la consola nunca lo envía y el 413 de la API se prueba en nivel 1 (IDS-U6-09).
<!-- aidlc-wave-memory:session-lifecycle:497fa16db1969c0ccee7499584c52e9ccfc53e9a2069a1135d4a3b38dbd3cb37 -->


- 2026-11-23T01:31:23Z — Se mantuvo lock_timeout = statement_timeout = 2 000 ms (valor aprobado del que dependen U7 y U13) con una prueba del empate, en vez de bajar el lock_timeout a 1 500 ms como sugería R-03: las dos cancelaciones dan el mismo 503.
<!-- aidlc-wave-memory:human-review:caa2eaa6248db3551140f50af7bba2f39f1beab4ea1e27f7f3f93afd2cb1355d -->


- 2026-11-23T01:31:23Z — Se retiró la precisión max by (session_id) de la revisión 1: la regla AIR es de U2 con > 0.25, y la alerta doble de ≤ 60 s durante el relevo de pods queda como riesgo aceptado porque nadie recibe notificaciones.
<!-- aidlc-wave-memory:human-review:3e2701b278b11bebb01a03de1b1ae71b30d1b9876e19a77c65124ad9f015ae74 -->


- 2026-11-23T01:41:06Z — El corte de Recreate se mide desde fuera con scripts/measure-cutover.sh (solo HTTP, umbral ≤ 90 s, contando la descarga de capas) en vez de con kubectl rollout status, que check-no-cluster-apply.sh prohíbe en scripts (IDS-U7-11).
<!-- aidlc-wave-memory:forensic-report:e3fe96d33ac82c1a95489b867b348d36eaa2102129dec220845156856d66a4a3 -->


- 2026-11-23T01:45:49Z — No se pide subir Redis a 768 MiB: el AofRewriteRequester reescribe con la cola vacía, y una prueba de nivel 1 exige un pico de RSS ≤ 427 MiB; solo si falla se pide a U2 por PR (IDS-U9-05).
<!-- aidlc-wave-memory:voice:6a218770f575bed308ef787cba579c27e3ef1b32db506fa938457bbd52d4d37d -->


- 2026-11-23T01:56:42Z — Sin alerta para el `Job`: lo lanza el humano y lee su salida al terminar; una regla sobre `kube_job_status_failed` avisaría a la misma persona más tarde y sin la causa.
<!-- aidlc-wave-memory:ethics-governance:e466e7a0e683681f713df03e36e0e78e656bde2104e50f975dbee613848b5a2e -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

- 2026-10-03T10:20:04Z — La memoria de GPU de la máquina GPU no se conoce; values-gpu.yaml asume que el juez de 7B cabe entero (≥ 6 GiB de VRAM) y U4 la confirma al elegir modelos más grandes para la evaluación.
<!-- aidlc-wave-memory:platform:763ba9cccd310ade902e0fcc321d49355d24a6398f2f413a3f05e0ed11e82064 -->

- 2026-11-23T00:43:37Z — Quedan cuatro peticiones a U2 para su Infrastructure Design: nombre del contenedor, consumidores de veridicus-auth y veridicus-bootstrap-admin, entrada de veridicus_app en managed.roles y smoke.sh con port-forward al /readyz (IDS-U3-03 a IDS-U3-06).
<!-- aidlc-wave-memory:identity-access:53eaa501c76f7c9e653bef00c79e78458a627b3ae231805e83cfe33cac18763a -->

- 2026-11-23T00:41:02Z — El contenedor ve un i7-14700KF pero WSL2 solo le entrega 8 procesadores y unos 3,8 GiB; P8 pide confirmar que el equipo de la demo es el mismo antes de fijar processors y --cpus.
<!-- aidlc-wave-memory:platform:1c57ce094e1bc2f55f7f120fdca33ede002109c8665d9af1103f90cf05cf76ac -->

- 2026-11-23T00:41:02Z — Con el driver Docker en WSL2 la minikube ip no se alcanza desde Windows: el runbook usará kubectl port-forward del ingress a 127.0.0.1:8443 y los modelos vivirán en el ext4 de la distribución, no en /mnt/c (se aplica sin preguntar).
<!-- aidlc-wave-memory:platform:f10794c1052edb5ffa13ddcba8837b33c4ee0de8834813c2311f95f5c45599e8 -->
