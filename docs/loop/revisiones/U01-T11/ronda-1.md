# Ronda 1: U01-T11

VEREDICTO: NO-VERDE

Revisión de `tarea/U01-T11` en 457ae17 (base 8e9fb75). El sha256 de la tarea coincide (`31263263…239e`).

## Criterios de aceptación

| # | Resultado |
|---|---|
| CA-1a | 356 passed |
| CA-1b | 4 passed, 20 deselected |
| CA-2 | 17 passed, 7 deselected |
| CA-3 | Cobertura del 100 %, sin nada sin cubrir: `scan_cases` tiene 236 sentencias y 116 ramas; `veracity`, 221 sentencias y 102 ramas |
| CA-4 | 8 passed |
| CA-5 | mypy `Success`; ruff `All checks passed!` |
| CA-6 | 0 apariciones |
| Rojo | Se reproduce: `ImportError` en los dos módulos y 4 fallos de T03 por «contrato ausente» |

**Mutación sistemática.** Se generaron mutantes sobre el árbol sintáctico de los dos módulos:

| Módulo | Mutantes | Vivos | Vivos no equivalentes |
|---|---|---|---|
| `scan_cases.py` | 379 | 2 | ver F-04 |
| `veracity.py` | 426 | 5 | ver F-04 |

## Hallazgos

### F-01 · NARANJA · `veracity.py:107` y `:295-300`: BR3.3 no detecta camelCase

`SEPARADOR_DE_SEGMENTOS` solo parte los nombres por `_`, `-` y espacios. Por eso no detecta `isLying`, `veracityScore`, `esFalso`, `esVerdadero`, `falsoPositivo` ni `MintioEnLaHora`.

**Corrección:** partir también en las fronteras de minúscula a mayúscula y añadir un control negativo.

### F-02 · NARANJA · `veracity.py:282-292`: `components.parameters` no se recoge

La guardia solo lee `parameters` cuando es una lista, y en `components` es un mapa. Por eso `{'components':{'parameters':{'P':{'name':'es_falso'}}}}` da `[]`.

### F-03 · NARANJA · `veracity.py:314-347`: BR3.2 incompleta

- Falta el enum `estado` (`ok` / `error`).
- El criterio de «dos o más valores compartidos» deja pasar una copia desviada que comparte un solo valor. Hay una prueba que fija ese comportamiento como correcto.

**Corrección:** comparar por la ruta declarada en C1, C7 y C19.

### F-04 · NARANJA · Mutantes vivos no equivalentes

- **`scan_cases.py:263`:** el mutante `+ 2` en el `range` sobrevive. Ningún caso de aviso de testimonio tiene las 8 palabras al final del turno.
- **`veracity.py:46`:** el sufijo `.yml` no tiene ninguna prueba.

### F-05 · NARANJA · Para el humano: contradicción entre fuentes aprobadas sobre C8

Dos grupos de fuentes aprobadas fijan listas distintas.

**Fijan 9 términos:**
- BR5.1;
- contract-summary C8, revisión 4 («1.0.0 conserva 9 términos»);
- la tarea.

**Piden más términos:**
- VE-02 (`requirements-adenda-02.md:44-46`, MUST, sin rebaja por DD-07) suma «prueba», «probatorio», «pliego», «inculpa», «miente», «engaño» y «falso», con sus variantes, «en una versión nueva de la lista, por PR».
- NFR11.3 de U1 (`security-requirements.md:130`) exige «C8 v2 … con los términos de VE-02».
- A-1 da por hecho que «prueba» se escanea.

**Comentario falso:** `contracts/integrity/notice.v1.yaml:3` afirma que «prueba» falla en cualquier otra cadena. Con la C8 actual eso no es cierto.

### F-06 · AMARILLO · E11 frente a D-2: no hay contradicción real

E11 no exige que el tramo sea solo el término, así que la lectura del codificador es correcta.

**Sugerencia:**
- anotar en la tabla de precisiones que E11 usa un tramo largo;
- llevar la excepción de D-2 a BR5.3, como manda FD-U1-14.

### F-07 · AMARILLO · Mejoras sin bloqueo

- El rojo de los módulos es un error de colección y no un fallo regla por regla.
- C8 añade `quote_fields` y `excluded_whole_texts` sin una precisión registrada.
- `DIRECTORIOS_DE_DATOS` es una lista fija.
- Los nombres de `$defs` y `components.schemas` no se comparan.
- Ninguna aclaración tiene un `expect` que no sea un objeto.

## Sin hallazgo

- **C8:**
  - los 9 términos y las 5 categorías;
  - coincidencia por palabra completa, sin distinguir mayúsculas ni tildes;
  - delimitadores «»;
  - las exclusiones de BR5.5.
- **Textos:** VE-01 y VE-05 son literales.
- **Casos de escaneo:** uno por término y por frase, más E10–E14, E30 y D-2.
- **Espacios en blanco:** `whitespace_code_points` es igual a `str.isspace()` y no incluye U+FEFF.
- **Rótulos:** los 9 son exactos, y E17 da rojo.
- **Datos:** todos sintéticos.
- **Términos prohibidos:** solo aparecen en C8, en los casos de escaneo y en el fixture negativo de T03.
- **Mensajes:** no llevan texto del documento.
- **Alcance:** no toca nada fuera de lo previsto.

## Candidata fuera de alcance

- §4.8 y NFR11.3 excluyen del escaneo `integrity/usage-rules.v1.yaml` y `integrity/clarification-speech.v1.yaml`, pero ningún paso del plan los produce.
