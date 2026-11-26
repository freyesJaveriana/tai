# Ronda 3 — U11-T02

`revisor` (`opus`), 2026-11-26, sobre `f5b0594`.

VEREDICTO: VERDE

Corrí yo los siete criterios y los siete pasan. F-07 a F-11 están cerrados y ninguna de las correcciones se rompió con los mutantes que probé. No queda ningún ROJO ni NARANJA. Hay un AMARILLO nuevo (F-12), que no bloquea.

## Criterios de aceptación, verificados por mí

| # | Resultado |
|---|---|
| CA-1 | Pasa: 100 pruebas; `validate.py` (98 líneas, 34 ramas) y `floors.py` al 100 % |
| CA-2 | Pasa: 186 pruebas; `scan.py` (24 ramas) y `notice.py` (6 ramas) al 100 % |
| CA-3 | Pasa: `git diff --exit-code c7e6542… -- <las 6 rutas>` da código 0, sin salida |
| CA-4 | Pasa con `--extra cli`: `errors="0" failures="111" tests="111"`; los 111 son `NotImplementedError` de T03 a T05 |
| CA-5 | Pasa: `mypy --strict`, `ruff check` y `ruff format --check`, 6 de 6 con código 0 |
| CA-6 | Pasa: `0 apariciones` en los tres scripts |
| CA-7 | Pasa: ninguna coincidencia |

**Otras comprobaciones:**
- **Alcance:** el diff contra `bolt/b11a-analyzer` solo toca `libs/execution_profiles`, `libs/integrity_policy` y `docs/loop`. En `pyproject.toml` solo se agregó el `force-include` del perfil.
- **Pruebas:** no hay `skip`, `xfail` ni `no cover`, y ningún umbral se bajó.
- **Worktree:** limpio al terminar.
- **Cadenas con forma de clave:**
  - Solo aparece `sk-sintetico-canario-7f3a91c2d4e5`, que es el que permite `.gitleaks.toml:24`. Está en `test_profile_contract.py:26` (congelado), `test_loader.py:25` y `test_validate.py:17`.
  - Ninguna coincidencia de `api03`, `AKIA…`, `ghp_`, `xox[bp]-` ni `BEGIN … PRIVATE`.

## Cierre de la ronda 2

**F-07, cerrado.** Hice dos barridos contra el escáner real (Unicode 15.0.0).
- **Se detectan todas las `Mn`, `Me` y `Cf`:** 1985 `Mn`, 13 `Me` y 170 `Cf`.
- **De los `Default_Ignorable_Code_Point`, solo evaden:**
  - los 4 rellenos Hangul `Lo`;
  - 3769 puntos `Cn` sin asignar.

  Los dos grupos van a la candidata de C8.
- **Mutante en memoria** (`{'Cf'}`): fallan las 8 pruebas nuevas.
- **Sin falsos positivos nuevos.**
- **Tildes precompuestas y descompuestas** (NFC y NFD): se detectan, también con U+034F o U+FE0F en medio.

**F-08, cerrado.** Cuatro mutantes sobre la prueba de las huellas, y los cuatro mueren.

**F-09, cerrado.** Lo documenta el docstring de `EffectiveConfig` (`loader.py:47-48`), y también la bitácora.

**F-10, cerrado.** `re.ASCII` está en `validate.py:32`. Si se quita en memoria, la prueba falla.

**F-11, cerrado como limitación declarada.** Lo cubre una prueba que remite a la candidata de C8.

## Hallazgos

### F-12 · AMARILLO · `libs/integrity_policy/src/veridicus_integrity_policy/scan.py:133` · El tramo de una coincidencia deja fuera las marcas que siguen a su última letra

`end = origin[found.end() - 1] + 1` termina en la última letra plegada.

**Evidencia:**
- `fals` + `o` + U+0301 da `(2, 7)`: la tilde queda fuera.
- `engañó` en NFD se informa como `engaño`.

**Impacto.** La detección se mantiene, así que AUTONOMIA-03 no se ve afectada. Lo que falla es la posición original que promete el docstring y el nombre del término cuando la entrada está en NFD. El defecto viene desde `58df79f`.

**Corrección sugerida:** extender `end` sobre las marcas descartadas que siguen, con su prueba, aquí o en T04.

## Tareas candidatas (fuera de alcance)

- **C8:** fijar la normalización (NFKC, homoglifos, los `Default_Ignorable` fuera de WB4) y la regla de separación con un `Cf` (F-11).
- **Bitácora:** anotar el commit `f5b0594` del orquestador, que unificó el *canary*.

```
VEREDICTO: VERDE
AMARILLO|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:133|El tramo de una coincidencia deja fuera las marcas que siguen a su última letra (engañó en NFD se informa como engaño)
INFORME: docs/loop/revisiones/U11-T02/ronda-3.md
```
