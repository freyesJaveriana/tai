**Collaborator:** aidlc-developer-agent

## Contribution

> Revisión ciega de apoyo (Paso 3) desde la perspectiva de desarrollo: nombres, fronteras de
> capas por servicio, manejo de errores en fronteras de integración, organización del
> repositorio y estilo de código. Proyecto *greenfield*: todo lo que sigue es **propuesta**
> derivada de `specs/prd.md` (Seg. 6, 8, 9, 11, 13), `docs/limite-autonomia.md`, la raíz del
> repo (commit `e0311bc`) y el borrador del líder. Nada está afirmado por el humano. Las
> preguntas nuevas se numeran P14–P18 para que el líder las integre; las que refinan preguntas
> del líder conservan su ID.

### 1. Organización del repositorio (monorepo en la raíz, nunca bajo `aidlc/`)

Observado: la raíz ya contiene `aidlc/`, `docker/` (contenedor de trabajo `tai-aidlc`, **no** la
imagen de la aplicación), `docs/`, `specs/`, `presentations/`, `research/`, `pvb.md`,
`plan-aidlc.md`. No hay código, `pyproject.toml`, `package.json` ni CI.

Propuesta de árbol (código en la raíz, un directorio por módulo del PRD Seg. 9):

```text
frontend/                      # Módulo A — React + TypeScript (Vite)
services/
  session-api/                 # Módulo B — FastAPI: orquestador, auth, máquina de estados
  audio-worker/                # Módulo C — Whisper/TTS en CPU (SHOULD), consume de Redis
  semantic-agent/              # Módulo D — RAG + LLM-as-a-judge, consume de Redis
  anonymizer-proxy/            # COULD — solo si se construye
libs/
  veridicus-contracts/         # paquete Python compartido: mensajes de cola, esquema de salida del LLM, errores base
contracts/
  openapi/                     # OpenAPI exportado de session-api (fuente de los tipos del frontend)
  schemas/                     # JSON Schema de mensajes de cola y de la salida del LLM
db/
  migrations/                  # migraciones de esquema (un solo dueño, ver §4 y P17)
deploy/
  charts/veridicus/            # Helm chart (o manifiestos) con requests/limits, NetworkPolicy, Secrets referenciados
  cluster/                     # recursos de plataforma: Cluster de CloudNativePG, namespaces
  argocd/                      # Application de Argo CD (SHOULD)
evaluation/
  golden-dataset/              # 10 transcripciones + 1 Hecho No Documentado (sintéticas)
  harness/                     # suite de evaluación offline, permutación, red-teaming
```

Criterios:

- **Cada servicio es autocontenido**: su `pyproject.toml`, su lockfile, su `Dockerfile`, sus
  pruebas (`services/<svc>/tests/`). Las imágenes de la aplicación **nunca** van en `docker/`,
  que ya es el contenedor de trabajo; mezclarlo rompería su `.gitignore` y su configurador.
- **Un solo paquete compartido** (`libs/veridicus-contracts`) para lo que cruza la cola
  (mensajes versionados con `schema_version`) y para el esquema de salida del LLM. Así se evita
  copiar modelos Pydantic entre servicios. Fuera de ese paquete, ningún servicio importa código
  de otro.
- **Configuración de estilo compartida en la raíz**: `ruff.toml` (heredado por cada servicio),
  `.editorconfig`, `.yamllint`; la configuración de ESLint/Prettier/TS vive en `frontend/`.
- Gestor de dependencias Python: **uv** con un lockfile por servicio; frontend: **npm** (Node 22
  ya está en el contenedor; el `.gitignore` ya ignora `node_modules`, `dist`).
- `docs/` y `specs/` siguen siendo documentación; nada de código en ellas.

### 2. Nombres e idioma de los identificadores (refina P12)

**Recomendación: identificadores en inglés y texto visible en español, con un glosario
único de dominio.**

Razones: las bibliotecas (FastAPI, Pydantic, SQLAlchemy, React), los *linters* (regla `N` de
Ruff), los mensajes de error del ecosistema y los modelos de código trabajan en inglés; mezclar
`crear_sesion()` con `session.commit()` vuelve el código bilingüe en cada línea. El costo es la
traducción de términos del PRD. Se resuelve con un glosario versionado (p. ej.
`docs/glosario-dominio.md`, o la sección de lenguaje ubicuo de Domain Design) que fije **una**
traducción por término:

