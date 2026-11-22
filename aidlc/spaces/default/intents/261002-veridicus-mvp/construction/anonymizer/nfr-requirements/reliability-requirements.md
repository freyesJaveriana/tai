# Requisitos de fiabilidad — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el Functional Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Se conservan los IDs. Lo nuevo toma el número siguiente (NFR4.3, NFR6.2).
- **Cambio principal.** U10 ya no es un COULD apagado: es MUST y está en el camino de toda llamada
  comercial. Lo esencial sigue igual: **ante cualquier duda, no sale nada**. Salen los códigos propios
  de la revisión 1 (`anonymizer.masking_failed`, `anonymizer.upstream_*`, `anonymizer.busy`); los
  sustituye la tabla de C21 y C13.

**Insumos.**
- F1, F3, F5, F6, F7 y F8, las máquinas de estado §3.1–§3.2 y los escenarios E11–E34 de
  `functional-design/functional-spec.md` (functional-spec).
- BR1.1, BR1.3, BR2.1, BR2.2, BR2.4, BR2.5, BR4.1, BR4.2, BR6.4 y BR6.5 de `functional-design/rules.md`
  (rules).
- FR11.3, FR15.2, NFR4, NFR6 y NFR10 de `inception/requirements-analysis/requirements.md`
  (requirements).
- C13 (tabla de errores), C16, C20 y C21 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- P2 = A de `nfr-requirements-questions.md`.

## 1. Objetivos

- **Fallo cerrado siempre.** Si algo falla antes del envío, **0 peticiones** al proveedor. Si algo
  falla después, se devuelve el error tipado con su `ModelCall`, nunca un resultado parcial
  (AUTONOMIA-05).
- **Como máximo una llamada externa por `generate`.** No hay reintentos hacia el proveedor, ni en U10
  ni en el cliente HTTP de U11 (tabla de C13). Quien decide usar el proveedor alterno ante `451` es U11,
  según el perfil.
- **Sin objetivo de disponibilidad propio en el MVP.** Una sola réplica en una sola máquina. Si el
  proxy se cae, la corrida termina en `estado: error` con `anonimizador_no_disponible` y el analista la
  relanza.

## 2. Fallo cerrado, plazo y arranque

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | Fallo cerrado en **cada rama** anterior al envío (BR2.1, F7). | Terminan en `AnonymizerUnavailable` (en el proxy, `503` `analysis.anonymizer_unavailable`) con **0 peticiones** al transporte: destino local o desconocido (NFR1.13); dominio, esquema o puerto fuera de la lista (NFR1.11); clave ausente; archivo de datos con SHA-256 distinto; NER no cargado o que lanza un error; presupuesto de seudonimización agotado (NFR3.5); tabla incoherente (una forma con dos marcas); cuerpo del proveedor que no se puede armar; saturación (NFR8.2); y cualquier excepción no prevista antes del envío. El `FakeTransport` cuenta las peticiones: 0 en cada rama. Todo `libs/anonymizer/` y `services/anonymizer-proxy/` tiene **100 % de ramas** (NFR13.2). | Nivel 0 |
| NFR10.4 | cambia | Un plazo total para cada llamada y sin reintentos (BR2.4; hallazgo R-04 de la revisión 1). | Todo `generate` corre dentro de `anyio.fail_after(timeout_s)`, que cubre seudonimizar, enviar, leer, validar y restaurar. Conexión ≤ 10 s, dentro de ese plazo. Si el plazo vence antes del envío, `AnonymizerUnavailable` y 0 peticiones. Si vence después, `Timeout` con su `ModelCall` (`504` `analysis.timeout` en el proxy). Pruebas con un `FakeTransport` lento, que devuelve 500, 429 o 529, que corta la conexión y que redirige (`307`): **exactamente 1** petición en cada caso, y el error tipado de C13 (`ProviderError` ante 429, 5xx o 3xx). `timeout_s` sale del perfil y lo limita `model_call_timeout_s` de C25. | Nivel 0 |
| NFR10.7 | cambia | El proxy no arranca mal configurado, y `/readyz` no sale del clúster (BR2.2, BR6.4, C16). | Al arrancar se comprueban: los SHA-256 de NFR10.11 y del NER; que cada entrada de `ProviderCapabilityTable` tenga su ADR (NFR1.2) y una combinación de modo estructurado y esfuerzo admitida (FD-U10-09); que `ProxyProfileCopy` valide y que cada destino externo de cada perfil tenga su variable `VERIDICUS_*` de clave presente; y que las cifras de C25 se carguen. Si algo falta, el proceso termina con código ≠ 0 y un log que nombra el ajuste, nunca su valor. `/healthz` responde 200 si el proceso vive. `/readyz` responde 200 solo con todo lo anterior y **no** abre ninguna conexión hacia fuera (C16). Prueba de nivel 0 por ajuste ausente o inválido; prueba de nivel 1 de que `/readyz` no abre conexiones. En la CLI, el mismo error impide construir el módulo y la línea de comandos sale con código ≠ 0 antes de cualquier llamada. | Nivel 0 y nivel 1 |

