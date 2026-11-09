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

---

## Segunda pasada (cambio 01, DT27, y adenda 02) — 2026-11-09

Las respuestas P1–P9 siguen vigentes salvo donde el cambio las supera: la regla «la primera unidad del
plan es el flujo de texto» quedó superada (`project.md`, cambio 01), U10 pasó a MUST, entraron U11
(analizador), U12 (reportes del investigador) y U13 (ética, demostración), y la tarea previa P0.2
(Golden Dataset con escenario) ya no tiene objeto en su forma anterior. Se mantiene un Bolt por unidad
(P9 = B) y etapa por etapa (P8 = A).

Un **Bolt** es una pasada de construcción sobre una unidad que termina en algo que corre y se puede
demostrar. Los ID B1–B9 conservan su número; B10 (antes condicional) pasa a ser el anonimizador MUST y
los Bolts nuevos toman el número de su unidad (B11–B13).

Solo se pregunta lo que el cambio, el grafo (`unit-of-work-dependency.md`) y `team.md` no deciden ya.

### Pregunta 10 — Orden de la primera rebanada de valor

`team.md` fija que la primera rebanada es la biblioteca del analizador con su CLI, el anonimizador como
módulo y un proveedor comercial. El grafo obliga a que U10 vaya antes que U11 (ModelGateway pasa por el
anonimizador ante todo destino externo).

A. **B1 Contratos (U1) → B10 Anonimizador (U10: módulo de `libs/` y proceso `anonymizer-proxy`) → B11
Analizador (U11: biblioteca, CLI, proveedor comercial y uno local)**; un Bolt por unidad
**(Recomendada)**
B. Igual, pero U10 en dos Bolts: el módulo de `libs/` antes de B11 y el proceso `anonymizer-proxy` junto
a la plataforma (B4), cuando ya hay clúster (rompe «un Bolt por unidad»)
C. B1 → B11 solo con perfil local y B10 después (el analizador no admite destino externo hasta que
exista el anonimizador; la primera rebanada queda sin proveedor comercial)
X. Other (please specify)

[Answer]: A

### Pregunta 11 — Orden después de la primera rebanada

La demo de la sesión 16 (PRD S13: cargar una transcripción sintética, elegir el perfil, ver los
hallazgos con sus dos citas, consolidar y descargar el reporte) necesita U3, U4, U2, U5 y U7.

A. **B2 Acceso (U3) → B3 Flujo de texto (U4) → B4 Plataforma (U2) → B5 Revisión humana (U5) → B6
Reporte (U7) → B12 Reportes del investigador (U12) → B7 Ciclo de vida (U6) → B13 Ética (U13)**: la demo
queda completa en B6, U12 sirve después al TG y U13 (demostración) cierra las MUST
**(Recomendada)**
B. Igual, pero B12 justo después de B3: la consola del investigador solo necesita U3 y U4 y sirve antes
al TG, a costa de retrasar la plataforma y la demo
C. B4 Plataforma justo después de B11, antes de la consola: `anonymizer-proxy`, `NetworkPolicy` y
Secrets (módulo 7) quedan en el clúster desde el principio, a costa de retrasar la consola
X. Other (please specify)

[Answer]: A

### Pregunta 12 — Tareas previas al primer Bolt

P0.1 (configuración de GitHub) sigue igual. P0.2 era el Golden Dataset con escenario y Hecho No
Documentado, que salieron con el cambio 01. El conjunto sintético de contradicciones internas
(US12.3) es de U11.

A. **Retirar P0.2**: el conjunto sintético y su arnés se construyen dentro de B11, como tareas del plan
de U11 (generado con un modelo comercial de otra familia que el juez, solo datos sintéticos)
**(Recomendada)**
B. Mantener P0.2 reescrita como «conjunto sintético de contradicciones internas», antes de B11, para que
B11 mida desde su primera tarea
X. Other (please specify)

[Answer]: A

### Pregunta 13 — Línea de corte y qué se recorta primero si falta tiempo

U8 y U9 son SHOULD y van después del corte (P5). Ninguna prueba ni umbral se rebaja en ningún caso.

A. **El corte va después de B13. Si el calendario no alcanza, se recorta en este orden: B13
(demostración) → las partes SHOULD/COULD de B4 y B7 → el alcance de B7**; nunca B1, B10, B11 ni la demo
(B2–B6) **(Recomendada)**
B. El corte va después de B6 (la demo): B12, B7 y B13 son MUST, pero se construyen después de la
sustentación si hace falta
C. Igual que A, pero B12 se recorta antes que B13
X. Other (please specify)

[Answer]: A

### Pregunta 14 — Dependencias externas a las que hacer seguimiento

Varias letras separadas por comas.

A. Calendario del curso (módulos 6–8 y sesión 16)
B. Cuenta y clave de API del proveedor comercial de la primera rebanada (Secret que crea el humano y
costo por corrida)
C. Clúster ZINE (cola SLURM y nodos `ingsistemas`; los `sbatch` los lanza el humano)
D. Descarga de modelos locales con revisión y `sha256` fijados (juez, verificador de otra familia,
Whisper y TTS)
E. Configuración de GitHub (P0.1)
F. Máquina GPU opcional
X. Other (please specify)

**(Recomendada: A, B, C, D, E)**

[Answer]: A, B, C, D
