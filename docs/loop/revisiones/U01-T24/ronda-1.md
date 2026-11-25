# Ronda 1 — U01-T24

VEREDICTO: VERDE

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Pruebas de la copia de C6 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T24/contracts pytest tests/contracts/test_analyzer_copy.py --no-cov` | pasa: `26 passed in 0.44s` |
| CA-2 | Suite completa, sin omitidas nuevas | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T24/contracts pytest tests --no-cov -q -rs` | pasa: `2600 passed, 1 warning in 13.57s`. No hay omitidas. El aviso es el de `test_socket_bloqueado`, que ya existía. |
| CA-3 | El diff solo toca los archivos permitidos | `git -C /workspace/.worktrees/U01-T24 diff --name-only feat/b1-contratos...HEAD` | pasa: son los 5 archivos esperados. En `speech.v2.yaml` cambia una sola línea (`version: 1.2.0` pasa a `2.0.0`). |
| CA-4a | mypy | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T24/contracts mypy --strict src` | pasa: `Success: no issues found in 46 source files` |
| CA-4b | ruff | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T24/contracts ruff check .` | pasa: `All checks passed!` |
| CA-4c | Nada aplica cambios al clúster | `bash /workspace/.worktrees/U01-T24/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T24` | pasa: `0 apariciones` |

## Comprobaciones dirigidas

- **Constantes.** `HUELLAS_APROBADAS_C6` vive solo en `contracts/tests/conftest.py:25-28`, con el comentario que pide la tarea.
  - **Un solo sitio:** grep de las dos huellas en `.py/.yaml/.sh/.toml` y `SHA256SUMS`. Solo aparecen en `conftest.py` y en `analyzer/v1/SHA256SUMS`.
  - **Los dos usos las importan:** `check_c6_copy` las usa directamente, y `test_analyzer_copy.py` las lee con `_conftest().HUELLAS_APROBADAS_C6`.
  - **Son las de la tarea y las del principal:** `sha256sum` del árbol y de `/insumos/app/contratos/analizador/v1/*.schema.json` dan `28606016…c41a8` y `e1528b7d…edeaf`, idénticas a las de la tarea.
- **F7 y el hueco de R-04, con mi propia sonda.** Copié `analyzer/v1/` al scratchpad, metí un espacio en un esquema y recalculé `SHA256SUMS`. Lo hice para cada uno de los dos esquemas.
  - **Con el `conftest.py` del HEAD:** dos problemas por esquema, los dos con `MENSAJE_F7` y con el nombre del esquema («su SHA-256 no es el de la versión aprobada» y «su línea de SHA256SUMS no es la huella…»).
  - **Con el `conftest.py` de `feat/b1-contratos`:** cargué su código con `git show`, sin escribir nada en el worktree, y sobre las mismas copias devuelve `[]` en los dos casos. El hueco era real y queda cerrado.
- **`VERSION_SEMANTICA`.** Con `fullmatch` probé:
  - **Acepta:** `0.1.2`, `0.0.0`, `10.0.0` y `1.10.100`.
  - **Rechaza:** `01.0.0`, `1.01.0`, `1.0.01`, `00.0.0`, `1.0`, `1.0.0-rc1`, `v1.0.0` y ` 1.0.0`.
  - **Mayor contra el nombre:** `a.v10.yaml` con `10.0.0` pasa. `a.v10.yaml` con `1.0.0` falla, y `a.v1.yaml` con `10.0.0` también. `a.v0.yaml` con `0.3.0` pasa.
- **Extensión de E-28.** El recorrido del árbol pasa la ruta, cubre los 30 contratos propios con `.vN` (los listé con `find`) y nombra `queues/speech.v2.yaml` en el rojo. Los dos controles negativos aíslan la regla del nombre:
  - el de C5 no lleva `$id`;
  - el del esquema JSON lleva un `$id` `.v1` que coincide con `1.0.0`, así que solo falla por el nombre `.v2`.