| Término del PRD | Identificador |
|---|---|
| compareciente | `deponent` |
| analista / admin (roles) | `analyst` / `admin` (ver nota) |
| escenario de control / marco de verdad documental | `control_scenario` / `reference_corpus` |
| testimonio, turno | `testimony`, `turn` |
| alerta de incongruencia | `incongruence_alert` |
| sugerencia de revisión (AUTONOMIA-03) | `review_suggestion` |
| estados pendiente / aceptada / editada / descartada | `pending` / `accepted` / `edited` / `discarded` |
| Hecho No Documentado | `undocumented_fact` |
| Paquete de Contexto de Traspaso | `handoff_context_package` |
| cadena de pensamiento (CoT) | `reasoning_trace` |
| consolidar reporte | `consolidate_report` |
| sesión suspendida | `SessionStatus.SUSPENDED` |

Nota sobre los roles: el PRD escribe los roles como literales `analista` y `admin`. Si el humano
quiere que el valor persistido sea exactamente el del PRD, se puede guardar `analista` como
valor del enum y usar `ANALYST` como nombre del miembro. Hay que decidirlo una vez y anotarlo en
el glosario.

**Regla de nombres derivada de AUTONOMIA-03 (candidata, P18):** ningún identificador, campo,
columna, clave JSON, métrica ni texto de la interfaz codifica un veredicto de veracidad sobre el
compareciente (`is_lie`, `is_liar`, `truth_score`, `veracity`, `deception_probability`,
`mentiroso`, `falso`). El vocabulario permitido es «incongruencia» o «sugerencia de revisión».
Es barato de comprobar con una prueba o un `grep` en CI y complementa la prueba que ya exige
AUTONOMIA-03 sobre la salida de la IA. Como la interfaz está en español, la lista de términos
prohibidos de esa prueba debe incluir ambos idiomas.

Convenciones idiomáticas (de acuerdo con el borrador, con detalle):

- Python: `snake_case` para funciones y variables, `PascalCase` para clases,
  `UPPER_SNAKE_CASE` para constantes; módulos en `snake_case`.
- TypeScript: `camelCase`, `PascalCase` para componentes y tipos; un componente por archivo,
  `PascalCase.tsx`.
- REST: `/api/v1/<recurso-en-plural-kebab-case>`, p. ej. `/api/v1/sessions/{session_id}/turns`,
  `POST /api/v1/reports/{report_id}/consolidate` para la acción explícita del analista.
- **Claves JSON en `snake_case` de punta a punta** (P15): evita una capa de alias en Pydantic y
  en los tipos generados del frontend. La alternativa, `camelCase` en el cable con
  `alias_generator`, es legítima pero agrega una fuente de errores sin beneficio para un solo
  autor.
- PostgreSQL: tablas y columnas en `snake_case` y en plural (`incongruence_alerts`), `id` UUID,
  `created_at`/`updated_at` como `timestamptz`, estados como `text` con `CHECK` (o enum de
  Postgres). Los campos de auditoría de AUTONOMIA-03 se llaman igual en todas las tablas:
  `changed_by`, `changed_at`, `consolidated_by`, `consolidated_at`.
- Kubernetes: `kebab-case` con prefijo `veridicus-` y etiquetas `app.kubernetes.io/name`,
  `app.kubernetes.io/component`, `app.kubernetes.io/part-of: veridicus`.
- Variables de entorno: `VERIDICUS_<AJUSTE>` en mayúsculas (p. ej.
  `VERIDICUS_SIMILARITY_THRESHOLD`); los nombres de los Secrets son `kebab-case`.
- Ramas: `<tipo>/<slug-del-bolt>` (`feat/session-api-text-flow`); el alcance de los
  Conventional Commits es el nombre del directorio del servicio (`feat(session-api): …`).

### 3. Fronteras de capas por servicio

Para los servicios FastAPI y los *workers* proponemos cuatro capas con dependencias en un solo
sentido:

```text
api/  (o worker/)  →  application/  →  domain/
                           ↓
                       adapters/   (implementa los puertos que declara application/)
```

