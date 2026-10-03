## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T11:52:00Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/voice/infrastructure-design/infrastructure-specification.md > §2 fila `veridicus-whisper` y §9 fila `veridicus-whisper` | La imagen de Whisper sigue sin nombrar: "la que fije U2 (su hallazgo R-06)". La opción B de P2 habría cerrado R-06 y se descartó con P2 = A, que solo cubre el TTS. Whisper es el tramo dominante de NFR3.1 y NFR3.2 y U9 le exige comportamientos que dependen de la imagen: `cpu_threads = 4`, `compute_type=int8`, modo sin conexión, sin registro del cuerpo, `/tmp` en memoria, raíz de solo lectura y UID sin root. Ningún workflow de `cicd-pipeline.md` construye, escanea con Trivy ni prueba esa imagen (solo `audio-worker.yml` y `tts-server.yml`). Quien implemente no puede saber qué servidor configurar ni verificar. | Nombrar la imagen de Whisper (por digest, o `services/whisper-server/` con su workflow) o dejar R-06 como precondición explícita de Code Generation de U9, con dueño y fecha. Añadir las puertas de CI de esa imagen: Trivy, usuario sin root y prueba de que no registra el cuerpo. | New |
| R-02 | Minor | .../voice/infrastructure-design/monitoring-design.md > §4 fila `veridicus-whisper`; .../cicd-pipeline.md > §1 | La única comprobación de que Whisper y el TTS reales no registran el audio ni el texto es "comprobación manual" sin comando ni umbral exacto. Los centinelas de CI usan *fakes* (`audio-worker` y `tts-server`). Es la frontera de AUTONOMIA-04 y de AUTONOMIA-02, que exige un comando exacto. | Escribir el comando (por ejemplo `kubectl -n veridicus logs deploy/veridicus-whisper \| grep -c <centinela>`) y el umbral (0), y citarlo por ID en el cierre de la corrida de voz. | New |
| R-03 | Minor | .../voice/infrastructure-design/cicd-pipeline.md > §3 paso 7 y §4; .../assistant-extras/infrastructure-design/infrastructure-specification.md > §1.1 y §1.2 | `voice.spec.ts` exige el turno evaluado en ≤ 75 s (NFR3.3) y no dice en qué máquina corre. La demostración (`values-gpu.yaml` + `values-extras.yaml`) declara p95 ≤ 150 s por turno y humo de 300 s. En esa máquina el umbral de 75 s no se puede cumplir si hay extras activos. | Fijar que `voice.spec.ts` y la corrida de voz corren solo con extras apagados (máquina de desarrollo), o parametrizar su umbral desde `smoke.timeoutSeconds`. | New |
| R-04 | Minor | .../voice/infrastructure-design/infrastructure-specification.md > §4 y .../cicd-pipeline.md > §1 fila `deploy-level0.yml` | `use-regex: "true"` en ingress-nginx se aplica a todos los paths del mismo host, también los del `Ingress` de U2 (`/` y `/api/`). Las pruebas son solo estáticas (existencia de las anotaciones) y no comprueban el enrutamiento ni la precedencia entre el `Ingress` de U2 y `veridicus-voice`. | Añadir al nivel 0 una prueba de enrutamiento sobre la configuración de nginx renderizada, o una comprobación manual de solo lectura tras el despliegue: voz, `/api/` y `/` llegan a su destino. | New |
| R-05 | Minor | .../voice/infrastructure-design/infrastructure-specification.md > §1.2 columna Desarrollo | El texto dice que los picos del juez y de Whisper suman ≈ 8 GiB "dentro de lo libre", pero lo libre por `requests` es ≈ 3,9 GiB. Las cifras de `requests` sí cuadran con U4: 13 + 1,5 + 1,6 = 16,1 GiB y 9,35 de 10 CPU. Lo que sostiene la afirmación es que ambos picos ya están dentro de sus `requests` (7 y 1 GiB), no que haya 8 GiB libres. La holgura de CPU es de 0,65 sobre 10. | Reescribir la justificación (picos ya contenidos en `requests`) y registrar que quedan 0,65 CPU de holgura. | New |
| R-06 | Minor | .../voice/infrastructure-design/infrastructure-specification.md > §3 y §9 fila `scripts/fetch-models.sh` | `verify-model` de U2 verifica un `sha256` por modelo. Las entradas de U9 tienen cuatro archivos (Whisper) y tres (voz). No se dice que `verify-model` los verifique todos, y `VERIDICUS_WHISPER_MODEL_SHA256` cubre solo `model.bin`. Tampoco hay revisión de la licencia de `piper-tts`, que puede traer GPL por espeak-ng. | Precisar que `verify-model` comprueba la lista completa (`sha256sum -c`), y añadir la licencia de `piper-tts` y de espeak-ng a la revisión previa a fijarlo. | New |
| R-07 | Minor | .../voice/infrastructure-design/monitoring-design.md > §2 alerta `VoiceComponentDown`; .../cicd-pipeline.md > §1 | La expresión regular `(audio-worker\|whisper\|tts)` lleva barras verticales sin escapar dentro de una tabla Markdown, que la rompe. Los seis `PrometheusRule` de U9 no tienen `promtool test rules`, a diferencia de la regla AIR de U2. | Escapar la expresión o sacarla de la tabla, y añadir `promtool test rules` para las reglas de voz a `deploy-level0.yml`. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON de `traceability.json` | PASS: carga correcta | Estructura válida |
| Cobertura de IDs NFR de `voice/nfr-requirements/` | PASS: 67 de 67 IDs, sin faltantes ni sobrantes; 61 OK y 6 N/A justificados | Cobertura completa |
| Presupuesto de memoria y CPU frente a U4 | PASS con reserva: requests 16,1 GiB, limits 21,9 GiB y CPU 9,35 coinciden con la suma de U4 (15,8 y 21,5) cambiando Whisper y `audio-worker` por el bloque de voz | Aritmética correcta; ver R-05 |
| Ingress sin búfer en disco | PASS con reserva | Anotaciones correctas en las dos rutas; ver R-04 |
| Redis y `BGREWRITEAOF` | PASS | No se renombra; `maxmemory` 384 MB; PVC 2 GiB; límite 768 MiB cubre el *fork* |
| Lista cerrada de formatos en `models.lock` | PASS con reserva | Lista por servidor y rechazo de formatos con *pickle*; ver R-06 |
| Red mínima, AUTONOMIA-01 y AUTONOMIA-04 | PASS | Sin `ipBlock`, controles negativos de Kyverno, frontera por componente declarada, sin aplicaciones desde la CI |
| Precisiones sin editar originales | PASS | §9 las registra en una tabla |
| AUTONOMIA-02 | PARCIAL | Puertas con comando y umbral, salvo la comprobación manual de R-02 |

### Summary

El diseño es implementable y consistente con U2, U4 y U8. La cobertura de NFR es completa, el presupuesto cuadra y la frontera de AUTONOMIA-04 está bien cerrada. El hueco que el humano debe sopesar antes de aprobar es R-01: la imagen de Whisper, que concentra el riesgo de latencia y de privacidad, sigue sin designar ni verificar en la CI. El resto son precisiones menores.
