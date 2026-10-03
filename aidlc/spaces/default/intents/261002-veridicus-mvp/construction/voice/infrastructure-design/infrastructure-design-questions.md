# Preguntas de Infrastructure Design — U9 voice

**Unidad.** U9 `voice` (tipo `service`, SHOULD): el analista graba un turno en la consola, `session-api`
lo lee en memoria y lo publica en base64 en la cola C5 (`veridicus:audio`), `audio-worker` lo transcribe
con Whisper `base` int8 en CPU (`veridicus-whisper`), publica el texto en `veridicus:transcripts` y borra
el audio; además, «Escuchar audio» sintetiza la pregunta aprobada con Piper por la ruta interna
`POST /internal/v1/speech` de `audio-worker`. El audio crudo nunca sale del clúster ni se conserva
(AUTONOMIA-04).

**Lo que ya está decidido y no se vuelve a preguntar.** De U2–U8: Minikube con Calico en las dos
máquinas, un namespace `veridicus` con negar todo y CoreDNS con lista blanca, Minikube con 20 GiB y
10 CPU en la máquina de desarrollo y 28 GiB en la de demostración (32 GB), límites de memoria con ≥ 20 %
sobre el pico medido, modelos descargados en la anfitriona con `fetch-models.sh` y `models.lock` y
verificados por el `initContainer` `verify-model`, Redis 7.2 con AOF `everysec`, `maxmemory 384mb` y
`noeviction`, `proxy-body-size` del Ingress igual al mayor tamaño de C1, kube-prometheus-stack sin
Alertmanager, GHCR privado y despliegue solo por PR, y los extras de U8 fijos solo en la máquina de
demostración. De U9: Whisper `base` int8 voraz con VAD e idioma `es` (D1), Piper con una voz `es_*`
`medium` en el pod `model-tts` (D3), síntesis por `audio-worker` con Bearer (D4), base64 en C5 con
máximo de 6 000 000 bytes (D5), un audio a la vez, `cpu_threads = 4` y `limits.cpu` 4 en Whisper,
lectura de la subida en *streaming* sin disco (P1 = A de NFR Design), `BGREWRITEAOF` pedido por
`audio-worker` con la cola vacía (P2 = A de NFR Design), topes de memoria por pod (performance-design
§7) y la lista de entregas de logical-components §4. Lo que queda abierto es qué servidor y qué formato
de modelo usa la voz, y en qué máquinas se enciende.

---

## P1 — Formato de los modelos de voz frente a la regla «GGUF o `safetensors`»

`## Deployment` de `team.md` pide artefactos de modelo «en formatos sin código ejecutable (GGUF,
`safetensors`)». Ninguno de los dos motores de voz aprobados usa esos formatos: `faster-whisper` carga un
`model.bin` de CTranslate2 (la revisión de U2 lo señaló en su hallazgo R-06) y Piper carga una voz
`.onnx`. Ninguno de los dos se deserializa con `pickle` ni ejecuta código al cargarse, pero no son los
dos formatos nombrados, y de esta respuesta dependen `models.lock`, `fetch-models.sh` y la prueba de
nivel 0 que rechaza formatos peligrosos.

A. Leer la regla por su propósito («sin código ejecutable») y admitir, con nombre y de forma cerrada,
   CTranslate2 (`model.bin` + `config.json` + `tokenizer.json` + `vocabulary.*`, del repositorio ya
   convertido de `faster-whisper-base`) y ONNX (`.onnx` + `.onnx.json` de la voz Piper). La prueba de
   nivel 0 sobre `models.lock` lleva una lista blanca de extensiones por servidor y rechaza `.pt`,
   `.pth`, `.pkl`, `.ckpt` y cualquier `.bin` fuera del directorio de CTranslate2. La precisión de la
   regla queda en la tabla de precisiones para que decidas en la aprobación si se actualiza `team.md`.
   (Recomendada)
B. Cumplir la regla al pie de la letra para Whisper: `fetch-models.sh` descarga `whisper-base` en
   `safetensors` (verificado por `sha256`) y lo convierte a CTranslate2 en la anfitriona con un
   conversor de versión fijada, verificando también el `sha256` del resultado; ONNX de Piper queda como
   única excepción declarada. Más pasos y una herramienta de conversión que mantener, a cambio de que
   todo lo descargado de internet sea `safetensors` o GGUF.
