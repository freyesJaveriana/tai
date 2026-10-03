# Decisiones de pila — U2 platform

**Insumos.** Definición de U2 en `inception/units-generation/unit-of-work.md`; FR12 y la pila fijada en
`inception/requirements-analysis/requirements.md` (requirements); C9, C14, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P4 de
`nfr-requirements-questions.md`; `security-requirements.md`; `## Deployment` de `team.md`.

La distribución de Kubernetes, el CNI, los namespaces y los `requests`/`limits` concretos los fija
Infrastructure Design; el modelo exacto del juez y de *embeddings* y el umbral se fijan con U4.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Servidor del juez y de *embeddings* | `llama.cpp` (`llama-server`), imagen fijada por digest, modelos GGUF, un `Deployment` por modelo | Ollama, vLLM para CPU | P1 = A. API compatible con OpenAI con `response_format` de esquema JSON (por gramática) y `seed`, eficiente en CPU, formato GGUF sin código ejecutable | NFR1.3, NFR2.1 |
| D2 | Servidor de Whisper (SHOULD) | `faster-whisper` detrás de un servidor compatible con OpenAI (`/v1/audio/transcriptions`), imagen fijada por digest | `whisper.cpp` con API propia | P1 = A. Encaja en C14 sin adaptador | NFR1.3 |
| D3 | Empaquetado | Chart paraguas `deploy/veridicus` (Helm 3) con un subchart por componente; `values-cpu.yaml` y `values-gpu.yaml` | Kustomize; manifiestos planos | P2 = A. Un solo `helm template` alimenta las políticas | NFR2.1, NFR8.1 |
| D4 | Operadores de terceros | Charts oficiales con versión exacta: CloudNativePG, `kube-prometheus-stack` (SHOULD), Argo CD (SHOULD), KEDA (COULD) | Instalar a mano | P2 = A. Versionados y revisables | NFR10.1 |
| D5 | PostgreSQL | `Cluster` de CloudNativePG de 1 instancia con imagen que incluya `pgvector`, fijada por digest | PostgreSQL en un `StatefulSet` propio | FR12.1 | NFR10.7 |
| D6 | Redis | `StatefulSet` propio de 1 réplica, imagen oficial de Redis por digest, AOF con `appendfsync everysec` en PVC, `requirepass` desde Secret | Chart de terceros; sin persistencia | P3 = A | NFR10.6 |
| D7 | Modelos en disco | `scripts/fetch-models.sh` en la anfitriona + `deploy/models.lock` (URL, revisión, `sha256`) + volumen de solo lectura + `initContainer` que verifica | Descarga en un `initContainer`; modelos dentro de la imagen | Ningún pod necesita internet (P4 = A) y las imágenes siguen pequeñas | NFR1.2, NFR10.4 |
| D8 | Red | `NetworkPolicy` de negar todo y reglas por dependencia (§3) | Solo pods sensibles | P4 = A | NFR1.1 |
| D9 | Políticas de manifiestos | `helm lint`, `helm template`, `kubeconform` (esquemas de Kubernetes y CRD copiados en el repositorio), Kyverno CLI, `yamllint`; todo sin red | Conftest/OPA | Ya elegido en team-practices | Todos |
| D10 | Prueba de humo | `scripts/smoke.sh <url-base>` en Bash con `curl`, más `frontend/e2e/smoke.spec.ts` (Playwright) | Solo Playwright | Ya fijada en team-practices; el *N* de segundos lo fija U4 | NFR10 |
| D11 | Regla AIR (SHOULD) | `PrometheusRule` sobre `veridicus_session_dismissal_ratio > 0.25` (C15) con una anotación que **propone** el umbral; nunca lo cambia | Alerta en Grafana | FR9.3, AUTONOMIA-03 | NFR15.1 |

## 2. Estructura de `deploy/`

```text
deploy/
  veridicus/                 # chart paraguas
    Chart.yaml  values-cpu.yaml  values-gpu.yaml
    charts/ session-api/ semantic-agent/ audio-worker/ frontend/ redis/ model-judge/ model-embeddings/ model-whisper/ postgres/ migrations-job/ create-admin-job/ network-policies/
  policies/                  # Kyverno, cada política con su control negativo en policies/tests/
  models.lock
scripts/
  fetch-models.sh  create-secrets.sh  smoke.sh
```

## 3. Dependencias de red permitidas (NFR1.1)

| Origen | Destino | Puerto |
|---|---|---|
| Todos los pods | `kube-dns` | 53 UDP/TCP |
| Entrada del clúster (*ingress*) | `frontend`, `session-api` | 80/8080 |
| `session-api` | PostgreSQL, Redis, `model-embeddings` | 5432, 6379, 8080 |
| `semantic-agent` | PostgreSQL (rol de solo lectura), Redis, `model-judge`, `model-embeddings` | 5432, 6379, 8080 |
| `audio-worker` (SHOULD) | Redis, `model-whisper` | 6379, 8080 |
| `migrations-job`, `create-admin-job` | PostgreSQL | 5432 |
| Prometheus (SHOULD) | `/metrics` de `session-api` | puerto interno |
| `anonymizer-proxy` (COULD) | Su destino externo declarado | 443 |

## 4. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| *Lint* de chart y YAML | `helm lint deploy/veridicus && yamllint deploy/` | 0 errores |
| Esquemas de Kubernetes | `helm template deploy/veridicus -f deploy/veridicus/values-cpu.yaml \| kubeconform -strict -schema-location deploy/schemas` (y lo mismo con `values-gpu.yaml`) | 0 inválidos |
| Políticas | `kyverno apply deploy/policies/ --resource <render>` y `kyverno test deploy/policies/tests/` | 0 violaciones en el render; cada control negativo falla como se espera |
| AUTONOMIA-01 estática | `scripts/check-no-cluster-apply.sh` | 0 apariciones |
| Imágenes | `trivy image` en el *job* de *build* | 0 `HIGH`/`CRITICAL` con corrección |

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| El esquema JSON por gramática de `llama-server` no garantiza todo C6 | U4 valida siempre contra C6; una salida inválida es `turn.error.invalid_output` |
| La licencia de las versiones recientes de Redis | Uso académico; Valkey es compatible con el mismo protocolo si hiciera falta cambiar |
| El CNI de la máquina no hace cumplir `NetworkPolicy` | Infrastructure Design elige un CNI que la cumpla; la verificación manual de NFR1.1 lo confirma |
