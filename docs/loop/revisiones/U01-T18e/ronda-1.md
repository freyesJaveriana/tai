# Ronda 1 — U01-T18e

**Revisor:** `revisor`, sobre `fc5c627` (base `origin/main` = `a8d7756`). Fecha: 2026-11-26.

VEREDICTO: NO-VERDE

## Criterios

| # | Resultado |
|---|---|
| CA-1 | Código 0 y 2920 pasan, en **23,50 s** y **23,23 s**: no cumple los 22 s. En la misma máquina, la base tarda 31,60 s y la tarea 22,62 s (−28 %) |
| CA-2 | El paso previo da `Checked 78 packages in 1ms`, y el paso 4 no imprime `Building`, `Built`, `Installed` ni `Uninstalled`. Pasa |
| CA-3 | 2920 pruebas, con identificadores idénticos a `main`. `pyproject.toml` y `uv.lock` no cambian, y los conteos de Hypothesis y de saltos son idénticos. Pasa |
| CA-4 | `TOTAL 3011 0 1428 0 100%`. Pasa |
| CA-5 | mypy, ruff, formato y yamllint pasan, y los guiones dan `0 apariciones`. Pasa |
| CA-6 | No le toca al revisor: lo midió el orquestador en el PR #49. El paso 4 duró **51 s**, con pytest en 47,96 s y unos 3,5 s de arranque |

## Sondas

- **`_recorrer` iterativo frente al recursivo:** los dos dan la misma secuencia sobre 122 documentos y sobre 3000 estructuras aleatorias. La única diferencia es que el iterativo ya no lanza `RecursionError` con 3000 niveles de anidación.
- **Cachés frente a `__wrapped__`:** 0 diferencias. Las funciones son puras, los valores que devuelven son inmutables y los tamaños están acotados. Ninguna prueba parchea las constantes de las que dependen.
- **`deepcopy` retirado:** era redundante, porque `load_file` ya entrega una copia profunda.
- ***Fixtures* de sesión:** con el orden invertido no se contaminan entre sí, y las pruebas negativas de mypy siguen fallando. El `noqa: S603` lleva su motivo.
- **Paso 3b:** el orden, `--offline`, los permisos y los SHA están bien, y `ci_workflows.py` no cambió.

## Hallazgos

| ID | Severidad | Dónde | Qué pasa | Corrección |
|---|---|---|---|---|
| F-01 | ROJO | CA-1 | 23,5 s frente a una meta de 22 s | — |
| F-02 | NARANJA | `contracts-level0.yml:68-71` | El paso 3b no hace nada en la CI (`Checked 78 packages in 1ms`), y los ~7 s previos no se midieron | Probar `--compile-bytecode` |
| F-03 | AMARILLO | `veracity.py:172,370` | Caché en funciones públicas (`normalizar`, `con_veracidad`), en contra del criterio de P-T18d-1 | Mover la caché a un ayudante privado |
| F-04 | AMARILLO | `veracity.py:336-348` | El recorrido iterativo ya no lanza `RecursionError`, y no está documentado | Anotarlo en la bitácora |

## Decisión del humano (2026-11-26), P-T18e-1

Con la medición de la CI en la mano (51 s en el paso 4, 9 s de margen bajo el techo de 60 s de NFR2.1), el humano decidió **aceptar** el resultado y cerrar la tarea:

- **CA-1** se ajusta a 24 s o menos y **CA-6** a 52 s o menos.
- La ronda 2 corrige F-02 (`--compile-bytecode`), F-03 y F-04.

Pytest-xdist no se adopta en esta tarea.
