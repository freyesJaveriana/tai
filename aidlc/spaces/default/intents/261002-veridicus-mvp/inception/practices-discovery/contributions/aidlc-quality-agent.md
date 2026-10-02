**Collaborator:** aidlc-quality-agent

## Contribution

> Revisión ciega del borrador del líder (`team-practices.md`, `discovered-rules.md`,
> `evidence.md`) desde la postura de pruebas. Proyecto greenfield: nada de lo que sigue se
> observó en código ni en CI, porque no existen. Todo es una propuesta trazada al PRD
> (`specs/prd.md`), a `docs/limite-autonomia.md` y a `memory/org.md` / `memory/team.md`.
> Contexto de motor relevante: scope `classic`, **Test Strategy: Standard** (5–8 pruebas por
> componente, unitarias + integración), etapa 3.7 `ci-pipeline` y toda Operation en SKIP, y
> el flujo se detiene en la Parte 1 (plan de tareas) de Code Generation.

### 1. Qué significa la postura de pruebas en este trabajo

En este flujo nunca se escribe código. La postura de pruebas importa porque **ordena y
nombra las tareas de prueba dentro de cada plan de tareas** de Code Generation (Parte 1), y
porque AUTONOMIA-02 exige que cada tarea nombre el comando que demuestra que terminó. Por
eso propongo que `## Testing Posture` incluya una convención concreta para ese campo de
verificación (sección 6) y no solo herramientas.

### 2. Metodología y orden: propuesta `custom` en lugar de `test-after` puro

El borrador toma `test-after` del valor por defecto de `org.md`. Recomiendo **`custom`**:
escribir primero las pruebas de las restricciones no negociables y aplicar `test-after` al
resto.

- Las pruebas de AUTONOMIA-03/04/05 y los contratos de datos (esquema JSON de la salida del
  juez, campos obligatorios de la alerta, mensajes de la cola Redis) **especifican** un
  comportamiento ya fijado por el PRD y `team.md`. No dependen del diseño interno, así que
  escribirlas primero y verlas fallar no cuesta nada y evita que la implementación las
  «acomode».
- El resto de cada capa (repositorios, endpoints, componentes de UI) se beneficia de
  `test-after`, porque el diseño funcional todavía no existe y TDD estricto en un equipo de
  una persona con plazo de curso agrega fricción sin ganancia clara.
- No recomiendo BDD con herramienta (`pytest-bdd`, Gherkin ejecutable). Los criterios
  Given/When/Then de las historias (regla de Inception) se trazan a pruebas `pytest`
  nombradas por el ID de la historia. Así se conserva la trazabilidad sin mantener una capa
  adicional.

Texto propuesto para los dos campos estructurados:

- `- **Methodology**: custom`
- `- **Ordering**: En cada unidad, las pruebas que materializan AUTONOMIA-03/04/05 y los contratos de datos (esquema JSON de la salida del juez, campos obligatorios de la alerta y mensajes de la cola) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.`

### 3. Cobertura y herramientas

- **Piso**: 80 % de cobertura de **líneas** por servicio Python **y** por el frontend,
  medido en CI y obligatorio antes de fusionar. Es el piso de `classic` y, según `org.md`,
  Build and Test no puede bajarlo. Además se **reporta** la cobertura de ramas
  (`--cov-branch`) sin piso global.
- **Recomendación adicional (P5)**: **100 % de ramas** en los módulos guardia, que son
  pequeños y concentran el riesgo ético: la decisión de umbral del Silencio Fáctico, la
  validación de la alerta, la máquina de estados de la alerta, la consolidación del reporte
  (quién, cuándo y SHA-256) y el anonimizador si se construye (COULD).
- **Exclusiones explícitas** de la medición, declaradas en la configuración y no ad hoc:
  migraciones, código generado y el arnés de evaluación (`eval`). Una exclusión nueva se
  justifica en el PR.