## 3. Restauración y calidad de la IA con el anonimizador en el camino

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR6.1 | cambia | La respuesta restaurada es exacta, y por eso la verificación de citas de U11 funciona (BR1.3, BR4.1; AC11.3.4 a). | Prueba de propiedades con Hypothesis sobre textos sintéticos sin formas de marca: seudonimizar y restaurar devuelve el **mismo texto, byte a byte**. Sobre respuestas grabadas: **0** marcas conocidas quedan en el contenido devuelto, y una cita restaurada es igual al texto del turno original (E5, E27). La restauración se hace sobre el JSON parseado, y los escapes no cambian (NFR10.14; cierra el hallazgo R-03 de la revisión 1). | Nivel 0 |
| NFR6.2 | nuevo | Las observaciones se leen con los nombres reales para la calificación Likert (NFR6). | En el conjunto que califican los dos evaluadores, 0 observaciones restauradas contienen una marca conocida. Las marcas alteradas aparecen en `altered_markers` y U11 invalida esos hallazgos (BR4.2), así que nunca llegan a la calificación. La calificación es de U11. | Nivel 0 (lado de U10) |
| NFR4.1 | cambia | El anonimizador no rompe la calidad de la IA (NFR4). | El reporte de nivel 2 de B11 con el perfil de la primera rebanada (juez de Anthropic, P2 = A, todo por el módulo) cumple los umbrales de NFR4 que fija U11, entre ellos **0 %** de error de formato JSON y **100 %** de citas verificadas. U10 aporta su parte del reporte: `altered_markers_count` por corrida y la tasa de llamadas en `InvalidOutput`. Los umbrales de U10 no se bajan para que pase. | Nivel 2, reporte adjunto al PR de B11 |
| NFR4.2 | cambia | La no repetibilidad del proveedor comercial se mide y no se oculta. | El ADR del proveedor declara si admite `seed` y `temperature`. Con Anthropic, `seed` queda nula en `ModelCall` (BR2.5), y el acuerdo entre 3 corridas lo mide U11 (NFR4). El módulo nunca inventa una semilla ni reintenta para buscar coincidencias. Prueba de nivel 0: `ModelCall.seed` es nula cuando la tabla de capacidades dice que el modelo no la admite. | Nivel 0 y nivel 2 (U11) |
| NFR4.3 | nuevo | Mismas marcas para el mismo texto dentro de una llamada. | Para un mismo cuerpo de entrada, dos `generate` seguidos producen el mismo cuerpo seudonimizado byte a byte (BR1.1: numeración por primera aparición). La variación entre corridas solo viene del proveedor. Prueba sobre el `FakeTransport`. | Nivel 0 |

## 4. Fallos y recuperación

| Fallo | Qué se pierde | Cómo se recupera |
|---|---|---|
| Error antes del envío (NFR10.1) | Nada salió; la corrida queda en `estado: error` con `anonimizador_no_disponible` (C13) | El analista relanza la corrida; si se repite, es un hallazgo de configuración o de datos del módulo |
| Plazo, bloqueo o error del proveedor | La llamada; U11 registra su `ModelCall` y la corrida termina en `estado: error` | Relanzar a mano; ante `451`, U11 usa el alterno si el perfil lo tiene. U10 no reintenta (NFR10.4) |
| Salida inválida o marcas alteradas | Esa llamada (`InvalidOutput`) o esos hallazgos (`altered_markers`) | U11 invalida lo afectado (BR4.2); nunca se emite un resultado parcial |
| Proxy saturado (NFR8.2) | Nada salió | U11 lo recibe como `AnonymizerUnavailable` y la corrida termina en error; sin reintento automático |
| Caída o reinicio del proxy | La llamada en curso; la tabla desaparece con el proceso | El cliente de U11 ve conexión rechazada → `AnonymizerUnavailable` (tabla de C13) |
| Proveedor que deja de cumplir su ADR | — | PR que saca sus modelos de `ProviderCapabilityTable`; el proxy no arranca con un perfil que los use. Con P2 = A, sacar Anthropic deja la primera rebanada sin juez comercial hasta que otro proveedor tenga ADR |

## 5. Degradación

No hay modo degradado que deje salir texto sin seudonimizar. Con el proxy caído:
- la consola sigue respondiendo (NFR3);
- las corridas con destino externo terminan en error con su código;
- un perfil todo local (`todo-local`) sigue funcionando, porque no pasa por U10 (FR11.3, P9).
