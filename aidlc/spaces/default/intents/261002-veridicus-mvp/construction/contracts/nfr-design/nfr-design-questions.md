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
