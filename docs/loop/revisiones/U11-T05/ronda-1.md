# Ronda 1 — U11-T05

**Veredicto:** NO-VERDE. El revisor fue `revisor` con opus, sobre `9a53d0c`.

Los criterios CA-1 a CA-8 pasan con las corridas del propio revisor:
- **CA-1:** 77 pruebas y 100 % de ramas en `composition.py`. Además, 71 pruebas y 98,24 % de cobertura en `cli/`.
- **CA-2:** solo cambió la línea de P-T04-1.
- **CA-3:** 111 pruebas, sin ningún fallo.
- **CA-4:** `lint-imports` da KEPT en los 5 paquetes y `tests/boundaries` pasa con 56 pruebas.
- **CA-5:** las 4 pruebas e2e pasan y la manual recolecta 2.
- **CA-6:** 235 y 161 pruebas al 100 %, y 459 en el anonimizador.
- **CA-7** y **CA-8:** limpios.

El revisor también comprobó lo siguiente:
- Los mutantes de `is_safe_for_corpus`, `_is_incident` y `_exceeded_limit` mueren todos.
- Los controles negativos de import-linter son reales.
- Un fallo de composición no hace ninguna llamada.
- La escritura es atómica y los códigos de salida coinciden con BR11.3.

## Hallazgos

| ID | Severidad | Lugar | Hallazgo | Arbitraje |
|---|---|---|---|---|
| F-01 | NARANJA | `cli/results_dir.py:46-47` | `is_safe_for_corpus` usa `absolute()` y no `resolve()`. Un `--salida` que pasa por un enlace simbólico hacia una carpeta rastreada por Git se acepta para el corpus (BR11.5). | **Corregir:** usar `resolve()` y añadir una prueba con un enlace simbólico. |
| F-02 | NARANJA | `tests/cli/test_results_dir.py:121` | `git ls-files resultados-locales` solo mira la raíz. No ve `libs/incoherence_analyzer/resultados-locales/`, que es justo donde escribe la corrida manual (BR11.6). | **Corregir:** usar el pathspec `:(glob)**/resultados-locales/**` y añadir un control negativo anidado. |
| F-03 | NARANJA | `tests/manual/test_real_provider.py:61-63` | La prueba manual pasa con una clave inválida: con un 401, la CLI sale con 0 y `estado: error`. | **Corregir:** exigir `estado == "ok"` y al menos una llamada en `registro.llamadas`. En el caso `contradiccion`, que la ausencia de hallazgos no se lea como éxito. |
| F-04 | AMARILLO | `README.md:24` | Al comando manual le falta decir que se corre desde la raíz del repositorio. Además, `timeout 900` es menor que el peor caso, unos 1800 s. | **Corregir el README:** indicar que se corre desde la raíz, conservar el literal de R-04 y la variante con `--extra cli`, y advertir que el peor caso pasa de 900 s. Recomendar `timeout 1800` como variante. Las dos diferencias con el plan van a la bitácora como precisión. |
| F-05 | AMARILLO | `cli/main.py:251-264` | Una señal que llega después de la última llamada termina con código 0. | **Corregir:** consultar la bandera también después del bucle, con su prueba. |
| F-06 | AMARILLO | `cli/main.py:273-276` | El aviso de VE-01 no sale cuando la entrada o el perfil fallan antes. Esto coincide con el orden de RD y BR11.2, pero BR9.5 dice «en cada ejecución». | **Aceptado como precisión:** anotarlo en la bitácora para la tabla de la unidad, sin cambiar el código. |
| F-07 | AMARILLO | `pyproject.toml`, contrato `layers` | El contrato no prohíbe que `domain` importe `api`. | **Corregir:** añadir el módulo a la lista prohibida. |

## Tareas candidatas

- BR11.6 nombra `evaluation/zine/paquete/`, que no está en `.gitignore` ni tiene prueba. Queda para US14 (ZINE).
