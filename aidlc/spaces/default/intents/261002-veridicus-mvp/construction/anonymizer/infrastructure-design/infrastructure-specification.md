# Especificación de infraestructura — U10 anonymizer

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** La revisión 1 describía un proxy COULD, apagado por defecto, con su propia
  `NetworkPolicy` por CIDR, su `Corefile` y su Secret. Ahora U10 es MUST (D1): el proxy forma parte del
  despliegue base y es el único pod con salida a internet, y la red, la lista blanca de CoreDNS, el
  Secret, el endurecimiento, el volumen del NER y los `requests`/`limits` son de U2 (security-design §5
  «Retirado», logical-components §4 y §5). Este documento fija lo que U10 necesita del pod y del
  anfitrión de la CLI, y lo que propone a U2.
- **Numeración.** §1, §2, §4 y §5 conservan su tema. §3 (DNS con lista blanca) queda «Retirado». La
  tabla de precisiones de la revisión 1 (§6) se retira entera (IDS-U10-11) y la sustituye la tabla
  IDS-U10-01 a IDS-U10-12.
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU y sin máquina GPU; el tamaño de Minikube lo
  decide U2 (brief del 2026-11-22). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna en esta pasada (`infrastructure-design-questions.md`, sección del 2026-11-23).

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 2): performance-design §1, §2, §4 y §5;
  security-design §1, §4, §6, §7, §8 y §12; scalability-design §2–§5; reliability-design §1–§4;
  observability-design §2 y §6; logical-components §2, §4 y §5; tabla NFRD-U10-01 a NFRD-U10-17.
