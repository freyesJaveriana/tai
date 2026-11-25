# Ronda 1 — U01-T23

VEREDICTO: NO-VERDE

Hay dos hallazgos NARANJA y ningún ROJO. Todos los criterios de aceptación pasan con mis propias ejecuciones. El rojo lo reproduje yo y falla por la regla. El *workflow* cumple también las reglas nuevas de U01-T22b. Lo que falla es la fidelidad del inventario del README frente al registro, y tres docstrings que dicen cosas que no son ciertas.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | README y herramienta | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T23/contracts pytest tests/test_readme.py tests/tools/test_check_tag.py --no-cov -p no:cacheprovider` | pasa, 26 passed |
| 2 | Etiqueta esperada | `uv run ... python -m veridicus_contracts.tools.check_tag --tag contracts-v0.1.0` y `--tag v0.1.0` | pasa: código 0, y código 1 con «la etiqueta 'v0.1.0' no es la esperada 'contracts-v0.1.0' …» |
| 3 | V-SUITE | `timeout 120 uv run --frozen --offline --directory .../contracts pytest -p no:cacheprovider -q` | pasa: 2645 passed, 0 omitidos, 29,5 s (por debajo de 60 s), cobertura 97,90 %, `check_tag.py` al 97 % |
| 4 | Los docstrings no cambian el código | `python -c` propio: `ast.dump` sin docstrings de `git show 8a5515a:<f>` contra `HEAD:<f>` | pasa: IGUAL en los 10 archivos existentes (no son 9, son 10); `check_tag.py` es nuevo |
| 5 | Tipos, *lint*, guardias y YAML | `mypy --strict src`, `ruff check .`, `check-no-cluster-apply.sh`, `check-no-insumos.sh`, V-YAML | pasa: sin errores, «All checks passed!», 0 apariciones, 0 apariciones, código 0 |
| 6 | Archivos del diff | `git -C /workspace/.worktrees/U01-T23 diff --name-only feat/b1-contratos...HEAD` | pasa: solo archivos permitidos; en `.github/workflows/contracts-level0.yml` cambian solo el disparador y un paso |

## Comprobaciones adicionales
- **Rojo.** Lo reproduje en el scratchpad con el esqueleto de 146a9a9 y el `test_check_tag.py` de HEAD: 14 fallos por la regla («assert 3 == 0», «DID NOT RAISE VersionInvalida») y ningún error de importación. `git diff 146a9a9 HEAD -- contracts/tests` está vacío, así que las pruebas no cambiaron después del rojo.
- **Sondas de `check_tag`.** Todas terminan con código 1:
  - `contracts-v0.1.0-rc1`, `contracts-v0.1`, `"contracts-v0.1.0 "` y `"contracts v0.1.0"`;
  - un `pyproject.toml` sin `[project]`, uno con `project = [1]` y uno con `version = 1`;
  - un archivo que no existe, un directorio y una versión con salto de línea.
  - `--tag` sin valor termina con 2. Todos los mensajes están en español.
- **Workflow.**
  - El disparador es `push.tags: ["contracts-v*"]`.
  - El paso nuevo lleva `if: github.ref_type == 'tag'` y recibe `ETIQUETA: ${{ github.ref_name }}` por `env`, sin interpolarlo en `run:`.
  - La raíz conserva `permissions: contents: read`, no hay `uses:` nuevos, los 3 existentes están fijados por SHA de 40 caracteres y no hay `--write`.
  - Pasé el `ci_workflows.py` **comprometido** de `tarea/U01-T22b`, leído con `git show`, sobre este worktree: `[]`, sin ningún problema.
- **`errors-level0` con la etiqueta.** No es un problema: es de solo lectura, con `contents: read` y sin publicar nada, y vuelve a validar `libs/errors` en el commit etiquetado.
- **uv.**
  - `uv add --help` (0.13.9) documenta `--tag`.
  - Corrí `uv add --frozen --offline` en un proyecto del scratchpad y escribió `dependencies = ["veridicus-contracts"]` y `{ git = "https://github.com/freyesJaveriana/tai", subdirectory = "contracts", tag = "contracts-v0.1.0" }`. Es equivalente a la línea del README; solo cambia el orden de las claves.
  - El remoto `origin` coincide.
- **Ejemplos del README.** Los tres corren con firmas reales: `limits.load` devuelve un dict de 64 cifras, `profiles.validate` devuelve el perfil `prueba-generica` y el validador da 1 error («{} should be non-empty»).
- **F5 y F7.** Son fieles a `functional-spec.md` §F5 y §F7. `gen_ts` y `gen_jcs_vectors` de verdad no tienen `--write`: escriben sin argumentos y comparan con `--check`. El README documenta esa forma real. `HUELLAS_APROBADAS_C6` existe en `tests/conftest.py:25`.
- **Comandos V-\*.** Son idénticos, uno a uno, a la tabla del plan (líneas 147 a 159).
- **Glosario.** Tiene los cinco términos, sin traducciones dobles. El control negativo está parametrizado por término y hay otro para cuando falta la sección.
- **Repositorio público.** No hay `/insumos`, datos del piloto ni datos reales en el README, en las pruebas ni en la bitácora.
- **Docstrings de lo público.** Todo módulo y toda función o clase pública de nivel superior de `src/` tiene docstring (lo comprobé con `ast`).
- **Worktree.** Limpio: solo hay cachés ignoradas.

## Hallazgos

### F-01 · NARANJA · contracts/README.md:14-48 · El inventario inventa IDs y le faltan contratos del registro
La tarea pide que el inventario «se lee del árbol y del registro, no se inventa». Lo comparé con `contract-summary.md` (líneas 89 a 137) y con `functional-spec.md` §1 (líneas 63 a 100):
- **IDs inventados.** El registro dice que estos archivos son «sin número de contrato», pero el README les pone uno:
  - `api/speech-internal.v1.yaml` aparece como **C5** (el registro dice «No es C1 … ni C16»);
  - `integrity/testimony-warning-cases.v1.yaml` y `integrity/scan-cases.v1.yaml` aparecen como **C8**;
  - `ui/result-labels.v2.yaml` aparece como **C8**.
- **Faltan contratos que U1 entrega.** No aparecen **C10, C11, C12, C23 y C24** (los `Protocol` de `human_review.py`, `report_ports.py`, `identity.py`, `access_log.py` y `retention.py`), ni los tipos de **C13** en `model_calls.py`. `functional-spec.md:83-84` los lista en el inventario de U1.
- **Lo que sí está bien.** Las versiones coinciden con el archivo en las 33 filas; las comparé con un guion propio contra `info.version`, `x-veridicus-version`, `schema_version`, `version` y `contrato.const`.
- **Por qué las pruebas no lo atrapan.** `test_el_inventario_nombra_cada_archivo_de_contrato` solo comprueba que aparezcan las rutas `.yaml` y `.json`; no mira los ID ni los `.py`.

Corrección sugerida: marcar esas filas como «(sin número)», añadir las filas de C10 a C13, C23 y C24 con su `.py` y, si se quiere, que la prueba compare los ID con una tabla fija.

### F-02 · NARANJA · docstrings de checks/auth_surface.py:3, checks/error_codes.py:3 e identity.py:20 · Docstrings que afirman algo falso
La tarea pide «cada módulo de `checks/`, con la regla que protege». Lo comparé con `rules.md` (líneas 345 a 380) y con `security-design.md:697`:
- **`auth_surface.py`** dice que protege «BR7.1 y BR7.4». BR7.1 trata de que no haya operaciones que escriban configuración, y BR7.4 de que cada `code` tenga una clase de excepción. El módulo comprueba sesión y roles, que es NFR10.12 / NFRD-U1-12.
- **`error_codes.py`** dice «BR7.2 y BR7.3 (… ningún `code` sin excepción)». BR7.3 trata de los cuerpos con `additionalProperties: false`; la regla de «code con excepción» es BR7.4.
- **`identity.py` `Principal`** dice que el principal tiene «su token anti-CSRF», pero el `Protocol` solo declara `user_id`, `username` y `role`. El token es `Authenticator.csrf_token`.

El AST no cambia, así que no hay desborde; el defecto es de contenido.

### F-03 · AMARILLO · contracts/README.md:141-142 · «Son los mismos que corre el *workflow*» es impreciso
`contracts-level0.yml` no corre V-YAML (yamllint solo aparece ahí en comentarios; el comando está en `repo-level0.yml`), y V-SURFACE va dentro de la suite. Mejor decir qué *workflow* corre cada uno.

### F-04 · AMARILLO · tools/check_tag.py:52-62 · `--tag` repetido: gana el último
`main(['--tag','x','--tag','contracts-v0.1.0'])` devuelve 0. En la CI no se puede explotar, porque se pasa un solo argumento, pero un argumento duplicado debería dar el código 2.

### F-05 · AMARILLO · tests/test_readme.py:129 · La prueba ata la etiqueta a la función, no a la salida de la CLI
Usa `etiqueta_esperada()`, que es lo mismo que imprime `main`. Es aceptable; si se quiere el vínculo literal con «lo que imprime `check_tag`», usar `main([])` con `capsys`.

## Tareas candidatas (defectos reales fuera de alcance)
- El correo del autor del commit 146a9a9 sale mal codificado en un repositorio público. Conviene revisar la configuración `user.email` del contenedor; no es de esta tarea.

  > Nota del orquestador: en esta copia se omitió el correo, que el informe original citaba literal, porque es un dato personal. El resto es literal.
- No corrí V-PKG (`check_package`), porque instala con red. `test_package_map` pasa en la suite.

No pude escribir el informe en `docs/loop/revisiones/U01-T23/ronda-1.md` porque soy de solo lectura: el contenido es este mensaje y te toca guardarlo a ti. Mis sondas quedaron en el scratchpad, en /tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/sondas-t23/.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/README.md:14-48|El inventario inventa IDs (C5/C8 en archivos sin número) y le faltan C10-C13, C23 y C24
NARANJA|contracts/src/veridicus_contracts/checks/auth_surface.py:3, checks/error_codes.py:3, identity.py:20|Docstrings con reglas BR equivocadas y un token anti-CSRF que Principal no tiene
AMARILLO|contracts/README.md:141-142|«Son los mismos que corre el workflow» es impreciso para V-YAML y V-SURFACE
AMARILLO|contracts/src/veridicus_contracts/tools/check_tag.py:52-62|--tag repetido: gana el último en vez de dar código 2
AMARILLO|contracts/tests/test_readme.py:129|La prueba ata la etiqueta a etiqueta_esperada() y no a la salida de la CLI
INFORME: docs/loop/revisiones/U01-T23/ronda-1.md
```
