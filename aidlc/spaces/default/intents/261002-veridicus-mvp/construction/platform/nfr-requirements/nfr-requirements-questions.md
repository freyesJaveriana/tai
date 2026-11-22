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

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) se escribió sobre el marco documental: `pgvector`,
servidor de *embeddings*, rol `veridicus_judge_ro` (C9), regla AIR que proponía umbral y un
`anonymizer-proxy` COULD. Desde entonces el cambio 01 (DT27), la adenda 02 y las revisiones 3 de Inception
cambiaron lo que U2 empaqueta:
- FR12.1 sin `pgvector`, C9 «Retirado» y US10.6 «Retirada»;
- `anonymizer-proxy` MUST como único pod con salida (FR12.3, US11.6, C21, C22);
- AC11.6.4: el Secret de las claves solo en `anonymizer-proxy` (CD-04);
- servidores locales del juez y del verificador, con Whisper y TTS (C14);
- el `Job` de retención de U13 y el usuario `veridicus_retention` (A-2, VE-12);
- y lo que piden a U2 los Functional Design de U4, U9, U10 y U13.

**Regla para preguntar** (`project.md`, decisión del humano del 2026-11-22). Solo pregunto cuando dos fuentes
aprobadas se contradicen o cuando la decisión cambia alcance, riesgo o un dato que sale del clúster. Lo
demás lo aplico siguiendo las fuentes y lo anoto en la tabla de precisiones NFR-U2-xx, que revisas en la
aprobación. Queda **una pregunta**, P5: es una contradicción entre fuentes aprobadas y decide una salida
del clúster.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| Respuestas de la revisión 1 | P1–P4 siguen: `llama-server` y `faster-whisper` compatibles con OpenAI, chart paraguas con valores por máquina, Redis propio con AOF y negar por defecto entrada y salida | Revisión 1, P1–P4 |
| Retirado por el cambio 01 | `pgvector`, servidor de *embeddings*, rol `veridicus_judge_ro` y la propuesta de umbral de la regla AIR | FR12.1, AC9.4.1, C9, US10.6 |
| Salida a internet | Negada a todos los pods salvo `anonymizer-proxy`, que sale solo por 443 y DNS; la lista de dominios la impone el módulo, junto con la lista blanca de CoreDNS | FR12.3, US9.1, US11.5, US11.6, C22, `team.md` (Deployment) |
| Claves de los proveedores | Un Secret que crea el humano, referenciado solo por `anonymizer-proxy`, con política sobre `helm template` y su control negativo | AC11.6.4, CD-04, B4 (punto 4) |
| Servidores locales | Juez y verificador locales, Whisper y TTS (SHOULD), con artefactos fijados por `sha256`; sale `/v1/embeddings` | C14, unit-of-work (U2) |
| Modelos concretos | Los fija U11 en su NFR Requirements (perfiles `comercial-piloto` y `todo-local`); U2 los empaqueta | C18 (pregunta abierta), requirements §7 |
| TTS | Piper con voz `es_*` | U9, D3 de su NFR |
| Distribución, CNI, CoreDNS concreto, valores de `requests`/`limits` | Los fija Infrastructure Design | requirements §7, unit-of-work (U2) |
| NFR de Inception | NFR1–NFR15. NFR9 está «Retirado» | requirements §3 |

## Cómo se registra la revisión 2

- `security-requirements.md`, `tech-stack-decisions.md` y `traceability.json` pasan a la revisión 2 en el
  mismo archivo, con una nota de cabecera que dice qué cambia y por qué.
- Los requisitos conservan su ID; cada fila dice si **se mantiene**, **cambia**, es **nuevo** o queda
  **Retirado** (sin renumerar). Lo nuevo toma el número siguiente de su grupo (NFR1.4, NFR10.11 en
  adelante, NFR11.2, NFR12.2). Las decisiones D1–D11 conservan su número; las nuevas empiezan en D12.
- `traceability.json` declara NFR9 como `N/A` («Retirado», cambio 01) y deja NFR8 con la parte de U2
  (NFR8.1) y la medición del 98 % nombrada en Build and Test (R-04 de la revisión 1).
- Las precisiones a artefactos aprobados van en la tabla NFR-U2-xx de `security-requirements.md`. Ningún
  original se edita.
- U2 es de tipo `packaging`: como en la revisión 1, solo produce seguridad, pila y trazabilidad.

## Lo que el diseño resolverá sin preguntar

