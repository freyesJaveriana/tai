# Resumen del código: U10 `anonymizer` (Bolt B10a «Anonimizador mínimo»)

B10a está en la rama `bolt/b10a-anonymizer`, con base `88efacb` en `main`. Falta el PR del Bolt, que el humano fusiona con *squash*. Se construyó con el loop de agentes en modo liviano (DT31, ML-1 a ML-14). Fueron 5 tareas (U10-T01 a U10-T05), y cada una terminó en una revisión adversarial VERDE de `revisor` con `opus`. Las tareas, bitácoras e informes están en `docs/loop/`.

## Archivos creados y modificados

La lista completa está en `source-manifest.json`, junto a este archivo.

- **`libs/anonymizer/`** (paquete nuevo, `veridicus-anonymizer` 0.1.0, *src layout* `src/veridicus_anonymizer/`):
  - `api.py`: `Anonymizer` (cumple `AnonymizingProvider` de C20) y `build_anonymizer(env, transport=None)`.
  - `application/generate.py`: comprobación del destino, seudonimización, un solo envío, restauración y liberación de la tabla. Cualquier error antes del envío sale como `AnonymizerUnavailable`; después del envío, como `ProviderError` con su `ModelCall` (PD-9).
  - `domain/`: `catalogs`, `sentence` (apertura de oración de PD-2), `detection`, `masking` (`MaskTable` en memoria y presupuesto de NFR3.5), `regex` (`google-re2`) y `restoration`.
  - `providers/`: `anthropic.py`, la Messages API con `httpx` directo, salida estructurada por JSON Schema, una sola petición, lectura con tope de bytes y rechazo de toda compresión; y `http.py`, con `default_transport()`, TLS ≥ 1.2, sin redirecciones, `retries=0` y `trust_env=False`.
  - `data/`: reglas de detección, palabras permitidas, dominios (C22) y capacidades, cada uno con su esquema JSON versionado.
  - `testing/`: `fake_transport.py` (lo reutiliza B11a), `bypass.py` (control negativo, solo en pruebas) y `coverage_gate.py`.
  - `tests/`: 456 pruebas en `guards`, `contracts`, `domain`, `application`, `providers`, `boundaries` y `testing`, más la demostración. Usa solo *fixtures* sintéticos.
  - `README.md` y `examples/demo_fake.py`.
- **`contracts/`**: K-56. `validate_instance` admite la lista cerrada de marcas `x-veridicus-*` y sale `veridicus-contracts` 0.1.1. El glosario de contratos se movió a `docs/glosario.md`, y en su lugar quedó un enlace (F-04 de U10-T05).
- **CI:**
  - `anonymizer-level0.yml` es nuevo y no tiene filtro de rutas.
  - `contracts-level0.yml` suma `ruff format --check` de `libs/errors` (K-76).
  - `repo-level0.yml` corre la autoprueba de las guardias.
- **Guardias del repositorio público:**
  - `check-no-cluster-ids.sh` y `check-no-datos-personales.sh` cierran los huecos de K-76, salvo los falsos positivos de `scp`.
  - `scripts/tests/autoprueba-guardias.sh` es nuevo: 17 sondas y 10 controles.
- **Loop:** `.claude/agents/codificador.md`, `.claude/agents/revisor.md` y `docs/loop/`, con ML-11 a ML-14, la lectura de varios archivos sin bucles y los mutantes sin copias en el scratchpad.

## Decisiones clave de implementación

- **PD-1:** Anthropic, con el modelo `claude-sonnet-5-5` y `httpx` directo, sin SDK. OpenAI y Google fallan cerrado hasta B10b.
- **PD-2:** sin NER. La red de seguridad marca toda palabra con mayúscula que abre oración; toda palabra con alguna mayúscula se enmascara entera. El apodo en minúscula queda como límite declarado.
- **PD-5 y K-84 (decisión A del humano):** el prefijo es estable, con un límite declarado. Si `system` contiene una forma que aparece por primera vez en un turno posterior, `system` cambia y se renumera. No es un riesgo de privacidad, solo se pierde la caché de esa llamada.
- **PD-7:** `build_anonymizer` lanza `ConfigInvalidProfileError` o `ConfigInvalidLimitError` de `veridicus_errors` y no tiene ningún parámetro para saltarse la seudonimización.
- **PD-9:** una excepción después del envío sale como `ProviderError` con su `ModelCall`.
- **Fronteras:** 4 contratos de import-linter. Cubren los nombres con y sin el prefijo `veridicus_`, el `__init__` raíz y los módulos de primer nivel.