- `functional-design/functional-spec.md` (functional-spec: §1, F3a, F3b, F8 y F9).
- Anonymizer, AnalyzerCli y la tabla de fronteras de `inception/domain-design/components.md` (components).
- C16, C20, C21, C22 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements/tech-stack-decisions.md` (D1, D2, D5, D6, D9, D13 y §2).
- Lo que U2 ya fijó en su NFR Design revisión 2 (`platform/nfr-design/security-design.md` §2.1–§2.3,
  §5, §6, §7.3 y §11; NFRD-U2-03 y NFRD-U2-08).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Contenedor en el clúster Minikube de U2: `Deployment` `veridicus-anonymizer-proxy` del subchart `anonymizer-proxy` del chart paraguas, **siempre renderizado** | D1: U10 es MUST y está en el camino de toda llamada comercial del clúster; qué genera el chart es de U2 |
| Réplicas | 1, sin HPA ni `PodDisruptionBudget` | scalability-design §1 y §3 (DE2): una corrida a la vez (NFR-U4-12) y un solo nodo |
| Proceso | Un proceso Uvicorn (DE3), mamparo de 4 peticiones (`VERIDICUS_ANONYMIZER_MAX_CONCURRENCY` = 4) que **solo** cubre `POST /v1/generate` (IDS-U10-04) | scalability-design §2; las sondas no pueden quedar sin cupo |
| Puertos | 8080 `http`: `POST /v1/generate`, `/healthz` y `/readyz`; 9090 `metrics`: `/metrics`. Ninguno lo publica un `Ingress` | security-design §6; NFRD-U10-09, NFRD-U10-11; NFR10.17 de U2 |
| Estrategia de actualización | `RollingUpdate` con `maxSurge: 1` y `maxUnavailable: 0`; `terminationGracePeriodSeconds: 290` y Uvicorn con `--timeout-graceful-shutdown 280` (IDS-U10-03) | Una llamada en curso dura como mucho `model_call_timeout_s` = 270 s más la conexión; el segundo pod cabe en 64 GB |
| Sondas | `startupProbe` `/readyz` en 8080, periodo 5 s y 24 fallos (120 s); `livenessProbe` `/healthz` y `readinessProbe` `/readyz` en 8080, periodo 10 s, plazo 2 s, 3 fallos | Arranque ≤ 60 s (performance-design §5) y sonda ≥ 90 s (NFRD-U2-08), con margen para la CPU de WSL2; `/readyz` nunca abre conexiones (reliability-design §4) |
| Imagen | `ghcr.io/<dueño>/veridicus-anonymizer-proxy`, publicada con la etiqueta del SHA y usada por digest; base Python 3.12 mínima por digest con `ca-certificates`; `torch` del índice solo CPU; **sin el NER dentro** | `team.md`; la verificación TLS usa las CA públicas de la imagen (security-design §6); el NER va en el volumen de solo lectura (D13) |
| Almacenamiento | Sin PVC de escritura. `/tmp` como `emptyDir` en memoria de 16 MiB (lo exige `memory-only-tmp` de U2, aunque el proceso no escribe); NER desde `veridicus-models` de solo lectura; perfiles desde el `ConfigMap` `veridicus-profiles` de solo lectura | security-design §12 (NFR10.10); NFR10.15 de U2; `volume-consumers` de U2 ya incluye el proxy |
| Red | Salida 443 hacia `0.0.0.0/0` con el `except` de los rangos privados y del clúster, más DNS; entrada solo desde `semantic-agent` a 8080 y Prometheus a 9090. Todo de U2 | `network-deps.yaml` de U2 (§2.1); el destino real lo fija el módulo con su lista y su URL constante (security-design §6) |
| Resolución de nombres | CoreDNS con la lista blanca de U2: reenvía hacia fuera solo los tres dominios de `allowed-domains.v1.yaml` y `github.com` | NFR1.4 de U2; F9 la compara con la lista del módulo |
| Entornos | Una sola máquina de 64 GB, solo CPU, con el mismo digest que publica la CI. Sin *staging* ni producción. La CLI corre en la misma máquina, fuera del clúster (§4) | Supuesto del brief; `team.md` |
| IaC | Subchart Helm de U2 con los *values* que U10 propone en §1.1; `values.schema.json` exige `nerThreads` entre 1 y 8 y `maxConcurrency` entre 1 y 4. Ningún *script* lo aplica | AUTONOMIA-01: el humano aplica lo ya fusionado y, desde el módulo 8, Argo CD sincroniza |
| Recursos (propuesta a U2) | CPU `requests` 1, `limits` 2; memoria `requests` 1536 MiB, `limits` 2 GiB; sin GPU | Pico ≤ 1,5 GiB × 1,2 + 16 MiB del `emptyDir` = 1,82 GiB (scalability-design §4); 2 hilos de `torch` (IDS-U10-02) |
| Clasificación | Etiqueta `veridicus.io/data-class: sensitive` y anotación `veridicus.io/provider-adr` con la ruta del ADR de Anthropic | Recibe testimonio en claro por C21; el ADR es obligatorio (NFR1.2) |

**Presupuesto.** El proxy pide 1 CPU y 1,5 GiB y puede llegar a 2 CPU y 2 GiB; durante una actualización
conviven dos pods (4 GiB de límite). Frente a la revisión 1 (256 MiB) crece porque ahora carga el NER en
memoria. U2 suma estas cifras a su presupuesto al fijar el tamaño de Minikube en la máquina de 64 GB.

## 1.1 Valores del pod que U10 propone a U2

```yaml
anonymizerProxy:
  replicas: 1
  ports: { http: 8080, metrics: 9090 }
  maxConcurrency: 4          # VERIDICUS_ANONYMIZER_MAX_CONCURRENCY
  nerThreads: 2              # VERIDICUS_ANONYMIZER_NER_THREADS, OMP y MKL
  terminationGracePeriodSeconds: 290
  resources:
    requests: { cpu: "1", memory: 1536Mi }
    limits:   { cpu: "2", memory: 2Gi }
  tmpSizeLimit: 16Mi
  startupProbe: { path: /readyz, port: 8080, periodSeconds: 5, failureThreshold: 24 }
