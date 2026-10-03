# Pipeline de CI/CD — U10 anonymizer

**Insumos.** De `nfr-design/` de esta unidad: performance-design §2–§5 (pruebas `-m perf` y reporte de
nivel 2 con el proxy), security-design §2, §4, §5 y §10 (pruebas de propiedad, prueba residual,
políticas Kyverno con controles negativos, ADR y Escenarios A y B), scalability-design §2 y §4
(admisión y corrida de NFR8.4), reliability-design §1–§6 (100 % de ramas, *fakes* de destino,
repetibilidad), observability-design §1–§2 (*canary* y cardinalidad) y logical-components §5 (sin red,
sin GPU, datos sintéticos, cobertura). También: `functional-design/functional-spec.md`
(functional-spec, escenarios E1–E8), procesos de `inception/domain-design/components.md` (components),
C13–C16 de `inception/contract-design/contract-summary.md` (contract-summary), comandos de
`nfr-requirements/tech-stack-decisions.md`, la respuesta **P1 = A** de
`infrastructure-design-questions.md` (CoreDNS con lista blanca), los `cicd-pipeline.md` de U2 y U4
(`deploy-level0.yml`, `libs.yml`, `ai-eval-gate.yml`) y `## Testing Posture` y `## Deployment` de
`team.md`.

## 1. Principios

- Todos los *workflows* declaran `permissions: contents: read`, fijan las acciones por SHA y no tienen
  `kubeconfig` ni credencial del proveedor; solo el *job* `build` tiene `packages: write`, y solo en
  `main`.
- Ninguna prueba de la CI llama a un proveedor real, descarga un modelo, pide GPU ni abre conexiones
  fuera de `localhost` (NFR2.1). Ninguna prueba de los niveles 0 y 1 se reintenta; una prueba inestable
  va a cuarentena con un *issue* enlazado y su umbral nunca baja.
- Las pruebas de las guardias de AUTONOMIA-04 y de los contratos (C13, C14) se escriben primero y se
  ven en rojo antes de implementar (`## Testing Posture` de `team.md`).

## 2. *Workflows* y puertas

| *Workflow* | Se dispara con | *Job* | Comando y umbral (AUTONOMIA-02) | Bloquea |
|---|---|---|---|---|
| `anonymizer-proxy.yml` (nuevo) | `services/anonymizer-proxy/**`, `libs/**`, `contracts/**`, `deploy/veridicus/charts/anonymizer-proxy/**` | `lint` | `ruff check` y `ruff format --check` con 0 hallazgos; `mypy --strict` con 0 errores; `lint-imports` con 0 contratos rotos (`domain/` sin `httpx`) | Sí |
| | | `test-level0` | `pytest -m "not integration and not perf and not residual" -p pytest_socket --allow-hosts=127.0.0.1,::1`: E1–E8, comprobación final con enmascarador defectuoso (0 peticiones al *fake*), 4 cabeceras salientes, rutas en `404`, *fakes* lento, goteo, 500, 429, 302 y corte con exactamente 1 petición, `RLIMIT_CORE = 0`, cardinalidad de etiquetas; 0 fallos | Sí |
| | | `guards` | `pytest --cov-branch --cov-config=.coveragerc-guards --cov-fail-under=100` sobre `domain/` y `application/` | Sí |
| | | `test-level1` | `pytest -m "integration or perf"` con servidor HTTPS local (`trustme`): *canary* con 0 apariciones en logs y `/metrics`, 5.ª llamada `503` en < 50 ms, similitud enmascarada, `/readyz` sin salida; `-m perf` con p95 ≤ 50 ms por 10 000 caracteres, ≤ 10 ms al restaurar, ≤ 250 ms por `judge` y pico de RSS ≤ 256 MiB, reporte en `out/anonymizer-perf.json` | Sí |
| | | `residual` | `pytest -m residual`: 0 escapes bloqueantes; tasa informativa en `out/anonymizer-residual.json` como artefacto del *job* | Sí |
| | | `coverage` | `pytest --cov=anonymizer_proxy --cov-fail-under=80` | Sí |
| | | `audit` | `pip-audit` sin `HIGH`+ con corrección; `gitleaks` con 0 hallazgos; comprobación de datos sintéticos de U1 sobre `tests/` con 0 hallazgos | Sí |
| | | `build` | `hadolint` sin errores; imagen sin root (UID ≠ 0); Trivy con `--exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed`; en `main` publica `veridicus-anonymizer-proxy:<sha>` | Sí |
| `libs.yml` (de U4) | `libs/**` | `model_gateway` | Suma `anonymizer_route.py` y `AnonymizerGateway` a `.coveragerc-guards` con 100 % de ramas; prueba de `502` del proxy con 1 petición y turno en `error` | Sí |
| `deploy-level0.yml` (de U2) | `deploy/**`, `scripts/**`, `.github/**` | `render` | `helm template` con `values-cpu.yaml`, `values-gpu.yaml` (proxy apagado) y `deploy/veridicus/ci/values-anonymizer-enabled.yaml` (proxy habilitado con host `api.proveedor.invalid` y CIDR `192.0.2.0/24`); `kubeconform -strict` con 0 errores | Sí |
| | | `policies` | `kyverno apply deploy/policies/` con 0 violaciones en los tres renders; `kyverno test deploy/policies/tests/` con cada control negativo fallando como se espera; 0 `nvidia.com/gpu` en el proxy (NFR2.2) | Sí |
| | | `coredns` | `scripts/check-coredns-allowlist.py deploy/cluster/coredns.yaml`: solo `github.com` y, si algún *values* habilita el proxy, su `upstreamHost` tienen `forward`; el bloque `.:53` no tiene `forward` y termina en `template ANY ANY` con NXDOMAIN; código 0 | Sí |
| | | `provider-adr` | `scripts/check-provider-adr.sh deploy/veridicus/values-cpu.yaml deploy/veridicus/values-gpu.yaml`: código 0 (con el proxy apagado no hay nada que comprobar) | Sí |
| | | `rules` | `promtool test rules` sobre `veridicus-anonymizer` con un caso que dispara y otro que no por alerta | Sí |
| `anonymizer-enable-gate.yml` (nuevo) | PR que cambia `anonymizer.*` en un *values*, `deploy/cluster/coredns.yaml` o `services/anonymizer-proxy/rules/**` | `enable-reports` | `scripts/check-anonymizer-enable.py` (§3): código 0; con el proxy apagado en todos los *values* termina en 0 | Sí |