## Cobertura de pruebas

- La suite de `libs/anonymizer` tiene 456 pruebas, con 99,54 % de líneas, y corre en unos 13 s.
- `coverage_gate` exige el 100 % de ramas en `domain/`, `application/`, `api.py`, `providers/` y `fake_transport.py`. Falla cerrado si al informe le falta un archivo de un grupo guardia.
- `mypy --strict`, `ruff` y `lint-imports` pasan.
- La suite de `contracts` pasa con 2920 pruebas.
- **Mutantes que detecta la suite:**
  - quitar el presupuesto de seudonimización (F-04 de U10-T04);
  - no seudonimizar `system` (F-11);
  - devolver a su texto los identificadores de una sola palabra en `system` (F-12).
- **Trazabilidad:** `traceability.json` cubre 49 IDs.
  - 36 están en `OK`.
  - 8 están en `Deferred`, todos para B10b (DP-03).
  - 5 están en `N/A`: AC11.3.8, que es de U11, y 4 retirados.

## Rondas del loop

| Tarea | Rondas | Resultado |
|---|---|---|
| U10-T01 | 2 | VERDE |
| U10-T02 | 2 | VERDE |
| U10-T03 | 2 + acotada (ML-5) | VERDE |
| U10-T04 | 2 + 2 acotadas (ML-5) | VERDE |
| U10-T05 | 2 + acotada (ML-5, decisión A) | VERDE |

Ninguna tarea salió VERDE en la primera ronda. Las reglas ML-11 a ML-14 nacen de este Bolt (`docs/loop/README.md` §9) y se medirán en B11a con ML-10.

## Desviaciones del plan

- **Paso 13, casilla sin marcar:** los falsos positivos de `scp` (F-05 a F-07 de T29) **no se cerraron**. La regla nueva dejaba de ver doce formas reales de `scp` hacia un host literal. Por ML-5, el humano decidió (opción A) volver a la regla base: falla cerrado y declara esos falsos positivos en «Límites conocidos». El refinamiento queda como K-87.
- **`testing/bypass.py`** se ajustó a la firma con `has_budget` de U10-T03. Es una costura fuera del candado del rojo.
- **Archivos fuera del «Dentro» literal de U10-T05:** `contracts/README.md` y `contracts/tests/test_readme.py`, por el glosario único que pide `team.md`.
- **Candidatas abiertas en `docs/loop/CANDIDATAS.md`:**
  - K-81: escrituras sin mayúsculas, para el NER de B10b.
  - K-85: proyección del esquema, `cache_control` y `max_tokens` fijo en 16000.
  - K-86: el oráculo de `system` junta las palabras de toda la entrada.
  - K-87: refinar la regla de `scp`.

## Precisiones para la aprobación del checkpoint

Se suman a CG-U10-01 a CG-U10-07 del plan. No se edita ningún artefacto aprobado: en la aprobación, el humano decide cuáles se llevan al original.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| CG-U10-08 | Plan de U10, paso 10 (candado del rojo) | El candado cubre también `tests/support.py` y `tests/fixtures`, con `ROJO_SHA` = `afa8f20`. La red de seguridad une en una sola marca `ENTIDAD` las palabras seguidas con mayúscula. La precedencia es EXPEDIENTE > IDENTIFICADOR > PERSONA > LUGAR > ENTIDAD | Revisión de U10-T02, decisión del humano |
| CG-U10-09 | Plan de U10, paso 12 (verificación) | `test_ci_workflows.py` se corre con `--no-cov`, porque al correr un solo archivo falla el piso global de cobertura de `contracts`. El umbral no cambia | U10-T05 |
| CG-U10-10 | FD-U10-01 y PD-5 | El prefijo es estable salvo cuando `system` contiene una forma de tramo completo que aparece en un turno posterior. `system` debe llevar instrucciones fijas, sin testimonio | K-84, decisión A del humano, 2026-11-25 |
| CG-U10-11 | Plan de U10, paso 13 | Los falsos positivos de `scp` de F-05 a F-07 quedan como límite declarado y la regla de `scp` sigue siendo la base | K-87, decisión A del humano por ML-5, 2026-11-25 |
