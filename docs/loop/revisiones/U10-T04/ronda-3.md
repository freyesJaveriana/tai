# Revisión acotada de F-11 en U10-T04 (arreglo corto por ML-5)

El arreglo corrige el caso que describía F-11, pero el oráculo nuevo de `system` deja fuera más de lo que debe: no comprueba ni los identificadores ni los nombres de una sola palabra.

## Hallazgo

**F-12 · NARANJA · `libs/anonymizer/tests/application/test_properties.py:102` y `:106`**
- **Qué pasa.** Los filtros por espacio se saltan toda entidad sin espacio. No solo las palabras sueltas de un nombre: también el radicado, la cédula y los nombres o apodos de una sola palabra. Los cuatro están en el *fixture* de entidades sembradas (`seeded.json:107` y `:114`) y en `WORDS`, así que pueden llegar a `system`. F-11 pedía «excluir solo las palabras sueltas», y esto no lo cumple.
- **Lo que hace el código real.** Los seudonimiza en `system` (`[EXPEDIENTE_1]`, `[IDENTIFICADOR_1]`, `[ENTIDAD_1]`). Por eso el oráculo puede exigirlo.
- **Prueba.** Un mutante de `_mask` que en `system` devuelve a su texto original las formas sin espacio filtra el radicado, la cédula y el apodo, y aun así el `pytest` completo da **418 pasan**. Es una regresión de AUTONOMIA-04 que nada detecta.
- **Corrección.** Excluir solo las entidades que son una palabra de una entidad de varias palabras del mismo turno, y exigir las demás. O bien, una prueba en `tests/application` con el radicado, la cédula y un apodo en `system`. El mutante descrito debe quedar en rojo.

## Lo que pide el encargo
1. **Alcance.** El diff `e095057..c1b8c8c` toca 4 archivos, todos en `tests/application/` y `docs/loop/bitacoras/`. No cambian `src/` ni `domain/`, ni baja ningún umbral.
2. **Mutante de F-11.** Aplicado en memoria con `mock.patch.object`, sin escribir nada: `_mask` devuelve `system` sin seudonimizar. Fallan 3 pruebas: los dos casos de `test_system_message.py` y la propiedad.
3. **Oráculo y pruebas nuevas.** Las pruebas nuevas no son vacuas: comprueban el nombre completo y cada palabra, la marca en `system`, que se conserva el resto del texto y la misma marca en `system` y en el turno. El oráculo sigue exigiendo los nombres completos y las formas de varias palabras, pero excluye de más (F-12). El nombre de las pruebas viene del *fixture* sintético.
4. **Criterios** (en el worktree):

| Criterio | Comando | Resultado |
|---|---|---|
| CA-3 | `git -C … diff --exit-code afa8f20 -- …guards …contracts …support.py …fixtures` | 0, sin cambios |
| CA-5 | `pytest -p no:cacheprovider -q` | 418 pasan |
| CA-6 | `mypy --strict src tests` | sin problemas en 47 archivos |
| CA-6 | `ruff check .` y `ruff format --check .` | limpios |
| CA-6 | las 4 guardias `scripts/check-no-*.sh` | `0 apariciones` en cada una |

```
VEREDICTO: NO-VERDE
NARANJA|libs/anonymizer/tests/application/test_properties.py:102|El oráculo de system excluye toda entidad sin espacio (radicado, cédula, apodo): un mutante que las filtra en system pasa las 418 pruebas
INFORME: docs/loop/revisiones/U10-T04/ronda-3.md
```
