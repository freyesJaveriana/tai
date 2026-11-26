# U11-T01 — revisión corta del rojo (ML-13), ronda 1

`revisor` (`sonnet`), 2026-11-26. Revisó las pruebas sin commit.

Se corrió CA-6 tal como está escrito:
- en el analizador, 85 `FAILED` y 0 `ERROR`;
- en `execution_profiles`, 11 `FAILED` y 0 `ERROR`.

Todas fallan por el `NotImplementedError` de un *stub*. El worktree solo tiene los 4 grupos de archivos sin seguimiento que se esperaban. No hay hallazgos ROJO.

## NARANJA

- **F-01 · `tests/contracts/test_c6_output.py:54-62`: la prueba de BR8.1 no se puede cumplir con una implementación correcta.**
  - El estímulo es `input_tokens=-5`, y queda en `registro.llamadas[*].tokens_entrada`, donde C6 pide `minimum: 0`.
  - BR7.1 conserva el registro en toda salida de error, y BR8.1 solo vacía `hallazgos` y `descartes` en la salida sustituta.
  - Por eso, `assert_error_output` exige `c6_problems == []` sobre una salida que sigue llevando los -5, y choca con BR7.1.
  - **Corrección:** usar el estímulo que da la regla, «hallazgo armado a propósito sin observaciones». Por ejemplo, parchar con `monkeypatch` el armador de `domain/output` y fijar esa costura en el docstring. Si no, registrar en la bitácora y en el plan que la salida sustituta lleva `llamadas: []`.

- **F-02 · `libs/execution_profiles/tests/contracts/test_profile_contract.py:97-99`: la propiedad puede fallar con una implementación correcta.**
  - `st.text(min_size=1)` genera claves de solo espacios, como `" "`.
  - BR2.2 dice «no existe o está vacía → CLI 3». Una implementación que recorte los espacios lanzaría `ConfigInvalidProfileError`, y la prueba fallaría por la razón equivocada.
  - **Corrección:** `.filter(lambda k: k.strip())`.

- **F-03 · `libs/incoherence_analyzer/tests/support.py`: el oráculo queda fuera de lo que se congela.**
  - `support.py` define `assert_error_output`, `c6_problems`, `assert_no_entity_in_payload`, `ScriptedGateway` y `ScriptedProvider`.
  - CA-7 y el paso 9 (`git diff --exit-code <ROJO_SHA>`) solo cubren `tests/guards`, `tests/contracts` y `execution_profiles/tests/contracts`. Si alguien debilitara un aserto de `support.py` en T02 a T05, el *diff* no lo vería.
  - **Corrección:** incluir `support.py` en el commit del rojo y en las rutas de CA-7 y del paso 9. Si no, se acepta como defecto.

## AMARILLO

1. **BR5.1 a nivel de `analyze`.**
   - Solo se prueban «campo ausente» y «campo extra». Faltan `null`, la cadena vacía y un `tipo` fuera del enum para `hecho`, `observaciones`, `cita_a.cita` y `cita_b.cita` (`test_autonomia_05_quotes.py:38-50`).
   - `test_response_schemas.py` cubre esos casos solo para `hecho` y `observaciones`, y contra el esquema, no a través de `analyze`.
2. **BR5.3, BR5.2 y BR5.6.**
   - Hay una sola marca alterada, en `cita_b`. Faltan una marca en `observaciones` y un puntero que no cae en ningún candidato, que debe dar `salida_invalida`.
   - Faltan el orden de los filtros (un candidato que falla dos) y las combinaciones con `cita_a` válida y `cita_b` de otro turno o inválida.
   - Esos huecos afectan el 100 % de ramas de la guardia.
3. **BR2.10.** Ninguna prueba exige que cambiar un parámetro cambie `config_sha256`, ni que el orden de las claves o el formato YAML no lo cambien. Un `config_sha256` constante pasa la prueba.
4. **BR9.1, BR9.2 y BR9.4.**
   - Nada llama a `scan()` directamente: no se prueban las mayúsculas y tildes, «mienten» y las falsas coincidencias, los tramos «…», la cadena del aviso ni los casos de `scan-cases.v1.yaml`. Hoy solo se prueba el descarte dentro del flujo.
   - El plan, sin embargo, da por cubiertas BR9.1 a BR9.5.
5. **BR11.2.** Las salidas CLI 3 por «sin módulo» y por la variante (e) no comprueban que `AVISO.txt` no exista (`test_autonomia_04_composite.py:94-96` y `206-208`).
6. **Variante (d).** `SilentProvider` lanza `TimeoutError` al instante en vez de agotar un plazo. Se acepta si la bitácora lo declara como simulación (`test_autonomia_04_composite.py:166-180`).
7. **`FORBIDDEN_FIELD_NAMES`.** Solo se revisan las claves de la raíz, del registro y del primer hallazgo. La comprobación de los esquemas sí recorre todo.

## Lo que está bien

- **Campo ausente o nulo.** La lectura «ausente o nulo da `salida_invalida`; `campo_faltante` solo con espacios» es correcta: coincide con BR5.1, BR5.4 y AC3.4.1. El texto del plan es ambiguo, y el codificador siguió la regla.
- **Firmas.** Las firmas de los *stubs* que fija la bitácora no contradicen C6, C13 (`GenerateRequest`, `ModelCall`) ni `anonymizer/api.py`.
  - `build_anonymizer` traduce `CatalogError` a `ConfigInvalidProfileError` y `LimitsConfigError` a `ConfigInvalidLimitError`, como supone la variante (e).
  - `now`, `pseudonymize`, `load_catalogs` y `limits` son costuras reales.
  - Los códigos, los motivos, `anonimizado`, `avisos`, `pagina` y los 7 tipos coinciden con `salida.schema.json`.
- **Marcadores.** Las 5 pruebas marcadas `cli` son las que pide la tarea.
- **Datos.** Solo hay datos sintéticos, y la clave es un *canary*.

VEREDICTO: NO-VERDE (3 NARANJA: F-01, F-02 y F-03; ningún ROJO)