- **Herramientas** (amplían P5):
  - Python: `pytest`, `pytest-cov`, `pytest-asyncio`, `httpx`/`TestClient` de FastAPI,
    Hypothesis (pruebas basadas en propiedades para el anonimizador y el umbral) y
    validación con Pydantic/`jsonschema`.
  - Integración: `testcontainers-python` o *service containers* de GitHub Actions con la
    imagen `pgvector/pgvector` y Redis reales. Matiz: CloudNativePG corre en el clúster, pero
    en CI basta un PostgreSQL con la misma versión mayor y la extensión `pgvector`.
  - Frontend: Vitest + React Testing Library + `@vitest/coverage-v8`
    (`coverage.thresholds.lines: 80`).
  - E2E: Playwright, con pocas pruebas y solo sobre el flujo de la Sesión 16.
  - Manifiestos: `helm lint` y `kubeconform` (ya en el borrador), más reglas de política
    sobre YAML con `conftest`/OPA (coordinar con devsecops): todo pod con
    `resources.requests`/`limits`, `NetworkPolicy` de salida denegada para los pods
    marcados como portadores de datos sin anonimizar, y ninguna imagen `latest`.
  - Carga (ver P18): k6 o Locust.
- **Dobles de prueba para la IA**: en pruebas unitarias y de integración, el cliente del LLM
  y el de *embeddings* se sustituyen por *fakes* deterministas detrás de una interfaz propia
  (nunca se simula la librería de un tercero). El modelo real ≤ 8B y `multilingual-e5-small`
  solo corren en la suite de evaluación (nivel 2). Así las pruebas que bloquean cada PR son
  rápidas, deterministas y corren en CPU.

### 4. Niveles de prueba y compuertas

| Nivel | Contenido | Cuándo corre | ¿Bloquea? |
|---|---|---|---|
| **0: rápido** | *lint*/formato; unitarias con *fakes* de LLM y *embeddings*; contratos (esquema JSON de la salida del juez con `additionalProperties: false`, campos obligatorios de la alerta, mensajes de la cola); pruebas guardia AUTONOMIA-03/05 deterministas; `helm lint`/`kubeconform`/`conftest`; cobertura ≥ 80 % | Cada PR, GitHub Actions, objetivo < 10 min | Sí, fusión |
| **1: integración** | Servicios contra PostgreSQL + `pgvector` y Redis reales en contenedor: consulta de similitud, persistencia y reanudación de sesión por turno (Journey 3), cola asíncrona (la API responde con un ID de trabajo sin esperar la inferencia, PRD Principio 2), registro de quién y cuándo en los cambios de estado y la consolidación | Cada PR | Sí, fusión |
| **2: evaluación de IA** | Suite sobre el Golden Dataset con el LLM local real en CPU (sección 5) | A demanda en la máquina del autor; **obligatoria** en todo PR que toque *prompts*, modelo, umbral, recuperación o esquemas de salida (filtro por rutas), y antes de cada etiqueta de entrega / la sustentación | Sí, para esos PR y para la entrega (evidencia adjunta) |
| **3: E2E y humo** | Playwright sobre el flujo de la Sesión 16 en texto (≤ 5 casos); humo tras desplegar | Antes de etiquetar una entrega y tras cada despliegue manual o de Argo CD | Sí, para la entrega |
| **Manual** | Calificación Likert de la CoT (≥ 4.5/5, dos evaluadores, PRD Seg. 11 §2.3); verificación de `NetworkPolicy` en el clúster ejecutada por el humano | Antes de la sustentación | Sí, para la entrega (hoja de calificación como evidencia) |

Política de pruebas inestables: ninguna prueba de los niveles 0 y 1 se reintenta para
ocultar un fallo. Una prueba inestable se arregla o se pone en cuarentena con un *issue*
enlazado. La no determinación del LLM queda confinada al nivel 2.

### 5. Suite de evaluación de IA sobre el Golden Dataset

