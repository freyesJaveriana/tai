# Tareas candidatas del loop de agentes

Trabajo real que apareció fuera del alcance de una tarea (codificador o revisor) y que el orquestador
no metió en el diff en curso. Cada fila se decide aparte: si es un defecto del plan aprobado, cambiarlo
exige volver a aprobarlo (`docs/loop/orquestador.md`, Paso 3).

| ID | Origen (tarea y ronda) | Descripción | Decisión |
|---|---|---|---|
| K-01 | U01-T04 ronda 1, F-02 | Publicar en `registry` una función `uri_for(archivo, contenido)` que deduzca `en_vendor` de la ruta, y que `tests/helpers.py` deje de llamar a `_uri_de`, que es privada | Pendiente. Encaja en una tarea que toque `registry.py` |
| K-02 | U01-T05 ronda 1 | El contract-summary revisión 4 pide C3 2.1.0, con el mensaje `RunStarted` y `kind: run_result` (FD-U4-02). El paso 7 se escribió sobre la revisión 3 y entregó la 2.0.0 | Pendiente. Puede exigir cambiar el plan y volver a aprobarlo; se lleva al humano antes de B4 |
| K-03 | U01-T05 ronda 1, Y-01 | El `LoadError` del registro no nombra el archivo, y un YAML que no es esquema y está mal formado tumba todo el registro. Falta una prueba que fije ese comportamiento | Pendiente. Junto con K-01 |
| K-04 | U01-T03 ronda 2 | §4.10: `checks/synthetic.py` debe eximir los campos `format: uuid` y las huellas `^[a-f0-9]{64}$` de la regla de 6 a 10 dígitos | Pendiente. Va en la tarea de `checks/synthetic.py` (paso 19) |
| K-06 | U01-T06 rondas 1 y 2, F-03 | Decidir si «vacío» en BR4.1 y BR4.4 incluye el texto de solo espacios. Si lo incluye, añadir un `pattern` en `hecho`, `observaciones`, `note` y `reformulation`, con sus *fixtures* negativos | Pendiente. Se lleva al humano al cerrar la etapa |
| K-07 | U01-T07 ronda 2 | Hay fuentes de otras unidades que usan `code` ausentes del catálogo: `session.not_open` (409), `scenario.too_large` (413) y `transcript.too_large` (422). Están en session-lifecycle y en restos de diseños retirados | Pendiente. Se limpian en la tarea previa de cada Bolt |
| K-08 | U01-T09 ronda 1 | `effective-config.v1.yaml` (C18, de T05) copia `destination` y `profile` en vez de apuntar con `$ref` a `profiles.schema.v1.yaml`; hace falta un `$ref` o una prueba de igualdad | Pendiente. Encaja en T09 si cabe en la ronda 2 sin tocar los *fixtures* de C2; si no, en una tarea propia |
| K-09 | U01-T09 ronda 1 | U11: `same_family_declared` solo en `demonstration`, y misma `family` prohibida en `evaluation`, cada una con su control negativo (C18, regla de project.md) | Pendiente. Va al plan de U11 |
| K-10 | U01-T10 ronda 1 | `limits.load` no comprueba las derivadas tras bajar una cifra. Por ejemplo, bajar `audio_base64_max_chars` sin bajar `audio_max_bytes` deja un tope de base64 menor que el audio permitido. Ninguna relación de §5 lo cubre | Pendiente. Es una decisión de diseño; se lleva al humano al cerrar la etapa |
| K-11 | U01-T10 ronda 1 | Alinear los `used_in` de `limits.v1.yaml` con las marcas reales de C1, C2, C5, C19 y C21 | Pendiente. Va en T14 y T15 |
| K-05 | U01-T07 ronda 1 | T15: la comprobación (b) de los `code` usados solo los busca bajo las claves `code` y `error_code`. En C21 aparecen dentro de `description`, y C1 los toma con `$ref ErrorCode` | Pendiente. Se contrasta en T15 |
