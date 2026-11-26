# Revisión acotada: arreglo corto de F-06 en U10-T03 (`d347c38..6374bb5`)

Decisión del humano después de la ronda 2 NO-VERDE (ML-5): las formas por palabra de un tramo de varias palabras no se propagan a `system`, y F-04 queda declarado como límite.

**VEREDICTO: VERDE.** El arreglo cumple lo que pidió el humano y pasan los cuatro criterios. Queda una sola cosa que no bloquea: la bitácora promete más de lo que el código garantiza, y detrás de eso hay un hueco de PD-5 que ya existía antes de este cambio y que debe decidir el humano.

## Hallazgos

**F-09 · AMARILLO · `docs/loop/bitacoras/U10-T03.md:22` · La frase sobre PD-5 es más amplia de lo que el código cumple**
- **Qué dice la bitácora:** que `system` y los turnos anteriores quedan idénticos byte a byte con y sin el turno nuevo.
- **Dónde sí se cumple:** con las formas por palabra, que es lo que pedía F-06.
- **Dónde no:** cuando el turno nuevo trae suelto un apellido que `system` ya contenía, ese apellido es una forma de tramo completo. Por la decisión del humano, esa forma tiene que seguir llegando a `system`. Entonces `system` cambia y el primer turno pasa de `[ENTIDAD_1]` a `[ENTIDAD_2]`.
- **Ya pasaba antes:** con el código de `d347c38` da el mismo resultado, así que este diff no lo introduce.
- **Qué falta:** ajustar la frase de la bitácora y abrir una tarea candidata (K-84).

## Comandos que corrí
Los de `uv` van con `--frozen --offline --directory .../libs/anonymizer`.
1. **Rojo:** con el código de `d347c38` y el `test_masking.py` de `6374bb5`, `pytest tests/domain/test_masking.py` da 5 fallos y 39 pasan (las dos pruebas de F-04 reescritas y los tres casos de PD-5 con `system` delante). En el worktree, las 44 pasan.
2. **Sonda de F-06:** un apellido suelto en `system`, delante y detrás, y un turno nuevo con nombre y apellido: `system` y los turnos anteriores quedan iguales y la restauración es exacta. Lo mismo con una palabra de inicio de frase no permitida pegada a un nombre, y con un apellido compuesto con guion.
3. **Lo que no debía romperse:** siguen llegando a `system` un nombre completo, un nombre suelto, un número de identificación y un radicado; F-01 sigue cerrado; `restore` devuelve el original exacto; `pytest tests/domain`: 191 pasan.
4. **CA-2:** 128 pasan, 100 % de ramas en `sentence`, `detection` y `masking`.
5. **CA-4:** `git diff --exit-code afa8f20 -- libs/anonymizer/tests/guards libs/anonymizer/tests/contracts libs/anonymizer/tests/support.py libs/anonymizer/tests/fixtures`: código 0.
6. **CA-5:** 100 pruebas, 0 errores, 87 fallan y las 87 por `NotImplementedError: build_anonymizer lo implementa U10-T04`.
7. **CA-6:** `mypy --strict src tests`, `ruff check .` y `ruff format --check .` sin problemas; las tres guardias en `0 apariciones`; el `grep` de `time` o `datetime` en `domain/` no imprime nada.
8. **Alcance:** el diff solo toca `masking.py`, `test_masking.py` y la bitácora; ningún umbral baja.
9. **`git status --porcelain` al terminar:** vacío.

```
VEREDICTO: VERDE
AMARILLO|docs/loop/bitacoras/U10-T03.md:22|La frase de PD-5 es más amplia de lo que se cumple: una forma de tramo completo nueva todavía cambia system y renumera (ya pasaba antes; K-84)
INFORME: docs/loop/revisiones/U10-T03/ronda-3.md
```
