# Requisitos de rendimiento — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U8.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** Ya no hay extras que encender: la permutación del verificador está activa en todos los
  perfiles (P5 = A) y la aclaración no llama a ningún modelo (P4 = A). P1 = A de la revisión 1 (p95
  ≤ 150 s con extras) queda Superada.
- **IDs.** Se conservan; lo que sale queda «Retirado». Lo nuevo es NFR3.13.

**Insumos.**
- Flujos F4–F9 y §9 de `functional-design/functional-spec.md` (functional-spec); reglas BR5.1, BR5.8,
  BR5.12, BR5.15, BR6.1, BR6.2 y BR6.5 de `functional-design/rules.md` (rules).
- FR10.3, FR10.5, NFR2, NFR3 y NFR8 de `inception/requirements-analysis/requirements.md` (requirements).
- C1, C3, C6 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- Cifras que fijaron hoy U11 (p95 incremental ≤ 180 s con `comercial-piloto`, *N* = 300 s, plazo
  incremental de 900 s en la máquina de desarrollo, verificador local en CPU) y U4 (sondeo de 2 s y 15 s,
  ≤ 10 s del humo para U4, carga de `GET /sessions/{id}`).

Las metas se miden en la **máquina de desarrollo con CPU** (NFR2). Una prueba de rendimiento inestable se
arregla o se pone en cuarentena con un *issue*; nunca se reintenta ni se baja su umbral (`team.md`).

## 1. Costo de las aclaraciones en la biblioteca

| ID | Estado | Qué se mide | Objetivo | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | cambia | Latencia de la corrida incremental con la permutación activa y `comercial-piloto` | Cabe en la meta de U11: **p95 ≤ 180 s**. U8 no fija otra meta; la medición de BR6.5 (NFR3.13) la confirma y separa lo que cuesta la llamada permutada | Nivel 2 (reporte de BR6.5) |
| NFR3.2 | cambia | Costo del módulo de aclaraciones | **0 llamadas adicionales** a modelos (BR5.1) y **≤ 50 ms** para armar, validar y deduplicar las aclaraciones de una salida de 50 hallazgos con citas de 2 000 caracteres, con un margen de 3× para la CI | Nivel 0 (gateway *fake* que cuenta llamadas; pytest con tiempo medido) |
| NFR3.3 | cambia | Llamadas al verificador por candidato | Con `permutation: true`: exactamente 2 (`verificador` y `verificador_permutado`); con `false`: 1 (BR6.2, E42). La aclaración: 0 | Nivel 0 (trabajador con gateway *fake*) |
| NFR3.4 | Retirado | Ventana de la segunda lectura del juez | Sale con la segunda lectura (cambio 01) | — |
| NFR3.5 | Retirado | Límite del *prompt* de la pregunta | Sale con la pregunta sugerida (cambio 01) | — |

## 2. Plazo con la permutación

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.6 | cambia | La permutación cabe en el plazo incremental, también con `todo-local`. | Con `comercial-piloto`, la cuenta de U11 (juez más 2 llamadas por candidato) cabe en `run_deadline_incremental_s` (900 s en desarrollo); una corrida que lo pasa termina en `tiempo_agotado` sin hallazgos (functional-spec §9), nunca con un resultado parcial. Con `todo-local`, el criterio para mantenerla es NFR8.7 (`reliability-requirements.md`) y se mide en NFR3.13 (NFR-U8-01). Prueba de nivel 0 con reloj simulado: un plazo agotado en la llamada permutada da `tiempo_agotado` y 0 hallazgos |
| NFR3.7 | Retirado | Reclamo de pendientes con extras | Sale: el reclamo es de U4 y ya no depende de U8 |

## 3. Consola

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.8 | cambia | La decisión sobre una aclaración responde enseguida. | `POST /conductor-observations/{id}/decision` p95 ≤ **300 ms** con 100 decisiones sobre aclaraciones distintas, con el bloqueo sesión → fila (BR5.12). Prueba `perf` de nivel 1 en proceso con PostgreSQL real |
| NFR3.9 | cambia | Las aclaraciones no frenan el sondeo de la sesión. | `GET /sessions/{id}` con `since`: p95 ≤ **200 ms**; sin `since`: p95 ≤ **1 s** (las metas de U4), con la carga de U4 (2 000 turnos, 100 sugerencias, 20 corridas, 200 llamadas) más **100 aclaraciones** con sus decisiones y temas de 2 000 caracteres (NFR-U8-03). 200 sondeos. Prueba `perf` de nivel 1 |
| NFR3.10 | cambia | El panel aparece con el resultado de la corrida. | Desde el *commit* de la ingesta hasta que «Aclaración sugerida · requiere tu decisión» aparece en M4: **≤ 3 s** con corridas en curso (sondeo de 2 s de U4). Tras «Aprobar» o «Descartar», el panel muestra el nuevo estado con la respuesta `200`, sin esperar al sondeo. Playwright de nivel 3 con el *fake* de C17, y Vitest |
| NFR3.11 | Retirado | Latencia del indicio afectivo | Sale con US11.1 |

## 4. Prueba de humo

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.12 | cambia | La prueba de humo corre con la permutación activa y U8 no le resta tiempo. | `scripts/smoke.sh <url-base>` con *N* = 300 s (U11) contra los perfiles tal como están, con `permutation: true`. U8 no añade casos ni tiempo: el módulo cuesta ≤ 50 ms (NFR3.2) y las aclaraciones viajan en el mismo resultado. Antes de los casos, `frontend/e2e/smoke.spec.ts` comprueba que el perfil de la sesión declara la permutación activa y falla si no |

## 5. Costo de la permutación (BR6.5)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.13 | nuevo | B8 mide el costo de la permutación antes de fusionarse. | La CLI corre el conjunto sintético (40 entrevistas) en modo incremental con `todo-local` y con `comercial-piloto`, tal como están aprobados (con la permutación activa). El costo de la permutación se lee **por papel en la misma corrida** (NFR-U8-09): llamadas, *tokens* de entrada y salida y latencia p50 y p95 de `verificador_permutado` frente a `verificador` en el reporte C19, y la duración de cada corrida con y sin la suma de sus llamadas permutadas. El reporte da además la fracción de corridas terminadas sin `tiempo_agotado`. Se compara con NFR3.1, con NFR8.7 y con el 98 % de NFR8. Sin el reporte, el PR de B8 no se fusiona. Como el verificador es local en todos los perfiles (P1 = A de U11), las llamadas permutadas deben registrar `anonimizado: false` y un proveedor local, y no suman *tokens* ni costo comercial |

## 6. Recursos

U8 no añade procesos ni servidores. Sus topes se miden dentro de los de U4 y U11:

| Pieza | Presupuesto | Medición |
|---|---|---|
| Módulo de aclaraciones en `semantic-agent` o la CLI | ≤ 5 MiB adicionales sobre el pico de U4 (768 MiB en `semantic-agent`) con 50 hallazgos | Nivel 0 con `tracemalloc` |
| Ingesta de aclaraciones en el trabajador de `session-api` | Dentro de los 512 MiB de U4 con un `RunResult` de 2 MiB | Nivel 1 con el caso máximo |
| Servidor del verificador local con la permutación | Mismo servidor y ranura que la llamada directa; sin memoria extra | NFR8.3 (`scalability-requirements.md`) |
