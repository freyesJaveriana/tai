# Ronda 2 — U11-T03

Revisión de `revisor` (`opus`), 2026-11-26, sobre `520db79`.

VEREDICTO: VERDE

Los siete criterios pasan cuando los corro yo. F-01, F-02 y F-04 están corregidos, y sus pruebas nuevas detectan el mutante de cada corrección. F-03 ya figura en la tarea U11-T04. Queda un solo AMARILLO, que no bloquea.

## Criterios de aceptación, verificados por mí

| # | Resultado |
|---|---|
| CA-1 | Pasa: 31 pruebas. `gateway.py` (14 ramas) y `anonymizing.py` al 100 % |
| CA-2 | Pasa: 161 pruebas, 54 ramas al 100 %. La prueba que recorre todos los puntos de código tarda 0,78 s |
| CA-3 | Pasa: 37 pruebas, al 100 % |
| CA-4 | Pasa: código 0 |
| CA-5 | Pasa: 111 pruebas. 89 fallan, todas por `NotImplementedError`, 22 pasan y hay 0 `ERROR` |
| CA-6 | Pasa: código 0 en los seis comandos |
| CA-7 | Pasa: `0 apariciones` en los tres scripts |

No hay *canaries* nuevos en el código, y el worktree quedó limpio al terminar.

## Correcciones de la ronda 1

**F-01, corregido.**
- Pasé 13 etiquetas adversas y ninguna tumba el filtro: dígitos no ASCII, ancho completo, espacios, U+200B, 10 dígitos y 5000 ceros.
- `T0` da `cita_no_verificada`.
- `T02` y `T000000002` se aceptan como el turno 2. Es indulgente pero seguro, porque la salida canoniza la etiqueta como `T2`.
- Mutante: con la etiqueta sin acotar, fallan 3 pruebas.

**F-02, corregido.** `git check-attr -a` sobre `prompt.v1.md` da `text: set` y `eol: lf`.

**F-04, corregido.**
- Los rangos coinciden exactamente con la propiedad `White_Space` de Unicode.
- Con entradas patológicas de 20 000 caracteres, cada caso tarda como máximo 2 ms.
- Mutante: con la vuelta a `str.split`, fallan 5 pruebas.

**F-03, resuelto.** Figura en `docs/loop/tareas/U11-T04-analyze.md`.

## Literales invisibles en `test_quotes.py`

Leí con `ast` la lista parametrizada de la línea 102. Trae diez blancos distintos y ninguno es un espacio normal, así que ninguna prueba es vacua.

## Hallazgos

### F-05 · AMARILLO · `libs/incoherence_analyzer/tests/domain/test_quotes.py:102` y bitácora · La justificación de los literales invisibles es incorrecta

`ruff format` y `ruff check --fix` no cambian los escapes `\uXXXX`: lo comprobé por stdin con la configuración del paquete. El U+2028 literal que quedó en el código fuente corta las líneas al leerlas y dificulta la revisión.

Sugerencia: usar escapes `\uXXXX` o `chr(0x…)` y corregir la frase de la bitácora.

## Tareas candidatas

- La configuración de import-linter, para T05.
- La prueba compuesta de destino frente a perfil en `RecordingGateway`, para T04.

```
VEREDICTO: VERDE
AMARILLO|libs/incoherence_analyzer/tests/domain/test_quotes.py:102|Literales invisibles (incluido U+2028) justificados con una afirmación sobre ruff format que no se reproduce
INFORME: docs/loop/revisiones/U11-T03/ronda-2.md
```
