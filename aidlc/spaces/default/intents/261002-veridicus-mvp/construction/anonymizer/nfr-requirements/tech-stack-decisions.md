# Decisiones de pila — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el Functional Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Las decisiones conservan su número. Lo retirado queda «Retirado» y lo nuevo toma D10–D13.
- **Respuestas.** P1 = A, en lo que el cambio 01 no supera, y P2 = A: Anthropic es el proveedor de la
  primera rebanada.

**Insumos.**
- F1–F9 de `functional-design/functional-spec.md` (functional-spec), BR1–BR6 de
  `functional-design/rules.md` (rules) y las entidades de `functional-design/entities.md`.
- FR11.3, FR11.4, FR15.1–FR15.3 y NFR1, NFR2, NFR10, NFR13 y NFR14 de
  `inception/requirements-analysis/requirements.md` (requirements).
- C13, C16, C20, C21, C22 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- P1 y P2 de `nfr-requirements-questions.md` y `security-requirements.md`.
- Lo que publica U1: `AnonymizingProvider`, errores tipados, `model-call.v1.yaml`, la validación de
  perfiles, la huella JCS y la carga de límites.

No se repite lo que ya fijan `team.md` y las unidades anteriores: Python 3.12, FastAPI, Pydantic v2,
`pydantic-settings`, `uv` con un lockfile por paquete, `pytest` + Hypothesis + `pytest-asyncio`, mypy
estricto, Ruff, import-linter, Problem Details desde `libs/`, `prometheus-client`, e imágenes fijadas
por digest y sin root.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | cambia | Estado de entrega | **MUST** en B10. El módulo vive en `libs/anonymizer/` y lo usan la CLI (en el mismo proceso) y `anonymizer-proxy`. El proxy forma parte del despliegue base; qué genera el chart es de U2 | Proxy apagado por defecto (P1 = A de la revisión 1) | El cambio 01 hace MUST a FR11.3 y FR14.1 exige un perfil comercial. De P1 = A queda el ADR del proveedor (D8) | NFR1.2 |
| D2 | cambia | Motor de detección | **NER** en español con `transformers` (*token classification*, pesos en `safetensors`, `trust_remote_code=False`, CPU, `torch` solo CPU) **unido a** reglas con `google-re2` (tiempo lineal) | spaCy (su formato de modelo no es `safetensors`); ONNX Runtime (exige una conversión que el autor del modelo no publica ni firma); solo reglas (no ve los nombres sueltos, FR11.3) | FR11.3 pide NER más reglas; `team.md` exige formatos sin código ejecutable y sin `trust_remote_code`. El modelo y su `sha256` los fija Infrastructure Design (NFR-U10-05) | NFR1.3, NFR1.10, NFR3.1, NFR3.4 |
| D3 | cambia | Prioridad entre categorías | Precedencia `EXPEDIENTE`, `IDENTIFICADOR`, `PERSONA`, `LUGAR`, `ENTIDAD`. Los tramos que se solapan se funden en su unión, sin recortarlos (BR1.2). Umbral del NER 0,30; `ORG` y `MISC` se ignoran | Recortar solapes; umbral 0,5 por defecto | Ningún tramo detectado sale en claro. El umbral bajo prefiere seudonimizar de más, y la red de seguridad cubre lo que se ignora | NFR1.3, NFR1.10 |
| D4 | Retirado | Origen de la lista de nombres | Retirado: sale la lista de nombres del escenario y `veridicus_masking` (cambio 01, BR1.2) | — | — | — |
| D5 | cambia | Servicio HTTP | FastAPI + Uvicorn, **1 proceso**, un semáforo `anyio` de 4 peticiones (NFR8.2), rutas de C21 y C16 y `/metrics` en un puerto interno | Proxy genérico (Envoy, nginx con Lua) | La seudonimización necesita código propio con 100 % de ramas; un proxy genérico no falla cerrado sobre el contenido | NFR1.8, NFR8.2, NFR10.7 |
| D6 | cambia | Cliente hacia el proveedor | Cada adaptador usa `httpx` directo: `ssl.SSLContext` con TLS mínimo 1.2, verificación activa, `follow_redirects=False`, `HTTPTransport(retries=0)`, lectura por bloques con tope `anonymizer_response_max_bytes`, y todo dentro de `anyio.fail_after(timeout_s)` | SDK oficial de cada proveedor | Los SDK reintentan solos, siguen su propia URL base y meten cabeceras propias. `httpx` deja fijar TLS, redirecciones, reintentos, cabeceras (NFR1.8) y plazos | NFR1.8, NFR10.4, NFR10.5, NFR10.8 |
| D7 | Retirado | Políticas de manifiestos | Retirado: pasan a U2 con la `NetworkPolicy`, la lista blanca de CoreDNS y el endurecimiento del pod (NFR-U10-10) | — | — | — |
| D8 | cambia | Comprobación del ADR | `scripts/check-provider-adr.py` (Python, sin dependencias fuera del lockfile) lee `ProviderCapabilityTable` y comprueba cada `provider_adr` en la CI | Bash + `yq` (revisión 1); solo revisión del PR | Mismo lenguaje que el resto; los compromisos del proveedor se comprueban de forma mecánica | NFR1.2 |
| D9 | cambia | Pruebas sin red | `FakeTransport` sobre `httpx.MockTransport` en `libs/anonymizer/testing/` (nivel 0), y un servidor HTTPS local con certificado de `trustme` (nivel 1). `pytest-socket` bloquea toda conexión fuera de `localhost`. Ninguna prueba llama a un proveedor real | Grabaciones (VCR) de un proveedor real | Sin red en la CI y sin datos que salgan. Las respuestas grabadas se escriben a mano (NFR12.1) | NFR2.1, NFR12.1 |
| D10 | nuevo | Proveedor de la primera rebanada | **Anthropic** (P2 = A): su adaptador (Messages API, salida estructurada o herramienta forzada según la tabla de capacidades) y su ADR van primero en B10. Los de Google y OpenAI van al final del plan de B10 | OpenAI o Google primero; no fijarlo | P2 = A. Mantiene la mitigación de R14. Consecuencia: el generador del conjunto sintético es de Google u OpenAI (NFR5.2) | NFR1.2, NFR5.2 |
| D11 | nuevo | JSON estricto y esquema | `json.loads` con `object_pairs_hook` que rechaza claves repetidas y `parse_constant` que rechaza `NaN` e `Infinity`; `jsonschema` (Draft 2020-12) con el registro `referencing` de U1, sin red | Pydantic sobre la respuesta; validar solo en U11 | El esquema llega en la petición (`req.schema`), no es un modelo fijo; validar en el adaptador cumple AC13.6.2 (FD-U10-10) | NFR10.16 |
| D12 | nuevo | Huella del perfil | La función JCS que publica U1 (`veridicus_contracts.canonical.sha256_jcs`), sin una segunda implementación | Implementar JCS en U10 | Dos implementaciones que no coinciden darían `409` en toda llamada (FD-U10-12) | NFR10.15 |
| D13 | nuevo | Datos versionados | `libs/anonymizer/data/` con `schema_version` y `SHA256SUMS`, comprobados al arrancar; el NER se monta de solo lectura (U2) y se comprueba contra `artifact_sha256` | Descargar el NER al arrancar | `team.md`: los artefactos de modelo se descargan en *build* o aprovisionamiento, nunca en ejecución | NFR10.10, NFR10.11 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Dónde |
|---|---|---|---|
| `VERIDICUS_ANONYMIZER_NER_PATH`, `VERIDICUS_ANONYMIZER_NER_SHA256` | Ruta del volumen de solo lectura; — | Obligatorios; directorio con pesos `safetensors`, sin archivos `.py` ni `.bin`; SHA-256 igual (NFR10.11) | Proxy y CLI |
| `VERIDICUS_ANONYMIZER_PROFILES_PATH` | Archivo de perfiles montado de solo lectura | Valida con la función de perfiles de U1 (NFR10.7) | Proxy |
| Claves de API, por el nombre que da `api_key_ref` en cada perfil (prefijo `VERIDICUS_`) | — (en el proxy, del `Secret` que crea el humano y que U2 monta solo en ese pod) | Presente y no vacía para cada destino externo; nunca se registra (NFR10.6) | Proxy y CLI |
| `VERIDICUS_ANONYMIZER_MAX_CONCURRENCY` | 4 | Entero entre 1 y 4 (NFR8.2) | Proxy |
| Cifras de C25 (`anonymizer_request_max_bytes`, `anonymizer_response_max_bytes`, `anonymizer_masking_budget_ratio`, `model_call_timeout_s`) | Del catálogo `contracts/limits.v1.yaml` | Se cargan con la carga de límites de U1; una variable de entorno solo puede bajarlas (`project.md`) | Proxy y CLI |

