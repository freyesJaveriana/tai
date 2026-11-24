# Ronda 4: U01-T18

VEREDICTO: VERDE

Corrí yo los cinco criterios sobre el HEAD `b969f03` (el código es `b89a635`) y todos pasan. F-01 y F-02 de la ronda 3 quedan cerrados, y los dos rojos los repetí yo: los dos fallan por la regla. No queda ningún ROJO ni NARANJA en pie. El humano fusiona.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 19 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18/contracts pytest tests/checks/test_loader_usage.py tests/checks/test_refs.py tests/checks/test_redos.py tests/checks/test_synthetic.py tests/checks/test_fixture_coverage.py tests/checks/test_ci_workflows.py --no-cov -q -p no:cacheprovider` | pasa: `202 passed in 6.55s` |
| 2a | Cobertura | `timeout 300 uv run … pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider` | pasa: `1886 passed in 269.50s (0:04:29)`. Quedan 30 s de margen. Mientras corría, lancé también CA-1, CA-4, CA-5 y las sondas. |
| 2b | 100 % en los seis | `uv run … coverage report --include=<los seis y _recorrido.py> --fail-under=100 --show-missing` | pasa: `TOTAL 512 0 236 0 100%`. `ci_workflows.py` da 19/0 y 4/0. |
| 3 | Suite del Bolt | `timeout 300 uv run … pytest tests --no-cov -q -p no:cacheprovider` | pasa: `2533 passed, 1 warning in 123.44s` |
| 4 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py --no-cov -q`, luego `mypy --strict src` y `ruff check .` | pasa: `8 passed`, `Success: no issues found in 41 source files` y `All checks passed!` |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T18/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18` | pasa: `0 apariciones` |

## Hallazgos de la ronda 3, comprobados

### F-01 (NARANJA): cerrado
- **El literal coincide con el módulo.** `REGLAS_EXACTAS` (`test_fixture_coverage.py:444-462`) tiene las 18 entradas de `REGLAS` con sus palabras clave: 15 BR más `NFR1.3`, `NFR10.2` y `NFRD-U1-07`. Entre `219b445` y `b89a635`, `src/` solo cambió en `ci_workflows.py`.
- **Mi mutación de la ronda 3 ahora falla.** Quité `NFRD-U1-07` y `NFR10.2` y amplié BR1.1 a `{required, pattern, type, enum}`, todo en memoria. Resultado: `1 failed, 22 passed`, `exit 1`. Falla `test_f01_la_lista_exacta_de_reglas_con_fixtures_y_sus_causas` en `:467`, con el diff exacto: BR1.1 distinta y faltan `NFR10.2` y `NFRD-U1-07`. Es la misma salida que pega la bitácora en sus líneas 5525-5553.
- **Una mutación más fina también falla.** Ampliar solo BR3.2 a `{enum, type}` da `1 failed, 22 passed`.

### F-02 (AMARILLO): cerrado
- **El patrón nuevo no tiene solapamiento.** Es `(?:\s+(?:--?[\w.][\w.-]*(?:=\S+|\s+[^\s-]\S*)?|--))*`:
  - el nombre empieza por `[\w.]`, así que `--a` solo se puede leer como `--` más `a`;
  - un valor no puede empezar por guion;
  - el `--` solo no es prefijo de las otras formas, porque detrás exige `\s` o el final.
- **La búsqueda es lineal.** Medí `kubectl apply` y `helm install` con las opciones `--a`, `-a`, `--a x`, `-n x`, `--`, `--a=1`, `--a-b.c`, `-- x` y `--n apply`, para n = 22, 30, 60 y 200. Ningún caso pasa de 0,0001 s. En la ronda 3, `--a` con n = 22 tardaba 1,04 s.
- **Los casos positivos y negativos no se aflojan.**
  - El diff de `test_ci_workflows.py` solo parametriza la prueba de tiempo; la sonda de las líneas 147-166 no cambió.
  - Repetí las formas prohibidas y todas se detectan: `kubectl -n x -- apply`, `-n x`, `--context=x`, `--namespace x`, `-v 9 --namespace x`, `/usr/bin/kubectl apply`, `--namespace=x -- apply`, `--dry-run=client apply`, `--kubeconfig x apply`, `helm --namespace v upgrade --install`, `helm -n v install` y `KUBE_CONFIG`.
  - Las lecturas no dan falso positivo: `describe applyset`, `--context=m -n x get pods`, `helm -n v list`, `helm --namespace v template` y `kubectl -- get apply`.
- **El rojo por tiempo es literal y falla por la regla.** Puse en memoria el `_OPCIONES` anterior y corrí la prueba final con `-k f02`. Resultado: `4 failed, 7 passed, 30 deselected`, `exit 1`. Fallan `[kubectl---a-30]`, `[kubectl---a-b.c-30]`, `[helm---a-30]` y `[helm---a-b.c-30]`, todos con `tarda más de 1 s`, igual que la bitácora en sus líneas 5561-5605. El `...` que aparece dentro de la cadena larga es el recorte de pytest, no de la bitácora.
- **Las pruebas no cambiaron después del rojo.** `git diff --stat c363cb5 b89a635` solo muestra `ci_workflows.py`.

## SHA y alcance
- **Alcance:** `git diff --name-status feat/b1-contratos...HEAD` da los mismos 16 archivos añadidos que en la ronda 3. Ninguno está fuera del alcance de la tarea ni de E-28. La base es `faa668c`, y entre `faa668c` y `35ec01c` solo cambia `decisiones-humano.md`, con 2 líneas.
- **SHA:** los 24 commits de `feat/b1-contratos..HEAD` cubren todos los SHA vigentes.
  - Cada marca «ronda 7: ahora X» apunta a un commit de la rama (`db9dc01`, `df6fa15`, `0d0b302`, `db44018`, `367e89a`, `6948bc0`, `bc7832b`, `4142fca`, `863c7da`, `460cfbc`, `ce901dc`, `abb0465`, `96b7239` y `219b445`).
  - Busqué líneas con un SHA sin marca de la ronda 7 y que no fueran de mapeo. Solo salen la línea 113 (`5f36fb4`, un commit de la base) y las líneas 5517, 5615 y 5885, que citan los SHA vigentes `c363cb5` y `b89a635`.
- **Precisiones:** E-31 está en `decisiones-humano.md:42`, P-T18-21 en `:85` y P-T18-22 en `:86`. Esta última corrige P-T18-17.
- **Worktree:** limpio al terminar (`git status --short` sale vacío).

## Hallazgos

### F-01 · AMARILLO · `checks/ci_workflows.py:31` · Falso positivo conservador con un valor que se llama como el verbo
`kubectl -n apply get pods` sale marcado como `kubectl apply`, porque `apply` se lee como verbo y no como valor de `-n`. Solo pasaría con un *namespace* o un valor que se llame `apply`. Falla hacia el lado seguro (marca de más, nunca de menos) y no bloquea.

## Tareas candidatas (defectos reales fuera de alcance)
- **K-53, tiempo de CA-2:** va en 269,50 s de los 300. En rondas anteriores fueron 245, 260,79 y 266,83 s, con otros comandos en paralelo; por sí solo no bloquea. Cada guardia nueva lo acerca al corte.
- **`queues/speech.v2.yaml:4`:** declara `info.version: 1.2.0` aunque su nombre dice v2 (lo anoté en la ronda 3).
- **Siguen abiertas:**
  - K-51, K-52 y K-55;
  - ampliar `ci_workflows` a `create`, `replace`, `patch`, `delete`, `uninstall` y `rollback`;
  - los dos archivos de §4.10 que siguen sin existir.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/ci_workflows.py:31|kubectl -n apply get pods sale marcado (falso positivo conservador, un valor que se llama como el verbo)
INFORME: docs/loop/revisiones/U01-T18/ronda-4.md
```
