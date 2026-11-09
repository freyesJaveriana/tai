# Preguntas de Functional Design — U1 contracts

**Unidad.** U1 `contracts` (tipo `spec`): contratos versionados en `contracts/` y sus pruebas de
validación con *fixtures*; ningún comportamiento (`unit-of-work.md`). Respalda AC2.2.3, US3.2
(AC3.2.1, AC3.2.4), AC5.5.3, AC5.5.4 y AC8.3.1 (`unit-of-work-story-map.md`, `bolt-plan.md` B1).

**Lo que ya está decidido y no se vuelve a preguntar.** Las formas de C1–C16, la versión semántica por
contrato con `schema_version` en cada mensaje, `additionalProperties: false` en C6 y C7, el enum de
tres calificaciones, los cuatro campos obligatorios de la alerta, el catálogo único de `code`, la
ausencia de rutas que escriban el umbral y los datos solo sintéticos (`contract-summary.md`,
`requirements.md`, `stories.md`, team-practices). Solo quedan los cuatro huecos de abajo.

---

## P1 — Cómo reconoce el escaneo una cita literal dentro de la CoT

La lista de vocabulario prohibido (C8) excluye las citas literales del testimonio y del escenario
(AC5.5.1, AC5.5.2), pero la CoT es texto libre y la regla de que una CoT con vocabulario prohibido
fuera de las citas es salida inválida (AC3.2.4) necesita saber dónde empieza y termina una cita. Esto
fija la regla del contrato C8 (y, en la opción C, la forma de C6).

A. Una cita es el texto entre comillas angulares «…», y solo cuenta como cita si aparece **literal** en
   el fragmento del turno o en uno de los pasajes recuperados; si no aparece, se escanea como texto
   normal (así «miente» entre comillas inventadas no pasa). (Recomendada)
B. Todo texto entre «…» o "…" se excluye del escaneo, sin comprobar que sea literal.
C. Cambiar C6: la CoT no puede llevar citas; las citas van solo en campos separados del juez y la CoT
   se escanea completa.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Lista inicial de vocabulario prohibido

La lista aprobada de C8 tiene 9 términos (mentiroso, mentirosa, miente, mintió, falso, falsa,
verdadero, verdadera, engaño). Como el escaneo es por palabra completa, una flexión que no esté en la
lista no se detecta (por ejemplo «mienten» o «falsedad»). La lista es la base de la prueba guardia de
AUTONOMIA-03.

A. Dejar los 9 términos y ampliarlos después, cada uno con su PR.
B. Ampliar desde la versión 1.0.0 con flexiones y derivados directos: mienten, mintieron, mentir,
   mintiendo, mentira, mentiras, mentirosos, mentirosas, falsos, falsas, falsedad, verdaderos,
   verdaderas, veraz, engaña, engañó, engaños, engañoso, engañosa. (Recomendada)
C. Lo de B más términos de credibilidad sobre la persona: creíble, increíble, fiable, sincero, sincera.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Rótulos de resultado visibles en la consola (AC5.5.4)

AC5.5.4 exige que los únicos rótulos de resultado en pantalla sean «Sugerencia de revisión»,
«Incongruencia semántica» y «Hecho No Documentado», y se prueba en nivel 0 en esta unidad.

A. U1 publica un contrato pequeño que asocia cada calificación y tipo de resultado con su rótulo
   visible; la consola lo importa y la prueba de U1 comprueba que solo existen esos tres rótulos.
   (Recomendada)
B. U1 solo fija el enum de calificación; la prueba de los rótulos en pantalla la hace U4 en la consola.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Formato de fecha compartido

C1 usa ISO 8601 en UTC (ejemplo `2026-10-02T21:40:00Z`) y la consola muestra hora de Colombia. Falta
fijar la precisión y si se aceptan desfases, porque la misma regla valida los mensajes de las colas,
las respuestas de la API y el reporte con su SHA-256.

A. RFC 3339 en UTC con `Z`, precisión de segundos, sin fracciones ni desfases
   (`2026-10-02T21:40:00Z`); cualquier otra forma se rechaza. (Recomendada)
B. RFC 3339 en UTC con `Z` y milisegundos opcionales (`2026-10-02T21:40:00.123Z`).
C. RFC 3339 con cualquier desfase horario (`-05:00` incluido); el consumidor normaliza a UTC.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada (cambio 01, adenda 02 y cambio 03) — 2026-11-09

**Qué cambió para U1.** U1 ahora guarda también el contrato común v1.0.0 (C6, aprobado en el principal
el 2026-11-09), los tipos de `model_calls` (C13), los esquemas de perfiles y precios (C18), el registro de
llamadas y el reporte de la CLI (C19), el catálogo de límites (C25), el aviso de VE-01 (C8) y la
jerarquía de excepciones (`unit-of-work.md` U1, revisión 2). El cambio 03
(`/insumos/app/cambios/veridicus-03_reutilizacion_en_sistema.md`) pide que esas piezas sirvan también a
`sistema`.

