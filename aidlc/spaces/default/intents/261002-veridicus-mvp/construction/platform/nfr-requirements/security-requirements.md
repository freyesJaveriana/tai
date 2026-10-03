# Requisitos de seguridad — U2 platform

**Insumos.** Definición de U2 en `inception/units-generation/unit-of-work.md`; FR12, NFR1, NFR2,
NFR8, NFR10–NFR12 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements); tabla
«Datos sensibles por contrato», C9, C14, C15 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary); respuestas P1–P4 de `nfr-requirements-questions.md`; prácticas `## Deployment` y
`## Forbidden` de `team.md` y `project.md`. U2 no tuvo Functional Design (tipo `packaging`).

Cada requisito hereda el ID del NFR de Inception que detalla. Todas las comprobaciones automáticas son
de **nivel 0**, sin red ni clúster: `helm template` → `kubeconform` → Kyverno CLI (políticas en
`deploy/policies/`), cada política con su **control negativo** (un manifiesto que debe fallar). Ningún
paso aplica cambios al clúster (AUTONOMIA-01).

## 1. Frontera (AUTONOMIA-04)

| Componente | Dentro o fuera del clúster | Datos sin anonimizar |
|---|---|---|
| `session-api`, `semantic-agent`, `audio-worker`, `frontend` | Dentro, namespace `veridicus` | Sí: testimonio, CoT, audio (C1–C3, C5) |
| PostgreSQL (CloudNativePG) y Redis | Dentro | Sí |
| Servidores de modelos (juez, *embeddings*, Whisper, TTS) | Dentro | Sí (reciben el texto) |
| `anonymizer-proxy` (COULD) | Dentro; única salida hacia un destino externo declarado | Solo datos ya enmascarados salen |
| Archivos de modelo | Se descargan **en la máquina anfitriona** con un script revisable, fuera de los pods | No |
| CI y GHCR | Fuera | No: solo código e imágenes |

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Un pod con testimonio envía datos a internet | Information disclosure | Alto | NFR1.1 |
| T2 | Un archivo de modelo alterado o un modelo descargado en ejecución | Tampering | Alto | NFR1.2, NFR10.4 |
| T3 | Una imagen sin fijar cambia entre la CI y el clúster | Tampering | Medio | NFR10.1 |
| T4 | Un contenedor con root o con privilegios escapa al nodo | Elevation of privilege | Medio | NFR10.2 |
| T5 | Un Secret con su valor en el repositorio | Information disclosure | Alto | NFR10.3 |
| T6 | Un *script* o *workflow* aplica cambios al clúster sin PR | Tampering | Alto | NFR10.5 |
| T7 | Un pod sin límites agota la máquina | Denial of service | Medio | NFR8.1 |
| T8 | Acceso a Redis, PostgreSQL o a un servidor de modelos desde un pod que no lo necesita | Spoofing, Information disclosure | Medio | NFR1.1, NFR10.6, NFR10.7 |
| T9 | Argo CD borra la base o sus volúmenes | Tampering, Repudiation | Alto | NFR11.1 |
| T10 | Una vulnerabilidad conocida en una imagen | Elevation of privilege | Medio | NFR10.1 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | Entrada y salida negadas por defecto en el namespace (P4 = A). | Una `NetworkPolicy` `veridicus-default-deny` con `podSelector: {}` y `policyTypes: [Ingress, Egress]`; las demás solo abren DNS del clúster (53 UDP/TCP hacia `kube-dns`) y las dependencias internas de la tabla de `tech-stack-decisions.md` §3. Ninguna regla de salida usa `ipBlock` hacia fuera del clúster, salvo la del `anonymizer-proxy` (si se construye) hacia su destino declarado. Política Kyverno con control negativo (una regla con `0.0.0.0/0`). Antes de la sustentación, verificación manual: desde cada pod, una petición a `https://example.com` falla. | Nivel 0 y manual |
| NFR1.2 | Ningún pod descarga modelos. | Los archivos de modelo los descarga `scripts/fetch-models.sh` en la máquina anfitriona, que verifica el `sha256` de cada uno contra `deploy/models.lock`; los pods los montan en un volumen de **solo lectura**. Ningún contenedor tiene un comando `curl`, `wget`, `huggingface-cli` ni equivalente (comprobación estática con control negativo). | Nivel 0 |
| NFR1.3 | Los destinos de los modelos son internos. | Las URL de `VERIDICUS_JUDGE_URL`, `VERIDICUS_EMBEDDINGS_URL` y `VERIDICUS_WHISPER_URL` en los valores del chart terminan en `.svc.cluster.local` (C14, ADR-005). | Nivel 0 |

