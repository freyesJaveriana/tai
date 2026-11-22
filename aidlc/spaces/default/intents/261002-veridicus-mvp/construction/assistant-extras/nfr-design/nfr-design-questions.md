# Preguntas de NFR Design — U8 assistant-extras

**Unidad.** U8 `assistant-extras` (extras del asistente, apagados por defecto): permutación del orden
de lectura (segunda lectura del juez solo para las afirmaciones candidatas a alerta), pregunta sugerida
que el analista aprueba o descarta, e indicio afectivo con una lista versionada de palabras sin LLM.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D10 de
`nfr-requirements/`: el mismo juez de U4 con una sola ranura para la segunda lectura y la pregunta,
p95 ≤ 150 s por turno con los tres extras activos (humo y carga de NFR8 con los extras apagados), una
sola llamada para todas las candidatas, la CoT visible es la de la primera lectura, salida de la
pregunta con solo `text` (1–300 caracteres) y esquema estricto, *timeout* de la pregunta 60 s, plazo
base 600 s y reclamo de pendientes 480 s cuando hay extras activos, banderas solo en los *values* del
despliegue copiadas a cada sesión, decisión del analista con actualización condicional y disparador,
módulos guardia puros en `domain/` con 100 % de ramas. De U4 ya está diseñado el reintento acotado del
juez ante fallos pasajeros (P1 = A de su NFR Design). Quedan dos huecos de diseño en cómo se cruzan los
extras con ese reintento y con el plazo del turno.

---

## P1 — Si el reintento acotado del juez de U4 cubre también las llamadas de los extras

El NFR Design de U4 añadió, solo para la primera lectura, hasta 2 reintentos dentro del mismo
procesamiento (esperas de 2 s y 6 s con variación aleatoria) ante conexión rechazada o `502`, `503` y
`504`, y solo si el plazo del turno lo permite. Los requisitos aprobados de U8 dicen lo contrario para
sus llamadas: si la segunda lectura encuentra el juez caído, no se confirma el mensaje y el turno entero
vuelve por `XAUTOCLAIM` (reclamo de mensajes pendientes de Redis) a los 480 s, repitiendo también la
primera lectura (NFR10.12); y la pregunta sugerida se omite sin reintento (NFR10.13). Un reinicio breve
del juez justo entre las dos lecturas le suma así 8 minutos al turno, y el reintento vive en una pieza
común (`ModelGateway`, `libs/model_gateway`), así que hay que decidir a qué llamadas se aplica.

A. El mismo reintento acotado de U4 se aplica a la segunda lectura, con la misma comprobación del
   plazo; la pregunta sugerida sigue sin reintento: ante un fallo pasajero se omite con motivo
   `unavailable` y el turno se publica con sus alertas y su paquete. El reintento se activa por llamada,
   no para todo el `ModelGateway`. (Recomendada)
B. Una sola política para todas las llamadas al juez: el reintento acotado cubre la primera lectura,
   la segunda y la pregunta, siempre que el plazo lo permita.
C. Se mantiene lo aprobado: ningún reintento en las llamadas de U8; la segunda lectura cae al reclamo
   de 480 s y la pregunta se omite.
X. Other (please specify)

[Answer]: A **Mode:** guided
## P2 — Qué hace el evaluador si al turno no le queda plazo para la pregunta sugerida

La pregunta es la última llamada del turno y es opcional, pero el plazo (`deadline_at`) es del turno
entero: si vence mientras `semantic-agent` espera la pregunta, el barrido de plazos de U4 (cada 15 s)
marca el turno `turn.error.timeout` y se pierden también las alertas y el paquete ya válidos. Pasa sobre
todo tras un reclamo de pendientes (a los 480 s solo quedan 120 s de los 600 s del plazo base de un turno
sin cola) o cuando los reintentos ya consumieron tiempo.

A. Antes de pedir la pregunta, el evaluador comprueba que `ahora + 60 s` (su *timeout*) `+ 15 s` (un
   ciclo del barrido) `< deadline_at`; si no alcanza, no llama al juez y omite la pregunta con motivo
   `timeout`, y el turno se publica sin ella. La segunda lectura no lleva esta comprobación porque no es
   opcional cuando está activa. (Recomendada)
B. Sin comprobación: el plazo base de 600 s ya cubre la suma de 450 s de NFR3.6 (*embeddings* 30 s +
   juez 180 s × 2 + pregunta 60 s) y se acepta perder el turno en el caso raro.