Cada punto sale de una fuente aprobada. Entra a los artefactos con su NFR-U2-xx.

1. **Red sin la base para el trabajador.** `semantic-agent` ya no alcanza PostgreSQL: sale el rol de solo
   lectura (C9) y la cancelación le llega por la clave de Redis (CD-06). Alcanza Redis, el juez y el
   verificador locales, y `anonymizer-proxy` (C21).
2. **`anonymizer-proxy`.** Entrada solo desde `semantic-agent` (C21). Salida a `0.0.0.0/0` por TCP 443,
   excepto los rangos privados y los del clúster, más DNS a `kube-dns`. Una `NetworkPolicy` no filtra por
   dominio: el módulo impone la lista y no sigue redirecciones (FD-U10-05, FD-U10-06). U2 ejecuta la función
   de comparación de U10 sobre su Corefile renderizado (F9 de U10, AC11.5.2). Queda como riesgo residual
   una conexión a una IP literal por 443, que el módulo no permite.
3. **Servidores de modelos.** Un `Deployment` por modelo local que nombra `config/profiles.yaml` (juez y
   verificador, de familias distintas en los perfiles de evaluación, FR14.4), más `model-whisper` y
   `model-tts` (SHOULD). Entrada solo desde `semantic-agent` (juez y verificador) y desde `audio-worker`
   (Whisper y TTS). `--api-key` desde un Secret.
4. **Perfiles y precios montados del mismo commit (C21).** Helm no lee fuera del chart (precedente de
   `project.md` con el *prompt*). Un solo `ConfigMap` con la copia del chart de `config/profiles.yaml` y
   `config/prices.yaml`, montado en solo lectura en `session-api`, `semantic-agent` y `anonymizer-proxy`. Una
   comprobación de nivel 0 exige el mismo SHA-256 que los originales de `config/`.
5. **Usuarios de base de datos.** `veridicus_owner` (solo el `Job` de migraciones), `veridicus_app`
   (`session-api` y `create-admin`) y `veridicus_retention` (solo el `Job` de retención, el único con
   `DELETE`; A-2, NFR11). Cada uno con su Secret, referenciado solo por su consumidor y comprobado en la
   política.
6. **`Job` de retención (U13, BR5.1, §11 pregunta 4).** Es un manifiesto revisable, nunca un `CronJob`, con
   `backoffLimit: 0` y `activeDeadlineSeconds`. Monta los volúmenes de reportes y de audio de `session-api` y
   sale solo a PostgreSQL y a Redis (`request_cancellation` escribe la clave de CD-06). Como el sistema no lo
   programa (VE-12), los `Job` de retención y de `create-admin` van en un chart aparte que Argo CD no
   sincroniza y que aplica el humano (F7 de U13, F7 de U3). La comprobación AUTONOMIA-01 falla ante un
   `CronJob` (E49 de U13). Las migraciones siguen como `Job` en su propio PR (`team.md`).
7. **Rutas internas nuevas.** `session-api` → `audio-worker` por la ruta interna de síntesis (D4 de U9), con
   el token `VERIDICUS_SPEECH_TOKEN` por Secret. El operador de CloudNativePG → pods de la base, y pods de la
   base → API server (R-01 de la revisión 1). Una comprobación de nivel 0 cruza cada dependencia declarada
   con su regla.
8. **Sin internet en los demás namespaces que instala U2.** FR12.3 dice «todos los pods», así que la regla
   también aplica a `ingress-nginx` (termina TLS y ve testimonio), `cnpg-system`, `monitoring` y `keda`.
   Solo se permite tráfico interno y al API server. Grafana va sin comprobación de versiones ni descarga de
   *plugins*. La excepción de Argo CD es P5.
9. **TLS en el *ingress*.** La cookie `Secure` (C1, P5) y la grabación de voz (contexto seguro del
   navegador) lo exigen. Certificado local en un Secret que crea el humano y redirección a HTTPS. Cierra R-06
   de la revisión 1.
10. **Hallazgos R-02, R-03, R-04, R-05 y R-07 de la revisión 1.**
    - Modelos en un PV estático de solo lectura más su PVC, y una política que rechaza `hostPath` en el
      render (R-02).
    - Digest obligatorio en las imágenes propias. En las de terceros, versión exacta y digest cuando se
      pueda; las excepciones se registran con motivo y caducidad (R-03, `team.md`).
    - NFR8: U2 aporta los `limits`, y el 98 % lo mide Build and Test (R-04).
    - El TTS entra en la estructura de `deploy/` y en la red (R-05).
    - La persistencia AOF se mide. NFR12.1 tiene comando. NFR10.5 se busca con expresiones regulares e
      incluye todos los verbos de escritura (R-07).
