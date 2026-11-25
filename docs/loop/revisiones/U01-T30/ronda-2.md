# Ronda 2 — U01-T30

VEREDICTO: VERDE

Los cinco criterios pasan con mis propias corridas sobre d82a1a8. F-01 y F-02 están corregidos y A-01, A-03 y A-04 quedan cubiertos. F-03 y A-02 quedan cerrados por la decisión del humano en P-T30-3. Solo queda un AMARILLO, que no bloquea: es el mismo comportamiento que había en la ronda 1. No se filtró ningún dato personal del autor.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Guardia sobre el repositorio | `bash /workspace/.worktrees/U01-T30/scripts/check-no-datos-personales.sh /workspace/.worktrees/U01-T30` | `0 apariciones`, código 0: pasa |
| CA-2 | Control negativo | `python3 -I /tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/ctl30/control_negativo.py` | 22 de 22 OK, `fallos: 0`: pasa |
| CA-3 | Solo cambian los datos | No usé `--word-diff`. Corrí `python3 -I …/ctl30/ca3.py`, que ahora compara contra d93a116, y mi método por segmentos con `python3 -I -c` | Pasa. `plan-aidlc.md` solo cambia en la línea 106 (1 correo de 23 caracteres). La propuesta solo cambia en la 30 (1 correo de 23) y en la 31 (1 documento de 10 y 1 correo de 21). El número de líneas no cambia |
| CA-4 | Sintaxis, guardias y CI | `bash -n …/check-no-datos-personales.sh`; `bash …/check-no-cluster-ids.sh /workspace/.worktrees/U01-T30`; `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T30/contracts pytest tests/checks/test_ci_workflows.py --no-cov`; `uv run … yamllint -s -c …/.yamllint.yaml …/.github` | Pasa: `bash -n` da 0, la guardia de T29 da `0 apariciones`, 79 pruebas pasan y yamllint da 0 |
| CA-5 | Archivos del diff | `git -C /workspace/.worktrees/U01-T30 diff --numstat feat/b1-contratos...HEAD` (la base resuelve a d93a116) | Pasa: salen solo los 5 archivos permitidos |

## Comprobaciones
- **Rojo con la guardia nueva.** Corrí la guardia de d82a1a8 sobre el clon del árbol anterior a la sustitución, en `…/scratchpad/rev30/rojo` (153dfb4). Da código 1 y `4 apariciones`, las mismas de la ronda 1. La bitácora trae el par falla-pasa del control: 3 fallos (F-01, F-02 y A-01) con la guardia anterior, y 0 con la final.
- **F-01, corregido.**
  - `a-vecino-tras-exento` da 1 (en la ronda 1 daba 0).
  - El orden inverso, `a-vecino-antes-de-exento`, da 1.
  - `a-vecino-tras-exento-con-puntos` da 1.
  - Siguen limpios `a-dos-exentos`, `a-exento-solo` y `a-exento-con-puntos-solo`.
- **El *lookahead* no deja pasar falsos exentos.** Dan 1:
  - un número que contiene un exento: `a-contiene-exento`;
  - un número que empieza por un exento: `a-empieza-por-exento`, `a-empieza-por-exento-10` y `a-empieza-por-exento-con-puntos`;
  - un exento escrito en otro formato: `a-exento-con-puntos` y `a-exento-sin-puntos-del-otro`.
- **F-02, corregido** con `core.quotePath=false`.
  - `b-alcance-ruta-con-tilde` da 1 y la salida trae la ruta legible.
  - Fuera del alcance dan 0: `b-alcance-ruta-con-tilde-fuera` y `b-alcance-dir-con-tilde-fuera`, que es un directorio con tilde parecido al del alcance.
  - `b-global-ruta-con-tilde` y `b-global-ruta-con-espacio` dan 1.
