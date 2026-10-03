# Pipeline de CI/CD — U9 voice

**Insumos.** Comandos de verificación, dependencias y riesgos de `nfr-requirements/tech-stack-decisions.md`
(§4–§6); dobles de prueba, cobertura, textos y accesibilidad de `nfr-design/logical-components.md`
(logical-components §5); pruebas `perf` y corrida de voz de `nfr-design/performance-design.md`
(performance-design §2, §6, §7); controles y sus pruebas de `nfr-design/security-design.md`
(security-design §1–§7); idempotencia y capacidad de `nfr-design/scalability-design.md`
(scalability-design §2–§4); fallos y configuración de `nfr-design/reliability-design.md`
(reliability-design §4–§8); métricas de `nfr-design/observability-design.md` (observability-design §2);
flujos de `functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C1, C5, C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas **P1 = A** (prueba de
formatos sobre `models.lock`), **P2 = A** (imagen propia `tts-server`) y **P3 = A** (voz encendida en
los dos *values*) de `infrastructure-design-questions.md`; flujo común de U2, *workflows* de U3 y U4
(sus `cicd-pipeline.md`); `infrastructure-specification.md` de esta carpeta; `## Testing Posture` y
`## Deployment` de `team.md`.

Reglas comunes de U2: `permissions: contents: read`, acciones fijadas por SHA, sin `kubeconfig` ni
credenciales del clúster; solo el *job* `build` tiene `packages: write`, y solo en `main`. Ninguna prueba
de los niveles 0 y 1 descarga un modelo, usa GPU, un micrófono real o se reintenta (NFR2.1).

## 1. *Workflows* y puertas

