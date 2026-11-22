# Requisitos de fiabilidad — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U8.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Se conservan; lo que sale queda «Retirado». Lo nuevo es NFR4.6 y NFR10.17.

**Insumos.**
- Flujos F4–F9, máquina de estados de §3 y §9 «Errores y bordes» de `functional-design/functional-spec.md`
  (functional-spec); reglas BR5.1–BR5.17 y BR6.1–BR6.5 de `functional-design/rules.md` (rules).
- NFR4, NFR6, NFR8 y NFR10 de `inception/requirements-analysis/requirements.md` (requirements) y VE-05 de
  `requirements-adenda-02.md`.
- C1, C3, C6, C16 y C19 de `inception/contract-design/contract-summary.md` (contract-summary).
- Lo que fijaron hoy U11 (permutación en todos los perfiles, 98 % de corridas completas, 40 muestras ×
  3 corridas, consistencia > 65 %) y U4 (ingesta en una transacción, orden sesión → fila).

## 1. Objetivos

Ningún MUST depende de U8. Su objetivo de fiabilidad es **no romper la corrida ni la ingesta**: una
aclaración que no pasa se quita sin tocar los hallazgos, y un fallo del propio módulo es un fallo de la
biblioteca, nunca una salida parcial.

| ID | Estado | Objetivo | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.6 | cambia | La prueba de humo no falla por U8. | 0 fallos atribuibles a U8 en cada corrida de `scripts/smoke.sh` con la permutación activa (NFR3.12) | Nivel 3 |
| NFR8.7 | cambia | Las corridas con la permutación terminan. | En la medición de BR6.5 (NFR3.13), el 100 % de las corridas termina `done` o `error` con un `code` del catálogo. Con `todo-local`, al menos el **98 %** de las corridas incrementales termina sin `tiempo_agotado` dentro de `run_deadline_incremental_s`; si no, la permutación se apaga en `todo-local` por PR (NFR-U8-01) | Nivel 2 |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.11 | cambia | Toda E/S nueva de U8 tiene *timeout* explícito. | El módulo de aclaraciones no hace E/S (prueba de nivel 0 con `open` y `socket` sustituidos por funciones que fallan). La decisión y la ingesta usan los *timeouts* de PostgreSQL de U4 (sentencia ≤ 2 s). La llamada permutada usa `model_call_timeout_s` de U11, sin plazo propio | Nivel 0 y nivel 1 |
| NFR10.12 | Retirado | Fallos de la segunda lectura del juez | Sale con la segunda lectura; los fallos del verificador son de U11 | — |
| NFR10.13 | cambia | Una aclaración que no pasa nunca rompe la corrida, y un fallo del módulo nunca da una salida parcial (BR5.7, functional-spec §9). | (a) Con una salida de dos hallazgos donde la aclaración de uno falla cada regla, salen los dos hallazgos y la otra aclaración, `estado: ok`, y se emite un evento de descarte por regla. (b) Con el módulo forzado a lanzar una excepción, la CLI termina con código 5 y el trabajador publica la corrida en `analysis.system`, sin hallazgos ni aclaraciones. (c) Modo final y `estado: error` no traen el campo (BR5.2, E12, E13) | Nivel 0 |
| NFR10.14 | cambia | La configuración de U8 se valida al arrancar. | `semantic-agent` y la CLI cargan la regla de aclaración neutra de C8 con el cargador seguro de U1; si falta, no valida o tiene una versión desconocida, la CLI termina con código 3 y `semantic-agent` no pasa `/readyz` (`503`, C16). La validación de perfiles de U11 rechaza un archivo inválido; la prueba de BR6.1 corre en la CI | Nivel 0 y nivel 1 |
| NFR10.15 | cambia | La decisión es atómica y concurrente sin pérdidas (BR5.12, BR5.13). | En una transacción: `change_cursor.bump` de la sesión, `SELECT … FOR UPDATE` de la aclaración (orden sesión → fila), comprobación del estado, cambio de `status` e inserción del historial. Dos decisiones simultáneas dan una `200` y una `409`, con una sola fila de historial (E31). Un corte de conexión antes de confirmar deja `proposed` y 0 filas | Nivel 1 |
| NFR10.16 | cambia | La consola sobrevive a un fallo al decidir. | Si `POST /conductor-observations/{id}/decision` falla por red o `5xx`, el panel conserva la aclaración pendiente, muestra el mensaje del catálogo y deja «Aprobar» y «Descartar» activos; ante un `409`, muestra su mensaje (functional-spec §6) y se actualiza con el siguiente sondeo | Vitest con un servidor *fake* |
| NFR10.17 | nuevo | La ingesta de aclaraciones es atómica e idempotente (BR5.10). | Las aclaraciones se insertan en la misma transacción de la ingesta, con el orden sesión → fila. Dos corridas con la misma aclaración dan una fila; el reintento de una corrida (`attempt` + 1) da una fila; el resultado de una corrida cancelada o vencida da 0 filas; un fallo forzado a mitad da 0 filas y el mensaje queda pendiente (E25, E26) | Nivel 1 |