- **El Golden Dataset es un entregable versionado en el repositorio** (p. ej.
  `eval/golden/v1/`, a decidir con developer) y tiene su propia prueba de esquema. Verifica
  la composición fija del PRD Seg. 11 §1: 1 escenario, 4 transcripciones alineadas, 6 con
  discrepancias sembradas (2 de fecha, 2 de lugar, 2 de rol) y 1 caso de Hecho No
  Documentado, además de los metadatos (a)/(b)/(c) por muestra. Solo contiene datos
  sintéticos (PRD Seg. 8, WON'T).
- **Umbrales que fija el PRD** (bloqueantes en el nivel 2):
  - Trazabilidad factual del 100 %: toda afirmación de la IA cita un pasaje recuperado.
  - 0 % de error de formato JSON.
  - Protocolo de permutación ejecutado en el 100 % de las consultas *offline* (MUST,
    Seg. 11 Escenario C).
  - Consistencia de juicio > 65 % al invertir el orden (Seg. 10 §3).
  - El caso de Hecho No Documentado produce 0 alertas, 0 preguntas y 1 Paquete de Contexto
    de Traspaso (AUTONOMIA-05).
- **Umbrales que el PRD no fija (hueco, ver P14)**: la sensibilidad de detección de las 6
  discrepancias sembradas y las alertas espurias sobre las 4 transcripciones alineadas. La
  tasa de relevancia > 85 % y de descarte < 15 % del Seg. 10 se miden con analistas en
  sesión y no sustituyen una meta *offline*. Sin esta meta, la suite no puede fallar por
  «no detecta nada», lo que choca con AUTONOMIA-02.
- **Red-teaming automatizado**:
  - Escenario A: casos de inyección dentro de la suite, más una prueba estática de que el
    *prompt* del sistema se monta como ConfigMap/variable de solo lectura.
  - Escenario B: comprobación de configuración. La familia del modelo generador registrada
    en los metadatos del dataset es distinta de la familia del juez configurado.
  - Escenario C: el protocolo de permutación de arriba.
  El borrador solo menciona el Escenario A.
- **Reproducibilidad**: temperatura 0, semilla fija, *digest* SHA-256 del modelo GGUF
  fijado, y un reporte JSON por corrida con el *hash* del *prompt*, el umbral, la versión del
  dataset y las métricas. El reporte se adjunta al PR como evidencia (AUTONOMIA-01/02). El
  sistema nunca recalibra sus umbrales: si la suite falla, el umbral no se toca para que
  pase (PRD Seg. 8, WON'T; `org.md`, «no se debilitan»).

### 6. Pruebas obligatorias de AUTONOMIA: mapa propuesto

Propongo que `## Testing Posture` remita a este mapa por ID, sin repetir las reglas, para
que cada plan de tareas sepa en qué nivel cae cada prueba.

| Regla | Prueba(s) | Nivel |
|---|---|---|
| AUTONOMIA-01 | No es una prueba de código. Revisión del plan, más una comprobación estática en CI de que ningún *workflow* ni *script* ejecuta `kubectl apply`/`helm install|upgrade`/`terraform apply` contra el clúster | 0 |
| AUTONOMIA-02 | Convención de plan: cada tarea lleva `Verificación: <comando exacto>` (p. ej. `pytest tests/unit/test_alerta.py -k campos_obligatorios`) y su umbral si aplica. Se revisa en la Parte 1 de Code Generation | Revisión del plan |
| AUTONOMIA-03 | (a) Máquina de estados de la alerta: solo un usuario autenticado con rol humano cambia el estado y cada cambio registra actor y hora. (b) La consolidación exige una acción explícita del analista, registra quién y cuándo, y el SHA-256 guardado coincide con el Markdown. (c) **Prueba de vocabulario prohibido**: el esquema de salida no admite campos de veracidad (`additionalProperties: false`, sin booleanos ni puntajes de verdad), y un escaneo de los textos generados por el sistema (etiquetas, títulos, cadenas de UI, DOM renderizado con RTL/Playwright) falla ante «mentiroso», «miente», «falso», «mentira», «verdadero/falso» o «puntaje de verdad». **Matiz**: el escaneo excluye los campos que citan literalmente la transcripción o el documento, porque un testimonio puede contener «falso» legítimamente. Sin esa exclusión la prueba da falsos positivos | 0 (a, b, c-esquema); 1 (b-persistencia); 0/3 (c-UI) |
| AUTONOMIA-04 | Prueba del *payload* saliente del anonimizador con los nombres y lugares del Golden Dataset más variantes generadas con Hypothesis (si el COULD se construye). Política estática de `NetworkPolicy` con `conftest` (nivel 0). Verificación en clúster ejecutada por el humano (un pod marcado no alcanza internet). **Riesgo**: el CNI por defecto de Minikube no aplica `NetworkPolicy`, y en Kind depende de la versión, así que hay que **verificarlo** (ver P7) | 0 + Manual |
| AUTONOMIA-05 | Parametrizada: una alerta sin cada uno de los 4 campos obligatorios se rechaza (4 casos). El umbral se lee de configuración y no del código. Por debajo del umbral, 0 alertas, 0 preguntas (incluida la sugerencia de pregunta SHOULD) y 1 Hecho No Documentado con su paquete de traspaso. **Caso límite exactamente en el umbral** (ver P15). El umbral solo cambia por una acción humana autenticada que registra quién, cuándo, el valor anterior y el nuevo (PRD Seg. 10 AIR) | 0 + 1 + 2 |

### 7. Otros puntos de calidad para el borrador

- **Prueba de humo medible**: «completa un testimonio del Golden Dataset» no cumple
  AUTONOMIA-02 tal como está redactada. Propuesta: un *script* o *spec* de Playwright con
  nombre fijo. Para la transcripción con discrepancia sembrada `<id>`, aparece ≥ 1 alerta
  con sus 4 campos obligatorios en ≤ *N* s (*N* lo fija NFR Requirements; el PRD da 8–12 s
  por turno de voz). Para el caso de Hecho No Documentado, aparece el paquete de traspaso
  sin alerta. Además, el `GET` de salud de cada pod responde 200.
- **Contratos entre servicios**: con un solo autor, recomiendo modelos Pydantic y esquemas
  JSON versionados y compartidos, validados en ambos extremos (productor y consumidor de la
  cola, API y frontend), en lugar de Pact.
- **Test Strategy Standard frente a las suites obligatorias**: Standard no incluye E2E ni
  seguridad. Las suites AUTONOMIA, la de evaluación y el humo son **adicionales**, impuestas
  por `team.md` y el PRD, y no cuentan contra el volumen de Standard. Conviene dejarlo
  escrito para que ningún plan las recorte «por volumen».
- **Riesgo 2 del PRD** (obligar a expandir la CoT antes de aceptar): si Requirements lo
  convierte en requisito, se agrega una prueba de RTL. No lo introduzco como requisito aquí.

### 8. Preguntas para la entrevista: refinamientos y nuevas

| ID | Pregunta (en palabras del humano) | Respuesta recomendada | Por qué |
|---|---|---|---|
| P4 (refina) | ¿Escribimos primero las pruebas de las reglas éticas y de los contratos de datos, y el resto después de cada capa? ¿O todo después (test-after) o todo antes (TDD)? | **Mezcla (`custom`)** con el orden de la sección 2 | Las guardias ya están especificadas por `team.md`; escribirlas primero es barato y protege lo no negociable |
| P5 (refina) | ¿Mantenemos 80 % de líneas por servicio y en el frontend? ¿Exigimos además el 100 % de ramas en los módulos guardia? | 80 % de líneas (no negociable en `classic`) + 100 % de ramas en guardias + ramas reportadas | Módulos pequeños de alto riesgo; con 80 % global puede quedar sin probar justo la rama ética |
| P6 (refina) | La evaluación con el modelo real tarda en CPU. ¿Debe bloquear todo PR, solo los que tocan la IA o solo la entrega? | **Solo los PR que tocan la IA (filtro por rutas) y toda etiqueta de entrega**, corrida en local con el reporte adjunto | En cada PR sería lenta e inestable; «aparte» sin compuerta dejaría sin exigir el 100 % / 0 % del PRD |
| P7 (amplía) | ¿El clúster que elijas aplica de verdad las `NetworkPolicy`? (Algunos clústeres locales las aceptan pero no las hacen cumplir.) | Elegir un CNI que las aplique (Calico o Cilium) y verificarlo con una prueba manual | Sin eso, AUTONOMIA-04 no se puede demostrar |
| P11 (amplía) | ¿Activamos la protección de `main` para que las comprobaciones del CI sean obligatorias? | Sí, con los niveles 0 y 1 como comprobaciones requeridas | Hoy se hace commit directo a `main`; sin protección, la compuerta es nominal |
| P13 (opina) | ¿«Ninguna prueba requiere GPU» es regla dura? | Sí | Las pruebas son el primer lugar donde se cuela la GPU (imágenes CUDA, `torch` con CUDA) |
| **P14 (nueva)** | En el Golden Dataset, ¿cuántas de las 6 discrepancias sembradas debe detectar la IA y cuántas alertas toleramos en las 4 transcripciones sin discrepancia? | Que lo fije **NFR Requirements** junto con el modelo y el umbral (como manda el PRD Seg. 9, Módulo D). Como punto de partida: ≥ 5/6 detectadas y 0 alertas en las alineadas | Sin meta, la suite no puede fallar por baja detección (AUTONOMIA-02); el valor es una decisión de producto y no se inventa aquí |
| **P15 (nueva)** | Cuando la similitud es **exactamente igual** al umbral, ¿hay alerta o Hecho No Documentado? | Hecho No Documentado (la opción conservadora: ante la duda, escala al humano) | Hace falta para escribir la prueba de límite de AUTONOMIA-05; es una ambigüedad del PRD |
| **P16 (nueva)** | ¿Quién puede cambiar el estado de una alerta: solo `analista` o también `admin`? | Solo `analista`; `admin` gestiona usuarios y umbral | La prueba de AUTONOMIA-03 necesita el rol exacto; el PRD Principio 1 dice «el analista es el único» |
| **P17 (nueva)** | ¿Cuándo corren las pruebas de punta a punta en el navegador (Playwright)? | Antes de cada etiqueta de entrega y tras cada despliegue; no en cada PR | Son lentas, pero cubren la demostración de la Sesión 16 |
| **P18 (nueva)** | La meta de > 98 % de sesiones sin `OOMKilled` ni `timeout` bajo concurrencia (PRD Seg. 10) necesita una prueba de carga, pero la validación de rendimiento (4.6) está en SKIP. ¿La hacemos en Build and Test, con cuántas sesiones simultáneas, o la declaramos fuera del MVP? | Una prueba ligera con k6/Locust en Build and Test; *N* sesiones fijado en NFR Requirements | Si no, el KPI queda sin comando que lo demuestre (AUTONOMIA-02) |

### 9. Candidatas a regla dura (solo si el humano las enuncia)

- (candidata, P11) `NEVER` fusionar a `main` un PR cuyo *lint*, pruebas de nivel 0/1 o piso
  de cobertura fallen. Apoyo la candidata del líder.
- (candidata, nueva) `NEVER` marcar como `skip`/`xfail`, borrar ni relajar una prueba
  AUTONOMIA o un umbral del Golden Dataset para que una compuerta pase.
- (candidata, nueva) `NEVER` usar datos reales (nombres, lugares, expedientes) en
  *fixtures*, *seeds* o el Golden Dataset; solo datos sintéticos.
- (candidata, P13) `NEVER` exigir GPU en pruebas, imágenes de prueba o el arnés de
  evaluación.

## Positions

- AGREE: Pruebas de integración contra PostgreSQL + `pgvector` y Redis reales en contenedor, sin *mocks* de la base vectorial. Es la única forma de probar la consulta de similitud y el umbral de verdad.
- AGREE: El piso del 80 % de líneas medido en CI y bloqueante. Es el piso de `classic` y no se puede debilitar.
- AGREE: `pytest`/`pytest-cov` y Vitest + RTL como base. Las amplío con Playwright, Hypothesis, `testcontainers` y `conftest`.
- AGREE: Validación estática de manifiestos (`helm lint`, `kubeconform`) sin tocar el clúster. Encaja con AUTONOMIA-01.
- AGREE: Todo corre en CPU. Recomiendo elevarlo a regla dura para las pruebas (P13).
- OBJECT: La metodología `test-after` pura. Recomiendo `custom` con las guardias AUTONOMIA y los contratos de datos primero, porque su comportamiento ya está especificado y es lo que no puede romperse.
- OBJECT: La sugerencia de P6 («corre aparte»). Sin compuerta, los umbrales del 100 % de trazabilidad y el 0 % de error de formato no se exigen nunca. Debe bloquear los PR que tocan la IA y toda entrega.
- OBJECT: La lista de tipos de prueba omite los contratos (esquema JSON del juez, mensajes de la cola) y los Escenarios B y C de red-teaming. El C es MUST *offline* según el PRD Seg. 11.
- OBJECT: La prueba de humo («completa un testimonio») no es medible tal como está redactada. Necesita un comando y un resultado esperado concreto para cumplir AUTONOMIA-02.
- OBJECT: Falta registrar que la suite de evaluación no tiene meta de detección de las discrepancias sembradas. Debe ir como pregunta abierta (P14) y no darse por resuelta.
