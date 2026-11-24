# Ronda 2 — U01-T14

VEREDICTO: VERDE

El revisor corrió él mismo los cinco criterios sobre 97524a9 y todos pasan. Las tablas nuevas de F-01 coinciden con contract-summary §C1 y detectan las 7 mutaciones que sobrevivieron en la ronda 1. Quedan mutaciones sin detectar en los esquemas de respuesta y en las propiedades opcionales: es un AMARILLO, que no bloquea.

## Criterios de aceptación, verificados por el revisor (HEAD 97524a9)

| # | Criterio | Comando | Resultado |
|---|---|---|---|
| 1a | Forma de C1 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T14/contracts pytest tests/contracts/test_console.py --no-cov -q` | 59 passed |
| 1b | Guardias c1 | `… pytest tests/guards -m c1 --no-cov -q` | 5 passed, 53 deselected |
| 2 | Suite del Bolt | `timeout 300 … pytest tests/checks tests/guards tests/contracts --no-cov -q` | 1770 passed |
| 3 | Rueda | `timeout 120 … pytest tests/test_package_map.py --no-cov -q` | 8 passed |
| 4 | Tipos y *lint* | `… mypy --strict src` · `… ruff check .` · `… yamllint api/console.v2.yaml` | sin hallazgos en los tres |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T14/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T14` | 0 apariciones |

## Tablas nuevas, comparadas por programa con el summary (líneas 209 a 1149, con el arreglo de K-26)

- **`AUTORIZACION`:** igual al summary en las 41 operaciones.
- **`ESTADOS`:** igual al summary más la regla declarada: `401` con seguridad, `403` con roles y el `413` de login y de `POST /users`.
- **`CUERPOS`, `REQUERIDOS` y `REQUERIDOS_DE_SESSION_VIEW`:** iguales.
- **`ENUMS` y `ENUMS_DE_CUERPO`:** cubren los 22 enum del summary. `ErrorCode` lo cubre la prueba contra el catálogo.
- **Cobertura:** una prueba exige exactamente las 41 operaciones.
- **Un rol de más, de menos o en otro orden:** se detecta.

## Mutaciones

- **Detectadas:**
  - las 7 que sobrevivieron en la ronda 1;
  - un rol de menos y uno de más, roles en otro orden y `owner-only: false`;
  - `access-log` movido, `x-veridicus-demo` en una ruta MUST, sin el parámetro `RunId`, sin el `allOf` de `Consent` y la cookie con `SameSite=Lax`.
- **Sobreviven:**
  - quitar `Turn.pagina`, que es opcional;
  - `Run.attempt` como `string`;
  - añadir una propiedad opcional al cuerpo de `POST /sessions`;
  - `required` de la respuesta 201 de `/problem-reports`;
  - el 200 de `GET /sessions/{id}` cambiado a `SessionSummary`;
  - un `enum` nuevo en `Notice.version`.

## Rojo de 90850a3 contra el C1 de 1260016

Da 1 failed y 58 passed, y lo que falla es `test_a_02_…`, igual que en la bitácora. Es lo esperado, porque el C1 de 1260016 ya era fiel al summary: el rojo de F-01 está en las mutaciones. La bitácora pega el rojo literal completo y marca los SHA de antes del rebase, así que A-03 queda cerrado.

## A-02

El nuevo patrón de `Content-Disposition` de `/exports` exige dos UUID 8-4-4-4-12 en minúsculas y la extensión `.md`. Es portable y rechaza los seis casos malos de la prueba.

## Alcance

El diff toca 4 archivos:
- `console.v2.yaml`: solo la línea del patrón;
- `test_console.py`;
- las dos bitácoras.

No toca nada de T15, de C25, del catálogo de errores ni de las pruebas de T03.

## Hallazgos

### A-01 · AMARILLO · `contracts/tests/contracts/test_console.py:1114` · La fidelidad de los esquemas de respuesta y de las propiedades opcionales sigue sin prueba

Sobreviven las 6 mutaciones de arriba. Ninguna toca autorización, propiedad, CSRF, estados, obligatorios ni una regla AUTONOMIA. Hoy C1 coincide con el summary. Como mejora: comparar el `$ref` de cada respuesta 2xx y los nombres de propiedad de cada esquema de `components`. El orquestador lo registra como K-30.

## Tareas candidatas

Ninguna nueva. K-29 ya está registrada para T15.

Estado final: el worktree quedó limpio y la copia del scratchpad, borrada.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/contracts/test_console.py:1114|Siguen sin prueba los esquemas de respuesta 2xx, los tipos y los nombres de propiedades opcionales (6 mutaciones sobreviven)
INFORME: docs/loop/revisiones/U01-T14/ronda-2.md
```
