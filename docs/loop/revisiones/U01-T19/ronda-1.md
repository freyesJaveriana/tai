# Ronda 1 — U01-T19

VEREDICTO: NO-VERDE

Veo dos defectos que bloquean y uno de evidencia. El más serio es CA-6. Ejecutado en el worktree, falla por una línea de la plantilla de PR nueva. La bitácora lo da en verde, pero su salida coincide con la que da el script corrido sin argumento desde `/workspace`: allí se revisa el `.github` de otra copia del repositorio, que no tiene la plantilla.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Pruebas de `tests/tools` | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T19/contracts pytest tests/tools --no-cov -p no:cacheprovider` | pasa: 60 passed en 5,14 s |
| 2a | V-GEN | `uv run … python -m veridicus_contracts.tools.gen_ts --check` | pasa: «4 archivos al día», código 0 |
| 2b | Vectores JCS | `uv run … python -m veridicus_contracts.tools.gen_jcs_vectors --check` | pasa, código 0 |
| 2c | V-SURFACE | `uv run … python -m veridicus_contracts.tools.security_surface --check` | pasa, código 0 (sus 13 pruebas están en el CA-1) |
| 3 | Compuerta con la lista real de excepciones | `uv run … python -m veridicus_contracts.tools.audit_gate tests/data/pip-audit-vacio.json --ignore .pip-audit-ignore.yaml` | pasa, código 0 |
| 4 | Suite completa del Bolt | `timeout 600 uv run … pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2585 passed, 1 warning, 127 s |
| 5 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py`, `mypy --strict src`, `ruff check .` | pasa: 8 passed, «Success: no issues found in 46 source files», «All checks passed!» |
| 6a | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T19/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T19` | **falla, código 1** (ver F-01) |
| 6b | Ningún *workflow* con `--write` | `uv run … pytest tests/checks/test_ci_workflows.py --no-cov -q` | pasa: 41 passed |

Al terminar, el worktree quedó limpio (`git status --porcelain` vacío).

## Hallazgos

### F-01 · ROJO · `.github/pull_request_template.md:27` y CA-6 · la plantilla de PR rompe AUTONOMIA-01 y la evidencia del CA-6 no sale del diff

- **El fallo.** El script que corrí con la raíz del worktree imprime:
  `check-no-cluster-apply: AUTONOMIA-01 incumplida. … .github/pull_request_template.md:27:- [ ] Ningún valor de Secret, .env, kubeconfig ni clave privada.`
  El patrón del script incluye `kubeconfig`, y `repo-level0.yml:55` corre ese script en la CI desde la raíz. Así, el PR de esta tarea fallaría en el nivel 0.
- **La evidencia falsa.** La bitácora (línea 83) dice `0 apariciones en ./.github ./scripts.`. Corrí el mismo script sin argumento desde `/workspace` y da exactamente ese texto, porque revisa el `.github` de esa copia del repositorio, que no tiene la plantilla.
- **El arreglo.** Queda dentro del alcance: reescribir la línea 27 de la plantilla sin el término, por ejemplo «credenciales de acceso al clúster». Ni el script ni el patrón se tocan. Después hay que volver a correr el CA-6 con la raíz del worktree.

### F-02 · NARANJA · `tools/security_surface.py:109-115` · la huella no distingue «autenticación opcional» de «autenticación obligatoria»

- **El problema.** `_esquemas_de_seguridad` convierte los requisitos de seguridad en un solo conjunto de nombres. Con eso se pierde la alternativa anónima `{}`, la diferencia entre «todos estos esquemas» y «cualquiera de ellos», y los *scopes*.
- **La sonda.** Sobre una copia en memoria de C1, puse `security: [{sessionCookie: []}, {}]` en `GET /auth/me`. El comando fue `uv run … python -c "… s.construir(r, {'api/console.v2.yaml': c1}) …"` y respondió `True ['sessionCookie'] ['sessionCookie']`: la huella no cambia aunque la operación pase a aceptar peticiones anónimas.
- **Por qué importa.** Es justo el «cambio de seguridad visible» que la tarea pide en la línea 40. La prueba actual solo cubre el caso `security: []`.
- **El arreglo.** Guardar los requisitos como lista de alternativas, cada una con sus esquemas y *scopes* ordenados, y sumar este control negativo a `test_security_surface.py`.

### F-03 · NARANJA · `docs/loop/bitacoras/U01-T19.md:14-26` · el rojo no está literal y no se volvió a correr tras cambiar las pruebas

