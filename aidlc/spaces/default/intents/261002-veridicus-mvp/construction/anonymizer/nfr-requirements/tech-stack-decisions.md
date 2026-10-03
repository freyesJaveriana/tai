# Decisiones de pila — U10 anonymizer

**Insumos.** Flujos F1–F3 de `functional-design/functional-spec.md` (functional-spec), reglas BR1–BR3 de
`functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`; FR11.3 y NFR1,
NFR2, NFR10, NFR13 y NFR14 de `inception/requirements-analysis/requirements.md` (requirements); C13,
C14 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`; `security-requirements.md`; las decisiones de pila ya aprobadas de U2
(chart, Kyverno, Secrets) y de U4 (ModelGateway con `httpx`, D10 de U4).

Lo que ya fijan `team.md`, U2, U3 y U4 no se repite: Python 3.12, FastAPI, Pydantic v2,
`pydantic-settings`, `uv`, `pytest` + Hypothesis, mypy estricto, Ruff, import-linter, Problem Details
desde `libs/`, `prometheus-client`, imágenes fijadas por digest y sin root, `helm template` →
`kubeconform` → Kyverno CLI.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Estado de entrega | **Apagado por defecto** (`anonymizer.enabled: false`); se habilita solo por un PR con ADR del proveedor y la `NetworkPolicy` de ese único destino | Cualquier proveedor compatible con OpenAI sin condiciones (P1 = B); no construir U10 (P1 = C) | P1 = A: el destino ve la estructura del testimonio aunque vaya enmascarado; el juez interno basta para el MVP | NFR1.1, NFR1.2 |
| D2 | Motor de detección | Expresiones regulares con **`google-re2`** (tiempo lineal, sin retroceso) para patrones y para la lista de nombres (alternación escapada, ≤ 2 000 términos), sobre una copia normalizada (minúsculas y sin tildes) con mapa de posiciones al original | `re` de la biblioteca estándar; `regex` con *timeout*; un modelo NER (spaCy) | Sin retroceso catastrófico (T12) y determinista; un NER añade un modelo, más memoria y resultados menos auditables; FR11.3 fija expresiones regulares | NFR3.1, NFR3.4, NFR10.1 |
| D3 | Prioridad entre categorías | `EXPEDIENTE` > `PERSONA` > `LUGAR`; ante la duda se enmascara (BR1.2); tramos solapados se funden en el más largo | Dejar sin enmascarar lo ambiguo | Ningún tramo que coincida sale en claro | NFR1.3, NFR1.10 |
| D4 | Origen de la lista de nombres | El cliente la envía en `veridicus_masking`; el proxy **no** tiene acceso a la base | El proxy lee la lista de PostgreSQL con un rol propio | El único pod con salida a internet no debe tener credencial de base de datos (T11, NFR10.10) | NFR1.8, NFR10.10 |
| D5 | Servicio HTTP | FastAPI + Uvicorn, **1 proceso**, semáforo de 4 llamadas (`anyio`), rutas C14 y C16 | Proxy genérico (Envoy, nginx con Lua) | El enmascarado necesita código propio y probado con 100 % de ramas; un proxy genérico no hace falla cerrada sobre el contenido | NFR8.2, NFR10.7 |
| D6 | Cliente hacia el destino | `httpx` con `ssl.SSLContext` de mínimo TLS 1.2, verificación activa, `follow_redirects=False`, `transport=HTTPTransport(retries=0)`, límite de lectura de 2 MiB y *timeouts* separados | SDK de cada proveedor | Control explícito de TLS, redirecciones, reintentos y *timeouts*; mismo cliente que U4 | NFR10.4, NFR10.5 |
| D7 | Políticas de manifiestos | Tres políticas Kyverno nuevas en `deploy/policies/` con sus controles negativos en `deploy/policies/tests/`: `veridicus-anonymizer-disabled-by-default`, `veridicus-egress-only-anonymizer`, `veridicus-anonymizer-hardening` | Revisión manual del manifiesto | Comprobable sin red en nivel 0 (team-practices) | NFR1.1, NFR1.5, NFR1.9, NFR10.10 |
| D8 | Comprobación del ADR | `scripts/check-provider-adr.sh` (Bash + `yq`) en la CI | Solo revisión del PR | Los cuatro compromisos y el destino quedan verificados de forma mecánica | NFR1.2 |
| D9 | Pruebas sin red | Destino *fake* con `httpx.MockTransport` (nivel 0) y un servidor HTTPS local con certificado de prueba (nivel 1); ninguna prueba llama a un proveedor real | Grabaciones (VCR) de un proveedor real | Sin red en la CI y sin datos que salgan; los *fixtures* son de U1 | NFR2.1, NFR12.1 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `anonymizer.enabled` (*values* del chart) | `false` | Si es `true`, exige `anonymizer.providerAdr`, `upstreamHost`, `upstreamCidrs` y `model` (NFR1.2) | chart |
| `VERIDICUS_ANONYMIZER_UPSTREAM_URL` | — | Obligatoria; `https://`, sin usuario, host igual al del ADR (NFR10.5) | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_API_KEY` | — (desde el Secret `veridicus-anonymizer-credential`) | Obligatoria y no vacía; nunca se registra (NFR10.6) | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_MODEL` | — | Obligatorio; `<proveedor>/<modelo>@<versión>` (NFR11.1) | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_RULES_PATH`, `VERIDICUS_ANONYMIZER_RULES_SHA256` | `/etc/veridicus/anonymizer/rules.yaml`, — | Archivo `readOnly`; SHA-256 de 64 hexadecimales igual al del archivo (NFR10.11) | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_MASKING_TIMEOUT_SECONDS` | 2 | Número entre 0,5 y 5 (NFR3.4) | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_CONNECT_TIMEOUT_SECONDS` | 5 | Entre 1 y 10 | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_JUDGE_TIMEOUT_SECONDS`, `_EMBED_TIMEOUT_SECONDS` | 170, 25 | ≤ 170 y ≤ 25 (menores que los del cliente de U4, NFR10.4) | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_MAX_CONCURRENCY` | 4 | Entero 1–8 (NFR8.2) | `anonymizer-proxy` |
| `VERIDICUS_ANONYMIZER_MAX_BODY_BYTES`, `_MAX_PROPER_NOUNS` | 524288, 2000 | Enteros positivos, no mayores que esos valores (NFR10.8) | `anonymizer-proxy` |
| `VERIDICUS_JUDGE_URL`, `VERIDICUS_EMBEDDINGS_URL` (clientes) | Servidores internos de U2 | NFR1.1 de U4 + NFR1.6: la URL del proxy solo se admite aquí, nunca en Whisper ni TTS | `semantic-agent`, `session-api` |

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR2.1 | Todo U10 se prueba en CPU y sin red. | Niveles 0 y 1 con el destino *fake* de D9; ninguna prueba descarga un modelo, exige GPU ni abre conexiones fuera de `localhost` (un *socket guard* de `pytest` falla si lo intentan). |
| NFR2.2 | El proxy no necesita GPU. | El chart no declara `nvidia.com/gpu` para el proxy en ningún perfil (prueba de nivel 0 sobre el render de `values-cpu.yaml` y `values-gpu.yaml`). |
| NFR13.1 | Cobertura de líneas. | ≥ 80 % en `services/anonymizer-proxy`, medido en la CI y bloqueante. |
| NFR13.2 | 100 % de ramas en el módulo guardia. | Todo U10 es guardia de AUTONOMIA-04: `services/anonymizer-proxy/src/anonymizer_proxy/domain/` (detección, tabla, enmascarado y restauración) y `application/` (orquestación de la llamada y falla cerrada), más la validación de destinos de `libs/model_gateway` que añade NFR1.6: `--cov-branch` con `fail_under = 100` sobre esos módulos. Las exclusiones se declaran en `.coveragerc-guards` y cada nueva se justifica en el PR. |
| NFR14.1 | Textos e identificadores según el glosario. | `detail` de los errores en español desde el catálogo; identificadores en inglés: `masking_request`, `mask_table`, `mask_category`, `detection_rule_set`, `outbound_destination`, `marker`, `proper_nouns`; los marcadores conservan sus categorías en español (`PERSONA`, `LUGAR`, `EXPEDIENTE`) porque son valores del contrato (functional-spec). Prueba de nivel 0 de que todo `detail` sale del catálogo. |