Salen de la revisión 1: `VERIDICUS_ANONYMIZER_UPSTREAM_URL` (la URL base es una constante de cada
adaptador), `VERIDICUS_ANONYMIZER_MODEL` (el modelo sale del perfil), `_RULES_PATH` (los datos van en
el paquete), los plazos por papel (el plazo es `timeout_s` del perfil) y `_MAX_PROPER_NOUNS`.

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR2.1 | cambia | Todo U10 se prueba en CPU y sin red. | Niveles 0 y 1 con el `FakeTransport` de D9. Ninguna prueba descarga un modelo, exige GPU ni abre conexiones fuera de `localhost` (`pytest-socket`). En nivel 0, el NER es un modelo diminuto de prueba en `safetensors`, generado con pesos sintéticos; la prueba de 0 fugas de NFR1.3 corre en nivel 1 con el NER real montado de solo lectura. |
| NFR2.2 | cambia | U10 no necesita GPU. | El lockfile de `libs/anonymizer` y de `services/anonymizer-proxy` usa el índice de `torch` solo CPU: una comprobación de nivel 0 falla si aparece algún paquete `nvidia-*` o `triton`. |
| NFR13.1 | cambia | Cobertura de líneas. | ≥ 80 % en `libs/anonymizer` y en `services/anonymizer-proxy`, medido en la CI y bloqueante. |
| NFR13.2 | cambia | 100 % de ramas en el módulo guardia (cierra R-06 de la revisión 1). | Todo U10 es guardia de AUTONOMIA-04: `libs/anonymizer/` (`domain/`, `application/`, `providers/`) y `services/anonymizer-proxy/src/` con `--cov-branch` y `fail_under = 100`. **Solo código de U10**: la validación de destinos de ModelGateway es de U11, y las comprobaciones de `semantic-agent`, de U4. Las exclusiones (`testing/`, el arranque de Uvicorn) se declaran en `.coveragerc-guards` y cada exclusión nueva se justifica en el PR. |
| NFR14.1 | cambia | Textos e identificadores según el glosario. | `detail` de los errores en español, del catálogo. Identificadores en inglés: `masking_request`, `mask_table`, `mask_category`, `detection_rule_set`, `allowed_word_list`, `provider_domain_list`, `provider_capability_table`, `outbound_destination`, `marker`, `altered_markers`. Las marcas conservan sus categorías en español (`PERSONA`, `LUGAR`, `EXPEDIENTE`, `IDENTIFICADOR`, `ENTIDAD`), porque son valores del contrato. Prueba de nivel 0: todo `detail` sale del catálogo. |