C. El *timeout* de la pregunta se acorta al tiempo que queda (`deadline_at − ahora − 15 s`, con un
   mínimo de 10 s por debajo del cual se omite con motivo `timeout`), en vez de omitirla de entrada.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) diseñó tres extras apagados por defecto: segunda
lectura del juez, pregunta sugerida e indicio afectivo. El cambio 01 los retira. U8 pasa a entregar las
**aclaraciones neutras** deterministas (US10.3), sin ninguna llamada a un modelo, y la **permutación del
verificador activa en todos los perfiles** (US10.5, P5 = A). El Functional Design revisión 2 (F4–F9,
BR4.1–BR6.5, FD-U8-01 a FD-U8-11) y el NFR Requirements revisión 2 (tabla NFR-U8-01 a NFR-U8-09) ya están
aprobados.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| P1 y P2 de la revisión 1 | Pierden su objeto: ya no hay segunda lectura del juez ni pregunta sugerida, así que no hay reintento por llamada de U8 ni comprobación de plazo de la pregunta | Cambio 01; FD revisión 2 |
| Requisitos | NFR1.1–NFR1.2, NFR2.1–NFR2.2, NFR3.1–NFR3.13, NFR4.1–NFR4.6, NFR5.1, NFR6.1, NFR8.1–NFR8.7, NFR10.1–NFR10.17, NFR11.1–NFR11.5, NFR12.1–NFR12.2, NFR13.1–NFR13.2, NFR14.1, NFR15.1–NFR15.4 (con sus Retirado); decisiones D3, D8, D9 y D11–D14 | `nfr-requirements/`, revisión 2 |
| Aclaración sin modelo | La biblioteca la arma del `hecho` y la valida con cuatro reglas puras; la ingesta repite las reglas | P4 = A; BR5.1–BR5.9 |
| Permutación | Activa en todos los perfiles; se apaga en `todo-local` solo por PR si incumple el 98 % | P5 = A; NFR-U8-01 |
| Verificador | Local (gpt-oss-20b) en todos los perfiles actuales; `verifier_permuted` no sale del clúster | Decisión de U11 de hoy |
| Orden de bloqueo | `change_cursor.bump` de la sesión primero y después la fila | Regla de `project.md`; U4 |
| Sondeo | Una instantánea `REPEATABLE READ` con filas `change_seq > n` | Diseño de U4 de hoy |
| Métricas | En `contracts/metrics/<unidad>.v1.yaml`, con la lista cerrada de etiquetas de U1 | Diseño de U1 de hoy |
| Límites | El catálogo es el techo y `limits.exceeded` responde `413` | Diseño de U1 de hoy |
| Auditoría | Marca en el `COMMENT` de la tabla y permisos por marca (`history`, `mutable`, `purgeable`) | Diseño de U3 de hoy |

## Cómo se registra la revisión

- Los seis documentos y `traceability.json` pasan a la revisión 2 en el mismo archivo, con una nota de
  cabecera que dice qué cambia. La revisión 1 queda en el historial de Git.
- Las secciones conservan su número cuando su tema sigue; las que salen quedan «Retirado» sin renumerar y
  lo nuevo toma números nuevos.
- Las precisiones a artefactos aprobados van en la tabla NFRD-U8-xx de `security-design.md` §9. Ningún
  original se edita.

## Lo que el diseño resolverá sin preguntar

1. **Hallazgos de la revisión 1 de esta etapa.** R-01, R-02, R-03 y R-05 desaparecen con los extras. R-04
   (el disparador no exigía el estado final ni quién y cuándo) se cierra con un disparador que exige el
   estado final y un disparador diferido que exige la fila de historial.
2. **Sondeo.** Las dos tablas de U8 llevan `change_seq`, y se pide a U4 que su lectura incremental las
   incluya.
3. **Índice único.** El índice único usa el SHA-256 de `tema_key`, porque un tema largo no cabe en una
   entrada de índice de PostgreSQL.
4. **Tope del cuerpo de la decisión.** Se reutiliza `review_body_max_bytes`, que ya está en C25, sin cifra
   nueva.
5. **Formas de los reportes de nivel 2.** Los reportes C19 v2 llevan la sección `clarifications`, y el
   resumen usa un esquema cerrado de solo números.
6. **Prueba de humo.** Comprueba la permutación en el registro de llamadas, porque la vista de la sesión no
   expone el perfil.

Ningún punto cambia el alcance ni el riesgo, ni deja salir del clúster algo que hoy no sale.

**Sin preguntas: todo lo fijan las fuentes.** Es una segunda pasada sin conflicto real entre fuentes
aprobadas (regla de `project.md`).