# Practices Discovery — preguntas

*Etapa 2.2 · intent `261002-veridicus-mvp` · proyecto greenfield*

Estas preguntas definen **cómo trabaja el equipo** en Veridicus. Al aprobar la etapa, las respuestas
reemplazan cinco secciones de `aidlc/spaces/default/memory/team.md`:

- Way of Working
- Walking Skeleton
- Testing Posture
- Deployment
- Code Style

Las reglas duras que marques en la pregunta 17 se añaden a `project.md`. Las reglas AUTONOMIA-01..05
y las de proceso **no cambian**.

Las propuestas vienen del borrador del ingeniero de despliegue y de las revisiones independientes de
calidad, desarrollo y seguridad. Puedes verlas en `team-practices.md` y en `contributions/`.

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es la propuesta del equipo.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

## Forma de trabajo

### Pregunta 1 — ¿Cómo entra el trabajo a `main`?

Hoy todo se hace con commit directo a `main`.

A. El código y la infraestructura entran por **pull request con evidencia** (la salida del comando de verificación de cada tarea), con squash-merge y `main` **protegida también frente al administrador**, con las comprobaciones de CI obligatorias. La documentación y los artefactos de AI-DLC siguen por commit directo **(Recomendada)**
B. Igual que A, pero sin proteger la rama: el PR es una convención, no una compuerta.
C. Todo sigue por commit directo a `main`.
X. Other (please specify)

[Answer]: A

### Pregunta 2 — ¿Quién revisa y aprueba cada PR?

A. Tú, apoyado en la revisión del agente y la evidencia adjunta; un par del curso solo cuando lo pidas **(Recomendada)**
B. Tú solo, sin revisión del agente.
C. Siempre un par del curso además de ti.
X. Other (please specify)

[Answer]: A

### Pregunta 3 — ¿Cómo se organiza el repositorio del código?

A. Monorepo en la raíz:
   - `frontend/`;
   - `services/<servicio>/` (p. ej. `session-api`, `audio-worker`, `semantic-agent`, `anonymizer-proxy`);
   - `libs/`, `contracts/` y `db/migrations/`;
   - `deploy/` (charts y manifiestos) y `evaluation/` (Golden Dataset).

   Nada de código bajo `aidlc/` ni en `docker/`, que es el contenedor de trabajo **(Recomendada)**
B. Un repositorio por servicio.
C. No se fija ahora; lo decide Domain Design.
X. Other (please specify)

[Answer]: A

## Primera entrega

### Pregunta 4 — ¿Construimos primero una rebanada delgada de punta a punta?

Un *walking skeleton* (esqueleto andante) es una versión mínima que recorre todo el sistema, construida
primero para probar que las piezas conectan antes de agregar las funciones reales.

A. No como ceremonia (el flujo de este trabajo no llega a escribir código), pero sí como orden: le pedimos a Delivery Planning que la primera unidad sea el flujo de **texto** de punta a punta. Ese flujo es: cargar el escenario, ingresar un testimonio, consultar `pgvector` y mostrar la alerta con su CoT al analista **(Recomendada)**
B. Sí, como ceremonia con su compuerta de verificación (exigiría ejecutar código, en contra de la regla de proceso).
C. No, y sin orden especial para la primera unidad.
X. Other (please specify)

[Answer]: A

## Pruebas

### Pregunta 5 — ¿En qué orden se escriben las pruebas?

A. **Mezcla (`custom`)**: primero las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (esquema de alerta, JSON del juez, mensajes de la cola), cuyo comportamiento ya está especificado. Las demás se escriben después de cada capa (test-after) **(Recomendada)**
B. Todo después de cada capa (test-after, el valor por defecto).
C. Todo antes (TDD).
D. Escenarios BDD (Given/When/Then) primero y pruebas unitarias después.
X. Other (please specify)

[Answer]: A

### Pregunta 6 — ¿Qué piso de cobertura exigimos?

A. 80 % de líneas por cada servicio Python y por el frontend, más el **100 % de ramas en los módulos guardia** (veredicto binario, anonimizador, umbral del Silencio Fáctico) **(Recomendada)**
B. Solo el 80 % de líneas, el piso del perfil `classic`.
X. Other (please specify)

[Answer]: A

### Pregunta 7 — ¿Con qué herramientas de prueba y de tipos?

A. `pytest` + `pytest-cov` y **mypy en modo estricto** para Python; Vitest + React Testing Library y **TypeScript estricto** para el frontend **(Recomendada)**
B. Las mismas herramientas de prueba, sin verificador de tipos.
X. Other (please specify)

[Answer]: A

### Pregunta 8 — La evaluación de la IA sobre el Golden Dataset tarda en CPU. ¿Cuándo bloquea?

A. Bloquea los PR que tocan la IA (filtrados por ruta) y toda entrega etiquetada. Se corre en local y se adjunta el reporte al PR **(Recomendada)**
B. Corre aparte, a demanda; solo es obligatoria antes de la sustentación.
C. Bloquea todos los PR.
X. Other (please specify)

