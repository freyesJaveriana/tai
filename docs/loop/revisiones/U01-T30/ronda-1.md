# Ronda 1 — U01-T30

> Nota del orquestador (P-T29-2): en esta copia persistida, el texto de la sonda `a-vecino-tras-exento` de F-01 se describe con palabras, porque contiene un número inventado no exento que la guardia detecta a propósito. El resto es literal.

VEREDICTO: NO-VERDE

Los cinco criterios pasan con mis propias corridas y el rojo se reproduce exacto. El veredicto es NO-VERDE por tres hallazgos NARANJA: dos defectos de la guardia que encontré con las sondas y un incumplimiento de proceso. No encontré ningún dato personal del autor que se haya filtrado.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Guardia sobre el repositorio | `bash /workspace/.worktrees/U01-T30/scripts/check-no-datos-personales.sh /workspace/.worktrees/U01-T30` | `0 apariciones`, código 0: pasa |
| CA-2 | Control negativo | `python3 -I /tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/ctl30/control_negativo.py` | 9 de 9 OK; los ataques dan código 1 con `nota.md:1` y los limpios, 0: pasa |
| CA-3 | Solo cambian los datos | No corrí el `--word-diff`. Corrí `ca3.py` con `-I` y un método mío con `python3 -I -c` que compara por segmentos sin imprimir nada | pasa (detalle abajo) |
| CA-4 | Sintaxis, guardias y CI | `bash -n …/check-no-datos-personales.sh`; `bash …/check-no-cluster-ids.sh /workspace/.worktrees/U01-T30`; `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T30/contracts pytest tests/checks/test_ci_workflows.py --no-cov`; `uv run … yamllint -s -c …/.yamllint.yaml …/.github` | `bash -n` da 0; la guardia de T29 da `0 apariciones`; 79 pruebas pasan; yamllint da 0: pasa |
| CA-5 | Archivos del diff | `git -C /workspace/.worktrees/U01-T30 diff --numstat feat/b1-contratos...HEAD` (la rama base resuelve a 153dfb4) | Salen exactamente los 5 archivos permitidos: pasa |

## Comprobaciones
- **CA-3, método propio.** Tomé la línea nueva y la partí en los marcadores. Exigí que la línea vieja coincida entera con esos segmentos y que cada hueco sea un correo o un número.
  - `plan-aidlc.md:106`: un hueco, un correo de 23 caracteres.
  - Propuesta, línea 30: un hueco, el mismo correo de 23.
  - Propuesta, línea 31: dos huecos, un documento de 10 caracteres y un correo de 21.
  - El número de líneas es el mismo en los dos archivos y no cambia ninguna otra línea.