11. **AUTONOMIA-01 también para ZINE.** La comprobación estática suma `sbatch`, `ssh`, `scp` y `rsync` hacia
    ZINE en *workflows* y *scripts* de la CI (AC9.5.2).
12. **Regla de descartes (US10.8).** Alerta por encima de 0,25 sobre las últimas *W* decisiones. *W* es
    `dismissal_window_w` de C25, que fija U5, dueña de la métrica (CD-07). `promtool` usa los *fixtures*
    5 de 20 (no alerta) y 6 de 20 (alerta), y la regla nunca cambia la configuración (AC10.8.2).
13. **Salud y humo (C16).** Sondas `/healthz` y `/readyz` en los cuatro servicios, incluido
    `anonymizer-proxy`. `scripts/smoke.sh` comprueba cada uno. El *N* de segundos lo fijan U4 y U11.
14. **Canario en los logs (AC9.1.4).** Es una prueba de nivel 1 sobre los logs capturados de todos los
    servicios, en el entorno de integración.

Ninguno de estos puntos hace que salga del clúster un dato que hoy no sale.

## P5 — Argo CD frente a «ningún pod sale salvo el anonimizador»

Hay fuentes aprobadas que se contradicen:
- **FR12.3**, **AC9.1.1** y el punto 3 de B4 niegan la salida a internet a **todos los pods** salvo
  `anonymizer-proxy`.
- **AC11.5.2** exige que la lista blanca de CoreDNS **coincida** con los tres dominios de proveedores del
  anonimizador.
- **FR12.6** y **US10.7** (SHOULD, módulo 8), junto con `team.md` («Argo CD sincroniza automáticamente con
  una *deploy key* de solo lectura»), piden que Argo CD lea el repositorio en GitHub. Para eso
  `argocd-repo-server` necesita resolver `github.com` y salir por 22 o 443.

La revisión 1 de Infrastructure Design dejaba Argo CD fuera de la política, pero es anterior al cambio 01
y a la redacción actual de FR12.3. Argo CD no maneja testimonio: lee el repositorio público. Aun así, es
una segunda salida del clúster, y decidirla cambia el alcance de B4 en su parte SHOULD.

A. **Excepción declarada solo para Argo CD.** La regla de AC9.1.1 sigue aplicando a todos los pods, con
   una sola excepción más: `argocd-repo-server`, que sale solo a `github.com` por 22 y 443 con su propia
   `NetworkPolicy`. La política de entrada de `veridicus` no admite nada desde `argocd`. La lista blanca de
   CoreDNS queda con los tres dominios de C22 más `github.com`. AC11.5.2 se comprueba así: los dominios de
   proveedores son exactamente los del anonimizador, y el resto de la lista blanca es una lista cerrada de
   dominios de infraestructura (hoy solo `github.com`), cada uno con su motivo. Esto precisa FR12.3 y
   AC11.5.2. **(Recomendada:** conserva el módulo 8 sin abrir ningún camino a los datos, y el anonimizador
   sigue rechazando `github.com` porque no está en su lista).
B. **Sin Argo CD en el MVP.** US10.7 queda fuera. El humano aplica siempre a mano lo fusionado, como antes
   del módulo 8. FR12.3 y AC11.5.2 se cumplen al pie de la letra. Esto precisa FR12.6, `team.md`
   (Deployment) y la parte SHOULD de B4.
C. **Argo CD con un espejo Git dentro del clúster.** Un `git-daemon` en `argocd` que el humano actualiza
   con `git push` desde la anfitriona tras cada fusión. FR12.3 y AC11.5.2 se cumplen al pie de la letra, a
   costa de una pieza más y de un paso manual que se parece a aplicar a mano.
D. **Argo CD fuera de la política sin tocar CoreDNS.** `argocd-repo-server` resuelve `github.com` con
   `hostAliases` y sale a los rangos de IP que publica GitHub. AC11.5.2 se mantiene exacta, pero las IP de
   GitHub cambian sin aviso y la sincronización se rompería sin que nada lo detecte en nivel 0.
X. Other (please specify)

[Answer]: A **Mode:** guided