## 4. Dependencias nuevas de U10

- `services/anonymizer-proxy`: `fastapi`, `uvicorn`, `pydantic-settings`, `httpx`, `google-re2`,
  `pyyaml`, `prometheus-client`; las de desarrollo de U3 más `pytest-socket` y `trustme` (certificado de
  prueba del nivel 1).
- `libs/model_gateway`: sin dependencias nuevas (la validación de NFR1.6 usa `urllib.parse`).
- CI: `yq` para `scripts/check-provider-adr.sh`.

Todas fijadas en el lockfile del servicio; `pip-audit` en la CI (team-practices). `google-re2` trae una
extensión nativa: Trivy y `pip-audit` la cubren como a las demás.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, *payload* saliente, falla cerrada (nivel 0) | `uv run --directory services/anonymizer-proxy pytest -m "not integration and not perf"` | Verde; NFR1.3, NFR1.4, NFR1.8, NFR10.1, NFR10.2, NFR10.4–NFR10.11 |
| Ramas del módulo guardia | `uv run --directory services/anonymizer-proxy pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Riesgo residual solo con reglas | `uv run --directory services/anonymizer-proxy pytest -m residual --residual-report out/anonymizer-residual.json` | 0 escapes en lo bloqueante; tasa informativa en el reporte (NFR1.10) |
| Integración y *canary* (nivel 1) | `uv run --directory services/anonymizer-proxy pytest -m integration` | Verde; 0 apariciones del *canary* (NFR10.3) |
| Rendimiento en proceso | `uv run --directory services/anonymizer-proxy pytest -m perf` | NFR3.1–NFR3.3, NFR8.1, NFR8.2 |
| Destinos de ModelGateway | `uv run --directory libs/model_gateway pytest` | Verde; NFR1.6 |
| Políticas de manifiestos | `helm template deploy/veridicus -f deploy/veridicus/values-cpu.yaml > out/render.yaml && kyverno apply deploy/policies/ --resource out/render.yaml` y `kyverno test deploy/policies/tests/` | 0 violaciones; cada control negativo falla como se espera (NFR1.1, NFR1.5, NFR1.9, NFR10.10) |
| ADR del proveedor | `scripts/check-provider-adr.sh deploy/veridicus/values-cpu.yaml deploy/veridicus/values-gpu.yaml` | Código 0 (con el proxy apagado, no hay nada que comprobar y termina en 0) |
| Habilitación: calidad y latencia (nivel 2) | `uv run --directory evaluation python -m golden.run --profile cpu --model-gateway anonymizer --report out/level2-anonymizer.json` | NFR3.5, NFR4.1, NFR4.2, NFR5.1, NFR5.2 |
| Habilitación: carga | `uv run --directory evaluation python -m load.run_batches --sessions 50 --concurrency 3 --report out/nfr8-anonymizer.json` | NFR8.4 |
| Verificación en el clúster (manual, solo lectura) | Comandos de NFR1.7 | Evidencia adjunta al PR de la sustentación |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en `services/anonymizer-proxy` | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Nombres de una sola palabra sin tratamiento escapan a las reglas (FR11.3) | Apagado por defecto; tasa medida en NFR1.10 y citada en el ADR; la lista de nombres del escenario cubre los del marco de verdad |
| `google-re2` no admite *lookbehind* ni referencias hacia atrás | Las reglas se escriben sin ellas; una regla que las necesite se descarta en su PR |
| El proveedor no garantiza `seed` ni repetibilidad | NFR4.2 impide habilitarlo |
| El proveedor usa IP cambiantes y la `NetworkPolicy` no puede fijar el destino | El ADR exige CIDR estables o un CNI con políticas por FQDN (Infrastructure Design); si no, no se habilita |
| Cambiar a *embeddings* externos invalida los vectores guardados y el umbral | NFR4.1: reindexar y recalibrar en el mismo PR |
| Mantener un servicio que no se despliega | Sus pruebas de niveles 0 y 1 corren en cada PR; un fallo bloquea como cualquier otro |
