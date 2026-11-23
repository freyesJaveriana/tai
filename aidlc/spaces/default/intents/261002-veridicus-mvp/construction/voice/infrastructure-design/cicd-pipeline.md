# Pipeline de CI/CD — U9 voice

**Revisión 2 (2026-11-23).** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git. Las
secciones conservan su número; lo que sale queda «Retirado». Cambian: los *workflows* siguen el patrón
`changes` + `gate` de U4 y U11; sale `libs.yml` (lo sustituye `analyzer.yml` de U11); el render solo usa
`values-cpu.yaml`; la corrida de voz y el E2E corren en la única máquina; el reporte de voz se versiona;
entra `whisper-server.yml` (IDS-U9-04). Supuesto de máquina: una sola de 64 GB, solo CPU (IDS-U2-01).

**Insumos.**
- Comandos de verificación, dependencias y riesgos de `nfr-requirements/tech-stack-decisions.md` (§4–§6).
- De `nfr-design/` revisión 2: dobles de prueba, cobertura, textos y accesibilidad (logical-components §5);
  corrida de voz y `perf` (performance-design §1, §2, §6, §7); controles y sus pruebas (security-design §1–§14);
  idempotencia y capacidad (scalability-design §2–§4); fallos y configuración (reliability-design §1–§13);
  métricas (observability-design §2).
- Flujos F1–F8 de `functional-design/functional-spec.md` (functional-spec); SpeechProcessing y ModelGateway de
  `inception/domain-design/components.md` (components); C1, C5, C13, C14, C16 y C25 de
  `inception/contract-design/contract-summary.md` (contract-summary).
- `cicd-pipeline.md` revisión 2 de U2 (flujo común, `deploy-level0.yml`), U4 (patrón `changes` + `gate`) y U11
  (`analyzer.yml`, evidencia de nivel 2); `infrastructure-specification.md` revisión 2 de esta carpeta.
- `## Testing Posture`, `## Deployment` y `## Code Style` de `team.md`.

Reglas comunes de U2: `permissions: contents: read`, acciones fijadas por SHA, sin `kubeconfig` ni
credenciales del clúster; solo el *job* `build` tiene `packages: write`, y solo en `main`. Ninguna prueba de los
niveles 0 y 1 descarga un modelo, usa GPU o un micrófono real, ni se reintenta (NFR2.1).

## 1. *Workflows* y puertas · cambia

Cada *workflow* propio se dispara con todo PR, filtra por rutas en su *job* `changes` y termina en un *job*
`gate`, la única comprobación obligatoria (IDS-U9-18), verde si todo pasó o si `changes` no encontró trabajo.

