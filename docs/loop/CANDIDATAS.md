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
| K-05 | U01-T07 ronda 1 | T15: la comprobación (b) de los `code` usados solo los busca bajo las claves `code` y `error_code`. En C21 aparecen dentro de `description`, y C1 los toma con `$ref ErrorCode` | Pendiente. Se contrasta en T15 |