- **El rojo.** Cloné la rama en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev30/rojo`, la puse en 153dfb4 y corrí sobre ese árbol la guardia de faad72e. Da código 1 y `4 apariciones`, las mismas de la bitácora: `plan-aidlc.md:106`, la propuesta en la 30 y la propuesta en la 31 dos veces.
- **Alcance de los dos hashes, sobre el árbol de 153dfb4.**
  - El personal (`57fade48`) aparece 1 vez, en `research/`.
  - El institucional (`a3bc2c29`) aparece 3 veces: en `README.md` (el pie que conserva P-T30-1), en `plan-aidlc.md` y en `research/`. La guardia ignora el de `README.md`, como debe.
- **Las sondas**, todas con datos inventados y con una copia de la guardia en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev30/sondas/g.sh`.
  - Regla (a), las que detecta:
    - `a-mayus-con-tilde`, `a-capitalizada`, `a-sin-tilde-mayus`, `a-documento-mayus` y `a-cc-minus`;
    - `a-cc-dos-puntos`, `a-cc-no` y `a-nbsp`;
    - `a-contiene-exento`, `a-exento-con-puntos`, `a-exento-sin-puntos-del-otro` y `a-vecino-antes-de-exento`;
    - en los límites: `a-6-digitos` y `a-a-20-caracteres`.
  - Regla (a), los límites que no salta, como pide la tarea: `a-5-digitos-limpio`, `a-11-digitos` y `a-a-21-caracteres`.
  - Regla (a), las que se escapan: `a-c-espacio-c`, `a-cc-punto`, `a-c.c-sin-punto-final`, `a-salto-de-linea`, `a-numero-con-espacios`, `a-numero-con-comas` y `a-vecino-tras-exento` (ver F-01 y A-01).
  - Regla (b), las que detecta:
    - `b-mayus`, `b-mixto`, `b-angulos`, `b-mailto`, `b-mailto-doble`, `b-punto-final`, `b-subdir-profundo` y `b-global-ruta-con-tilde`;
    - el hash de alcance limitado cuenta en `b-alcance-en-plan`, `b-alcance-en-research06`, `b-alcance-en-research06-subdir` y `b-alcance-mayus-en-plan`.
  - Regla (b), lo que no cuenta, como debe: el hash de alcance limitado en `b-alcance-en-readme`, `b-alcance-en-docs` y `b-alcance-en-research-otra`, y el correo de `b-correo-otro-limpio`.
  - Regla (b), las que fallan: `b-alcance-ruta-con-tilde` (F-02), `b-alcance-prefijo-falso-plan`, `b-codificado-url` y `b-prefijo-pegado` (A-02).
  - **Falsos positivos.**
    - `uv.lock` tiene segmentos `/cc/`: 8 en `contracts/uv.lock` y 2 en `libs/errors/uv.lock`. `contracts/ts/package-lock.json` existe. CA-1 da 0 sobre todos ellos.
    - Los únicos binarios versionados son 2 `.pptx` en `presentations/`. La guardia los salta por `-I`, así que abrí los zip y los revisé: 0 correos de cualquier tipo y 0 apariciones de los datos.
    - Con una raíz que no es un repositorio, la guardia sale con 2.
- **`repo-level0.yml`.** El diff solo añade 3 líneas: el paso con `name` y `run`, justo después del de `check-no-cluster-ids.sh`. No hay `uses:` ni permisos nuevos.
- **Sin datos personales.** Todo lo conté con `python3 -I`, solo cuentas, sin imprimir nada:
  - árbol de faad72e: los dos correos personales, el documento con y sin puntos y la parte local de 11 letras dan 0. Esto incluye los binarios, porque leí bytes.
  - El correo institucional aparece 1 vez, en `README.md`, que P-T30-1 conserva.
  - Mensajes de commit de la rama, diff de `scripts/`, `.github/` y `docs/` (con la bitácora) y los 4 `.py` de `ctl30/`: 0 de cada dato.
  - Hashes completos de 64 caracteres en la bitácora y en esos `.py`: 0. Los dos hashes completos solo están en `scripts/check-no-datos-personales.sh:28,31`, como pide la tarea.
- **Worktree.** `git status --porcelain` sale vacío y HEAD es faad72e.

## Hallazgos
### F-01 · NARANJA · scripts/check-no-datos-personales.sh:69-82 · Un número exento tapa a un número real vecino
El cuantificador perezoso `.{0,19}?` hace que cada palabra de contexto se quede con el primer número que encuentra. Si ese número es exento, el número que viene después, dentro de los mismos 20 caracteres, ya no se compara. Con la sonda `a-vecino-tras-exento` (la sigla con puntos, el número exento de 8 cifras y, tras «y», otro número inventado de 8 cifras no exento) la guardia da código 0. El orden inverso sí se detecta.
Arreglo sugerido: excluir los exentos dentro de la expresión, con un lookahead negativo antes del número, para que el motor siga hasta el siguiente. Hace falta un caso nuevo en el control.

