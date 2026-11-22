# Decisiones de pila — U2 platform

**Revisión 2 (2026-11-22). Segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git. D1–D11 conservan
su número y cada una dice si **se mantiene** o **cambia**. Lo nuevo empieza en D12. Respuestas: P1–P4 de
la revisión 1 y P5 = A (excepción de Argo CD).

**Insumos.** Definición de U2 en `inception/units-generation/unit-of-work.md`; FR12, NFR1–NFR15 y la pila
de `inception/requirements-analysis/requirements.md` (requirements, revisión 3); C14–C16, C21, C22, C25,
CD-04, CD-06 y CD-07 de `inception/contract-design/contract-summary.md` (contract-summary, revisión 3);
D3 y D4 del NFR de U9, F9 de U10, F7 de U3 y de U13; `security-requirements.md` (revisión 2);
`## Deployment` de `team.md`; `nfr-requirements-questions.md` (P1–P5).

La distribución de Kubernetes, el CNI, la ruta del PV de modelos, el Corefile concreto y los
`requests`/`limits` los fija Infrastructure Design. Los modelos concretos del juez y del verificador los
fija U11 en sus perfiles.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | Cambia | Servidores del juez y del verificador | `llama.cpp` (`llama-server`) con la imagen fijada por digest y modelos GGUF. Un `Deployment` por modelo local que nombra el perfil (juez y verificador, de familias distintas en los perfiles de evaluación). Sale el de *embeddings* | Ollama, vLLM para CPU | P1 = A. API compatible con OpenAI con esquema JSON por gramática y `seed`; eficiente en CPU; GGUF no trae código ejecutable | NFR1.3, NFR10.8, NFR2.1 |
| D2 | Se mantiene | Servidor de Whisper (SHOULD) | `faster-whisper` detrás de un servidor compatible con OpenAI (`/v1/audio/transcriptions`), con la imagen fijada por digest | `whisper.cpp` con API propia | P1 = A. Encaja en C14 sin adaptador | NFR1.3 |
| D3 | Cambia | Empaquetado | Chart paraguas `deploy/veridicus` (Helm 3) con un subchart por componente, y `values-cpu.yaml` y `values-gpu.yaml`. Los `Job` de retención y de `create-admin` van aparte, en `deploy/jobs/` | Kustomize; manifiestos planos | P2 = A. Un solo `helm template` alimenta las políticas. Separar los `Job` deja fuera de la sincronización lo que borra o crea cuentas | NFR2.1, NFR8.1, NFR10.16 |
| D4 | Cambia | Operadores de terceros | Charts oficiales con versión exacta: CloudNativePG, `kube-prometheus-stack` (SHOULD), Argo CD (SHOULD, con la excepción de P5 = A) y KEDA (COULD) | Instalar a mano | P2 = A. Versionados y revisables | NFR10.1, NFR1.7 |
| D5 | Cambia | PostgreSQL | `Cluster` de CloudNativePG de 1 instancia, imagen oficial fijada por digest, **sin `pgvector`**, `enableSuperuserAccess: false` y tres usuarios (`veridicus_owner`, `veridicus_app`, `veridicus_retention`) | PostgreSQL en un `StatefulSet` propio | FR12.1, AC9.4.1, A-2 | NFR10.7, NFR10.13 |
| D6 | Se mantiene | Redis | `StatefulSet` propio de 1 réplica, imagen oficial por digest, AOF con `appendfsync everysec` en un PVC y `requirepass` desde un Secret. Ahora se mide con NFR11.2 | Chart de terceros; sin persistencia | P3 = A | NFR10.6, NFR11.2 |
| D7 | Cambia | Modelos en disco | `scripts/fetch-models.sh` en la anfitriona, `deploy/models.lock` (URL, revisión y `sha256`), un `PersistentVolume` estático de solo lectura con su PVC y un `initContainer` que verifica el `sha256` | Descarga en un `initContainer`; modelos dentro de la imagen; `hostPath` | Ningún pod necesita internet. El perfil `restricted` prohíbe `hostPath` (R-02, `project.md`) | NFR1.2, NFR10.4, NFR10.11 |
| D8 | Cambia | Red | Una `NetworkPolicy` de negar todo en `veridicus` y en cada namespace de operadores, y reglas por dependencia (§3). Solo hay dos salidas externas: `anonymizer-proxy` (443) y `argocd-repo-server` (22 y 443) | Solo pods sensibles; Argo CD fuera de la política | P4 = A, FR12.3, P5 = A | NFR1.1, NFR1.5–NFR1.7 |
| D9 | Se mantiene | Políticas de manifiestos | `helm lint`, `helm template`, `kubeconform` (esquemas de Kubernetes y CRD copiados en el repositorio), Kyverno CLI y `yamllint`, todo sin red | Conftest/OPA | Ya elegido en team-practices | Todos |
| D10 | Cambia | Salud y humo | Sondas de C16 en los cuatro servicios. `scripts/smoke.sh <url-base>` en Bash con `curl` comprueba los cuatro `/healthz`, y `frontend/e2e/smoke.spec.ts` (Playwright) comprueba el resto | Solo Playwright | `team.md`, C16. El *N* lo fijan U4 y U11 | NFR10.17, NFR8.3 |
| D11 | Cambia | Regla AIR (SHOULD) | Una `PrometheusRule` sobre `veridicus_session_dismissal_ratio > 0.25`, una fracción sobre las *W* de C25. Solo avisa, sin proponer umbral | Alerta en Grafana | US10.8, US10.6 «Retirada», AUTONOMIA-03 | NFR15.1 |
| D12 | Nuevo | Servidor de TTS (SHOULD) | Piper con una voz `es_*`, imagen fijada por digest, modelo ONNX fijado en `models.lock` y montado del mismo PV | Coqui TTS | D3 del NFR de U9; cierra R-05 | NFR1.3, NFR10.8 |
| D13 | Nuevo | `anonymizer-proxy` | Un `Deployment` con la imagen de `services/anonymizer-proxy` (módulo de `libs/anonymizer` con sus adaptadores nativos), el único que monta `veridicus-provider-keys` | Adaptadores en `semantic-agent` | C21, C22, CD-04, AC11.6.4 | NFR1.5, NFR10.12 |
| D14 | Nuevo | Lista blanca de DNS | `deploy/coredns/Corefile` como artefacto revisable, que el humano aplica tras la fusión. Une `allowed-domains.v1.yaml` del módulo con `deploy/coredns/infra-domains.yaml` (hoy `github.com`). Se comprueba con F9 de U10 | Editar CoreDNS a mano; `hostAliases` en Argo CD (P5 D) | FR12.3, AC11.5.2 precisada por P5 = A | NFR1.4 |
| D15 | Nuevo | Perfiles y precios en el clúster | El `ConfigMap` `veridicus-profiles` se genera de la copia del chart (`deploy/veridicus/files/`), y `scripts/check-config-copy.sh` compara el SHA-256 | Un `initContainer` que clona el repositorio; montar desde la anfitriona | C21; Helm no lee fuera del chart (`project.md`) | NFR10.15 |
| D16 | Nuevo | TLS | Un `Ingress` de ingress-nginx con el Secret `veridicus-tls` (certificado local que crea el humano) y `ssl-redirect` | HTTP en la máquina local | Cookie `Secure` (C1) y contexto seguro para la voz; cierra R-06 | NFR10.14 |
| D17 | Nuevo | Excepciones de imágenes de terceros | `deploy/image-exceptions.yaml` con imagen, motivo y caducidad; Kyverno lo lee y falla ante una excepción vencida | Excepciones en línea en cada política | `team.md` (excepciones con caducidad); cierra R-03 | NFR10.1 |

