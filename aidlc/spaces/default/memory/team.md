# Team-Level Rules

> This team's affirmed practices and corrections. Loaded after `org.md` as
> strict-additive guidance; contradictions with broader policy are rejected.
> Populated by the practices-discovery affirmation gate. Edit at the gate,
> not directly.

## Way of Working

<!-- Affirmed during practices-discovery. Example: -->
<!-- We use GitHub Flow with feature branches. Branches live 3-5 days max. -->
<!-- Hotfixes branch from main and merge back via expedited review. -->

## Walking Skeleton

<!-- Affirmed during practices-discovery. Example: -->
<!-- We don't run a walking skeleton — our deployment pipeline is mature -->
<!-- and the slice cost outweighs the value at our maturity stage. -->

## Testing Posture

<!-- Affirmed during practices-discovery. Example: -->
<!-- We use BDD. Specifications drive scenarios; scenarios drive code. -->
<!-- Each Unit ships with feature files in /features/. -->

## Guard Policy

<!-- Affirmed by the team. Mode: strict, relaxed, or off. Strict here holds for every intent and cannot be changed from chat. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

<!-- Affirmed during practices-discovery. -->

## Code Style

<!-- Team-specific conventions beyond the linter. Example: -->
<!-- - Prefer named exports over default exports -->
<!-- - All async functions return Result<T, E>, never throw -->

## Forbidden

- **AUTONOMIA-01:** NEVER incluir en un plan de tareas un paso que ejecute `kubectl apply`, `helm install`, `helm upgrade`, `terraform apply`, una migración de esquema sobre la base del clúster o equivalente sin un paso previo de aprobación humana registrada; el destino es un PR con evidencia, nunca un cambio directo.
- **AUTONOMIA-02:** NEVER aceptar criterios de aceptación de opinión («funciona correctamente», «es usable», «tiene buen rendimiento») sin un comando o umbral medible.
- **AUTONOMIA-03:** NEVER producir una etiqueta automática de veracidad sobre el compareciente («mentiroso», «falso», «miente», puntaje binario de verdad) ni consolidar el reporte forense final sin la validación explícita de un analista humano.
- **AUTONOMIA-04:** NEVER enviar fuera del clúster local audio crudo, transcripciones sin anonimizar, nombres de víctimas o identificadores reales del proceso.
- **AUTONOMIA-05:** NEVER generar una alerta ni una pregunta automática cuando la similitud recuperada está por debajo del umbral configurado.
- **Proceso:** NEVER escribir código de aplicación en este trabajo: el flujo se detiene en la Parte 1 (plan de tareas) de Code Generation de cada unidad y nunca se responde `Approve Plan`.
- **Proceso:** NEVER elegir ni proponer autonomía en Construction («Continue automatically»).

## Mandated

- **Fuente:** las reglas AUTONOMIA-01..05 vienen de `docs/limite-autonomia.md` (PRD Segmento 6). Son bloqueantes: si una etapa no cumple un criterio, la única salida es «Request Changes», y cada verificación se cita por su ID.
- **AUTONOMIA-01:** ALWAYS que una tarea toque un entorno compartido (clúster, base CloudNativePG, nube), su salida es un artefacto revisable (manifiesto, chart, script de migración, PR) precedido de aprobación humana.
- **AUTONOMIA-02:** ALWAYS que cada tarea de cada unidad nombre el comando, la prueba o la comprobación que demuestra que terminó.
- **AUTONOMIA-03:** ALWAYS modelar todo hallazgo de la IA como «sugerencia de revisión» con estado editable (pendiente / aceptada / editada / descartada) cambiado por un humano; la consolidación del reporte exige una acción explícita del analista que registra quién y cuándo; existe al menos una prueba automatizada que falla si la salida de la IA o la interfaz contiene una etiqueta de veracidad binaria.
- **AUTONOMIA-04:** ALWAYS declarar en el diseño, para cada componente, si corre dentro o fuera del clúster y qué datos cruzan esa frontera; toda integración con un servicio externo incluye una prueba de que el payload saliente pasó por el anonimizador; existe una tarea que produce la `NetworkPolicy` que niega salida a internet a los pods con datos sin anonimizar (como artefacto revisable).
- **AUTONOMIA-05:** ALWAYS que una alerta de incongruencia tenga como campos obligatorios fragmento de transcripción, cita del documento, ID del documento y traza CoT (una alerta sin ellos se rechaza); el umbral de similitud es configurable y existe una prueba que, por debajo del umbral, verifica que no se emite alerta ni pregunta y sí el «Hecho No Documentado» con el Paquete de Contexto de Traspaso.
- **Proceso:** ALWAYS una aprobación humana por etapa; en Construction, ALWAYS «Review each checkpoint».

## Corrections

<!-- Self-learning loop appends here. -->
