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

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

- 2026-10-03T10:20:04Z — La memoria de GPU de la máquina GPU no se conoce; values-gpu.yaml asume que el juez de 7B cabe entero (≥ 6 GiB de VRAM) y U4 la confirma al elegir modelos más grandes para la evaluación.
<!-- aidlc-wave-memory:platform:763ba9cccd310ade902e0fcc321d49355d24a6398f2f413a3f05e0ed11e82064 -->
