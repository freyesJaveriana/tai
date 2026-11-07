# Team-Level Rules

> This team's affirmed practices and corrections. Loaded after `org.md` as
> strict-additive guidance; contradictions with broader policy are rejected.
> Populated by the practices-discovery affirmation gate. Edit at the gate,
> not directly.

## Way of Working

Somos un equipo de una persona que trabaja con agentes de IA: el agente propone, el humano aprueba.

- **Tronco único** (`main`) y ramas cortas (1–2 días) con nombre `<tipo>/<slug-del-bolt>`. El código y la infraestructura entran solo por **pull request con evidencia** (la salida del comando de verificación de cada tarea) y **squash-merge**: cada Bolt queda como un commit en `main`. Los *worktrees* de Construction parten de `main` y fusionan a `main`.
- `main` está **protegida también frente al administrador**: sin *push* directo para código, manifiestos ni charts, y con las comprobaciones de CI obligatorias. La documentación (`docs/`, `specs/`) y los artefactos de AI-DLC (`aidlc/`) siguen por commit directo.
- Revisa y aprueba cada PR el autor, apoyado en la revisión del agente y la evidencia adjunta; un par del curso solo cuando el autor lo pide. La fusión del PR en `main` protegida es la aprobación humana registrada.
- **Monorepo en la raíz**: `frontend/`, `services/<servicio>/` (p. ej. `session-api`, `audio-worker`, `semantic-agent`, `anonymizer-proxy`), `libs/`, `contracts/`, `db/migrations/`, `deploy/` (charts y manifiestos) y `evaluation/` (Golden Dataset y arnés). Cada servicio es autocontenido (su `pyproject.toml`, lockfile, `Dockerfile` y `tests/`); solo `libs/` se comparte entre servicios. Nada de código bajo `aidlc/` ni en `docker/` (contenedor de trabajo).
- **Antes de cualquier desarrollo**, una tarea conjunta (autor + agente) configura y valida GitHub: protección de `main`, comprobaciones obligatorias, GHCR privado, *deploy key* de solo lectura, permisos de Actions y Dependabot. Se valida con un PR de prueba que la CI bloquea y que el *push* directo se rechaza.
- **Pre-commit local** con `gitleaks`, Ruff y `yamllint`; la CI repite todo, porque el hook local se puede saltar.
- Mensajes de commit en **Conventional Commits en español** (`tipo(alcance): descripción`); el alcance es el directorio del servicio o del documento y se cita el ID de la regla o del hallazgo cuando aplica (`fix(prd): … (H6)`). El cierre de cada etapa de AI-DLC se registra como `aidlc(<etapa>): …` y se hace *push*.
- Los defectos del PRD o del PVB se corrigen en el **original**, en su propio commit; nunca se crean copias de los insumos.

## Walking Skeleton

- No ejecutamos la ceremonia de esqueleto andante: el scope `classic` la declara apagada (`skeleton: off`).
- Sí fijamos el **orden de entrega** (cambio 01, DT27): la primera rebanada de valor es la **biblioteca del analizador de incoherencias con su línea de comandos**, con el **anonimizador** como módulo de la biblioteca y la validación del perfil (la línea de comandos rechaza un destino externo sin anonimizador antes de cualquier llamada, igual que los servicios), y un proveedor comercial, sobre transcripciones sintéticas (y, fuera de Git, las 10 entrevistas del piloto del TG). Siguen la consola con la revisión, el reporte y la voz (User Stories, pregunta 10).

## Testing Posture

