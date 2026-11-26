# Ronda 1 — U11-T03

`revisor` (`opus`), 2026-11-26, sobre `5e1baae`.

VEREDICTO: NO-VERDE

Los siete criterios pasan cuando los corro yo. Queda en pie un NARANJA: una salida del juez que el testimonio puede inducir tumba el filtro guardia con una excepción sin tratar, en vez de descartar el candidato.

## Criterios de aceptación, verificados por mí

| # | Resultado |
|---|---|
| CA-1 | Pasa: 31 pruebas; `gateway.py` al 100 % (14 ramas) y `anonymizing.py` al 100 % |
| CA-2 | Pasa: 142 pruebas; 54 ramas al 100 %, con la prueba de rendimiento |
| CA-3 | Pasa: 37 pruebas, con la propiedad Hypothesis; 100 % (6 ramas) |
| CA-4 | Pasa: código 0; ninguna de las 6 rutas está en el diff |
| CA-5 | Pasa: 111 pruebas; 89 fallos, 22 pasan, 0 `ERROR`; los 89 son `NotImplementedError` de `analyze` o de `run` |
| CA-6 | Pasa: código 0 en los seis comandos |
| CA-7 | Pasa: `0 apariciones` en los tres scripts |

**Otras comprobaciones:**
- **Claves:** solo entra con el diff `sk-sintetico-canario-7f3a91c2d4e5`, en `libs/model_gateway/tests/support.py:24`.
- **Worktree:** limpio al terminar.

## Sondas adversariales

**Adaptador y gateway: no rompí nada.**
- Con el gateway real, el `Anonymizer` real y un `MockTransport` que lanza `RuntimeError` y `httpx.ConnectError` con un *canary* del testimonio, salen `ProviderError` y `AnonymizerUnavailable`. El *canary* no aparece en `str`, `repr`, la cadena `__cause__`/`__context__` ni el *traceback*.
- No hay camino a un proveedor sin `Anonymizer`: `build` solo devuelve `RecordingGateway(AnonymizingAdapter(provider))`.
- El alias `verifier_permuted` es `const: verifier` en `profiles.schema.v1.yaml`, así que no puede saltarse las comprobaciones de `build`.

**Mutantes en memoria (`mock.patch.object`).** Probé doce, y todos hacen fallar al menos una prueba:
- reintento único;
- `raise … from err`;
- el piso bajado a 269;
- `build` que ignora el alterno;
- `verify_quote` sin orden de fragmentos;
- la deduplicación por par ordenado;
- `fail` sin la precedencia del incidente;
- el orden de BR5.2 alterado de dos formas;
- `scan` sin `literal_sources`;
- una salida en error que conserva los hallazgos;
- las citas sin `avisos`.

**`verify_quote`:**
- Rechaza la cita vacía, la que solo trae espacios, los fragmentos fuera de orden o solapados, un cambio de mayúsculas, `[...]` y el separador solo o al inicio.
- NFD frente a NFC da `not_found`, que es fallo cerrado y coherente con la regla del piloto.
- Con entradas patológicas sobre 20 000 caracteres, tarda como máximo 1,5 ms.

***Prompt* y esquemas:**
- La huella coincide con los bytes.
- El `scan` real da `[]`, y el control negativo sí detecta.
- Los siete tipos coinciden con C6.
- Los esquemas locales son cerrados en todos los niveles.
- `build_messages` pone el JSON en `user` y solo el texto fijo en `system`.
- **No verificado contra la documentación en vivo:** la herramienta MCP no estaba disponible. Los esquemas de cable solo usan `type`, `properties`, `required`, `additionalProperties: false`, `enum`, `items`, `title` y `description`, y concuerdan con PD-11.

## Hallazgos

### F-01 · NARANJA · `libs/incoherence_analyzer/src/veridicus_incoherence_analyzer/domain/filter.py:101` · Una etiqueta de turno muy larga tumba el filtro guardia

**El fallo.** `_number` hace `int(matched.group(1))` sin límite de longitud. Python rechaza convertir cadenas de más de 4300 dígitos, y ni el esquema de cable ni el local acotan `turno`.

**Sonda:** `turno = "T" + "9"*5000` da `ValueError: Exceeds the limit (4300 digits)`, que se propaga desde `_quote_failure`.

**Consecuencia:**
- La salida del juez se puede inducir con el testimonio (Escenario A).
- Un solo candidato tumba la corrida como defecto del código (CLI 5).
- BR5.5 y BR5.6 piden `cita_no_verificada`.

**Corrección:**
- Acotar `_TURN_LABEL`, por ejemplo con `T([0-9]{1,9})`. `output.py::_quote` solo recibe candidatos que ya pasaron `_number`, así que con eso basta.
- Probar esa etiqueta.

### F-02 · AMARILLO · `/.gitattributes` · El archivo con huella fijada no tiene `eol=lf`

`data/prompt.v1.md` tiene su SHA-256 fijado (PD-13), pero no tiene `text eol=lf`, como sí tiene `contracts/**` (NFRD-U1-13). Un *checkout* en Windows con `autocrlf` cambiaría los bytes, y entonces toda corrida daría `salida_invalida`.

### F-03 · AMARILLO · plan, paso 8 (línea 329) · La prueba «un byte cambiado da `salida_invalida` sin llamar» queda para T04

El diferimiento es razonable, porque la prueba necesita `analyze`. Pero tiene que quedar escrito en la tarea U11-T04.

### F-04 · AMARILLO · `domain/quotes.py::normalize_spaces` · Normaliza algo más que los espacios en blanco Unicode

`str.split()` toma U+001C–U+001F como espacio, y `verify_quote('a\x1cb', 'a b')` da `verified`. BR5.5 dice «nada más».

## Diferimientos declarados

- **BR5.8:** lo permite el plan (línea 495, Deferred a B11b, y CG-U11-07).
- **BR7.3:** lo permite el plan (línea 504, sin alterno en B11a).
- **La prueba del byte cambiado:** ver F-03.

## Tareas candidatas (fuera de alcance)

- La configuración de import-linter todavía no existe. Toca al paso 11 (T05).
- `RecordingGateway.generate` no compara `request.destination` con el perfil, y hoy depende del `Anonymizer`. Conviene una prueba compuesta en T04.

```
VEREDICTO: NO-VERDE
NARANJA|libs/incoherence_analyzer/src/veridicus_incoherence_analyzer/domain/filter.py:101|Etiqueta de turno con más de 4300 dígitos lanza ValueError en el filtro guardia en vez de cita_no_verificada
AMARILLO|.gitattributes|prompt.v1.md, con huella fijada, sin eol=lf
AMARILLO|code-generation-plan.md:329|La prueba del byte cambiado del prompt queda para T04 y debe constar en su tarea
AMARILLO|libs/incoherence_analyzer/src/veridicus_incoherence_analyzer/domain/quotes.py:normalize_spaces|str.split normaliza U+001C-U+001F, que no son White_Space Unicode
INFORME: docs/loop/revisiones/U11-T03/ronda-1.md
```
