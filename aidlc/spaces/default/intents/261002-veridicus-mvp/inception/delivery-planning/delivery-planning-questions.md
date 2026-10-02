# Preguntas — Planificación de entregas (Veridicus)

Esta etapa ordena el trabajo de Construction en **Bolts**. Un Bolt es una pasada de construcción
sobre una o varias unidades de trabajo que termina en algo que funciona y se puede demostrar, con su
definición de terminado y lo que su entrega nos enseña. Salen cuatro documentos: el plan de Bolts
(`bolt-plan.md`), quién ejecuta cada Bolt (`team-allocation.md`), por qué este orden
(`risk-and-sequencing-rationale.md`) y qué depende de algo externo (`external-dependency-map.md`).

Ya están decididos y no se vuelven a preguntar:

- La **primera unidad del plan es el flujo de texto** de punta a punta (`text-flow`, U4): cargar el
  escenario → ingresar un testimonio en texto → consultar `pgvector` → mostrar la alerta con su CoT. La
  voz se agrega solo cuando ese flujo funciona (team-practices, Walking Skeleton).
- **No hay ceremonia de esqueleto andante** (`skeleton: off` en el scope `classic`).
- Somos un equipo de una persona con agentes de IA: no se trabaja en varias unidades a la vez, y todos
  los Bolts los ejecuta el agente desarrollador con el autor como revisor (team-practices; Team
  Formation no se ejecutó en este scope).
- Cada Bolt entra a `main` como **un PR con evidencia y squash-merge**, en una rama
  `<tipo>/<slug-del-bolt>` (team-practices).
- Antes de cualquier desarrollo va la **tarea conjunta de configuración de GitHub** (protección de
  `main`, CI obligatoria, GHCR privado, *deploy key*, Dependabot) validada con un PR de prueba
  (team-practices).
- El grafo de dependencias entre unidades (`unit-of-work-dependency.md`) está aprobado: `contracts` →
  `identity-access` → `text-flow` → (`human-review`, `session-lifecycle`, `assistant-extras`,
  `anonymizer`); `human-review` → `forensic-report`; `assistant-extras` → `voice`; `platform` solo
  depende de `contracts`.
- Este trabajo **no escribe código**: se detiene en la Parte 1 (plan de tareas) de Code Generation de
  cada unidad. El plan de Bolts ordena esos planes de tareas y la construcción posterior del autor.
- Los Bolts siguen los **módulos 6–8 del curso** y la sustentación de la sesión 16; los módulos 4–5 ya
  pasaron (`docs/coherencia-insumos.md`, PRD S13).

## Cómo responder

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es mi propuesta; no está aplicada todavía.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

### Pregunta 1 — ¿Cómo se arma el primer Bolt?

El flujo de texto (U4) depende de los contratos (U1: mensajes de la cola, esquemas del juez y de la
alerta, vocabulario prohibido, OpenAPI) y del inicio de sesión con roles (U3), porque toda ruta de la
consola exige token y rol. Por eso el «primer Bolt = flujo de texto» obliga a construir antes, o junto,
esas dos unidades.

A. **Un solo Bolt «flujo de texto» con U1 + U3 + U4.** Su definición de terminado es el flujo de texto
de punta a punta con inicio de sesión, más la evaluación de nivel 2 sobre el Golden Dataset. Es el Bolt
más grande del plan, pero es el único que prueba de verdad que la arquitectura funciona
**(Recomendada)**
B. Tres Bolts seguidos: «contratos» (U1), «acceso» (U3) y «flujo de texto» (U4). Cada uno es más
pequeño, pero los dos primeros no se pueden demostrar a un analista.
C. Dos Bolts: «contratos y acceso» (U1 + U3) y luego «flujo de texto» (U4).
X. Other (please specify)

[Answer]: B

> Cambiada de A a B en el cierre de la etapa: el autor decidió «un solo commit por Bolt; la unidad es
> lo suficientemente precisa» (ver Pregunta 9).

### Pregunta 2 — ¿Dónde va la plataforma (U2)?