| *Workflow* | Se dispara con | Puerta | Comando | Umbral |
|---|---|---|---|---|
| `audio-worker.yml` (nuevo) | `services/audio-worker/**`, `libs/**`, `contracts/**` | *Lint*, tipos y fronteras | `uv run --directory services/audio-worker ruff check . && mypy --strict . && lint-imports` | 0 errores |
| | | Nivel 0 (contratos C5 primero, configuración, `AofRewriteRequester`, URL internas) | `uv run --directory services/audio-worker pytest -m "not integration and not perf"` | Verde |
| | | Ramas del ciclo de vida del audio | `uv run --directory services/audio-worker pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % en `audio_lifecycle.py` y en el `AofRewriteRequester` (NFR13.2) |
| | | Nivel 1 (Redis 7.2 configurado como U2 con `save ""`, PostgreSQL 16 real, Whisper y TTS *fakes*) | `uv run --directory services/audio-worker pytest -m integration` | Verde: `XLEN` = 0 tras cada resultado, centinela ausente del AOF en ≤ 120 s, 10 mensajes de 8 MB sin `OOM`, 1 llamada a Whisper con dos entregas, 3 centinelas fuera de logs |
| | | Cobertura | `pytest --cov --cov-fail-under=80` | ≥ 80 % de líneas (NFR13.1) |
| | | Auditoría | `pip-audit` y `gitleaks` | 0 `HIGH`+ con corrección; 0 secretos |
| | | *Build* | `hadolint Dockerfile`; `docker build`; `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1` | 0 hallazgos; `USER 10001`; publica en GHCR por SHA solo en `main` |
| `tts-server.yml` (nuevo, P2 = A) | `services/tts-server/**` | *Lint* y tipos | `uv run --directory services/tts-server ruff check . && mypy --strict .` | 0 errores |
| | | Nivel 0 con la voz Piper *fake* detrás de una interfaz propia | `uv run --directory services/tts-server pytest` | Verde: 1 y 300 caracteres → `200` `audio/wav`; 0 y 301 → `422`; segunda petición espera (concurrencia 1); `/readyz` `503` antes de cargar la voz; el texto centinela no aparece en logs |
| | | Cobertura | `pytest --cov --cov-fail-under=80` | ≥ 80 % de líneas |
| | | Auditoría y *build* | `pip-audit`, `gitleaks`, `hadolint`, Trivy como arriba | Igual que `audio-worker` |
| `session-api.yml` (de U3) | Sus rutas | U9 añade pruebas de voz al nivel 0 y 1, ramas de `AudioValidator` y `VoiceUploadReader` y la prueba de rutas sin `UploadFile` ni `Form` | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards` y `pytest -m perf -k voice` | 100 % de ramas; p95 del `202` ≤ 500 ms y diferencia de RSS ≤ 32 MiB en 20 subidas (NFR3.4, NFR8.4) |
| `libs.yml` (de U4) | `libs/**` | Adaptadores `transcribe` y `synthesize` de ModelGateway | `uv run --directory libs pytest --cov --cov-fail-under=80` | ≥ 80 % |
| `frontend.yml` (de U4) | `frontend/**` | Componentes de voz, ESLint con `speechSynthesis` y `SpeechRecognition` prohibidos (control negativo), `vitest-axe` | `npm --prefix frontend run lint && npm --prefix frontend run typecheck && npm --prefix frontend run test -- --coverage` | Verde; ≥ 80 % de líneas (NFR1.3, NFR14.1, NFR14.2) |
| `deploy-level0.yml` (de U2) | `deploy/**`, `scripts/**`, `evaluation/voice/**` | Render y políticas | `helm template` con `values-cpu.yaml`, `values-gpu.yaml` y `values-gpu.yaml` + `values-extras.yaml` → `kubeconform` → `kyverno test deploy/policies/tests/` | Cada control negativo de voz falla como se espera (infrastructure-specification §5): etiqueta, salida, volúmenes, Secret, anotaciones del `Ingress` `veridicus-voice`, banderas de voz que difieren |
| | | Formatos de modelo (P1 = A) | `python scripts/check-models-lock.py deploy/models.lock` | 0 entradas fuera de la lista por servidor, 0 `.pt/.pth/.pkl/.pickle/.ckpt/.joblib`, 0 `.bin` fuera de `ctranslate2`, voz `es_*`, `VERIDICUS_WHISPER_MODEL_SHA256` igual al del *lock* |
| | | Audio sintético | `scripts/check-synthetic-audio.sh` | 0 `.wav`/`.mp3` fuera de `evaluation/voice/manifest.json` (NFR12.1) |
| | | AUTONOMIA-01 | `scripts/check-no-cluster-apply.sh` | 0 verbos de aplicación en *workflows* y *scripts* |
| `voice-eval-gate.yml` (nuevo) | §2 | Reporte de la corrida de voz | `python scripts/check-voice-report.py out/voice.json` | §2 |

## 2. Corrida de voz de nivel 2 (fuera de la CI)

**Filtro de rutas.** `voice-eval-gate.yml` exige el reporte cuando el PR toca: entradas `whisper-*` o
`piper-*` de `deploy/models.lock`; `deploy/veridicus/charts/whisper/**`, `deploy/veridicus/charts/tts/**`;
`services/tts-server/**`; los adaptadores de voz de `libs/model_gateway/`; los parámetros de Whisper de
`services/audio-worker/` (modelo, idioma, `beam_size`, VAD, `cpu_threads`); los ajustes
`VERIDICUS_WHISPER_*`, `VERIDICUS_TTS_*`, `VERIDICUS_VOICE_*` y `VERIDICUS_AUDIO_*` de los *values*; y
`evaluation/voice/**`. Además bloquea toda entrega etiquetada.

| Paso | Diseño |
|---|---|
| Dónde | Máquina de desarrollo, contra Whisper y el TTS del clúster desplegado con `values-cpu.yaml` (P3 = A), por `port-forward` (lectura; no cambia el clúster) |
| Comando | `uv run --directory evaluation python -m voice.run --profile cpu --report out/voice.json` |
| Contenido del reporte | `model_digest` de Whisper y de la voz, `manifest` de clips con su `sha256`, perfil, p50/p95/máximo por tramo, WER, picos de RSS por pod, resultados por `result` |
| Umbrales que comprueba `check-voice-report.py` | Digests iguales a los de `models.lock` del PR; perfil `cpu`; p95 ≤ 12 s (`le30`) y ≤ 40 s (`le120`) de transcripción, ≤ 100 s de turno con 120 s; WER ≤ 20 %; 0 textos en 3 clips de silencio o ruido; 100 % de textos iguales en dos pasadas; mismas alertas que el texto escrito (incluido el Escenario A); p95 de síntesis ≤ 5 s y WER ≤ 20 % de 5 preguntas sintetizadas; 0 `turn.error.timeout` con 1 y 3 sesiones; turnos escritos de la corrida mixta con p95 ≤ 60 s; picos de RSS ≤ topes; 0 `OOMKilled`; 0 errores de reescritura del AOF |

`ai-eval-gate.yml` de U4 deja de pedir el Golden Dataset cuando el cambio de `models.lock` solo toca
entradas de voz (precisión en infrastructure-specification §9).

## 3. Del PR al clúster

| Paso | Qué pasa |
|---|---|
| 1 | PR de la migración de U9 (índice parcial sobre `processing_stage = 'transcribing'`) como `Job` aparte, antes del código que la usa |
| 2 | PR de código con sus *workflows* en verde y, si toca §2, con el reporte de voz |
| 3 | En `main`, `build` publica `audio-worker`, `tts-server`, `session-api` y `frontend` por SHA |
| 4 | Si cambió un modelo: el humano ejecuta `scripts/fetch-models.sh` en cada máquina (solo escribe en `/srv/veridicus/models/<nombre>/<revisión>/` y verifica `sha256`; no toca el clúster) |
| 5 | PR de despliegue con los digests y los *values*; `deploy-level0.yml` valida el render de las tres combinaciones |
| 6 | Aplicación manual del artefacto fusionado (antes del módulo 8) o sincronización de Argo CD; `audio-worker` sin corte (`RollingUpdate`), Whisper y TTS con `Recreate` (la voz deja de estar disponible unos segundos; el texto sigue) |
| 7 | `scripts/smoke.sh https://veridicus.local` (incluye `/readyz` de `audio-worker`) y, antes de etiquetar una entrega, `npx --prefix frontend playwright test e2e/voice.spec.ts` |

## 4. Entornos

| Entorno | Qué es | Voz |
|---|---|---|
| CI | Render, políticas y pruebas en contenedor; sin clúster | *Fakes* de Whisper, TTS y micrófono |
| Máquina de desarrollo (Minikube 20 GiB, 10 CPU) | `values-cpu.yaml` | Encendida, en CPU; ahí corren la corrida de voz y la medición de convivencia |
| Máquina de demostración (Minikube 28 GiB) | `values-gpu.yaml` + `values-extras.yaml` | Encendida, en CPU (solo el juez usa GPU) |

## 5. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o `voice.spec.ts` tras desplegar | `git revert` del PR de despliegue y nueva aplicación o sincronización |
| Un modelo de voz nuevo da peores métricas | `git revert` del PR de `models.lock`; la revisión anterior sigue en su carpeta y `verify-model` la acepta sin descargar |
| `veridicus-tts` no arranca | Nada más se rompe: «Escuchar audio» responde `503` `speech.unavailable`; revertir su PR |
| `audio-worker` no arranca | El flujo de texto sigue; los audios en cola vencen por plazo y el analista graba de nuevo |
| La migración de U9 | Solo avanza; corrección con otra migración |

## 6. Secretos en CI/CD

| Secreto | Dónde vive | Quién lo usa |
|---|---|---|
| `GITHUB_TOKEN` con `packages: write` | Solo los *jobs* `build` en `main` | Publicar `audio-worker` y `tts-server` |
| Token de la ruta interna en las pruebas | Generado en la *fixture* de cada corrida (aleatorio de 32 bytes), nunca en el repositorio | Pruebas de nivel 1 de `audio-worker` y `session-api` |
| `VERIDICUS_SPEECH_TOKEN` real | `.env` del humano → `create-secrets.sh` → Secret `veridicus-speech-token` | Pods por `secretKeyRef`; la CI nunca lo ve |
| Token de Hugging Face | No se usa: los repositorios de modelos son públicos y la descarga la hace el humano con `fetch-models.sh` | — |
