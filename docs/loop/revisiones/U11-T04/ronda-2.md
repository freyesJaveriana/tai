# Ronda 2 — U11-T04

**Revisor:** `revisor` (opus), sobre `19f83df` (base `fa06b71`; la ronda 1 llegó hasta `3fdf3b3`). Fecha: 2026-11-26.

VEREDICTO: VERDE

Los siete criterios pasan con las corridas del revisor, F-01 queda cerrado y los cinco mutantes mueren. Queda un solo AMARILLO, que no bloquea.

## Criterios

| # | Resultado |
|---|---|
| CA-1 | 235 pasan. Ramas: `analyze.py` 20/20, `preflight.py` 20/20, `deadline.py` 6/6, `messages.py` 6/6 y `api.py` al 100 %. `test_run_perf` en 0,24 s |
| CA-2 | Contra `c7e6542` solo cambia la línea 109 (P-T04-1); la línea 108 y el control negativo siguen intactos |
| CA-3 | 6 fallan (CLI, `NotImplementedError` en `cli/main.py:29`), 105 pasan y 0 `ERROR` |
| CA-4 | 195 pasan; `scan.py` 26/26 y `notice.py` 6/6 |
| CA-5 | Dominio 161 pruebas y gateway 31, los dos al 100 % |
| CA-6 | mypy, ruff y formato dan código 0 en las seis corridas |
| CA-7 | `0 apariciones` ×3; ninguna clave `sk-` nueva fuera del canario |

## Sondas

- **Una sola lectura del *prompt*:** `prompt_bytes()` se llama una sola vez en `src` (`analyze.py:313`), y `build_messages` siempre recibe `self.prompt`. Los `@cache` solo guardan esquemas.
- **Mutantes:** los cinco mueren.
  - M-1 y M-2: vuelven a leer el archivo (`4 == 1`).
  - M-3: `_stamp` sin efecto.
  - M-4: `_prompt_matches` sin la huella de los bytes.
  - M-5: `_prompt_matches` siempre verdadero.
- **A-01:** `_stamp` informa la huella de los bytes en los tres caminos (`ok`, `_failed` y la salida sustituta).
- **K-88:** con los 64 ceros sigue dando `salida_invalida`, con 0 peticiones.
- **A-02 y A-03:** la bitácora quedó corregida, y el plan no tiene cambio neto en `fa06b71..19f83df`.

## Hallazgos

### A-04 · AMARILLO · `domain/output.py:131,141`

**Qué pasa:** dos reglas aprobadas dicen cosas distintas sobre de dónde sale la huella en la salida de error. BR3.1 (`rules.md:180`) dice «bytes leídos» y BR8.7 (`rules.md:478`) dice «configuración». La implementación sigue a BR3.1, pero el docstring de `build_output` todavía cita BR8.7.

**Qué hacer:** anotarlo en la tabla de precisiones de la unidad y ajustar el docstring. Va a U11-T05.

## Candidatas

- `load_response_schema` vuelve a leer `data/schemas/*` en cada llamada, y esos bytes no entran en ninguna huella. Hay que decidir si se leen una sola vez por corrida.
- Siguen las de la ronda 1:
  - literales invisibles;
  - límites que no se leen del entorno;
  - U10: `[PERSONA_n]` sin tratamiento, y `TEST`/`T2` enmascarados como `[ENTIDAD_n]`.