```

## 2. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-anonymizer-proxy` (Service) | load-balancer interno | `ClusterIP`; puertos 8080 (`http`) y 9090 (`metrics`); `http://veridicus-anonymizer-proxy.veridicus.svc.cluster.local:8080` | HTTP sin TLS dentro del clúster, como el resto de servicios internos; lo protegen las `NetworkPolicy` de U2. La URL la configura U4 en `semantic-agent` |
| `veridicus-models` (PV estático y PVC, U2) | almacenamiento de solo lectura | Entrada `ner` en `deploy/models.lock` (URL, revisión, `sha256`, lista de archivos); montado en `/models` con `readOnly: true` | El modelo concreto se fija con los criterios de IDS-U10-01; `VERIDICUS_ANONYMIZER_NER_PATH` y `_NER_SHA256` salen de esa entrada |
| `veridicus-profiles` (ConfigMap, U2) | configuración | `profiles.yaml`, copia de `config/profiles.yaml` con el mismo SHA-256, montado de solo lectura | `VERIDICUS_ANONYMIZER_PROFILES_PATH` apunta al archivo montado (NFRD-U10-11) |
| `veridicus-provider-keys` (Secret, U2) | secreto | Una clave por cada `api_key_ref` externa de `config/profiles.yaml`, con su nombre exacto; se consume con `envFrom` (IDS-U10-06) | Creado por el humano con `create-secrets.sh` desde el `.env`; montado solo en este pod (`secret-consumers.yaml` de U2) |
| CoreDNS (`kube-system`, U2) | dns | Lista blanca de U2 | U10 aporta la lista de dominios y la comparación de F9 |
| Destino externo (C22) | API de terceros | `https://api.anthropic.com/v1/messages` en la primera rebanada; TLS ≥ 1.2, sin redirecciones, un intento | Fuera del clúster; solo recibe el cuerpo seudonimizado que pasó la verificación final |
| `ServiceMonitor` y reglas (U2, módulo 8) | monitoreo | Raspado del puerto 9090 cada 30 s; reglas informativas de `monitoring-design.md` | NFRD-U10-09, NFRD-U2-03 |
| Base de datos, Redis, colas, caché | — | No aplica | El proxy no tiene credencial de ninguno ni guarda estado (scalability-design §3) |

### 2.1 Ajustes del contenedor

| Variable | Valor | Origen |
|---|---|---|
| `VERIDICUS_ANONYMIZER_NER_PATH` | `/models/<ruta de la entrada ner>` | tech-stack-decisions §2 |
| `VERIDICUS_ANONYMIZER_NER_SHA256` | `sha256` del manifiesto de la entrada `ner` de `models.lock`, inyectado por el chart | security-design §4 |
| `VERIDICUS_ANONYMIZER_PROFILES_PATH` | `/etc/veridicus/profiles/profiles.yaml` | NFRD-U10-11 |
| `VERIDICUS_ANONYMIZER_MAX_CONCURRENCY` | 4 | scalability-design §2 |
| `VERIDICUS_ANONYMIZER_NER_THREADS` | 2 | NFRD-U10-07 |
| `OMP_NUM_THREADS`, `MKL_NUM_THREADS` | Igual a `VERIDICUS_ANONYMIZER_NER_THREADS` | IDS-U10-05 |
| `CUDA_VISIBLE_DEVICES` | `""` | scalability-design §5 |
| `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`, `HF_HUB_DISABLE_TELEMETRY` | `1` (también en el `Dockerfile`) | security-design §12 |
| `TOKENIZERS_PARALLELISM` | `false` | IDS-U10-05 |
| Claves de API | Del Secret `veridicus-provider-keys` por `envFrom` | security-design §8 |
| `VERIDICUS_LIMIT_*` | Sin definir: rigen las cifras de `contracts/limits.v1.yaml` (solo se pueden bajar) | security-design §7 |

Salen de la revisión 1 `VERIDICUS_ANONYMIZER_UPSTREAM_URL`, `_MODEL`, `_RULES_SHA256` y
`_MASKING_TIMEOUT_SECONDS`, y el `ConfigMap` `veridicus-anonymizer-rules`: las reglas van en el paquete
con su `SHA256SUMS` (DS12) y el plazo sale del perfil y de C25.

## 3. Resolución DNS con lista blanca · Retirado

Retirado: la lista blanca de CoreDNS (P1 = A de la revisión 1) es de U2 (NFR1.4 de U2,
`deploy/coredns/Corefile`). Con ella se van los hallazgos R-02, R-03 y R-04 de la revisión 1 de esta
etapa. U10 conserva `allowed-domains.v1.yaml` y la función de comparación de F9, que U2 ejecuta sobre su
Corefile renderizado (NFR1.12).