### NFR10 — Seguridad de la plataforma

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | Toda imagen está fijada y escaneada. | Toda imagen del manifiesto renderizado lleva `@sha256:`; ninguna usa `latest`; Trivy sin vulnerabilidades `HIGH` o `CRITICAL` con corrección en las imágenes propias; los charts de terceros con versión exacta. | Nivel 0 (Kyverno) y CI (Trivy) |
| NFR10.2 | Todo pod cumple el perfil `restricted` de Pod Security. | El namespace lleva `pod-security.kubernetes.io/enforce: restricted`; cada contenedor declara `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault` y `readOnlyRootFilesystem: true` (con `emptyDir` donde haga falta escribir). | Nivel 0 |
| NFR10.3 | Los manifiestos solo referencian Secrets. | 0 objetos `kind: Secret` con `data` o `stringData` en `deploy/`; los valores sensibles llegan por `secretKeyRef` o `envFrom`; `gitleaks` sin hallazgos. El humano crea los Secrets desde su `.env` con `scripts/create-secrets.sh` (revisable, sin valores). | Nivel 0 y CI |
| NFR10.4 | Los archivos de modelo se verifican también al arrancar. | Un `initContainer` de cada servidor de modelos calcula el `sha256` del archivo montado y termina con error si no coincide con el de `models.lock`; el servidor no arranca. Control negativo con un archivo alterado en una prueba de nivel 1 de U2 (contenedor local). | Nivel 0 (presencia) y nivel 1 |
| NFR10.5 | Nada aplica cambios al clúster sin PR (AUTONOMIA-01). | Comprobación estática sobre `.github/`, `scripts/` y `deploy/`: 0 apariciones de `kubectl apply`, `kubectl create`, `helm install`, `helm upgrade`, `terraform apply` ni migraciones contra el clúster; control negativo con un *workflow* que las contiene. La CI no tiene `kubeconfig`. | Nivel 0 |
| NFR10.6 | Redis exige contraseña y solo lo alcanzan sus clientes. | `requirepass` desde un Secret; `protected-mode yes`; la `NetworkPolicy` de entrada a Redis solo admite `session-api`, `semantic-agent` y `audio-worker`. | Nivel 0 |
| NFR10.7 | PostgreSQL sin superusuario expuesto y con roles separados. | `enableSuperuserAccess: false` en el `Cluster` de CloudNativePG; TLS entre clientes y base (por defecto en CloudNativePG); el rol de la aplicación y el de solo lectura del evaluador (`veridicus_judge_ro`, C9) son distintos; solo `session-api`, `semantic-agent` y el `Job` de migraciones alcanzan el puerto 5432. | Nivel 0 |
| NFR10.8 | Los servidores de modelos solo atienden a sus clientes. | Su `NetworkPolicy` de entrada solo admite `semantic-agent`, `session-api` (*embeddings* de la indexación) y `audio-worker` (Whisper, TTS); `llama-server` exige `--api-key` leída de un Secret. | Nivel 0 |
| NFR10.9 | Los pods no reciben credenciales de Kubernetes. | `automountServiceAccountToken: false` en todo pod de la aplicación; ningún `Role` ni `ClusterRole` para ellos. | Nivel 0 |
| NFR10.10 | Las migraciones solo corren como `Job` aparte. | Ningún `Deployment` ni `initContainer` ejecuta Alembic; el `Job` de migraciones está en su propio archivo del chart (prohibición de `project.md`). | Nivel 0 |

### NFR11 — Integridad

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | La sincronización nunca borra la base ni sus volúmenes. | La `Application` de Argo CD (SHOULD) desactiva *prune* para el `Cluster` de CloudNativePG, sus PVC y el PVC de Redis (anotación `argocd.argoproj.io/sync-options: Prune=false`), y usa una *deploy key* de solo lectura. | Nivel 0 |

### NFR8 — Recursos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.1 | Todo contenedor declara `requests` y `limits` (FR12.2). | 100 % de los contenedores e `initContainers` con `requests` y `limits` de CPU y memoria; control negativo. Los valores concretos por máquina los fija Infrastructure Design. | Nivel 0 |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | `deploy/` no contiene datos. | Ni valores, ni *seeds* ni `ConfigMap` con testimonios, nombres o expedientes; el Golden Dataset vive en `evaluation/` con las reglas de U1. | Revisión del PR y `gitleaks` |

### NFR2 — CPU primero

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR2.1 | El chart corre completo sin GPU. | `values-cpu.yaml` es el valor por defecto y no pide `nvidia.com/gpu`; solo `values-gpu.yaml` lo pide. `helm template` con cada archivo de valores pasa las mismas políticas. | Nivel 0 |

### NFR15 — Observabilidad (SHOULD)

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR15.1 | La regla AIR solo propone. | La `PrometheusRule` dispara cuando `veridicus_session_dismissal_ratio > 0.25` (C15, FR9.3) con una anotación que propone un umbral; 0 acciones que cambien la configuración. Su prueba con `promtool test rules` incluye un caso por debajo y otro por encima. | Nivel 0 |

## 4. Correspondencia con AUTONOMIA-01..05

| Regla | Qué aporta U2 | Requisitos |
|---|---|---|
| AUTONOMIA-01 | Todo cambio al clúster es un artefacto revisado; nada lo aplica solo | NFR10.5, NFR10.10 |
| AUTONOMIA-02 | Cada requisito tiene su comprobación con control negativo | Todas |
| AUTONOMIA-04 | Salida negada por defecto, modelos locales y verificados | NFR1.1–NFR1.3, NFR10.4 |

## 5. Precisiones a artefactos ya aprobados

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `units-generation/unit-of-work.md` (U2) | Añade `scripts/fetch-models.sh`, `deploy/models.lock` y `scripts/create-secrets.sh` a lo que entrega U2. | NFR1.2, NFR10.3 |