| Capa | Contiene | No puede |
|---|---|---|
| `api/` | Routers FastAPI, esquemas Pydantic de petición/respuesta, dependencias (auth, sesión de BD), manejador único de excepciones | Contener reglas de negocio ni consultas SQL |
| `worker/` | Consumidor de la cola: deserializa el mensaje versionado y llama a un caso de uso | Lo mismo que `api/` |
| `application/` | Casos de uso (`submit_testimony`, `evaluate_turn`, `change_alert_status`, `consolidate_report`), transacciones, puertos (interfaces) | Importar FastAPI, SQLAlchemy, Redis ni el cliente del LLM |
| `domain/` | Entidades, máquina de estados de sesión y alerta, invariantes puras: campos obligatorios de una alerta (AUTONOMIA-05), transiciones válidas de estado y quién las ejecuta (AUTONOMIA-03), decisión de umbral → `undocumented_fact` | Importar nada de infraestructura; hacer E/S |
| `adapters/` | Repositorios (SQLAlchemy + `pgvector`), cola Redis, cliente LLM (Ollama/llama.cpp), Whisper, embeddings, cliente del proxy de anonimización | Decidir reglas de negocio |

Por qué importa en este proyecto: las invariantes de AUTONOMIA-03/05 quedan en `domain/` como
código puro, comprobable con pruebas unitarias sin BD ni LLM, y las pruebas obligatorias de
`team.md` se vuelven baratas y deterministas. Se hace cumplir en CI con **import-linter**
(contratos de capas por servicio), no solo con revisión.

Frontend: `src/features/<funcionalidad>/` (componentes, *hooks*, estado) y un único cliente HTTP
en `src/api/`, con tipos generados del OpenAPI de `contracts/openapi/`. Los componentes nunca
llaman a `fetch` directamente.

### 4. Manejo de errores en fronteras de integración

Proponemos estas convenciones (P15). Cumplen la guía de la fase Construction («errores en
fronteras de integración», «nunca silenciosos», «recuperable frente a fatal»):

1. **Jerarquía única de excepciones** en `libs/veridicus-contracts`: `VeridicusError` →
   `DomainRuleViolation` (422), `NotFound` (404), `StateConflict` (409, p. ej. consolidar un
   reporte ya consolidado o reanudar una sesión no suspendida), `NotAuthorized` (401/403) e
   `IntegrationError` (502/503/504) con el atributo `retryable: bool`.
2. **Un solo manejador** en `api/` traduce excepciones a **RFC 9457 Problem Details**
   (`application/problem+json`) con una extensión `code` estable en `UPPER_SNAKE_CASE`
   (`ALERT_MISSING_REQUIRED_FIELDS`, `LLM_OUTPUT_INVALID`, `REPORT_ALREADY_CONSOLIDATED`), un
   `detail` en español para el analista y un `request_id`. Los routers no arman respuestas de
   error a mano.
3. **Nada sensible en errores ni en logs**: ni texto de transcripción, ni nombres, ni rutas de
   audio; solo IDs. Las trazas de pila nunca llegan al cliente. Va alineado con AUTONOMIA-04 y
   con el Principio 3 del PRD. Los logs son JSON estructurado a stdout con `request_id`,
   `session_id`, `job_id`.
4. **Toda llamada de E/S lleva un timeout explícito** (PostgreSQL, Redis, LLM, Whisper,
   embeddings, proxy). Los reintentos solo aplican a errores `retryable` y a operaciones
   idempotentes, con un número de intentos y un *backoff* acotados y configurables.
5. **Trabajos de la cola idempotentes** por `job_id`. Un trabajo que agota sus reintentos queda
   en estado `failed`, visible para el analista con la opción de reintentar; nunca se descarta en
   silencio. El `request_id` viaja en los metadatos del mensaje.
6. **Salida del LLM validada en la frontera** (adaptador) contra el esquema Pydantic/JSON Schema
   de `contracts/schemas/`. Si no valida, hay **un** reintento acotado y luego el error
   `LLM_OUTPUT_INVALID`. **Nunca se emite una alerta parcial**: una alerta sin fragmento, cita,
   ID de documento y traza CoT se rechaza en `domain/` (AUTONOMIA-05). Esto también sostiene la
   meta de 0 % de error de formato JSON del PRD Seg. 11.
7. **Por debajo del umbral no es un error**: el «Hecho No Documentado» es un **resultado
   normal del dominio**, no una excepción ni un 4xx. Modelarlo como error lo escondería en los
   logs y rompería la prueba de AUTONOMIA-05.
8. **Falla cerrada en la anonimización**: si el proxy falla o no está disponible, la llamada
   externa **no ocurre** y se devuelve `IntegrationError` no reintentable hacia la nube (COULD;
   AUTONOMIA-04).
