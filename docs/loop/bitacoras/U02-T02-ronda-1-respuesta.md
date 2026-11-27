F-01: Corregido en 509054f: la regla de la NetworkPolicy rechaza `endPort` en el 443 y en el 53 (rojo en 76c30bc).
F-02: Corregido en 509054f: AUTONOMIA-01 ve los verbos escritos como lista de argumentos en `.py` y `.yaml` (lista entre corchetes y bloque YAML) y `(which herramienta) verbo`.
F-03: Corregido en 509054f: la regla (c) mira el `securityContext` de cada contenedor y rechaza `hostPath`; la `ClusterPolicy` veridicus-pod-restricted cubre lo mismo.
F-04: Corregido en 509054f: las cuatro `ClusterPolicy` cubren los tres tipos de contenedor y la imagen usa las mismas expresiones que pytest; 23 recursos de fallo y de paso nuevos. Sin correr Kyverno: la sintaxis queda por confirmar en U02-T03.
F-05: Corregido en 509054f: la política suma `request.userInfo.username` del controlador de Jobs y el comentario es exacto; ensayo con otro usuario en `otro-usuario/kyverno-test.yaml`.
F-06: Fuera de alcance: tarea candidata propuesta (ampliar los verbos a todo `## Forbidden`), como pidió el orquestador.
F-07: Corregido en 509054f: el guardián de shell salta solo `scripts/humano`.
F-08: Corregido en 509054f: la excepción nombra `comun.sh` y `comprobar_reporte.py`.
F-09: Corregido en 509054f: shebang con `-x`, `export` con sustitución de un archivo y nombres de variable `secreto` o `key`.
Candidata del informe (last-applied-configuration): Corregido en 509054f: los dos scripts que crean Secrets aplican con `--server-side` y una regla falla si no lo hacen; desvío declarado en la bitácora.
