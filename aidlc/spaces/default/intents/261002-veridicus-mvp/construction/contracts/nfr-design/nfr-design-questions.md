# Preguntas de NFR Design — U1 contracts

**Unidad.** U1 `contracts` (tipo `spec`): contratos versionados en `contracts/` y la suite de
validación de nivel 0. Por ser `spec`, en esta etapa solo produce el diseño de seguridad
(`security-design.md`) y la trazabilidad; no tiene rendimiento, escalado, fiabilidad ni observabilidad
propios en ejecución.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos NFR1.1–NFR15.1 y decisiones D1–D12
de `nfr-requirements/` (paquete Python autocontenido, `jsonschema` 2020-12, `openapi-spec-validator`,
meta-esquema de AsyncAPI copiado con SHA-256, `ruamel.yaml` seguro, `pytest-socket`, 100 % de ramas en
`checks/`, catálogo de nombres sintéticos, suite ≤ 60 s). Los valores que la revisión de NFR
Requirements echó en falta ya los fijaron las unidades dueñas: escenario hasta 1 048 576 bytes con
`413` `scenario.too_large` (U6), audio hasta 6 000 000 bytes con `422` (U9), sesión web con
`Max-Age=43200` e inactividad de 1 800 s (U3) y *N* = 120 s de la prueba de humo (U4). Tampoco se
pregunta cómo separar los pasos con red de la CI ni cómo detectar un cargador YAML inseguro: los
resuelvo en el diseño.

Quedan tres decisiones de diseño.

---

## P1 — Dónde viven los límites numéricos (turno, transcripción, archivos, sesión)

Hoy cada cifra aparece en dos sitios: en el contrato (`maxLength` de 2 000, 100 000, 120; tamaño de
archivo) y en la configuración del servicio que la aplica (U4, U6, U9). La suite de U1 solo comprueba
que el `maxLength` exista, no su valor, así que el contrato y el servicio pueden divergir sin que nada
falle (hallazgo R-05 de NFR Requirements).

A. Un catálogo único `contracts/limits.v1.yaml` con cada límite y su unidad dueña. La suite exige que
   cada `maxLength` y cada tamaño de archivo del contrato coincida con el catálogo, y los servicios leen
   el valor de ese catálogo (importado del paquete `contracts`) en vez de escribirlo en su código. Una
   variable de entorno, como `VERIDICUS_VOICE_MAX_BYTES`, solo puede **bajar** el límite, nunca
   subirlo; el servicio no arranca si lo supera. (Recomendada)
B. Las cifras quedan solo en los documentos del contrato; la suite comprueba su valor contra una tabla
   escrita en la propia prueba, y cada servicio mantiene su configuración con su prueba de contrato.
C. Se deja como está: la suite solo exige que exista el límite; cada unidad confirma la cifra al
   construirse.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Cómo probar que ningún `pattern` cuelga a un servicio (ReDoS)

NFR10.6 pide que ningún `pattern` de los esquemas admita retroceso catastrófico, medido hoy con un
tiempo de pared de 50 ms por patrón. La revisión anterior advirtió que un tiempo de pared es sensible a
la carga de la CI y, como no se reintenta el nivel 0 para ocultar fallos, una prueba inestable
bloquearía PR sin causa real (R-04).

A. Comprobación determinista, sin reloj: todo campo con `pattern` declara además un `maxLength`
   (≤ 256 caracteres salvo justificación en el PR) y el patrón pasa un análisis estático de su árbol
   (`re._parser`) que rechaza cuantificadores ilimitados anidados y alternativas que se solapan dentro
   de una repetición. Hypothesis sigue generando entradas adversarias, pero solo para comprobar que el
   validador acepta y rechaza bien, no para medir tiempo. (Recomendada)
B. Se mantiene la medición de 50 ms por patrón con Hypothesis.
C. Las dos cosas: el análisis estático de A y una medición de tiempo con margen amplio (1 s por
   patrón).
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Cómo se ve en el PR un cambio que toca la seguridad de un contrato

Las reglas de la suite detectan los cambios prohibidos (un campo de veracidad, una ruta que escribe el
umbral, un cuerpo sin `additionalProperties: false`). Pero un cambio permitido que cambia la superficie
de seguridad, como una ruta nueva que pasa a ser pública, quitar un rol de `x-veridicus-roles` o subir
un `maxLength`, puede pasar en verde y perderse dentro de un PR grande (amenaza T1).

A. Una «huella de seguridad» versionada: la suite genera `contracts/security-surface.json` con, por
   cada operación de C1, C14 y C16, su seguridad, roles, anti-CSRF, códigos de respuesta y límites, y
   por cada esquema su estrictez. La suite falla si el archivo no coincide con lo generado, así que
   todo cambio de seguridad aparece como un diff legible en el PR y obliga a regenerarlo a propósito.
   (Recomendada)