## 2. Estructura de `deploy/`

```text
deploy/
  veridicus/                 # chart paraguas (lo sincroniza Argo CD)
    Chart.yaml  values-cpu.yaml  values-gpu.yaml
    files/                   # copia de config/profiles.yaml y config/prices.yaml (NFR10.15)
    charts/ session-api/ semantic-agent/ audio-worker/ anonymizer-proxy/ frontend/ redis/
            model-judge/ model-verifier/ model-whisper/ model-tts/ models-volume/
            postgres/ migrations-job/ network-policies/ ingress/ monitoring-rules/
  jobs/                      # chart aparte que Argo CD no sincroniza; lo aplica el humano
    retention-job/  create-admin-job/
  coredns/
    Corefile  infra-domains.yaml
  policies/                  # Kyverno; cada política con su control negativo en policies/tests/
    secret-consumers.yaml
  network-deps.yaml  image-exceptions.yaml  models.lock
  argocd/
    application.yaml         # path: deploy/veridicus; sin deploy/jobs
scripts/
  fetch-models.sh  create-secrets.sh  smoke.sh
  check-no-cluster-apply.sh  check-network-deps.sh  check-coredns-domains.sh
  check-config-copy.sh  check-no-data.sh
```

## 3. Dependencias de red permitidas (NFR1.1, NFR10.18)