## 4. Frontera de AUTONOMIA-04

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera | Control |
|---|---|---|---|
| `anonymizer-proxy` | Dentro, namespace `veridicus`, 1 réplica | Entra por C21 (HTTP interno): mensajes con testimonio en claro y el `run_id`. Sale: solo el cuerpo seudonimizado, la proyección del esquema y los parámetros del perfil, por 443, hacia `api.anthropic.com` en la primera rebanada | Verificación final del cuerpo, URL constante, lista de dominios, TLS fijo (security-design §3 y §6); `NetworkPolicy` y CoreDNS de U2 |
| `MaskTable` | Memoria del proceso del proxy o de la CLI | Nada | Vaciada en `finally`; sin escritura en disco (security-design §12) |
| Módulo en la CLI (AnalyzerCli) | **Fuera** del clúster: la máquina del humano | Sale lo mismo que en el proxy, directo desde la máquina | En la anfitriona no hay `NetworkPolicy` ni CoreDNS de U2: la única barrera es la del proceso (lista, URL constante, `trust_env=False`, verificación final). Las claves son variables de la máquina (IDS-U10-09) |
| CLI en ZINE | Fuera, clúster ZINE | Nada pasa por U10 | Solo perfiles locales (components); el humano lanza los `sbatch` |
| CoreDNS | Dentro, `kube-system` | Hacia fuera, consultas de los tres dominios de la lista y de `github.com`, desde cualquier pod | Lista blanca de U2; riesgo residual aceptado por U2 (P5 = A) |
| Destino externo | **Fuera** | Recibe marcas y la estructura del testimonio; devuelve texto con marcas | ADR de Anthropic (NFR1.2), con la reentrega de hasta 3 veces (NFRD-U10-14) |
| Demás pods de `veridicus` | Dentro | Nada hacia fuera | `NetworkPolicy` de U2; `veridicus-provider-keys` solo en el proxy |

## 5. Infraestructura compartida

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| `NetworkPolicy` del proxy, `default-deny` y `allow-dns` | U2 | U10 | El proxy es uno de los dos pods con `ipBlock` externo, solo 443 |
| CoreDNS y su `Corefile` | U2 | Todas; U10 aporta la lista y F9 | Cambia por PR que aplica el humano |
| `veridicus-models` y `deploy/models.lock` | U2 | Servidores de modelos y el proxy (entrada `ner`) | Solo lectura; `fetch-models.sh` en la anfitriona con `sha256` |
| `veridicus-profiles` | U2 (copia de `config/`) | `semantic-agent` y el proxy | Solo lectura; mismo SHA-256 que `config/profiles.yaml` |
| `veridicus-provider-keys` | U2 (lo crea el humano) | Solo el proxy | `secret-consumers.yaml` y Kyverno |
| `contracts/limits.v1.yaml` y `contracts/metrics/anonymizer.v1.yaml` | U1 | U10 | Cambian por PR de U1 |
| Prometheus, Grafana y el subchart de reglas (módulo 8) | U2 | U10 con su panel y sus reglas | Solo el puerto 9090; panel con el mismo SHA-256 (IDS-U10-08) |
| `libs/anonymizer` | U10 | U11 (CLI) y el proxy | import-linter: `semantic-agent` no lo importa (contrato de U4) |