[Answer]: A.  Sin embargo, planeo ejecutarla con GPU en otra máquina.  Incluye requerimientos para los pasos que requieran GPU, que se ejecutarán en una máquina con GPUs, aunque la mayoría del desarrollo se ejecutará en esta máquina (con GPUs pequeñas y más limitadas).

### Pregunta 9 — El PRD no fija qué porcentaje de las discrepancias sembradas debe detectar el sistema. ¿Qué hacemos?

A. Queda como pregunta abierta para Requirements Analysis, que debe fijarla como requisito medible **(Recomendada)**
B. Lo fijamos ya: detectar al menos el 5 de 6 discrepancias sembradas (≥ 83 %).
X. Other (please specify)

[Answer]: A

## Despliegue

### Pregunta 10 — ¿En qué entorno se despliega?

A. Un solo entorno: un clúster **Kind** local en CPU con un CNI que **sí hace cumplir** las `NetworkPolicy` (Calico), y los namespaces `veridicus-apps` y `veridicus-system`. Sin nube ni *staging* **(Recomendada)**
B. Igual, pero con Minikube (con Calico o Cilium).
C. No se fija ahora; lo decide Infrastructure Design.
X. Other (please specify)

[Answer]: C.  Como contesté en la pregunta 8, prefiero que se defina una infraestructura mínima para ejecutarlo, con máximo 4 GPUs y 32 GB RAM, que es la mejor máquina que tengo disponible para desarrollo y demostración.  Sin embargo, prefiero dejar la mayor parte del desarrollo en mi máquina 
(con CPUs) y solo los tests que finalmente requieran GPUs, agrupados en una etapa separada, para poder usar el equipo de GPUs solo cuando sea estrictamente necesario.

### Pregunta 11 — ¿Cómo llega un cambio aprobado al clúster?

AUTONOMIA-01 exige aprobación humana registrada antes de aplicar cambios.

A. La fusión del PR en `main` protegida **es** la aprobación registrada. Argo CD sincroniza automáticamente, con *prune* desactivado sobre la base de CloudNativePG y una *deploy key* de solo lectura. Las migraciones de esquema corren como un `Job` aparte que entra por su propio PR; nunca al arrancar un pod. Antes del Módulo 8 (sin Argo CD), aplicas tú a mano el artefacto ya fusionado **(Recomendada)**
B. Igual que A, pero Argo CD sincroniza solo cuando tú das clic.
C. Siempre aplicas tú a mano; sin Argo CD.
X. Other (please specify)

[Answer]: A

### Pregunta 12 — ¿Cómo se construyen y distribuyen las imágenes?

A. Se construyen y cargan **localmente** (`kind load`), etiquetadas con el SHA del commit y nunca `latest`. Las imágenes base van fijadas por digest, los contenedores corren sin root y el escaneo con Trivy bloquea las vulnerabilidades HIGH/CRITICAL que tengan corrección **(Recomendada)**
B. Igual, pero publicadas en un registro (GHCR).
X. Other (please specify)

[Answer]: A

### Pregunta 13 — ¿Cómo se manejan los Secrets?

A. Los manifiestos solo **referencian** Secrets; los valores los creas tú desde un `.env` no versionado. Se amplía `.gitignore` (`.env`, `*.pem`, `*.key`, `kubeconfig*`, `secrets*.yaml`) y gitleaks corre en pre-commit y en CI **(Recomendada)**
B. Secrets cifrados en el repositorio (Sealed Secrets o SOPS).
X. Other (please specify)

[Answer]: A

## Estilo de código y CI

### Pregunta 14 — ¿Qué lenguajes y linters?

A. **Python 3.12** con Ruff para *lint* y formato, reglas de seguridad `S` incluidas, y `uv` con un lockfile por servicio. Frontend en **TypeScript** con ESLint + Prettier (`react/no-danger` como error). Para infraestructura: `yamllint`, `hadolint` y `helm lint` **(Recomendada)**
B. Igual, pero con Black como formateador y el frontend en JavaScript.
X. Other (please specify)

[Answer]: A

### Pregunta 15 — ¿En qué idioma van los identificadores del código?

A. En **inglés**, con un glosario único que traduce cada término del PRD (p. ej. «Hecho No Documentado» → `undocumented_fact`, «sugerencia de revisión» → `review_suggestion`). Los textos visibles, los mensajes de error y los comentarios van en español **(Recomendada)**
B. Todo en español, incluidos los identificadores.
X. Other (please specify)

[Answer]: A

### Pregunta 16 — ¿Qué corre en CI y qué bloquea la fusión?

A. **GitHub Actions**:
   - Bloquean: *lint*, tipos, pruebas, cobertura, gitleaks, `pip-audit`/`npm audit`, Trivy y las políticas de manifiestos (`helm template` → `kubeconform` → Kyverno CLI, todo *offline*).
   - Solo avisan: Semgrep y Dependabot.
   - La CI no tiene credenciales del clúster.

   **(Recomendada)**