9. **Desconexión ≠ error**: la sesión pasa a `SUSPENDED` (Journey 3) como transición de estado.
10. **Configuración que falla al arrancar**: `pydantic-settings` sin valores por defecto para
    secretos ni para el umbral de similitud; si falta una variable, el pod no arranca (falla
    rápido y visible) en lugar de usar un umbral implícito.
11. Frontend: el cliente HTTP convierte Problem Details en un error tipado, usa *error
    boundary* por vista y muestra el `detail` en español; nunca un error vacío.

### 5. Estilo de código (refina P10 y agrega P16)

- **Python 3.12** fijado (`requires-python`). **Ruff** como *linter* y formateador (una sola
  herramienta; de acuerdo con la sugerencia del líder en P10). Conjunto de reglas sugerido:
  `E`, `F`, `I`, `B`, `UP`, `N`, `SIM`, `PL`, `RUF`, más `S` (bandit) en coordinación con
  devsecops. Largo de línea 100.
- **Verificador de tipos (P16, falta en el borrador):** **mypy** en modo `strict` al menos en
  `domain/` y `application/` (o en todo el servicio), con Pydantic v2 y su plugin. El framework
  trae el sensor `aidlc-type-check`, y sin una práctica afirmada no tiene qué verificar.
  Alternativa: pyright.
- **TypeScript** en modo `strict` (de acuerdo con P10), ESLint *flat config* + Prettier,
  `typescript-eslint`.
- Pydantic v2 en toda frontera (HTTP, cola, LLM, configuración). Nada de `dict` sin tipo
  cruzando capas.
- Docstrings y comentarios en **español** (el lector es el equipo y el jurado del curso),
  identificadores en inglés (§2). Los comentarios explican el **porqué**, citando el ID de la
  regla cuando aplica (`# AUTONOMIA-05: …`).
- **Solo CPU** en código e imágenes (refuerza P13 desde el código): ruedas de PyTorch para CPU
  si se usan, `faster-whisper` o `whisper` con `device="cpu"` y `compute_type="int8"`, sin
  dependencias CUDA en ningún `pyproject.toml`. Esto también mantiene las imágenes pequeñas para
  `kind load`/`minikube image load`.

### 6. Migraciones de esquema y AUTONOMIA-01 (P17, nueva)

Hay una tensión que el borrador no recoge: si un servicio ejecuta `alembic upgrade head` (o
equivalente) al **arrancar el pod**, una sincronización automática de Argo CD (P8) aplicaría una
migración sobre la base del clúster **sin un paso de aprobación humana propio**. Eso es lo que
prohíbe AUTONOMIA-01. Recomendación:

- **Un solo dueño del esquema**: `db/migrations/` (Alembic, propiedad de `session-api`). El
  `semantic-agent` usa un rol de BD con permisos mínimos sobre las tablas que necesita.
- **Las migraciones nunca corren implícitamente al arrancar una aplicación.** Se ejecutan como
  `Job` de Kubernetes (artefacto revisable en `deploy/`) que el humano aprueba de forma
  explícita, aunque Argo CD sincronice solo lo demás.
- Las migraciones solo avanzan (*expand–contract*), como ya dice el borrador en «Reversión».

### Preguntas para la entrevista (refinadas y nuevas, con respuesta recomendada)