## 6. Precisiones a artefactos ya aprobados (IDS-U10-xx)

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Todas salen de las fuentes aprobadas o de un hecho técnico, y
ninguna deja salir del clúster algo que hoy no sale.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| IDS-U10-01 | `nfr-requirements/tech-stack-decisions.md` (D2) y entrada `ner` de `deploy/models.lock` (U2) | **Modelo NER.** Criterios: NER en español con etiquetas de persona y lugar; pesos `model.safetensors` publicados por el autor en la revisión fijada (sin conversiones de terceros); `fetch-models.sh` descarga solo una lista cerrada de archivos (`config.json`, los del tokenizador y `model.safetensors`), así un `.bin` o un `.py` del repositorio nunca llega al volumen; licencia que permita el uso; RSS cargado ≤ 700 MiB (scalability-design §4). Candidato preferente: el RoBERTa base de la BNE afinado en CAPITEL-NER (PlanTL / BSC); alternativa: BETO afinado para NER. Se queda el primero que cumpla todos los criterios y pase la prueba de 0 fugas de nivel 1; su revisión y su `sha256` se fijan en B10. Si ninguno la pasa, se cambia de modelo o se añaden reglas, nunca se baja el umbral | D2 deja el modelo a esta etapa; `team.md` (artefactos de modelo) |
| IDS-U10-02 | Infrastructure Design de U2 (`requests`/`limits`) | Propuesta: CPU 1/2, memoria 1536 MiB/2 GiB. En B10, con `out/anonymizer-perf.json`, el límite pasa a `max(2 GiB, 1,2 × pico + 16 MiB)` | scalability-design §4; logical-components §5 |
| IDS-U10-03 | Infrastructure Design de U2 (subchart del proxy) | `terminationGracePeriodSeconds: 290` y `--timeout-graceful-shutdown 280`, en lugar de los 180 s de la revisión 1, porque el plazo por llamada es ahora 270 s | performance-design §1; reliability-design §2 |
| IDS-U10-04 | `nfr-design/scalability-design.md` §2 | El mamparo se aplica solo a `POST /v1/generate`. `/healthz` y `/readyz` responden sin cupo: con 4 llamadas en curso, una sonda que esperara cupo daría 503 y la `livenessProbe` reiniciaría el pod a mitad de una llamada. Prueba de nivel 0: con 4 peticiones en curso, `/healthz` y `/readyz` responden 200 | Kubernetes reinicia ante 3 fallos de la sonda de vida |
| IDS-U10-05 | `nfr-design/performance-design.md` §2 | `OMP_NUM_THREADS` y `MKL_NUM_THREADS` iguales a `VERIDICUS_ANONYMIZER_NER_THREADS`, y `TOKENIZERS_PARALLELISM=false`: `torch` y los tokenizadores cuentan los CPU de la máquina, no el `limit` del contenedor, y sin esto abrirían un hilo por núcleo de la anfitriona | Comportamiento de `torch` en contenedores |
| IDS-U10-06 | `platform/nfr-design/security-design.md` §6 (U2) | El proxy lee el Secret con `envFrom`, y el Secret lleva una clave por cada `api_key_ref` externa de `config/profiles.yaml`, con su nombre exacto. Como el proxy no arranca si falta una (F3a paso 3), `create-secrets.sh` termina con código ≠ 0 si el `.env` no trae alguna de esas claves, antes de escribir nada | functional-spec F3a; reliability-design §4 |
| IDS-U10-07 | `nfr-requirements/tech-stack-decisions.md` (NFR2.1) y `fetch-models.sh` (U2) | La prueba de 0 fugas con el NER real (nivel 1) corre en la CI: un paso previo provisiona solo la entrada `ner` de `models.lock` con `fetch-models.sh --only ner`, verifica su `sha256` y lo guarda en la caché de Actions por ese `sha256`. Las pruebas siguen bajo `pytest-socket`: ninguna prueba descarga nada | NFR2.1; `team.md` (descarga en aprovisionamiento) |
| IDS-U10-08 | `platform/nfr-design/security-design.md` §10 y §11 (U2) | `check-config-copy.sh` suma el panel: la copia del chart de U2 y `services/anonymizer-proxy/observability/grafana-dashboard.json` tienen el mismo SHA-256; control negativo con un byte distinto | NFRD-U10-09 |
| IDS-U10-09 | `functional-spec.md` (F3b) | En la máquina del humano, la CLI construye el módulo con `VERIDICUS_ANONYMIZER_NER_PATH` apuntando al mismo directorio que escribe `fetch-models.sh` y el mismo `sha256`; las claves vienen de variables de la máquina cargadas desde el `.env` no versionado. Ahí no hay `NetworkPolicy`: lo declara la tabla de §4 | components (tabla de fronteras); FR12.4 |
| IDS-U10-10 | `nfr-design/observability-design.md` §3 y §7 | La saturación (503 por falta de cupo) y el fallo cerrado comparten `error_code` `analysis.anonymizer_unavailable`; la alerta de saturación se calcula con `veridicus_anonymizer_inflight` y la de memoria con el límite que renderiza el chart, sin depender de `kube-state-metrics` | `monitoring-design.md` §2 |
| IDS-U10-11 | Revisión 1 de esta etapa (los cuatro artefactos) | Se retiran: el proxy apagado y el PR de habilitación (R-01 y R-05 de la revisión 1 ya no aplican), la `NetworkPolicy` por CIDR ≥ /24 (la sustituye `0.0.0.0/0` con `except`, P5 = A de U2), el `Corefile` y `check-coredns.sh` (U2), el `ConfigMap` de reglas, el Secret `veridicus-anonymizer-credential` (ahora `veridicus-provider-keys`), el puerto 8081, la ruta `embed`, `AnonymizerGateway` y `anonymizer_route.py` (U11), las métricas por `operation` y las cabeceras `X-Veridicus-*`, y la tabla de precisiones de §6 de la revisión 1 | Cambio 01; NFRD-U10-16; NFR Design de U2 |
| IDS-U10-12 | `team.md` (`## Deployment`, dos máquinas) | Con el supuesto del brief (una máquina de 64 GB sin GPU), U10 no tiene *values* por máquina: el proxy es igual en todos los *values* que U2 mantenga, y ninguno pide `nvidia.com/gpu` | Cambio de máquinas del 2026-11-22 (lo pregunta U2) |