- **Methodology**: custom
- **Ordering**: En cada unidad, las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (contrato común del analizador, esquema del hallazgo, mensajes de la cola, perfil de ejecución) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.
- **Cobertura**: 80 % de líneas por cada servicio Python y por el frontend, medido en CI y bloqueante; **100 % de ramas** en los módulos guardia (verificación determinista de citas, validación y máquina de estados de la alerta, consolidación del reporte, anonimizador). Las exclusiones (migraciones, código generado, arnés de evaluación) se declaran en la configuración y cada exclusión nueva se justifica en el PR.
- **Herramientas**: `pytest` + `pytest-cov` (+ `pytest-asyncio`, Hypothesis) y mypy estricto en Python; Vitest + React Testing Library y TypeScript estricto en el frontend; Playwright para E2E; validación de manifiestos con `helm template` → `kubeconform` → Kyverno CLI.
- **Dobles de prueba**: los modelos se sustituyen por *fakes* deterministas del `ModelGateway` en los niveles 0 y 1, sin red; PostgreSQL y Redis son reales en contenedor.
- **Niveles y compuertas**:
  - **Nivel 0 (cada PR, bloquea)**: *lint*, tipos, unitarias, contratos, guardias AUTONOMIA deterministas, políticas de manifiestos, cobertura.
  - **Nivel 1 (cada PR, bloquea)**: integración contra PostgreSQL y Redis reales (persistencia y reanudación de sesión, cola asíncrona, registro de quién y cuándo, anonimizador con su fallo cerrado).
  - **Nivel 2, evaluación de IA con la línea de comandos del analizador**: corre contra cualquier proveedor del perfil, en la anfitriona o en ZINE, sobre el **conjunto sintético** versionado en `evaluation/` (contradicciones internas sembradas de los 7 tipos, relatos coherentes y casos trampa). Bloquea los PR que tocan la IA (filtro por rutas: *prompts*, perfiles, adaptadores de modelos, esquemas de salida) y toda entrega etiquetada. Se corre fuera de la CI y el reporte JSON (versión del dataset, *hash* del *prompt*, perfil con su huella, modelos por llamada, métricas) se adjunta al PR. Umbrales: 100 % de citas verificadas en lo emitido, 0 % de error de formato JSON, permutación de las dos citas en el 100 % de las consultas *offline*, consistencia > 65 % al invertir el orden, acuerdo entre 3 corridas y precisión y sensibilidad sobre el conjunto (umbrales en NFR Requirements). Incluye *red-teaming* (Escenarios A, B y C). Aparte, la CLI sobre las 10 entrevistas del piloto, con resultados fuera de Git, es prueba de humo frente a sus 4 contradicciones; no mide.
  - **Nivel 3, E2E y humo**: antes de etiquetar una entrega y tras cada despliegue.
  - **Manual**: calificación Likert de la CoT (≥ 4.5/5, dos evaluadores) y verificación de `NetworkPolicy` en el clúster, antes de la sustentación.
- **CPU y GPU**: la suite completa corre en **CPU**, en la máquina de desarrollo. Las pruebas que de verdad requieren GPU (evaluación con modelos más grandes, ensayo de la demo) se agrupan en una **etapa separada del perfil GPU**, que se corre a demanda en la máquina GPU solo cuando es estrictamente necesario. Ninguna prueba de los niveles 0 y 1 exige GPU.
- **Mapa AUTONOMIA** (cada plan de tareas cita la prueba por ID): 01 → comprobación estática de que ningún *workflow* ni *script* aplica cambios al clúster (nivel 0); 02 → cada tarea lleva `Verificación: <comando exacto>` y su umbral; 03 → máquina de estados con actor y hora, consolidación explícita con SHA-256, esquema sin campos de veracidad y escaneo de vocabulario prohibido en salida e interfaz que excluye las citas literales (niveles 0, 1 y 3); 04 → prueba del *payload* saliente del anonimizador, prueba de fallo cerrado, arranque rechazado con un destino externo sin anonimizador y política estática de `NetworkPolicy` (nivel 0) más verificación manual en el clúster; 05 → hallazgo rechazado sin cada uno de sus campos obligatorios, cita alterada o en otro turno que no sale, `error` ⇒ hallazgos vacíos y cita restaurada antes de verificarse (niveles 0, 1 y 2).
- **Prueba de humo**: `scripts/smoke.sh <url-base>` termina con código 0 solo si (a) el *endpoint* de salud de cada servicio responde 200 y (b) el *spec* `frontend/e2e/smoke.spec.ts` comprueba que una transcripción sintética con una contradicción sembrada produce ≥ 1 hallazgo con sus dos citas en ≤ *N* s (*N* lo fija NFR Requirements) y que un relato coherente produce 0 hallazgos.
- Las suites AUTONOMIA, de evaluación y de humo son **adicionales** al volumen de la Test Strategy y ningún plan las recorta. Ninguna prueba de los niveles 0 y 1 se reintenta para ocultar un fallo; una prueba inestable se arregla o se pone en cuarentena con un *issue* enlazado. Los umbrales nunca se bajan para que una compuerta pase.

## Guard Policy

<!-- Affirmed by the team. Mode: strict, relaxed, or off. Strict here holds for every intent and cannot be changed from chat. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