**Ya decidido y no se vuelve a preguntar.** V-1 con la opción A (el autor, 2026-11-09): papel como
cadena con patrón en C13, C19 y C21; esquema de perfil genérico con `roles` y `role_aliases`, y el del
analizador como especialización que exige `judge` y `verifier`; prefijo de `api_key_ref` como parámetro
del código (Veridicus fija `VERIDICUS_`); C6 sin cambios. `contracts/analyzer/v1/` es una copia sin
editar de los esquemas del principal y la prueba de nivel 0 compara su contenido (cambio 03 §1). Las
precisiones a artefactos aprobados van en una tabla y el autor decide.

## P5 — Cómo compara la prueba de nivel 0 la copia del contrato común

La CI no ve `/insumos`, así que necesita una referencia versionada de lo aprobado.

A. `contracts/analyzer/v1/SHA256SUMS` con las huellas de los dos esquemas tal como llegan del principal;
   la prueba recalcula el SHA-256 de los bytes de la copia, compara y además valida `contrato: "1.0.0"`.
   Solo se copian los dos esquemas, sin el `README.md`. (Recomendada)
B. Como A, pero también se copia el `README.md` del principal, con su huella.
C. La prueba compara contra `/insumos` en la máquina local y se omite en la CI.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — Nombre de importación del paquete de contratos (V-3)

Hoy los contratos se importan como `contracts.python.model_calls` y `contracts.analyzer.v1`. `sistema`
los instalará como dependencia, y un paquete de primer nivel llamado `contracts` choca con facilidad.

A. Distribución `veridicus-contracts` con el paquete `veridicus_contracts` (por ejemplo,
   `veridicus_contracts.model_calls` y `veridicus_contracts.analyzer.v1`), con los esquemas como datos
   del paquete; la carpeta del repositorio sigue siendo `contracts/`. Cambian las rutas de importación
   de C10–C13, C17, C20, C23 y C24 (precisión para la aprobación). (Recomendada)
B. Conservar `contracts` como nombre de importación y aceptar el riesgo de choque en `sistema`.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — Proveedor alterno en el perfil genérico

El perfil actual tiene un solo `fallback_provider`, que usa el núcleo ante un bloqueo de contenido.

A. Uno por perfil, como hoy, y sirve a cualquier papel. (Recomendada)
B. Opcional por papel (`roles.<papel>.fallback`), además del de perfil.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P8 — Rótulos de los 7 tipos de hallazgo (AC5.5.4)

AC5.5.4 dice que los únicos rótulos de resultado son «Sugerencia de revisión», «Contradicción en el
relato» y los rótulos de los 7 tipos, pero ningún artefacto fija el texto de esos 7. El catálogo de
rótulos de U1 (P3 = A) los publica.

A. `fecha` «Fecha», `numero` «Número», `lugar` «Lugar», `persona` «Persona», `negacion` «Negación»,
   `secuencia` «Secuencia», `otro` «Otro». (Recomendada)
B. Más descriptivos: «Fecha», «Cantidad», «Lugar», «Persona», «Afirmación y negación», «Orden de los
   hechos», «Otro».
X. Other (please specify)

[Answer]: A **Mode:** guided

# Hallazgos de la revisión 1 de la segunda pasada — 2026-11-09

Opción B del humano: resolver R-01 a R-03 en U1 antes del lote de U10 e identity-access.

## P9 — Funciones ejecutables de U1 (R-01)

F8 y BR11.1 piden validar perfiles con un prefijo y leer límites que el entorno solo puede bajar,
pero U1 es «sin lógica».

A. U1 publica dos funciones puras en `veridicus_contracts` (`profiles.validate` y `limits.load`),
   declaradas con módulo, firma y excepción; FD-U1-10 enmienda el «sin lógica». (Recomendada)
B. U1 solo esquemas y fixtures; U10, U11 y `sistema` validan cada uno por su cuenta.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P10 — Quién ejecuta los escenarios de vocabulario (R-02)

El escáner `scan(text, literal_sources)` es de U11, que se construye después de U1.

A. Los escenarios pasan a ser datos (`scan_case`) que U1 valida por forma y U11 ejecuta en B11;
   BR6.3 y BR3.3 usan una comparación trivial documentada. (Recomendada)
B. U1 incluye un escáner de referencia mínimo que U11 importa.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P11 — Hallazgos menores R-04 a R-09

A. Corregirlos todos en esta pasada; R-05 queda como riesgo residual en §9 para decidir. (Recomendada)
B. Solo R-01 a R-03.
X. Other (please specify)

[Answer]: A **Mode:** guided