## 4. Dependencias nuevas de U10

- **`libs/anonymizer`:** `httpx`, `google-re2`, `transformers`, `torch` (índice CPU), `safetensors`,
  `jsonschema`, `referencing` y `pyyaml`, más la biblioteca de contratos de U1.
- **`services/anonymizer-proxy`:** `fastapi`, `uvicorn`, `pydantic-settings`, `prometheus-client` y
  `libs/anonymizer`.
- **Desarrollo:** `pytest-socket`, `trustme` y `psutil`.

Todas van fijadas en el lockfile de su paquete, con `pip-audit` y Trivy en la CI (`team.md`).
`google-re2` y `torch` traen extensiones nativas; Trivy y `pip-audit` las cubren como a las demás.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, *payload*, fallo cerrado, proxy (nivel 0) | `uv run --directory libs/anonymizer pytest -m "not integration and not perf"` y `uv run --directory services/anonymizer-proxy pytest -m "not integration and not perf"` | Verde: NFR1.2, NFR1.8, NFR1.11–NFR1.14, NFR4.3, NFR6.1, NFR8.2, NFR8.4, NFR10.1–NFR10.16 |
| Ramas del módulo guardia | `uv run --directory libs/anonymizer pytest --cov-branch --cov-config=.coveragerc-guards` (y lo mismo en `services/anonymizer-proxy`) | 100 % (NFR13.2) |
| 0 fugas con el NER real y riesgo residual (nivel 1) | `uv run --directory libs/anonymizer pytest -m "integration and leakage" --residual-report out/anonymizer-residual.json` | 0 fugas (NFR1.3); tasas informativas en el reporte (NFR1.10) |
| Integración, *canary* y TLS (nivel 1) | `uv run --directory services/anonymizer-proxy pytest -m integration` | Verde; 0 apariciones del *canary* (NFR10.3, NFR10.5, NFR10.7, NFR15.3) |
| Rendimiento y memoria | `uv run --directory services/anonymizer-proxy pytest -m perf --perf-report out/anonymizer-perf.json` | NFR3.1–NFR3.5, NFR8.3 |
| Cifras atadas de C25 | `uv run --directory libs/anonymizer pytest -m limits` | NFR-U10-04 (a) y (b) |
| ADR del proveedor | `uv run --directory libs/anonymizer python ../../scripts/check-provider-adr.py` | Código 0; los controles negativos fallan como se espera (NFR1.2) |
| Fronteras | `uv run --directory libs/anonymizer lint-imports` | 0 contratos rotos; cada control negativo falla (NFR10.13) |
| Tipos y *lint* | `mypy --strict` y `ruff check` en `libs/anonymizer` y `services/anonymizer-proxy` | 0 errores |
| CPU solamente | `uv run --directory libs/anonymizer pytest -m lockfile` | Ningún paquete `nvidia-*` ni `triton` (NFR2.2) |
| Escenario A con anonimizador (nivel 2, U11) | La CLI de U11 en modo evaluación con el perfil de la primera rebanada | NFR5.1, NFR4.1; reporte adjunto al PR de B11 |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El NER no reconoce un nombre al inicio de oración que no se repite (FD-U10 §8) | Prueba de 0 fugas que incluye nombres al inicio de turno; si falla, se cambia de modelo o se añaden reglas, nunca se baja el umbral |
| `torch` pesa (imagen y memoria) | Índice solo CPU (NFR2.2); el pico de memoria se mide (NFR8.3) y U2 dimensiona el pod |
| `google-re2` no admite *lookbehind* ni referencias hacia atrás | Las reglas se escriben sin ellas; una regla que las necesite se descarta en su PR |
| La API de Anthropic cambia el modo estructurado o su versión | La versión de la API es una constante del adaptador; la prueba de contrato con respuestas grabadas (AC13.6.1) detecta el cambio, y un modelo nuevo entra por PR a la tabla de capacidades |
| Anthropic no admite `seed` | Se declara en el ADR y en `ModelCall` (nula); el acuerdo entre 3 corridas lo mide U11 (NFR4.2) |