## 3. Calidad de la IA con U8

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR4.1 | cambia | Por el camino del producto, la permutación solo quita hallazgos (BR6.2, AUTONOMIA-05). | Prueba de propiedad (Hypothesis) del trabajador con un verificador *fake* que decide al azar por orden: el conjunto de hallazgos con permutación está contenido en el de sin permutación, y todo candidato confirmado en un solo orden queda como `rechazado_permutacion`. Control negativo: un verificador que confirma en los dos órdenes deja salir el hallazgo | Nivel 0 |
| NFR4.2 | cambia | La permutación queda registrada (BR6.3). | Con `permutation: true`, el 100 % de los candidatos verificados tiene dos llamadas en el registro (`verificador` y `verificador_permutado`) y `GET /runs/{run_id}/model-calls` las devuelve con su papel (E43) | Nivel 1 |
| NFR4.3 | cambia | **0 %** de las aclaraciones emitidas contiene texto de una cita (FR10.3, AC10.3.2, BR5.17). | Por entrevista del conjunto sintético, una corrida de la CLI en modo incremental de todos los turnos; una comprobación independiente busca cada fragmento de cita en cada tema emitido: **0 coincidencias**, y 0 de C8 y de la regla de DT23 (NFR10.5). **Bloquea** los PR que tocan la aclaración o la IA y toda entrega etiquetada. Control negativo: un tema sembrado con una cita en un *fixture* hace fallar la comprobación | Nivel 2 y nivel 0 |
| NFR4.4 | cambia | Consistencia de la permutación. | La consistencia > 65 % al invertir el orden y la permutación en el 100 % de las consultas *offline* las mide la evaluación de U11 (40 muestras × 3 corridas). U8 no mide una tasa propia: adjunta ese reporte al PR de B8 y comprueba que su diff no toca el código de la permutación (BR6.4) | Nivel 2 y revisión del PR |
| NFR4.5 | cambia | Las aclaraciones son deterministas. | Prueba de propiedad: la misma salida da siempre las mismas `observaciones_conductor`, en el mismo orden. La CLI y el trabajador dan las mismas aclaraciones con la misma entrada incremental (BR5.1) | Nivel 0 |
| NFR4.6 | nuevo | La tasa de aclaraciones descartadas por regla se reporta. | Tasa = descartadas / (emitidas + descartadas), sobre el conjunto sintético, desde la sección `clarifications` de C19 v2. **No bloquea.** Por encima de **0,50**, la revisión humana del PR nombra la cifra y decide (NFR-U8-02). El reporte da también el conteo por regla a partir de los eventos de descarte | Nivel 2 |
| NFR6.1 | cambia | La permutación no cambia el texto que ve el analista. | Un hallazgo que sobrevive a la permutación conserva el `hecho`, el `tipo`, las citas y las `observaciones` de la llamada del juez: la prueba del trabajador compara la salida con y sin permutación cuando el verificador confirma en los dos órdenes (iguales salvo el registro). La calificación Likert de NFR6 vale así con la permutación activa | Nivel 0 |

## 4. Recuperación y degradación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Todas las aclaraciones de una corrida no pasan | Las aclaraciones de esa corrida | Nada que recuperar: la corrida sigue `ok` con sus hallazgos (NFR10.13) |
| Excepción en el módulo de aclaraciones | La corrida | `analysis.system` o código 5; el humano reintenta la corrida (reintento de U4) |
| La regla de aclaración neutra no carga | Nada; el servicio no arranca | `/readyz` en `503` hasta corregir por PR (NFR10.14) |
| Caída de PostgreSQL al ingerir | Nada | La transacción revierte y el mensaje vuelve por la cola de U4 (NFR10.17) |
| Caída de PostgreSQL al decidir | La decisión | La aclaración sigue `proposed`; el analista decide de nuevo (NFR10.16) |
| Plazo agotado en la llamada permutada | Los hallazgos de esa corrida | `tiempo_agotado` sin hallazgos (NFR3.6); el humano reintenta |

Una aclaración que el analista no decide se queda `proposed`: no bloquea la consolidación y no entra en el
reporte (BR5.14).