B. Mínimo: *lint*, pruebas y cobertura bloquean; nada de escaneo de seguridad.
X. Other (please specify)

[Answer]: A.  Incluye (si no lo estaba ya) una tarea conjunta de configuración y validación de Github antes del desarrollo.

## Reglas duras

### Pregunta 17 — ¿Cuáles de estas declaras como restricciones duras del equipo? (select all that apply)

Las que marques se escriben en `project.md` como reglas `NEVER`.

A. NEVER asumir GPU en código, pruebas, imágenes o manifiestos: todo corre en CPU.
B. NEVER guardar datos reales (testimonios, nombres o expedientes) en el repositorio ni en la CI: solo datos sintéticos.
C. NEVER versionar valores de Secret, `.env`, `kubeconfig` ni claves.
D. NEVER usar identificadores, columnas, métricas o textos de interfaz que expresen un veredicto de veracidad (en inglés o en español).
E. NEVER ejecutar migraciones de esquema al arrancar un pod.
F. Ninguna: basta con lo que ya dicen el PRD y las prácticas.
X. Other (please specify)

**(Recomendada: A, B, C, D, E)**

[Answer]: B, C, E.  Para A, se puede contar con GPU para la presentación y algunas etapas de desarrollo, pero evitar aplicar para todo (la máquina de GPU no puedo usarla todo el tiempo).  D yo esperaría que la interfaz pudiera llegar a dar una opinión de veracidad, más no es obligatorio.  La idea es 
establecer un marco de verdad en lo que le hayan dicho al agente (si le dicen que los "elefantes vuelan", puede ser "falso" de principio, a menos que "elefantes" se refiera a aviones de gran tamaño.  El agente puede expresar sus dudas de veracidad, para que el usuario sepa y decida.

---

## Preguntas de seguimiento (contradicciones detectadas en las respuestas)

### Seguimiento 1 — Opinión de veracidad (respuesta 17, nota sobre D)

Tu nota pide que la interfaz pueda dar una «opinión de veracidad» (p. ej. «falso» para «los elefantes vuelan»).
AUTONOMIA-03 (bloqueante, `team.md`) y el PRD Principio 1(c) prohíben etiquetas automáticas de veracidad
(«falso», «miente», puntaje binario).

A. Se mantiene AUTONOMIA-03 tal cual. La IA califica cada **afirmación** frente al marco de verdad como «congruente», «incongruente» o «no documentada», con su CoT, como sugerencia editable que decide el analista. Nunca dice «falso», «verdadero» ni «miente» **(Recomendada)**
B. Se enmienda AUTONOMIA-03 y el PRD para permitir una **duda de veracidad graduada sobre la afirmación**, nunca sobre la persona. Sería una sugerencia editable con CoT, sin las palabras «falso» o «mentira» y sin puntaje binario.
C. Se enmienda AUTONOMIA-03 y el PRD para permitir la etiqueta «falso» sobre una afirmación que contradice el marco, como sugerencia que el analista confirma o descarta.
X. Other (please specify)

[Answer]: A

### Seguimiento 2 — Papel de la GPU (respuestas 8, 10 y 17-A)

El PRD (WON'T, Principio 2) y `project.md` dicen «sin GPU / 100 % en CPU».

A. **GPU opcional.** El sistema sigue funcionando completo en CPU. Se añade un perfil GPU opcional (una máquina con hasta 4 GPU) para la evaluación del Golden Dataset con modelos más grandes y para la demo. Las pruebas que la necesitan van en una etapa separada que se corre a demanda. Hay que ajustar el WON'T del PRD («GPU no requerida») y `project.md` **(Recomendada)**
B. **GPU requerida** para algunas funciones en la demo (p. ej. Whisper o el juez), con CPU solo para desarrollo. Cambia el Principio 2 del PRD.
C. Solo CPU: la máquina con GPU queda fuera del alcance de este trabajo.
X. Other (please specify)

[Answer]: A

### Seguimiento 3 — Los «32 GB» de la máquina con GPU

A. Son 32 GB de RAM del sistema; la memoria de las GPU se documenta aparte en Infrastructure Design.
B. Son 32 GB de memoria total de GPU (VRAM).
C. Son 32 GB de RAM del sistema y además conozco la VRAM (escríbela en `X`).
X. Other (please specify)

[Answer]: A

### Seguimiento 4 — Cómo llega la misma imagen a las dos máquinas (respuesta 12)

A. Se publican en **GHCR privado** etiquetadas por SHA, y cada máquina descarga exactamente la misma imagen. Se mantienen Trivy, el digest y el usuario sin root **(Recomendada)**
B. Se construyen localmente en cada máquina desde el mismo commit (`kind load`/equivalente), aceptando que los binarios pueden diferir.
X. Other (please specify)

[Answer]: A