| *Workflow* | *Job* | Comando | Umbral |
|---|---|---|---|
| `audio-worker.yml` | `changes` | `scripts/ci-paths.py audio-worker`: `services/audio-worker/**`, `libs/model_gateway/**`, `libs/integrity_policy/**`, `contracts/**`, `.github/workflows/audio-worker.yml` | — |
| | `lint` | `uv run --directory services/audio-worker ruff check .`, `ruff format --check .`, `mypy --strict .`, `lint-imports` (sin `libs.anonymizer`, NFR1.4) | 0 errores; cada control negativo de import-linter falla |
| | `test-level0` | `uv run --directory services/audio-worker pytest -m "not integration"` con `pytest-socket`: contratos C5 primero, configuración, URL internas, `speech_text.py`, latido con `busy_until`, `AofRewriteRequester` | Verde |
| | `guards` | `uv run --directory services/audio-worker pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % de ramas en `audio_lifecycle.py`, `speech_text.py` y `AofRewriteRequester` (NFR13.2) |
| | `test-level1` | `uv run --directory services/audio-worker pytest -m integration` con Redis 7.2 configurado como U2 y Whisper y TTS *fakes* | `XLEN` = 0 tras cada resultado; centinela fuera del AOF tras la reescritura; 10 mensajes de 8 MB sin `OOM command not allowed` y pico de RSS de Redis ≤ 427 MiB (IDS-U9-05); 1 llamada a Whisper con dos entregas; *fake* de 60 s sin reinicio; 0 centinelas en logs |
| | `coverage` | `pytest --cov --cov-fail-under=80` | ≥ 80 % de líneas (NFR13.1) |
| | `audit` | `pip-audit` y `gitleaks detect --no-git --source services/audio-worker` | 0 `HIGH`/`CRITICAL` con corrección; 0 secretos |
| | `build` (solo `main`) | `hadolint Dockerfile`, `docker build`, `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`, *push* a GHCR por SHA | 0 hallazgos; `USER 10001` |
| | `gate` | Depende de todos | Verde |
| `tts-server.yml` (P2 = A) | `changes` | `services/tts-server/**`, `.github/workflows/tts-server.yml` | — |
| | `lint`, `test-level0`, `coverage` | `uv run --directory services/tts-server` con `ruff`, `mypy --strict` y `pytest` con la voz *fake* tras una interfaz propia | 0 errores; 1 y 400 caracteres → `200` `audio/wav`; 0 y 401 → `422`; respuesta ≤ `speech_audio_max_bytes`; concurrencia 1; `/readyz` `503` antes de cargar la voz; centinela fuera de logs; ≥ 80 % de líneas |
| | `licenses` | `pip-licenses` frente a `services/tts-server/licenses-allowed.yaml` y la versión fijada de `piper-tts` | 0 licencias fuera de la lista (IDS-U9-20) |
| | `audit`, `build`, `gate` | Como `audio-worker.yml` | Igual |
| `whisper-server.yml` (si se adopta IDS-U9-04) | `changes` … `gate` | Mismos *jobs* que `tts-server.yml` sobre `services/whisper-server/**`, con un modelo *fake* tras la interfaz | `200` con un WAV sintético; `/health` `503` antes de cargar; modo sin conexión (`pytest-socket`); centinela fuera de logs; ≥ 80 % de líneas; Trivy y `USER 10001` (cierra R-01) |
| `session-api.yml` (U3) | Sus *jobs* | U9 añade las pruebas de voz al nivel 0 y 1, las ramas de `AudioValidator`, `VoiceGuards` y `hold_release.py`, la prueba del archivo antes que fila con fallo inyectado y `pytest -m perf -k voice` | 100 % de ramas en los módulos guardia; p95 del `202` ≤ 500 ms y pico ≈ 14 MB por subida (NFR3.4, NFR8.4) |
| `analyzer.yml` (U11) | Sus *jobs* | Cubre los adaptadores `transcribe` y `synthesize` de `libs/model_gateway` y sus *fakes* (D13) | Los de U11, ≥ 80 % |
| `frontend.yml` (U4) | Sus *jobs* | Componentes de voz, ESLint con `speechSynthesis` y `SpeechRecognition` prohibidos (control negativo), `vitest-axe` | Verde; ≥ 80 % de líneas (NFR1.3, NFR14.1, NFR14.2) |
| `deploy-level0.yml` (U2) | Pasos 4–10 | Render de `values-cpu.yaml` con `voice.enabled` en `true` y en `false`; Kyverno con los controles negativos de la especificación §5; `scripts/check-models-lock.py deploy/models.lock`; `scripts/check-synthetic-audio.sh`; `promtool test rules` con `voice.test.yaml`; `deploy/tests/level0/test_voice_ingress.py` | Cada control negativo falla como se espera; 0 entradas de modelo fuera de su lista; 0 `.wav`/`.mp3` fuera de `evaluation/voice/manifest.json` (NFR12.1) |
| `voice-eval-gate.yml` | `check` | `scripts/check-voice-report.py` (§2): sin cambios en las rutas de voz, verde; con cambios o con una etiqueta de entrega, exige un reporte válido del árbol del PR | §2 |
| `libs.yml` (U4) | **Retirado** | Lo sustituye `analyzer.yml` (IDS-U9-14) | — |

## 2. Corrida de voz de nivel 2 (fuera de la CI) · cambia

**Rutas de voz.** `voice-eval-gate.yml` exige el reporte cuando el PR toca: entradas `whisper-*` o `piper-*`
de `deploy/models.lock`; `services/tts-server/**` y `services/whisper-server/**`; `libs/model_gateway/speech.py`
y `libs/model_gateway/adapters/speech_local.py`; los parámetros de Whisper de `services/audio-worker/`
(modelo, idioma, `beam_size`, VAD, `cpu_threads`); `contracts/integrity/clarification-speech.v1.yaml`; las
cifras de voz de C25; y `evaluation/voice/**`. También bloquea toda entrega etiquetada.

| Paso | Diseño |
|---|---|
| Dónde | En WSL2 de la única máquina, contra `model-whisper` y `model-tts` del clúster desplegado con `values-cpu.yaml`, por `kubectl port-forward` (no cambia el clúster); la corrida mixta usa `todo-local` con el juez encendido (IDS-U9-21) |
| Comando | `uv run --directory evaluation python -m voice.run --report evaluation/reports/voice/<fecha>-voice.json` |
| Contenido | `model_digest` de Whisper y de la voz, `manifest` de clips con su `sha256`, p50/p95/máximo por tramo de duración, WER, picos de RSS por pod, resultados por `outcome`, y un YAML de evidencia con el *commit* evaluado y los digests (IDS-U9-19) |
| Umbrales que comprueba `check-voice-report.py` | Digests iguales a los de `models.lock` del PR; p95 de transcripción ≤ 12 s (clips ≤ 30 s, sola y mixta) y ≤ 40 s (120 s); p95 del turno de voz ≤ 192 s; WER ≤ 20 %; 0 textos en 3 clips de silencio o ruido; 100 % de textos iguales en dos pasadas; mismas alertas que el texto escrito en 10 relatos sintetizados; p95 de síntesis ≤ 5 s y WER ≤ 20 % en 5 frases de la plantilla; 0 turnos vencidos con 1 y 3 sesiones; tramo incremental con p95 ≤ 180 s en la corrida mixta; p95 de espera ≤ 12 s; picos de RSS ≤ topes; 0 `OOMKilled`; 0 errores de reescritura del AOF. Control negativo: un reporte con un digest distinto falla |

Ningún paso envía nada fuera de la máquina ni a ZINE.

## 3. Del PR al clúster · cambia

| Paso | Qué pasa |
|---|---|
| 1 | PR de la migración de B9 (tablas de voz, índice parcial y permisos sin `DELETE` para `veridicus_app`) como `Job` aparte, antes del código que la usa |
| 2 | PR de código con sus *workflows* en verde y, si toca §2, con el reporte de voz versionado |
| 3 | En `main`, `build` publica `audio-worker`, `tts-server`, `whisper-server` (si aplica), `session-api` y `frontend` por SHA |
| 4 | Si cambió un modelo, el humano ejecuta `scripts/fetch-models.sh` en WSL2 (solo escribe en `/srv/veridicus/models` y verifica cada `sha256`; no toca el clúster) |
| 5 | PR de despliegue de U2 con los digests; `deploy-level0.yml` valida el render |
| 6 | El humano aplica el artefacto fusionado (antes del módulo 8) o lo sincroniza Argo CD; `audio-worker` sin corte, `model-whisper` y `model-tts` con `Recreate` (la voz se pausa unos segundos; el texto sigue) |
| 7 | `scripts/smoke.sh https://veridicus.local:8443` (incluye `/readyz` de `audio-worker`) y `scripts/check-ingress-routes.sh https://veridicus.local:8443` con los dos casos de voz |
| 8 | Antes de etiquetar una entrega, en WSL2: `npx --prefix frontend playwright test e2e/voice.spec.ts` contra `https://veridicus.local:8443` con el micrófono *fake* de Chromium (p95 del turno ≤ 192 s con clips ≤ 30 s y 0 violaciones `serious` o `critical` de axe) y después `scripts/check-voice-logs.sh` con 0 apariciones del centinela (cierra R-02 y R-03) |

## 4. Entornos · cambia

| Entorno | Qué es | Voz |
|---|---|---|
| CI | Render, políticas y pruebas en contenedor; sin clúster | *Fakes* de Whisper, TTS y micrófono |
| Máquina única (Minikube 50 GiB, 16 CPU) | `values-cpu.yaml` | Encendida en CPU; ahí corren la corrida de voz, la mixta con el juez, el E2E y la demostración |
| Máquinas de desarrollo (20 GiB) y de demostración (28 GiB) | **Retirado** (IDS-U9-02) | — |
| ZINE | No aplica a la voz | — |

## 5. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh`, `check-ingress-routes.sh` o `voice.spec.ts` tras desplegar | `git revert` del PR de despliegue y nueva aplicación o sincronización |
| Un modelo de voz nuevo da peores métricas | `git revert` del PR de `models.lock`, `fetch-models.sh` y reinicio del servidor |
| `model-tts` no arranca | Nada más se rompe: «Escuchar audio» responde `503` `speech.unavailable`; revertir su PR |
| `audio-worker` o `model-whisper` no arrancan | El flujo de texto sigue; los audios en cola vencen por plazo o por el recorte de 1 920 s y el analista graba de nuevo |
| Presión de memoria en la máquina | PR que pone `voice.enabled: false`; el humano lo aplica |
| La migración de B9 | Solo avanza; se corrige con otra migración |

## 6. Secretos en CI/CD

| Secreto | Dónde vive | Quién lo usa |
|---|---|---|
| `GITHUB_TOKEN` con `packages: write` | Solo los *jobs* `build` en `main` | Publicar las imágenes de voz |
| Token de la ruta interna en las pruebas | Generado en la *fixture* de cada corrida (32 bytes aleatorios), nunca en el repositorio | Nivel 1 de `audio-worker` y `session-api` |
| `VERIDICUS_SPEECH_TOKEN` real | `.env` del humano → `create-secrets.sh` → Secret `veridicus-speech-token` | Pods por `secretKeyRef`; la CI nunca lo ve |
| Token de Hugging Face | No se usa: los repositorios son públicos y descarga el humano con `fetch-models.sh` | — |
