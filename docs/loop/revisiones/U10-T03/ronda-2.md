# Ronda 2 de U10-T03: NO-VERDE

Los arreglos de F-01 y F-02 están bien y pasan los seis criterios. Pero el arreglo de F-04 rompe el prefijo estable de PD-5 cuando hay un mensaje `system` delante, que es el orden normal. Lo comprobé contra el código anterior: la ruptura no existía antes de este cambio, así que es un NARANJA nuevo.

## Cierre de la ronda 1
- **F-01, cerrado.** Las ocho formas de `test_detection.py` y las dos pruebas nuevas de F-01 **fallan** con el código anterior al arreglo (`29dfdeb`) y pasan con `d946600`. Como dice la bitácora, `guion_bajo` y `digito` ya pasaban antes. Sondas nuevas: una mayúscula en medio o al final de la palabra, la palabra entera en mayúsculas, palabras de `allowed-words` pegadas con guion a un nombre (en ambos sentidos) y la escritura de escape de 8 cifras. En todos los casos la palabra sale entera dentro de una marca.
- **F-02, cerrado.** La prueba de la lista negativa falla con el YAML anterior (Abril, Mayo, Junio y Marzo) y pasa con el nuevo.
- **F-04, cerrado en lo que pedía.** Un apellido suelto en `system` y en otro turno `user` lleva la misma marca. Un tramo cortado por una palabra permitida da dos formas, y cada una se propaga a `system`. Las dos pruebas de F-04 fallan con el código anterior.
- **Sobre el desvío de F-04 (marca propia por palabra):** la marca no filtra nada, porque el número no depende del contenido. La restauración sigue siendo byte a byte: `restore` devolvió el original exacto en las nueve sondas, sin `altered_markers`. Pero rompe PD-5 (ver F-06).

## Hallazgos
### F-06 · NARANJA · `libs/anonymizer/src/veridicus_anonymizer/domain/masking.py:132-138` · Una palabra de un tramo nuevo cambia `system` y renumera los turnos anteriores
Llamada de prueba: `system` con un apellido suelto, luego un turno `user` con otro nombre, y después un turno nuevo con nombre y apellido.
- **Sin el turno nuevo:** `system` queda intacto y el primer turno lleva `[ENTIDAD_1]`.
- **Con el turno nuevo:** el apellido de `system` pasa a `[ENTIDAD_1]` y el primer turno pasa a `[ENTIDAD_2]`.

Con `system` detrás pasa lo mismo: el texto de `system` cambia, que también forma parte de T. Con `29dfdeb`, el mismo caso da un prefijo idéntico.

Además, una palabra de inicio de frase que no esté permitida, si queda pegada a un nombre en un turno, enmascara esa misma palabra en las instrucciones de `system`. La prueba de PD-5 no lo ve porque no lleva `system`.

**Corrección:** la mejor opción es quitar la propagación por palabra hacia `system` y declarar F-04 como límite, que es lo que permitía la ronda 1. La alternativa es numerar primero los valores que no son `system` y garantizar que `system` no cambie al añadir turnos. En cualquier caso, hay que añadir a la prueba de PD-5 un caso con `system` delante que contenga una palabra de un tramo posterior.

### F-07 · AMARILLO · `domain/masking.py:134` · Las partes con guion de un tramo no se propagan
Con un tramo de dos apellidos unidos por guion seguidos de un nombre, el segundo apellido suelto en `system` sale sin marca, porque `split()` solo corta en espacios. Pertenece a la misma clase que F-04. Desaparece si F-06 se corrige quitando la propagación hacia `system`; si no, hay que cortar también en guiones.

### F-08 · AMARILLO · `domain/detection.py:36-41` · Escapes que no son de unicode
En texto que no es JSON siguen sin marca:
- una mayúscula escrita como escape hexadecimal de dos cifras;
- una mayúscula escrita como entidad HTML numérica;
- una mayúscula escrita como codificación por porcentaje.

Con una entidad HTML hexadecimal o con nombre, la marca tapa la entidad pero el resto del nombre queda visible en minúscula.

**Corrección:** declarar el límite (el texto debe llegar decodificado) y abrir una tarea candidata para U11, que construye el bloque. No es plausible en el flujo actual.

## Comandos que corrí (los de `uv` con `--directory /workspace/.worktrees/U10-T03/libs/anonymizer`)
- `uv sync --frozen`: código 0.
- CA-1: 54 pasan, 100 % de ramas.
- CA-2: 125 pasan, 100 % de ramas en los tres módulos.
- CA-3: 22 pasan, 9 fallan, las 9 por `NotImplementedError: build_anonymizer lo implementa U10-T04` (excepción permitida); 100 % de ramas.
- CA-4, `git diff --exit-code afa8f20 -- tests/guards tests/contracts tests/support.py tests/fixtures`: código 0.
- CA-5: 100 pruebas, 13 pasan, 87 fallan, 0 errores; en el JUnit las 87 fallan por `NotImplementedError` de `build_anonymizer`.
- CA-6: `mypy --strict src tests`, `ruff check .` y `ruff format --check .` sin problemas; las tres guardias en `0 apariciones`; el `grep` de `time` o `datetime` en `domain/` no imprime nada.
- Prueba del rojo con `src/` de `29dfdeb`: 11 fallan, 4 pasan.
- `git diff --stat 4e9af78...tarea/U10-T03` sobre `application/`, `api.py`, `providers/`, `pyproject.toml`, `contracts/`, `scripts/` y `.github`: vacío. Ningún umbral bajó.
- `git status --porcelain` al terminar: vacío.

```
VEREDICTO: NO-VERDE
NARANJA|libs/anonymizer/src/veridicus_anonymizer/domain/masking.py:132-138|La propagación por palabra de F-04 cambia system y renumera los turnos anteriores: rompe el prefijo estable de PD-5
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/domain/masking.py:134|Las partes con guion de un tramo de varias palabras no se propagan a system
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/domain/detection.py:36-41|Escapes hexadecimales, entidades HTML y codificación por porcentaje esconden una mayúscula; declarar el límite
INFORME: docs/loop/revisiones/U10-T03/ronda-2.md
```