- **Dos máquinas**: la máquina de desarrollo (CPU), donde ocurre casi todo el trabajo y donde el sistema funciona completo, y una máquina GPU opcional (hasta 4 GPU y 32 GB de RAM del sistema) para el perfil GPU de evaluación y la demostración. El entorno concreto de cada una (distribución de Kubernetes, CNI que haga cumplir las `NetworkPolicy`, namespaces, memoria de GPU) lo define **Infrastructure Design** como infraestructura mínima. No hay nube, *staging* ni producción separados en este MVP.
- **Imágenes**: se construyen en CI y se publican en **GHCR privado**, etiquetadas con el SHA del commit y nunca `latest`; ambas máquinas descargan exactamente la misma imagen. Imágenes base mínimas fijadas por digest, contenedores sin root, y Trivy bloquea las vulnerabilidades `HIGH`/`CRITICAL` que tengan corrección. Solo el *job* de *build* tiene `packages: write`. Las imágenes de terceros llevan versión de chart fijada y, cuando se puede, digest.
- **Cambios al clúster**: todo despliegue es un artefacto revisable (manifiesto o chart con `requests`/`limits`, `NetworkPolicy`, script de migración) que entra por PR. La fusión en `main` protegida es la aprobación registrada; Argo CD sincroniza automáticamente con una *deploy key* de solo lectura y con *prune* desactivado sobre la base de CloudNativePG y sus PVC. Antes del Módulo 8 (sin Argo CD), el humano aplica a mano el artefacto ya fusionado.
- **Migraciones**: `session-api` es dueño del esquema; las migraciones solo avanzan (*expand–contract*) y corren como un `Job` aparte que entra por su propio PR, nunca al arrancar un pod.
- **Secrets**: los manifiestos solo los referencian (`secretKeyRef`/`envFrom`); el humano crea los valores (incluidas las claves de API de los proveedores comerciales) desde un `.env` no versionado con un script revisable.
- **Salida a internet**: la `NetworkPolicy` la niega a todos los pods salvo al anonimizador, que solo sale por 443 y DNS; la lista de dominios de los proveedores la impone el propio anonimizador, con su prueba, junto con la lista blanca de CoreDNS. `.gitignore` cubre `.env`, `*.pem`, `*.key`, `kubeconfig*` y `secrets*.yaml`.
- **La CI no despliega**: no tiene `kubeconfig` ni credenciales del clúster, declara `permissions: contents: read` por defecto y fija las acciones por SHA.
- **Artefactos de modelo** (Whisper, LLM, *embeddings*): revisión fijada y verificada con `sha256`, descargados en *build* o aprovisionamiento y nunca en ejecución, en formatos sin código ejecutable (GGUF, `safetensors`) y sin `trust_remote_code`.
- **Verificación y reversión**: tras cada despliegue se ejecuta la prueba de humo; si falla, se revierte con `git revert` del commit de manifiestos y una nueva sincronización.

## Code Style

- **Python 3.12** con Ruff para *lint* y formato (reglas `S` incluidas; toda supresión `# noqa: S…` lleva su motivo), mypy estricto y `uv` con un lockfile por servicio. **Frontend en TypeScript** estricto con ESLint + Prettier y `react/no-danger` como error. **Infraestructura**: `yamllint`, `hadolint` y `helm lint`.
- **CI en GitHub Actions**. Bloquean la fusión: *lint*, tipos, pruebas, cobertura, `gitleaks`, `pip-audit`/`npm audit` (`HIGH`+ con corrección), Trivy y las políticas de manifiestos (`helm template` → `kubeconform` → Kyverno CLI, todo *offline*). Solo avisan: Semgrep y Dependabot. Las excepciones se registran en archivos versionados (`.trivyignore`, `.gitleaksignore`) con motivo y fecha de caducidad.
- **Idioma**: identificadores en **inglés**, con un glosario único que traduce cada término del PRD (p. ej. «Hecho No Documentado» → `undocumented_fact`, «sugerencia de revisión» → `review_suggestion`, «reporte de revisión» → `review_report`, que sustituye a «reporte forense» por D10.4 y VE-03); los textos visibles, los mensajes de error y los comentarios van en español. Ningún término se traduce de dos formas.
- **Nombres** idiomáticos: `snake_case` en Python, `camelCase`/`PascalCase` en TypeScript, `kebab-case` con prefijo `veridicus-` en recursos de Kubernetes, variables de entorno `VERIDICUS_<AJUSTE>`.
- **Capas por servicio**: `api/` o `worker/` → `application/` → `domain/`, con `adapters/` implementando los puertos de `application/`. Las invariantes de AUTONOMIA-03/05 viven en `domain/` como código puro; las fronteras se hacen cumplir con import-linter.
- **Errores en fronteras**: una jerarquía única de excepciones en `libs/`, traducida por un solo manejador a Problem Details (RFC 9457) con un `code` estable y un `detail` en español. Toda E/S lleva un *timeout* explícito, y los reintentos se limitan a errores recuperables y operaciones idempotentes. Los logs no llevan datos sensibles, solo IDs. La salida del LLM se valida contra su esquema y nunca se emite una alerta parcial. Por debajo del umbral, el Hecho No Documentado es un resultado normal y no un error. Una configuración faltante impide arrancar el pod.
- Los agentes leen primero la configuración del *linter* del proyecto; una sugerencia de estilo del agente solo aplica si el *linter* no la cubre.
## Forbidden