La plataforma son los charts y manifiestos: CloudNativePG con `pgvector`, Redis, servidores locales de
modelos, la `NetworkPolicy` de salida denegada (AUTONOMIA-04), Secrets por referencia, el `Job` de
migraciones, las políticas de manifiestos y `scripts/smoke.sh`. Las pruebas de niveles 0 y 1 no la
necesitan (usan contenedores), pero el despliegue en el clúster y la prueba de humo sí. Además trae
partes SHOULD/COULD del módulo 8 (Argo CD, regla AIR en Prometheus/Grafana, KEDA). Una unidad no se
puede repartir entre dos Bolts.

A. **Segundo Bolt, justo después del flujo de texto**: el flujo de texto corre en el clúster con la
prueba de humo y la `NetworkPolicy` durante los módulos 6–7. Las partes SHOULD/COULD (Argo CD, AIR,
KEDA) quedan como las últimas tareas del plan de U2, marcadas para el módulo 8 **(Recomendada)**
B. Dentro del primer Bolt, para que el flujo de texto nazca desplegado en el clúster (primer Bolt aún
más grande).
C. Al final, después de todas las unidades de aplicación MUST, en el módulo 8.
X. Other (please specify)

[Answer]: A

### Pregunta 3 — ¿En qué orden van las demás unidades obligatorias?

Después del flujo de texto y de la plataforma quedan tres unidades MUST:
- revisión humana (U5): aceptar, editar o descartar sugerencias;
- reporte forense (U7): finalizar, consolidar con SHA-256 y descargar; depende de U5;
- ciclo de vida de la sesión (U6): versión nueva de escenario, pegar una transcripción completa, lista
  de sesiones y reanudación tras una interrupción.

La demostración de la sustentación termina con la descarga del reporte consolidado (PRD S13, paso 5),
así que necesita U5 y U7; no necesita U6.

A. **U5 → U7 → U6**: primero se completa la historia de la demostración (revisar y consolidar), luego
lo que la hace robusta (reanudar, pegar transcripciones) **(Recomendada)**
B. U6 → U5 → U7: primero lo que completa la sesión, al final el reporte.
C. U5 → U6 → U7.
X. Other (please specify)

[Answer]: A

### Pregunta 4 — ¿Puntuamos los Bolts con un modelo formal?

WSJF (*Weighted Shortest Job First*) ordena por (valor + urgencia + reducción de riesgo) ÷ tamaño.
Aquí el orden ya lo fijan casi del todo las reglas del equipo, el grafo de dependencias y la
demostración de la sustentación.

A. **No**: el documento de razones explica el orden con argumentos explícitos (regla del flujo de
texto, demo de la sustentación, módulos del curso, riesgos del PRD S12) y muestra que respeta el grafo
**(Recomendada)**
B. Sí, WSJF con pesos iguales, como tabla de apoyo al razonamiento.
C. Sí, WSJF con más peso al riesgo.
X. Other (please specify)

[Answer]: A

### Pregunta 5 — ¿Qué hacemos con las unidades SHOULD y COULD?

Son: extras del asistente (U8, SHOULD/COULD: pregunta sugerida, confirmación en ambos órdenes,
indicio afectivo), voz (U9, SHOULD: grabar un turno y escuchar la pregunta; depende de U8) y
anonimizador (U10, COULD: solo si se decide usar un modelo externo). Ninguna MUST depende de ellas.

A. **Se planifican después de todas las MUST, con una línea de corte explícita**: ningún Bolt SHOULD
empieza hasta que los Bolts MUST pasan su definición de terminado. Orden: U8 → U9. U10 queda fuera del
plan mientras no se decida usar un modelo externo, y se documenta cómo entraría **(Recomendada)**
B. Igual que A, pero U10 entra como último Bolt del plan aunque no haya modelo externo.
C. Solo se planifican las MUST; las SHOULD/COULD se listan aparte sin orden.
X. Other (please specify)

[Answer]: A

### Pregunta 6 — ¿Cómo y cuándo se produce el Golden Dataset?

La evaluación de nivel 2 del flujo de texto (definición de terminado del primer Bolt) necesita el
Golden Dataset: un escenario sintético, 10 transcripciones (4 alineadas y 6 con discrepancias
sembradas) y el caso de Hecho No Documentado (`docs/coherencia-insumos.md`, H18). Para evitar la fuga
de preferencias, el juez local debe ser de otra familia de modelos distinta de la que generó los datos
(PRD S11 §3, NFR5). Nadie ha decidido todavía quién lo genera ni cuándo.