### F-02 · NARANJA · scripts/check-no-datos-personales.sh:57,98-101 · Una ruta con tilde rompe el alcance del hash institucional
`git grep` cita las rutas que no son ASCII (`core.quotePath`). Una ruta así llega como `"research/06-…/c\303\251dula.md"` y no empieza por el prefijo del alcance. Con la sonda `b-alcance-ruta-con-tilde` la guardia da 0 cuando debía dar 1. La salida de `archivo:línea` también sale con octales.
Hoy no hay ningún archivo así en `research/06-documentacion-propia/`, pero el defecto es real en una carpeta de documentos en español.
Arreglo sugerido: `git -c core.quotePath=false -C … grep`.

### F-03 · NARANJA · bitácora:38 y scratchpad `sustituir.py`, `parchar_hashes.py` · Ediciones hechas sin Edit ni Write
La tarea (Notas: «Edición: solo con Edit o Write») y las reglas comunes piden usar solo esas dos herramientas, porque solo ellas disparan `write-audit-log` y `run-sensors`. El codificador cambió con scripts de Python los dos archivos de datos y puso los hashes en la guardia.
El motivo es entendible: no poner los datos en el `old_string` de un Edit. Aun así es un conflicto que la tarea mandaba parar y avisar, y no resolver por cuenta propia. El resultado es correcto. Lo decide el humano: aceptarlo como riesgo o pedir que se rehaga.

### A-01 · AMARILLO · :69 · Formatos de documento que no se detectan
No salta con `C. C.` con espacio, con `CC.` (lo excluye P-T30-2 de forma literal), con `C.C` sin el punto final, con la palabra y el número en líneas distintas ni con un número escrito con espacios o con comas. Ninguno incumple la letra de la tarea.
`CC.` es frecuente en Colombia. Una alternativa es `CC\.(?=\s)`, que no afecta a `uv.lock`.

### A-02 · AMARILLO · :85,100 · Límites de la regla (b)
- `plan-aidlc.md.bak` cuenta como si estuviera dentro del alcance (el `case` compara por prefijo).
- Un correo pegado a un prefijo de palabra (`abc_…@…`) cambia el hash y se escapa.
- `%40` en lugar de `@` se escapa; está declarado como límite conocido.

### A-03 · AMARILLO · control_negativo.py · El control no prueba el alcance limitado
Ningún caso prueba el hash que cuenta solo en las dos rutas, ni las exenciones con un número vecino. Mis sondas cubren el alcance, pero conviene llevarlas al control.

### A-04 · AMARILLO · bitácora:44 · La evidencia de CA-3 no está en la bitácora
La bitácora dice que el resultado de CA-3 «queda en el informe final», pero no pega la salida de `ca3.py`.

## Tareas candidatas (defectos reales fuera de alcance)
- Un SHA-256 de un correo en minúsculas, publicado, sirve de oráculo: quien adivine el correo a partir del nombre y de dominios comunes lo confirma. La alternativa es un HMAC con una clave fuera de Git, que no sirve en la CI pública, o dejar la lista solo en el pre-commit local. Lo decide el humano; la tarea pedía SHA-256.
- La historia de Git conserva los datos (K-75 = A, decisión ya tomada).

Archivos que dejé en el scratchpad, fuera de Git: el clon `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev30/rojo` (en 153dfb4, con los datos originales) y los repositorios de las sondas en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev30/sondas/`. Conviene borrarlos al cerrar la tarea.

```
VEREDICTO: NO-VERDE
NARANJA|scripts/check-no-datos-personales.sh:69-82|Un número exento tapa a un número real vecino
NARANJA|scripts/check-no-datos-personales.sh:57,98-101|Una ruta con tilde rompe el alcance del hash institucional
NARANJA|docs/loop/bitacoras/U01-T30.md:38|Ediciones hechas sin Edit ni Write
AMARILLO|scripts/check-no-datos-personales.sh:69|Formatos de documento que no se detectan
AMARILLO|scripts/check-no-datos-personales.sh:85,100|Límites de la regla (b)
AMARILLO|control_negativo.py|El control no prueba el alcance limitado
AMARILLO|docs/loop/bitacoras/U01-T30.md:44|La evidencia de CA-3 no está en la bitácora
INFORME: docs/loop/revisiones/U01-T30/ronda-1.md
```