- **AUTONOMIA-01:** NEVER incluir en un plan de tareas un paso que ejecute `kubectl apply`, `helm install`, `helm upgrade`, `terraform apply`, una migración de esquema sobre la base del clúster o equivalente sin un paso previo de aprobación humana registrada; el destino es un PR con evidencia, nunca un cambio directo.
- **AUTONOMIA-02:** NEVER aceptar criterios de aceptación de opinión («funciona correctamente», «es usable», «tiene buen rendimiento») sin un comando o umbral medible.
- **AUTONOMIA-03:** NEVER producir una etiqueta automática de veracidad sobre el compareciente («mentiroso», «falso», «miente», puntaje binario de verdad) ni consolidar el reporte de revisión final sin la validación explícita de un analista humano.
- **AUTONOMIA-01:** NEVER enviar trabajos al clúster ZINE ni a otro clúster de cómputo; los scripts `sbatch` los lanza el humano.
- **AUTONOMIA-04:** NEVER enviar fuera del clúster local audio crudo, transcripciones sin seudonimizar, nombres de víctimas o identificadores reales del proceso; NEVER llamar a un proveedor externo sin el anonimizador delante o si este falla.
- **AUTONOMIA-05:** NEVER emitir un hallazgo de contradicción sin sus dos citas literales verificadas en su turno, ni un resultado parcial cuando el analizador falla.
- **Proceso:** NEVER copiar al repositorio entrevistas, fragmentos, codificaciones ni revisiones del piloto del TG, ni usar la partición `referencia`; las pruebas usan transcripciones sintéticas y los resultados de corridas sobre el corpus se escriben fuera de Git.
- **Proceso:** NEVER elegir ni proponer autonomía en Construction («Continue automatically»).

## Mandated

- **Fuente:** las reglas AUTONOMIA-01..05 vienen de `docs/limite-autonomia.md` (PRD Segmento 6). Son bloqueantes: si una etapa no cumple un criterio, la única salida es «Request Changes», y cada verificación se cita por su ID.
- **AUTONOMIA-01:** ALWAYS que una tarea toque un entorno compartido (clúster, base CloudNativePG, nube), su salida es un artefacto revisable (manifiesto, chart, script de migración, PR) precedido de aprobación humana.
- **AUTONOMIA-02:** ALWAYS que cada tarea de cada unidad nombre el comando, la prueba o la comprobación que demuestra que terminó.
- **AUTONOMIA-03:** ALWAYS modelar todo hallazgo de la IA como «sugerencia de revisión» con estado editable (pendiente / aceptada / editada / descartada) cambiado por un humano; la consolidación del reporte exige una acción explícita del analista que registra quién y cuándo; existe al menos una prueba automatizada que falla si la salida de la IA o la interfaz contiene una etiqueta de veracidad binaria.
- **AUTONOMIA-04:** ALWAYS declarar en el diseño, para cada componente, si corre dentro o fuera del clúster y qué datos cruzan esa frontera; un destino externo exige el anonimizador delante o el servicio no arranca; toda integración con un proveedor externo incluye una prueba de que el payload saliente pasó por el anonimizador y otra de que, si este falla, no sale ninguna llamada; existe una tarea que produce la `NetworkPolicy` que niega salida a internet a todos los pods salvo al anonimizador (como artefacto revisable); las claves de API viven en un `Secret` que crea el humano.
- **AUTONOMIA-05:** ALWAYS que un hallazgo de contradicción tenga como campos obligatorios `hecho`, `tipo` (7 valores), `cita_a`, `cita_b` (cada una con texto, turno y página si la hay) y `observaciones` (sin ellos se rechaza); existen pruebas de que una cita alterada o en otro turno no sale del analizador, de que `estado: error` implica hallazgos vacíos y de que la cita seudonimizada se restaura antes de verificarse.
- **Proceso:** ALWAYS una aprobación humana por etapa; en Construction, ALWAYS «Review each checkpoint».
- **Proceso:** ALWAYS `Approve Plan` lo elige solo el humano, después de revisar el plan de tareas regenerado de la unidad; luego se construye por Bolts (DT27 levanta el alto antes de la Parte 2).

## Corrections

<!-- Self-learning loop appends here. -->
