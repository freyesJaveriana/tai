# Ronda 2 — U01-T23

VEREDICTO: NO-VERDE

Los seis criterios pasan con mis propias ejecuciones sobre ef522a8, el rojo falla por la regla y el *workflow* pasa la guardia de 5405c91. F-02, F-03, F-04 y F-05 quedan cerrados. Queda en pie **un NARANJA**: lo que queda de F-01 es la versión de C13, que el README pone como «(el del paquete)» aunque el registro dice v1.0.0.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | README y herramienta | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T23/contracts pytest tests/test_readme.py tests/tools/test_check_tag.py --no-cov -p no:cacheprovider -q` | pasa: 112 passed |
| 2 | Etiqueta esperada | `uv run ... python -m veridicus_contracts.tools.check_tag --tag contracts-v0.1.0` y `--tag v0.1.0` | pasa: código 0 y código 1 (el mensaje nombra las dos); `--tag x --tag contracts-v0.1.0` da código 2 |
| 3 | V-SUITE | `timeout 60 uv run --frozen --offline --directory .../contracts pytest -p no:cacheprovider -q` | pasa: 2731 passed, 0 omitidos, 29,2 s, cobertura 97,90 % |
| 4 | El AST no cambia | `python -c` propio: `ast.dump` sin docstrings, `git show b406ae0:<f>` contra `HEAD:<f>` | pasa: IGUAL en los 14 archivos existentes; `check_tag.py` es nuevo |
| 5 | Tipos, *lint*, guardias y YAML | `mypy --strict src`, `ruff check .`, `check-no-cluster-apply.sh`, `check-no-insumos.sh`, V-YAML | pasa: sin errores, «All checks passed!», 0 apariciones, 0 apariciones, código 0 |
| 6 | Archivos del diff | `git -C /workspace/.worktrees/U01-T23 diff --name-only feat/b1-contratos...HEAD` (la base común es b406ae0) | pasa: solo archivos permitidos, más `U01-T23-ronda-1-respuesta.md`, que aceptaste |

## Comprobaciones adicionales
- **Rojo.** `git diff 9f02b84 HEAD -- contracts/tests` está vacío. Pasé las pruebas de HEAD sobre el README y el `check_tag.py` de 9f02b84 y falla todo lo que debe fallar, por la regla:
  - el inventario da 20 discrepancias: 6 filas `.py` que faltan y 14 IDs que no coinciden con el registro;
  - las 13 claves V-* salen sin columna de *workflow*;
  - `--tag` y `--pyproject` repetidos devolvían 0.
- **Guardia de T22b.** El `ci_workflows.py` de 5405c91, leído con `git show` y corrido sobre este worktree, da `[]`. El *workflow* no cambió en esta ronda.
- **Asignaciones propuestas en F-01.**
  - `model-call.v1.yaml` en **C19** es fiel al registro: el archivo está dentro de la sección «C19 — Reporte de la CLI» (`contract-summary.md:2418-2428`), la línea 109 dice «registro de llamadas en U1 (`contracts/model_calls/`)» y BR1.4 dice «C19 con el registro de llamadas».
  - Las métricas que no son review.v2 como «(sin número) … familia de C15» son fieles: la línea 134 las pone en la tabla «sin número de contrato», con «(ver C15)».
  - `SHA256SUMS` como «(sin número)» es fiel: `functional-spec.md:74` dice «Huellas aprobadas (P5)» y no le da número.
  - `role-translation` como «(sin número)» se sostiene: `contract-summary.md` no la nombra en ninguna parte y `functional-spec.md:85` le da un nombre sin número.
  - El resto de las filas también coincide con el registro: C1–C3, C5, C6, C7, C8 (los tres archivos de la línea 98), C10–C12, C16, C18, C19, C21, C23, C24, C25 y las seis filas «sin número» de las líneas 126 a 135.
- **Controles negativos del inventario.** Los probé yo con la función `discrepancias_del_inventario`:
  - un ID inventado (C15 en `voice`) se detecta;
  - una fila que falta (C23) se detecta;
  - una fila de más con un archivo nuevo se detecta.
  - Los dos huecos que encontré van en F-07.
- **Docstrings (F-02).** Contrasté con `rules.md` y `security-requirements.md:107-120` los cambiados y una muestra de los otros:
  - cambiados: `auth_surface` (NFR10.11, NFR10.12), `error_codes` (BR7.4, BR7.2, BR3.4), `_openapi`, `fixture_coverage` (NFR10.10, BR1.5), `limits_catalog` (BR11.1, NFR10.14), `metrics` (BR8.2), `scan_cases` (BR5.8) y `strict_bodies` (BR7.3, BR1.4);
  - muestra: `refs`, `redos`, `loader_usage`, `servers`, `report_closed`, `suggestion_conditions`, `config_write` y `synthetic`.
  - Todas las reglas citadas existen y dicen lo que el docstring afirma. `Principal` ya no habla del token anti-CSRF.
- **F-04 y F-05.** Cubiertos por pruebas parametrizadas: `test_una_opcion_repetida_sale_con_codigo_2` tiene 3 casos, y la etiqueta del README sale ahora de `main([])` con `capsys`.
- **Repositorio público y worktree.** No hay `/insumos` ni datos del piloto en el README, la bitácora ni la respuesta. El worktree está limpio.

## Hallazgos

### F-06 · NARANJA · contracts/README.md (fila C13 del inventario) · La versión de C13 es «(el del paquete)», contra el registro
La fila de `src/veridicus_contracts/model_calls.py` pone como versión «(el del paquete)», es decir, 0.1.0. El registro dice otra cosa: `contract-summary.md:1921` trae «`contracts/python/model_calls.py` — v1.0.0 (U1)». El README también se contradice a sí mismo, porque el párrafo de debajo de la tabla dice que «la versión del contrato no es la del paquete».

La tarea pide la versión «leída del árbol y del registro, no inventada». El árbol no declara ninguna versión (el docstring dice «C13, revisión 4»), así que la fuente es el registro.

Corrección: poner `1.0.0`, y si se quiere añadir la versión al docstring del módulo; eso es un cambio de docstring, dentro del alcance. Las pruebas no lo detectan porque la tabla fija no mira versiones.

### F-07 · AMARILLO · contracts/tests/test_readme.py:336-352 · Huecos del control de inventario
Con un guion propio sobre `discrepancias_del_inventario` encontré estos casos que devuelven `[]`:
- **Fila duplicada con un ID inventado.** Una fila `| C99 | … | \x60api/console.v2.yaml\x60 |` puesta delante de la fila buena no se detecta: el dict se queda con la última fila.
- **Fila duplicada con el ID correcto.** Tampoco se detecta.
- **Versión equivocada.** Cambiar la de `limits.v1.yaml` a `7.0.0` pasa. La prueba no compara versiones; es la misma causa por la que F-06 pasó.

Sugerencia: rechazar los archivos repetidos y comparar la versión con la del archivo o con una columna de la tabla fija.

### F-08 · AMARILLO · contracts/tests/test_readme.py:438-441 · El control negativo de F-03 es casi una tautología
`test_control_negativo_v_yaml_atribuido_a_otro_workflow_se_detecta` solo comprueba que `str.replace` quita la cadena; no pasa la fila alterada por la comprobación de `test_cada_comando_v_dice_que_workflow_lo_corre`. Además, `repo-level0.yml` corre `yamllint -s .github/` y no el comando V-YAML literal, que incluye `.pre-commit-config.yaml`. Conviene matizar «Lo corre» para V-YAML.

## Tareas candidatas (defectos reales fuera de alcance)
- Sigue la de la ronda 1: el correo del autor de los commits sale mal codificado en un repositorio público (K-72).

  > Nota del orquestador: se omitió el correo, que el informe original citaba literal, por ser un dato personal. El resto es literal.
- `checks/ci_workflows.py` sigue sin citar una regla BR o NFR en su docstring; solo cita AUTONOMIA-01. Lo dejo como candidata, porque el archivo es de T22b.

No pude escribir el informe en `docs/loop/revisiones/U01-T23/ronda-2.md` porque soy de solo lectura: el contenido es este mensaje y te toca guardarlo a ti.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/README.md (fila C13 del inventario)|La versión de C13 es «(el del paquete)» y el registro dice v1.0.0 (contract-summary.md:1921)
AMARILLO|contracts/tests/test_readme.py:336-352|El control del inventario no detecta filas duplicadas ni versiones equivocadas
AMARILLO|contracts/tests/test_readme.py:438-441|El control negativo de V-YAML es casi una tautología; repo-level0 no corre el comando V-YAML literal
INFORME: docs/loop/revisiones/U01-T23/ronda-2.md
```