- **Pruebas que ya pasaban en rojo.** Las comento en F-01.
- **La «parada adicional» de `1.2.0`.** El grep de `1\.2\.0` en `contracts/`, `scripts/` y `.github/` solo encuentra `uv.lock` (versiones de paquetes), los tres *fixtures* de la carga (`schema_version`, que ya es K-66 y que el patrón `^1\.` acepta) y las propias pruebas. Nada lee `info.version` de C5.
- **Interacción con T21.**
  - **Mezcla limpia:** `git -C /workspace/.worktrees/U01-T24 merge-tree --write-tree feat/b1-contratos tarea/U01-T24` da el árbol `87551a3`, sin conflictos.
  - **Archivos disjuntos:** `git diff --stat 8377162 feat/b1-contratos` muestra que T21 solo añade `tools/check_package.py`, `tests/tools/test_check_package.py` y documentos, ninguno de los archivos de T24.
  - **`check_package` no depende de lo que cambia T24:** un grep sobre `check_package.py` no encuentra `version`, `queues`, `SHA256SUMS` ni `conftest`. Solo empaqueta bytes y valida *fixtures*, y la línea `info.version` de C5 no entra en ninguna validación de esquema.
  - **No corrí V-PKG sobre la mezcla.** Habría que extraer el árbol en disco, y eso no es de solo lectura. Por lo anterior no lo juzgo necesario. Si el humano quiere la prueba empírica, la CI del PR la cubre.
- **Worktree.** `git status --porcelain --untracked-files=all` sale vacío antes y después de mi revisión.

## Hallazgos

### F-01 · AMARILLO · contracts/tests/conftest.py:61-62 · La comprobación «línea de SHA256SUMS distinta de la constante» nunca falla sola
Hay dos casos posibles:
- si los bytes son distintos de la huella aprobada, falla la línea 59;
- si los bytes son la huella aprobada y la línea es distinta, falla la línea 57, porque los bytes tampoco coinciden con la línea.

Así, la línea 61 siempre falla junto con otra. Quitarla no rompería ninguna prueba. Por eso `test_f7_rechaza_sha256sums_con_otra_huella_y_esquemas_intactos` ya pasaba en rojo y no distingue nada nuevo. La tarea pedía los dos, y el codificador lo dejó dicho en la bitácora. No bloquea, pero conviene saber que ese control es una regresión del comportamiento anterior y no prueba la regla nueva.

### F-02 · AMARILLO · contracts/tests/checks/test_fixture_coverage.py:459-463 · Los controles negativos no son copias de los contratos reales
La tarea pide «copias en memoria» de C5 y de un esquema JSON. El codificador usa diccionarios mínimos, como `{"info": {"version": "1.2.0"}}`. Bastan para probar la regla, y el recorrido del árbol cubre la forma real de los contratos. Aun así, cargar C5 y cambiarle la versión sería más fiel a lo que pide la tarea.

### F-03 · AMARILLO · contracts/tests/checks/test_fixture_coverage.py:363 · `MAYOR_DEL_NOMBRE` no reconoce extensiones compuestas
El patrón `\.v([0-9]+)\.[A-Za-z]+$` no ve el `.vN` en un nombre como `x.v2.schema.json`. Hoy no hay ningún archivo así (`cli/report.schema.v2.yaml` termina en `.v2.yaml`), pero un contrato futuro con ese nombre quedaría fuera del control.

### F-04 · AMARILLO · contracts/tests/contracts/test_analyzer_copy.py:109 · Los nombres de los esquemas están repetidos
`NOMBRES_C6` repite `ESQUEMAS_C6` de `conftest.py`. Si se desalinean, lo detecta `assert set(aprobadas) == set(NOMBRES_C6)`, pero importarlo evitaría tener dos listas.

## Tareas candidatas (defectos reales fuera de alcance)
- `src/veridicus_contracts/tools/security_surface.py:54,260` toma como huella de C6 los bytes de `analyzer/v1/SHA256SUMS`, que un PR puede recalcular. Con F7 abortando la sesión esto ya no deja pasar una copia alterada. Aun así, la superficie podría usar las huellas aprobadas, y eso toca `src/`, que está fuera de esta tarea.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/conftest.py:61-62|La comprobación de la línea de SHA256SUMS contra la constante nunca falla sola y su control negativo ya pasaba en rojo
AMARILLO|contracts/tests/checks/test_fixture_coverage.py:459-463|Los controles negativos son diccionarios mínimos y no copias de C5 ni de un esquema real
AMARILLO|contracts/tests/checks/test_fixture_coverage.py:363|MAYOR_DEL_NOMBRE no reconoce .vN seguido de una extensión compuesta
AMARILLO|contracts/tests/contracts/test_analyzer_copy.py:109|NOMBRES_C6 repite ESQUEMAS_C6 en vez de importarlo
INFORME: docs/loop/revisiones/U01-T24/ronda-1.md
```