A. **Lo genera el autor con un modelo comercial de otra familia** (p. ej., por API de un proveedor),
solo con datos sintéticos, lo revisa a mano y lo versiona en `evaluation/` como **tarea previa del
primer Bolt**; el reporte de evaluación declara la familia del generador **(Recomendada)**
B. Lo escribe el autor a mano, sin modelo, como tarea previa del primer Bolt.
C. Lo genera un modelo local de otra familia, dentro del primer Bolt.
X. Other (please specify)

[Answer]: A

### Pregunta 7 — ¿Qué más de fuera puede frenarnos?

Dependencias externas que veo en los insumos (selecciona todas las que apliquen; las que no marques
quedan como riesgo bajo sin seguimiento):

A. El **calendario del curso**: módulos 6, 7 y 8 y la sustentación de la sesión 16.
B. El **par del curso** que califica la CoT en escala Likert (NFR6) y su disponibilidad antes de la
sustentación.
C. La **máquina GPU** opcional para el perfil GPU de evaluación y el ensayo de la demo.
D. La **descarga de los modelos** (juez, *embeddings*, Whisper, TTS) con revisión fijada y `sha256`,
y su tamaño frente al disco y la memoria de la máquina CPU.
E. La **configuración de GitHub** (protección de `main`, GHCR privado, *deploy key*) que bloquea todo
desarrollo hasta validarse.
X. Other (please specify)

(select all that apply) **(Recomendada: A, B, C, D, E)**

[Answer]: A, C, D, E

### Pregunta 8 — ¿En qué orden recorre Construction las unidades?

Hoy el flujo está en **unidad por unidad**: cada unidad pasa por diseño funcional, NFR, diseño de
infraestructura y plan de tareas antes de que empiece la siguiente. Tu `plan-aidlc.md` (Paso 4) pide
**etapa por etapa**: todas las unidades pasan por cada etapa de diseño (3.1 a 3.4) antes de que alguna
llegue al plan de tareas, para que la primera unidad no se quede detenida en su plan sin aprobar y
bloquee el diseño de las demás. En ambos casos el trabajo es en serie, una unidad a la vez, y revisas
cada etapa.

A. **Etapa por etapa** (todas las unidades en cada etapa de diseño antes del plan de tareas), como dice
`plan-aidlc.md` **(Recomendada)**
B. Unidad por unidad (lo que está registrado hoy).
X. Other (please specify)

[Answer]: A

---

## Seguimiento

### Pregunta 9 — ¿Cómo entra a `main` un Bolt de varias unidades?

Al cruzar las respuestas apareció una contradicción:

- **P1 = A**: el primer Bolt junta contratos, acceso y flujo de texto (U1 + U3 + U4), el más grande
  del plan (U4 es tamaño XL).
- **team-practices (Way of Working)**: ramas cortas de **1–2 días** y «cada Bolt queda como **un
  commit** en `main`» (un PR con squash por Bolt).
- **U1 (`unit-of-work.md`)**: «cada cambio de contrato entra por **su propio PR**».

Un Bolt de tres unidades no cabe en una rama de 1–2 días ni en un solo PR, y los contratos exigen PR
aparte. Hay que elegir qué cede.

A. **El Bolt es un grupo de entrega, no un PR**: dentro de cada Bolt, cada PR corto (≤ 2 días) cubre
una tarea o un grupo pequeño de tareas del plan de una unidad, con squash; los cambios de contrato van
en su propio PR; el Bolt cierra cuando el último PR fusionado cumple su definición de terminado. La
regla «un Bolt = un commit» se precisa como «un PR = un commit» y se propone registrarla como
corrección del proyecto en el cierre de esta etapa **(Recomendada)**
B. Volver a P1 = B (un Bolt por unidad) y aceptar que cada Bolt sea un PR grande, aunque supere los 2
días; los contratos siguen en PR aparte.
C. Mantener «un Bolt = un PR = un commit» con una rama larga para el primer Bolt (rompe la regla de
1–2 días).
X. Other (please specify)

[Answer]: B

> Cambiada de A a B en el cierre de la etapa, al revisar el aprendizaje que contradecía `org.md`
> («Each Bolt becomes one commit on the trunk»). Respuesta del autor, literal: «Dejémoslo como un solo
> commit por Bolt. La unidad es lo suficientemente precisa.» Confirmado: un Bolt por unidad.