| ID | Pregunta | Respuesta recomendada | Por qué |
|---|---|---|---|
| P10 (refina) | ¿Ruff también formatea? ¿TypeScript o JavaScript? ¿Python 3.12? | Ruff lint + formato; TypeScript `strict`; Python 3.12 fijado | Una sola herramienta por lenguaje; los tipos generados del OpenAPI solo tienen valor con TS |
| P12 (refina) | ¿Identificadores en inglés o español? ¿Comentarios en qué idioma? | Identificadores en inglés con glosario único de dominio; texto visible, mensajes `detail`, comentarios y docstrings en español | Ecosistema y *linters* en inglés; el lector humano es hispanohablante; el glosario conserva la trazabilidad con el PRD |
| P14 (nueva) | ¿Monorepo con `frontend/`, `services/<svc>/`, `libs/`, `contracts/`, `db/`, `deploy/`, `evaluation/` en la raíz? ¿uv y npm? | Sí, con ese árbol; uv con lockfile por servicio; npm | Un solo PR puede cambiar contrato, servicio y chart juntos; evita chocar con `docker/` (contenedor de trabajo) |
| P15 (nueva) | ¿Formato de error y de JSON? | RFC 9457 Problem Details con `code` estable y `detail` en español; claves JSON `snake_case` de punta a punta | Estándar, sin capa de alias; los `code` estables permiten pruebas y métricas |
| P16 (nueva) | ¿Verificador de tipos? ¿Bloquea la fusión? | mypy `strict` sobre `domain/` y `application/` como mínimo; bloquea la fusión junto con el *lint* (P11) | Las invariantes de AUTONOMIA-03/05 viven ahí; el sensor `aidlc-type-check` necesita una práctica afirmada |
| P17 (nueva) | ¿Quién es dueño del esquema y cómo se ejecutan las migraciones? | `session-api` es dueño; migraciones como `Job` aprobado por el humano, nunca al arrancar la app | Evita una migración no aprobada vía sincronización automática (AUTONOMIA-01, P8) |
| P18 (nueva, candidata a `## Forbidden`) | ¿Prohibir identificadores y textos que codifiquen un veredicto de veracidad, comprobado en CI? | Sí, como regla dura enunciada por el humano: `NEVER` nombrar un identificador, campo, métrica o texto de interfaz con un veredicto de veracidad (`is_lie`, `truth_score`, `veracity`, `mentiroso`, `falso`); el vocabulario es «incongruencia» / «sugerencia de revisión» | Lleva AUTONOMIA-03 al nivel del código, donde la prueba de salida de la IA no llega (columnas, métricas, nombres de componentes) |
| (opcional) | ¿Hacer cumplir las capas con import-linter en CI? | Sí | Las fronteras sin verificación se erosionan; costo mínimo |

Candidatas a regla dura que **solo** se promueven si el humano las enuncia (no repiten
AUTONOMIA-01..05; las amplían al código):

- (candidata — P17) `NEVER` ejecutar migraciones de esquema al arrancar una aplicación; toda
  migración corre como `Job` revisable con aprobación humana.
- (candidata — P18) `NEVER` usar en identificadores, columnas, métricas o textos de interfaz un
  término que exprese veredicto de veracidad sobre el compareciente.
- (candidata — §4.6) `NEVER` emitir una alerta parcial cuando la salida del LLM no valida contra
  su esquema; el turno queda en error visible.

## Positions

- AGREE: Conventional Commits en español con alcance e ID de hallazgo — ya es la práctica observada en el historial reciente; sugerimos que el alcance sea el directorio del servicio.
- AGREE: nombres idiomáticos por lenguaje y la regla de que el agente lee primero la configuración del *linter* — coincide con `org.md` y evita sugerencias duplicadas.
- AGREE: Ruff y TypeScript como sugerencia de P10 — una sola herramienta por lenguaje y tipos útiles para el contrato con el backend.
- AGREE: validación estática de YAML/Helm (`yamllint`, `helm lint`, `kubeconform`) sin tocar el clúster — es compatible con AUTONOMIA-01.
- AGREE: candidata P13 (solo CPU) — desde el código se concreta en dependencias sin CUDA y `device="cpu"`.
- AGREE: dejar vacías `## Mandated` / `## Forbidden` en `discovered-rules.md` hasta que el humano enuncie reglas — evita promover centinelas o inferencias.
- OBJECT: P12 queda como «Abierta» sin recomendación — conviene llevar a la entrevista una respuesta recomendada (inglés + glosario único, texto visible en español) para que el humano decida sobre opciones concretas.
- OBJECT: `## Code Style` no fija la organización del repositorio — en un monorepo con 3–4 servicios, frontend, charts y suite de evaluación, la ubicación del código es una práctica del equipo; además hay que evitar `docker/` (ya es el contenedor de trabajo) y `aidlc/` (P14).
- OBJECT: falta un verificador de tipos — el framework trae el sensor `aidlc-type-check` y las invariantes AUTONOMIA-03/05 se benefician de tipos estrictos (P16).
- OBJECT: el borrador no define convenciones de manejo de errores ni de fronteras de capas — la fase Construction exige errores en fronteras de integración y distinguir recuperable de fatal; sin una convención afirmada, cada servicio inventará la suya (P15, §3–§4).
- OBJECT: «Reversión» trata las migraciones, pero no prohíbe ejecutarlas al arrancar el pod — combinado con Argo CD en sincronización automática (P8), eso sería una migración sin aprobación propia, contraria a AUTONOMIA-01 (P17).