Esta tabla es la fuente de `deploy/network-deps.yaml`. Todos los pods alcanzan `kube-dns` por 53 UDP/TCP.

| Origen | Destino | Puerto |
|---|---|---|
| `ingress-nginx` | `frontend`, `session-api` | 8080 |
| `session-api` | PostgreSQL, Redis, `audio-worker` (ruta interna de síntesis) | 5432, 6379, 8080 |
| `semantic-agent` | Redis, `model-judge`, `model-verifier`, `anonymizer-proxy` | 6379, 8080, 8080, 8080 |
| `audio-worker` (SHOULD) | Redis, `model-whisper`, `model-tts` | 6379, 8080, 8080 |
| `anonymizer-proxy` | Internet salvo rangos privados y del clúster (dominios de C22, los impone el módulo) | 443 |
| `migrations-job`, `create-admin-job` | PostgreSQL | 5432 |
| `retention-job` | PostgreSQL, Redis | 5432, 6379 |
| Operador CloudNativePG (`cnpg-system`) | Instancias de PostgreSQL | 8000, 5432 |
| Instancias de PostgreSQL y operadores | API server de Kubernetes | 443 |
| Prometheus (`monitoring`, SHOULD) | `/metrics` de `session-api` y `semantic-agent` | puerto interno |
| KEDA (`keda`, COULD) | Redis | 6379 |
| `argocd-repo-server` (`argocd`, SHOULD) | `github.com`, salvo rangos privados y del clúster (P5 = A) | 22, 443 |

## 4. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| *Lint* de charts y YAML | `helm lint deploy/veridicus deploy/jobs && yamllint deploy/` | 0 errores |
| Esquemas de Kubernetes | `helm template deploy/veridicus -f deploy/veridicus/values-cpu.yaml \| kubeconform -strict -schema-location deploy/schemas` (lo mismo con `values-gpu.yaml` y con `deploy/jobs`) | 0 inválidos |
| Políticas | `kyverno apply deploy/policies/ --resource <render>` y `kyverno test deploy/policies/tests/` | 0 violaciones en el render; cada control negativo falla como se espera |
| AUTONOMIA-01 y ZINE | `scripts/check-no-cluster-apply.sh` | 0 apariciones; cada control negativo detectado |
| Red declarada | `scripts/check-network-deps.sh deploy/network-deps.yaml <render>` | 0 dependencias sin regla y 0 reglas sobrantes |
| DNS | `scripts/check-coredns-domains.sh deploy/coredns/Corefile deploy/coredns/infra-domains.yaml` | F9 sin diferencias; 3 controles negativos fallan |
| Perfiles del mismo commit | `scripts/check-config-copy.sh` | SHA-256 iguales |
| Sin datos | `scripts/check-no-data.sh <render>` y `gitleaks detect` | 0 hallazgos |
| Regla AIR | `promtool test rules deploy/veridicus/charts/monitoring-rules/tests/air.test.yaml` | Pasan los *fixtures* 5/20 y 6/20 |
| Imágenes | `trivy image` en el *job* de *build* | 0 `HIGH`/`CRITICAL` con corrección |
| AOF y modelos (nivel 1) | `uv run pytest deploy/tests/level1 -m platform` (contenedores locales de Redis y de `llama-server`) | Las 10 entradas sobreviven; el archivo alterado impide arrancar |

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| El esquema JSON por gramática de `llama-server` no garantiza todo C6 | El analizador valida siempre contra su esquema; una salida inválida es un error del tramo, nunca un hallazgo parcial |
| La licencia de las versiones recientes de Redis | Uso académico; Valkey habla el mismo protocolo si hiciera falta cambiar |
| El CNI de la máquina no hace cumplir `NetworkPolicy` | Infrastructure Design elige Calico; las verificaciones manuales de NFR1.1 y NFR1.7 lo confirman |
| Salidas por IP literal desde el proxy o desde `argocd-repo-server` | Declarado en `security-requirements.md` §6; el módulo y CoreDNS lo acotan |
| `deploy/jobs/` queda sin aplicar en una instalación nueva | La guía de instalación de Infrastructure Design lo nombra como paso manual del humano |