- **No es literal.** El bloque del rojo es un resumen escrito a mano («(19 pruebas: …)», «el arnés recorta el centro»), no la salida completa. La tarea (línea 138) y la regla del loop piden redirigirla a un archivo y anexarla con `cat >>`. Eso no se hizo, aunque el recorte del arnés lo hacía necesario.
- **Las pruebas cambiaron después del rojo.** `git diff 0659b13 46db948 -- contracts/tests/tools` muestra cambios en `test_security_surface.py` (la aserción de las secciones) y en `test_audit_gate.py` (dos casos con parámetros y una prueba nueva). El paso 4 de la tarea (línea 140) pide repetir el rojo con los archivos del commit final y pegar esa salida, y no está.
- **La forma del rojo sí vale.** Que falle por «módulo ausente» es lo que la tarea admite en la línea 142, porque la bitácora lo declara y el verde muestra cada control negativo. Con esqueletos de firma habría sido mejor, pero no era obligatorio. El defecto es solo de evidencia.

### F-04 · AMARILLO · `tests/tools/test_security_surface.py:149-158` · la prueba de comentarios y espacios no incluye C1

La tarea pide que un comentario o un espacio en la copia de C1 no mueva la huella. La prueba lo hace con C8, C25, el catálogo de errores y los rótulos, pero no con un contrato OpenAPI. Agregarlo es barato.

## Hechos pedidos (no son hallazgos)

**P-T19-4, generador con `random.Random`:**
- Los bytes son idénticos en todas las corridas. El SHA-256 da `641add80d71a…0499` en cuatro casos:
  - `sha256sum` del archivo;
  - `python -c` desde fuera de pytest;
  - `python -X dev`, generando dos veces seguidas (`True`);
  - con `PYTHONHASHSEED=987`.
- Dentro de pytest también coincide: `test_lo_generado_es_igual_a_lo_versionado` pasa.
- Están `1e21`, `-0.0`, `5e-324` y `0.1`, además de claves no ASCII (incluida una fuera del plano básico) y anidamiento. Los cubren los vectores fijos y los comprueba `test_estan_los_cuatro_numeros_limite…`.
- Ningún rango de caracteres cae en los sustitutos UTF-16, así que no salen sustitutos sueltos.
- `src/` no importa Hypothesis: `grep -rn -i hypothesis …/contracts/src` solo encuentra comentarios y listas de carpetas ignoradas.
- Aceptar el cambio lo decide el humano.

**P-T19-2, `schema_version` en la huella:**
- Las claves de la raíz son las siete secciones más `schema_version`, y la prueba lo fija así.
- La guardia de T18 sigue intacta: el diff de `tests/checks` y `src/veridicus_contracts/checks` está vacío.
- `pyproject.toml`, `uv.lock`, `conftest.py` y `helpers.py` no se tocaron, y no hay nada fuera del alcance en el diff.

**Notas para T20 y la CI:**
- **`-0.0`:** `JSON.parse` de JavaScript ya lo lee como menos cero, y JCS lo escribe como `0`. No hace falta resolver nada ahora; basta con que T20 lo pruebe.
- **`build/` para `pip-audit`:** `audit_gate` corre después de `pip-audit`, así que crear la carpeta en él no basta. El paso del *workflow* (paso 24) debe crearla antes de correr `pip-audit`. El *workflow* está fuera del alcance de esta tarea, así que la nota queda bien diferida. Conviene que conste en la tarea del *workflow* y no solo como «T22/CI».

## Tareas candidatas
- Ninguna además de la nota de `build/`, que pertenece a la tarea del *workflow*.

```
VEREDICTO: NO-VERDE
ROJO|.github/pull_request_template.md:27 (CA-6)|La plantilla de PR dispara check-no-cluster-apply.sh (kubeconfig) y la evidencia «0 apariciones» de la bitácora no sale del diff
NARANJA|contracts/src/veridicus_contracts/tools/security_surface.py:109-115|La huella no distingue autenticación opcional ({}), alternativas ni scopes de los requisitos de seguridad
NARANJA|docs/loop/bitacoras/U01-T19.md:14-26|Rojo no literal y no repetido tras cambiar las pruebas después de 0659b13
AMARILLO|contracts/tests/tools/test_security_surface.py:149-158|La prueba de comentarios y espacios no cubre C1
INFORME: docs/loop/revisiones/U01-T19/ronda-1.md
```