C. Cumplir la regla sin excepciones: Whisper con `safetensors` servido con `transformers` (más lento en
   CPU, pone en riesgo el p95 ≤ 12 s por turno de 30 s) y sin TTS en el MVP (la pregunta solo se lee en
   pantalla, porque no hay voz Piper en `safetensors` ni GGUF). Es el cambio de alcance más grande.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Servidor que sirve la voz Piper en el pod `model-tts`

NFR Requirements eligió Piper (D3) y dejó a esta etapa el servidor concreto; C14 dice que el TTS no
tiene estándar y que lo cubre un adaptador propio de ModelGateway. El servidor decide qué imagen entra al
clúster, qué API habla el adaptador, si registra el texto de la pregunta en sus logs (NFR10.6 exige que
no) y quién lo mantiene. Si en P1 eliges C, esta pregunta no aplica.

A. Una imagen propia mínima `services/tts-server/` (FastAPI con el paquete `piper-tts` fijado en su
   lockfile, del orden de 80 líneas) construida en la CI con las mismas reglas que los demás servicios:
   sin root, raíz de solo lectura, Trivy, ≥ 80 % de cobertura, sin registro del cuerpo. Expone
   `POST /v1/audio/speech` con la forma de OpenAI (`input`, `voice`, `response_format: wav`), `/healthz`
   y `/readyz` con la voz ya cargada, y carga la voz del volumen de modelos de solo lectura.
   (Recomendada)
B. Un servidor de terceros de código abierto compatible con OpenAI que ya sirve `faster-whisper` y Piper
   (por ejemplo Speaches, licencia MIT), fijado por digest y desplegado dos veces con la misma imagen
   (`veridicus-whisper` y `veridicus-tts`), en modo sin conexión y leyendo el volumen de modelos. Cierra
   también la imagen de Whisper que R-06 pidió nombrar, pero trae funciones que no se usan (descarga de
   modelos, otras voces, interfaz) que hay que desactivar, y hay que comprobar que no registra el texto.
C. El servidor HTTP que trae el propio Piper (`python -m piper.http_server`) en una imagen construida en
   la CI sin código propio; el adaptador de ModelGateway se ajusta a su API, que no es la de OpenAI. Menos
   código propio que A, pero sin `/readyz` ni control sobre lo que registra.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — En qué máquinas se encienden Whisper, el TTS y `audio-worker`

U2 dejó las partes SHOULD detrás de banderas del chart (`whisper.enabled`, `audioWorker.enabled`) y U9
añade `model-tts`; las tres van juntas, porque `/readyz` de `audio-worker` depende de Whisper y del TTS.
NFR Design pide medir la voz con `values-cpu.yaml` y medir en la máquina de desarrollo que Whisper no
frena los turnos escritos (NFR8.8). Con la voz encendida en desarrollo, la suma de `requests` de memoria
pasa de unos 15,8 a unos 16,2 GiB (cabe en 20 GiB) y la de `limits` queda en unos 21,6 GiB (como hoy, solo
el juez se acerca a su pico).

A. Encendidas en las dos máquinas por defecto (`values-cpu.yaml` y `values-gpu.yaml`), con Whisper y el TTS
   en CPU en ambas. La corrida de voz, la medición de convivencia con el juez y el humo con
   `audio-worker` corren siempre sobre lo que está desplegado, sin PR extra; la carga de NFR8 de los
   turnos escritos corre con la voz encendida pero ociosa. (Recomendada)
B. Apagadas por defecto; un archivo `values-voice.yaml` se suma de forma permanente en la máquina de
   demostración, y en la de desarrollo solo para cada corrida de voz, con un PR que lo añade y un
   `git revert` que lo quita. Más holgura de memoria en desarrollo, a cambio de dos PR por cada corrida.
C. Como A, pero en la máquina de demostración Whisper corre en GPU (el mismo modelo `base`, con una
   imagen con CUDA): transcripción más rápida en la sustentación, a cambio de una segunda variante de
   imagen y de compartir la GPU con el juez.
X. Other (please specify)

[Answer]: A **Mode:** guided
