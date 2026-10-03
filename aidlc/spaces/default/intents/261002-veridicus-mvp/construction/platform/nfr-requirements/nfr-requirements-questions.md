# Preguntas de NFR Requirements — U2 platform

**Unidad.** U2 `platform` (tipo `packaging`): charts y manifiestos de `deploy/` para CloudNativePG con
`pgvector`, Redis, servidores locales de modelos, `NetworkPolicy`, `requests`/`limits`, Secrets por
referencia, `Job` de migraciones, políticas de manifiestos y `scripts/smoke.sh`
(`inception/units-generation/unit-of-work.md`; sin Functional Design propio).

**Lo que ya está decidido y no se vuelve a preguntar.** Imágenes en GHCR privado por SHA, base mínima
por digest, sin root, Trivy bloqueante; `helm template` → `kubeconform` → Kyverno CLI sin red; Secrets
solo por referencia; migraciones como `Job` aparte; artefactos de modelo fijados por `sha256`, en GGUF
o `safetensors`, sin `trust_remote_code`; la CI no despliega; Argo CD con *prune* desactivado sobre la
base (team.md). La distribución de Kubernetes, el CNI y los namespaces los fija Infrastructure Design;
el modelo concreto del juez y de *embeddings* y el umbral se fijan con U4.

---

## P1 — Software de los servidores de modelos

C14 exige servidores internos con la API compatible con OpenAI: `/v1/chat/completions` con
`response_format` de esquema JSON y `seed`, `/v1/embeddings` y (SHOULD) `/v1/audio/transcriptions`,
todos en CPU.

A. `llama.cpp` (`llama-server`, imagen fijada por digest) para el juez y los *embeddings* con modelos
   GGUF, y `faster-whisper` detrás de un servidor compatible con OpenAI para Whisper. (Recomendada)
B. Ollama para el juez y los *embeddings*.
C. vLLM en su versión para CPU.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Forma del empaquetado en `deploy/`

Los mismos artefactos se aplican en la máquina de desarrollo (CPU) y en la máquina GPU opcional, y las
políticas se validan con `helm template`.

A. Un chart paraguas `deploy/veridicus` con un subchart por componente y un archivo de valores por
   máquina (`values-cpu.yaml`, `values-gpu.yaml`); los operadores de terceros (CloudNativePG, Argo CD,
   Prometheus) con su chart oficial y versión fijada. (Recomendada)
B. Kustomize con una base y un *overlay* por máquina.
C. Manifiestos planos, uno por recurso.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Cómo se despliega Redis

Redis guarda las colas C2–C5 (Redis Streams). Si pierde datos al reiniciar, se pierden turnos en cola;
el contrato ya cubre la reentrega de pendientes, pero no la pérdida del *stream*.

A. Manifiesto propio: un `StatefulSet` de una réplica con la imagen oficial de Redis fijada por digest,
   persistencia AOF con `fsync` cada segundo en un PVC y contraseña desde un Secret. (Recomendada)
B. Un chart de terceros (por ejemplo Bitnami) con versión fijada.
C. Redis sin persistencia: tras un reinicio, InterviewSession marca en error los turnos en curso.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Alcance de la `NetworkPolicy` (AUTONOMIA-04)

AUTONOMIA-04 exige al menos una política que niegue la salida a internet a los pods con datos sin
anonimizar. Se puede limitar a esos pods o aplicar a todo el namespace.

A. Negar por defecto la entrada y la salida en el namespace de Veridicus y abrir solo lo necesario
   (DNS del clúster y cada dependencia interna declarada); ningún pod sale a internet, y solo el
   `anonymizer-proxy` (si se construye) tiene una salida explícita hacia su destino externo. (Recomendada)
B. Negar solo la salida a internet de los pods marcados con datos sin anonimizar; el resto sin
   restricción.
C. Lo de A más políticas de entrada por puerto entre cada par de servicios.
X. Other (please specify)

[Answer]: A **Mode:** guided