B. Bastan las reglas de la suite; no hace falta una huella aparte.
C. Una herramienta externa de diferencias de OpenAPI (`oasdiff`, en Go) en un *job* aparte de la CI
   que comenta los cambios incompatibles en el PR.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) diseñó la seguridad sobre C1–C16 y
NFR1.1–NFR15.1 de la primera pasada. NFR Requirements revisión 2 suma `contracts/ts/` (P8 = A),
`limits.exceeded` siempre `413` (P7 = A), las extensiones `x-veridicus-limit` y `x-veridicus-max-bytes`,
los decimales en `ratio` y `s` y el paso del paquete con 180 s. Además, las tablas NFR-U3 a NFR-U13 piden
a U1 cifras nuevas de C25 y cambios en C1, C2, C5, C13, C15 y C19.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| Respuestas de la revisión 1 | P1 = A (catálogo único de límites), P2 = A (ReDoS por análisis estático), P3 = A (huella de seguridad versionada) | Esta etapa, revisión 1 |
| Requisitos | NFR1.1–NFR1.4, NFR2.1–NFR2.2, NFR3.1, NFR10.1–NFR10.16, NFR11.1–NFR11.5, NFR12.1–NFR12.3, NFR13.1–NFR13.2, NFR14.1, NFR15.1; decisiones D1–D16 | `nfr-requirements/`, revisión 2 |
| Estado de `limits.exceeded` | `413` en todas las rutas | P7 = A; NFR-U1-03 |
| Mitad TypeScript | `contracts/ts/` en el *job* `contracts-level0` | P8 = A; NFR-U1-04 |
| Cifras de C25 | Las fija la unidad dueña en su NFR Requirements; U1 las nombra, valida su forma y las admite por PR | NFR10.14; NFR-U1-07; tablas NFR-U3 a NFR-U13 |
| Métodos de voz de C13 | Van en el puerto de U11 y los escribe U9; los tipos de `model_calls.py` no cambian | NFR-U9-01 |
| FD-U1-14 | Sigue pendiente de la aprobación de Functional Design; aquí no se pregunta | functional-spec §9 |

## Cómo se registra la revisión 2

- `security-design.md` y `traceability.json` pasan a la revisión 2 en el mismo archivo, con una nota de
  cabecera que dice qué cambia y por qué.
- Los controles §4.1–§4.13 y las decisiones DS1–DS5 conservan su número; lo que sale queda «Retirado» y
  lo nuevo empieza en §4.14 y DS6.
- Las precisiones a artefactos aprobados van en la tabla NFRD-U1-xx de `security-design.md`. Ningún
  original se edita.
- Como U1 es de tipo `spec`, la etapa sigue produciendo solo el diseño de seguridad y la trazabilidad.

## Lo que el diseño resolverá sin preguntar

1. **Hallazgos R-01 a R-08 de la revisión 1 de esta etapa.** Recorrido completo del árbol de cada
   `pattern`, canonización de la huella, umbral medible de `pip-audit`, separación de pasos y alcance de
   las excepciones. Cada uno sale de su hallazgo.
2. **Contenido de C25 v1.** Entra cada cifra que fijaron las unidades dueñas en sus tablas NFR-Ux. Los
   nombres de la revisión 1 que no siguen (escenarios, `turn_text_max_chars`, `voice_audio_*`,
   `web_session_max_age_s`) quedan «Retirado» frente a los nombres de contract-summary.
3. **Métricas de otras unidades.** C15 sigue siendo el contrato de U5. Las métricas que U4, U6, U8, U9 y
   U10 piden registrar van en archivos propios de `contracts/metrics/`, con la misma comprobación de
   etiquetas. Así U3 y U7, que las dejan internas, no se contradicen con las demás.
4. **`VERIDICUS_LIMITS_PATH` de U11.** El catálogo empaquetado es siempre el techo, como dicen
   `project.md`, C25 y BR11.1. Cualquier otra fuente solo puede bajar una cifra.
5. **Lista cerrada de extensiones `x-veridicus-*`.** Es la unión de NFR10.12, NFR10.7 y
   `x-veridicus-priority` de contract-summary, más `x-veridicus-cookie` de la revisión 1.
6. **Tipo de la parte de archivo en `multipart`.** U6 y U12 deciden por el contenido, así que el contrato
   no exige `encoding.contentType`. Si lo declara, la lista es cerrada.

Ningún punto cambia qué datos salen del clúster.

Sin preguntas: todo lo fijan las fuentes.