## 3. PR de habilitación

Un solo PR, con ADR, cambia `anonymizer.enabled: true` en el *values* de la máquina elegida. Antes
(o en el mismo PR) el `Corefile` suma la zona del host. `check-anonymizer-enable.py` exige:

| Evidencia | Comando que la produce | Umbral |
|---|---|---|
| ADR con las secciones de NFR1.2 y «Seudónimos estables», CIDR IPv4 ≥ /24 | `scripts/check-provider-adr.sh` | Código 0 |
| Zona del host en el `Corefile` | `scripts/check-coredns-allowlist.py` | Código 0 |
| Nivel 2 con el proxy | `uv run --directory evaluation python -m golden.run --profile cpu --model-gateway anonymizer --report out/level2-anonymizer.json` | Umbrales de NFR4.1; p95 ≤ 60 s (NFR3.5); Escenarios A y B con 0 valores sembrados y familia del juez ≠ generador (NFR5.1, NFR5.2) |
| Repetibilidad | Dos corridas de nivel 2 | Mismas calificaciones, `passage_ids` y alertas (NFR4.2) |
| Carga | `uv run --directory evaluation python -m load.run_batches --sessions 50 --concurrency 3 --report out/nfr8-anonymizer.json` | ≥ 98 % sin turnos en error; 0 `OOMKilled`; `busy` = 0 (NFR8.4) |
| Memoria | `out/anonymizer-perf.json` | `limits.memory` ≥ 1,2 × pico medido (NFR8.1) |
| Residual | `out/anonymizer-residual.json` | Citado por el ADR (NFR1.10) |
| *Embeddings* externos (si cambian) | Reindexado y barrido del umbral de U4 | `ready_at` < 180 s (NFR9.1); umbral recalibrado |

Los reportes viajan en el PR con el mismo mecanismo de `ai-eval-gate.yml` de U4, que también corre si
el PR cambia `VERIDICUS_JUDGE_URL` o `VERIDICUS_EMBEDDINGS_URL`.

## 4. Despliegue

| Paso | Qué pasa | Quién |
|---|---|---|
| 1 | `create-secrets.sh` genera `veridicus-anonymizer-credential` con `--dry-run=client -o yaml` desde el `.env` | Humano revisa y aplica |
| 2 | PR del `Corefile` con la zona del host fusionado; `kubectl apply` del `ConfigMap` y reinicio de CoreDNS; `scripts/check-coredns.sh` con código 0 | Humano |
| 3 | PR de habilitación fusionado (§3) | Humano (aprobación registrada) |
| 4 | Antes del módulo 8, `helm upgrade` manual del chart fusionado; después, Argo CD sincroniza | Humano / Argo CD |
| 5 | `scripts/smoke.sh https://veridicus.local` con el proxy en el camino y verificación manual de solo lectura (NFR1.7 y `getaddrinfo` de P1 = A) | Humano |

Ningún *workflow* ni *script* aplica cambios al clúster (AUTONOMIA-01, comprobado por
`check-no-cluster-apply.sh` de U2).

## 5. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la verificación manual tras habilitar | `git revert` del PR de habilitación: `anonymizer.enabled: false`, las URL vuelven al juez interno, el proxy desaparece en la siguiente aplicación o sincronización |
| El proveedor incumple el ADR o cambia de CIDR | PR con `anonymizer.enabled: false`; después, PR que quita la zona del `Corefile` |
| Una versión de reglas causa `failed_closed` | `git revert` del PR de reglas; nada salió mientras tanto |
| `Corefile` roto (CoreDNS no resuelve el clúster) | `git revert` del PR del `Corefile`, aplicación manual y reinicio de CoreDNS |
| `check-coredns.sh` detecta deriva tras `minikube start` | Volver a aplicar el `ConfigMap` versionado |

## 6. Entornos y secretos

| Entorno | Qué corre de U10 |
|---|---|
| CI | Pruebas de niveles 0 y 1, render con el proxy apagado y habilitado, políticas, `Corefile`; sin clúster ni credencial |
| Máquina de desarrollo (`values-cpu.yaml`) | Apagado salvo PR de habilitación para esa máquina |
| Máquina de demostración (`values-gpu.yaml`) | Apagado salvo PR de habilitación para esa máquina |

| Secreto | Dónde vive | Quién lo usa |
|---|---|---|
| Credencial del proveedor | `.env` del humano → `create-secrets.sh` → `veridicus-anonymizer-credential` | Solo el proxy, por `secretKeyRef` |
| `GITHUB_TOKEN` con `packages: write` | GitHub Actions, *job* `build` en `main` | Publicar la imagen |

La rotación de la credencial la hace el humano: nuevo valor en el `.env`, `create-secrets.sh`, revisión
y `kubectl -n veridicus rollout restart deployment veridicus-anonymizer-proxy`. `gitleaks` y una regla
Kyverno rechazan un valor literal en el manifiesto.