- **A-01.**
  - `CC.` seguido de un espacio en blanco ahora cuenta: dan 1 `a-cc-punto`, `a-cc-punto-minus` y `a-cc-punto-tab`.
  - No saltan, sin falsos positivos: `a-cc-punto-pegado`, `a-etc-punto` y `a-ruta-cc-punto`.
  - En `contracts/uv.lock`, `libs/errors/uv.lock` y `contracts/ts/package-lock.json` hay 0 líneas que casen con `CC.` seguido de espacio, y CA-1 da 0.
  - Quedan como límites declarados `a-c-espacio-c`, `a-c.c-sin-punto-final`, `a-salto-de-linea`, `a-numero-con-espacios` y `a-numero-con-comas`.
- **El resto de las sondas de la ronda 1 da lo mismo.**
  - Mayúsculas, sin tilde, `documento de identidad`, `cc`, `CC:`, `CC No.`, NBSP y los límites de 6 dígitos y de 20 caracteres: siguen dando 1.
  - Los de 5 dígitos, 11 dígitos y 21 caracteres: siguen dando 0.
  - Regla (b): las 24 sondas coinciden con lo esperado. Los casos de A-02 (`b-alcance-prefijo-falso-plan`, `b-codificado-url` y `b-prefijo-pegado`) se comportan como declara la guardia.
- **A-02.** La sección «Límites conocidos» (`scripts/check-no-datos-personales.sh:16-20`) declara los tres casos: `%40`, el prefijo `.bak` y el prefijo pegado. Declara también los formatos de A-01 que no se detectan.
- **A-03.** El control trae 2 casos f01, 2 f02, 2 a01 y 6 a03. Los a03 prueban el hash de alcance limitado dentro y fuera de las dos rutas, y el hash global en `README.md`, `docs/` y `plan-aidlc.md`.
- **A-04.** La bitácora pega la salida literal de `ca3.py`, igual a la que obtuve yo.
- **`repo-level0.yml`.** Sigue igual que en la ronda 1: 3 líneas, solo `name` y `run`, sin `uses:` ni permisos nuevos.
- **Sin datos personales.** Conté 6 cadenas derivadas de los datos originales, solo con cuentas:
  - En el árbol de d82a1a8 dan 0 los dos correos que se retiraron, el documento con y sin puntos y la parte local de 11 caracteres.
  - El correo institucional sale 1 vez, en `README.md`, que P-T30-1 conserva.
  - La parte local de 6 letras sale 21 veces, todas por coincidencia con texto común y con el nombre, que queda fuera del alcance.
  - En los mensajes de commit, en el diff de `scripts/`, `.github/` y `docs/`, en la bitácora y en los 4 `.py` de `ctl30/` hay 0 de cada dato. Tampoco hay ningún hash de 64 caracteres en la bitácora, los `.py` ni los mensajes.
- **Worktree.** `git status --porcelain` sale vacío y HEAD es d82a1a8.

## Hallazgos
### A-05 · AMARILLO · scripts/check-no-datos-personales.sh:79 · Un exento seguido de punto y cifras sigue exento
En `a-exento-seguido-de-punto-y-cifras`, la palabra de contexto va seguida del exento de 8 cifras, un punto y tres cifras. La guardia da 0. Pasa porque el *lookahead* solo exige que no siga un dígito, y el *lookbehind* `(?<![\d.])` impide empezar después del punto.
No es una regresión: la guardia de la ronda 1 hacía lo mismo. Tampoco es un formato de documento que la tarea pida detectar. Si se quiere cerrar, el *lookahead* de exentos puede exigir `(?![\d.])`, con su caso en el control.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna nueva. Lo del oráculo del SHA-256 quedó decidido en P-T30-3.

Conviene borrar al cerrar la tarea lo que dejé en el scratchpad. El clon `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev30/rojo` contiene los datos originales. Los repositorios de las sondas están en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev30/sondas/`.

```
VEREDICTO: VERDE
AMARILLO|scripts/check-no-datos-personales.sh:79|Un exento seguido de punto y cifras sigue exento
INFORME: docs/loop/revisiones/U01-T30/ronda-2.md
```
