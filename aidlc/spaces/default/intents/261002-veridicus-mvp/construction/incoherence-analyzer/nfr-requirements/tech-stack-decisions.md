# Decisiones de tecnología — U11 incoherence-analyzer

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todas las decisiones son **nuevas**.
- **Respuestas.** P1 = A fija los modelos de los perfiles (D9); P2 = A y P3 = A, los archivos de umbrales y
  del conjunto (D10).
- **Límite.** El *stack* común (Python 3.12, Ruff, mypy estricto, `uv`, `pytest`) lo fija `team.md`; aquí
  solo se decide lo propio de U11.

**Insumos.** functional-spec y rules de U11 (entidades `ExecutionProfile`, `GatewayAssembly`,
`LocalModelAdapter`, `AnonymizerHttpClient`, `CliInvocation`); requirements (NFR2, NFR13, NFR14, FR13–FR16);
contract-summary (C13, C14, C17–C21, C25); `tech-stack-decisions.md` de U1 y de U10 (cargador YAML seguro, JCS,
NER y transportes); reporte de ZINE (M1–M6).

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | nuevo | Empaquetado | Cuatro paquetes en `libs/` (`incoherence_analyzer`, `model_gateway`, `execution_profiles`, `integrity_policy`), cada uno con su `pyproject.toml` y `uv.lock`. `libs-anonymizer` es solo dependencia del extra `cli` | Un solo paquete; el anonimizador como dependencia común | `semantic-agent` instala el núcleo sin el anonimizador (BR10.5) y import-linter lo comprueba | NFR10.5 |
| D2 | nuevo | CLI | `argparse` de la biblioteca estándar, punto de entrada `veridicus` | Typer, Click | Sin dependencias para la wheelhouse de ZINE; los mensajes en español se controlan a mano | NFR14, NFR2.3 |
| D3 | nuevo | Validación de esquemas | `jsonschema` (Draft 2020-12) con los esquemas de `veridicus_contracts` de U1 | Pydantic como fuente de esquema | El esquema de C6 y C19 lo publica U1 y no se duplica; Pydantic solo para los tipos internos si hace falta | NFR10.6 |
| D4 | nuevo | Cliente HTTP del adaptador local y de C21 | `httpx` síncrono con `follow_redirects=False`, `HTTPTransport(retries=0)`, *timeout* por llamada y lectura por bloques con tope | `requests`, `aiohttp` | Un turno a la vez (NFR8.1); los reintentos son de BR10.3, no del transporte | NFR10.8, NFR10.11 |
| D5 | nuevo | YAML y JSON canónico | Cargador seguro y JCS de `veridicus_contracts` (U1) | `yaml.load`, una JCS propia | Una sola implementación de la huella (NFR11.1) y sin etiquetas de objeto | NFR10.9, NFR11.1 |
| D6 | nuevo | Servidor de modelos locales | Servidor compatible con OpenAI de `llama.cpp` (`llama-server`) con `response_format: json_schema`, razonamiento apagado y 1 ranura | vLLM (exige GPU), Ollama (sin `json_schema` estricto medido) | Es lo que se midió en ZINE: 20/20 JSON válidos y 4/4 pares repetibles con semilla (M4, M5) | NFR2, NFR4.2, NFR4.14 |
| D7 | nuevo | Pruebas | `pytest`, `pytest-cov`, Hypothesis (huellas y verificación de citas), `pytest-socket` (sin red en niveles 0 y 1), *fake* determinista del `ModelGateway` y `FakeTransport` de U10 | Grabar respuestas reales con red | Niveles 0 y 1 sin red ni GPU (`team.md`) | NFR2.1, NFR13 |
| D8 | nuevo | Fronteras | import-linter con los contratos de BR10.5 y uno que prohíbe clientes de métricas | Revisión manual | Se comprueba en cada PR con control negativo | NFR10.5, NFR15.2 |
| D9 | nuevo | Modelos por perfil (P1 = A) | Ver §2 | Verificador comercial de OpenAI o de Google, alterno de Google (P1 B–D) | Solo Anthropic recibe datos; B10 no crece | NFR1.7, NFR5.2 |
| D10 | nuevo | Archivos de evaluación | `evaluation/thresholds.v1.yaml` (P2 = A), `evaluation/synthetic/manifest.yaml` (P3 = A) y `evaluation/zine/` (solo `.sbatch`, `empaquetar.py` y manifiesto) | Umbrales en código | Cambian solo por PR y se citan en el reporte | NFR4, NFR12.2 |

## 2. Perfiles iniciales de `config/profiles.yaml`

Los identificadores exactos de los modelos de Anthropic y Google entran con el PR del perfil y el ADR del
proveedor (NFR-U11-01). Los archivos locales llevan su SHA-256 y formato GGUF sin código ejecutable
(`team.md`).

| Perfil | Propósito | Juez | Verificador | Alterno | Permutación | Fragmentado |
|---|---|---|---|---|---|---|
| `comercial-piloto` | Producción y CLI | Anthropic, externo | gpt-oss-20b Q8_0, local, `family: openai` | Ninguno | Sí | No (juez externo, NFR-U11-04) |
| `evaluacion-comercial` | Evaluación, bloquea (P2 = A) | Igual que `comercial-piloto` | Igual | Ninguno | Sí | No |
| `todo-local` | Demostración en el clúster | Qwen cuantizado que quepa en el clúster, `family: qwen`; archivo y SHA-256 en Infrastructure Design de U2 | gpt-oss-20b Q8_0 | Ninguno | Sí (FD-U8-08) | Ventana 40, solapamiento 10 |
| `evaluacion-local-zine` | Evaluación en ZINE, `batch_only: true` | Qwen3.6-35B-A3B Q8_0, SHA-256 `d1a395809f65a43a13ad119eb4e7acdef1ac6d68120f39902c8ab96e72794a59` | gpt-oss-20b Q8_0, SHA-256 `bcd455d4034ec02f71a875b46cb17df44a97911d7258291973be4d21f98329f3` | Ninguno | Sí | Ventana 60, solapamiento 20 |

Generador del conjunto sintético: Google (familia distinta del juez y del verificador de todo perfil de
evaluación, BR13.5).

## 3. Configuración

Prefijo `VERIDICUS_`. Toda cifra de límite sale de `contracts/limits.v1.yaml` (C25); el entorno solo la baja,
y una cifra que la sube impide arrancar (NFR10.15).

| Cifra de C25 | Tope del catálogo (NFR-U11-05) | Máquina de desarrollo y clúster | ZINE |
|---|---|---|---|
| `model_call_timeout_s` | 3600 | 300 (≥ 200, NFR-U10-04) | 3600 |
| `run_deadline_incremental_s` | 1200 | 900 | — (solo modo final) |
| `run_deadline_final_s` | 43200 | 3600 | 43200 |
| `fragment_window_turns` | 60 | 40 en `todo-local` | 60 |
| `fragment_overlap_turns` | 20 | 10 en `todo-local` | 20 |
| `model_response_max_bytes` (nueva, NFR-U11-06) | 2 097 152 | 2 097 152 | 2 097 152 |

Una comprobación de nivel 1 exige, para cada perfil local, que la ventana más el *prompt* y una reserva de
salida quepan en el contexto del servidor declarado en el perfil.

| Variable | Uso |
|---|---|
| `VERIDICUS_PROFILES_PATH`, `VERIDICUS_PRICES_PATH`, `VERIDICUS_LIMITS_PATH` | Rutas de configuración; sin ellas, las del repositorio |
| `VERIDICUS_<AJUSTE>` de C25 | Bajar una cifra en un despliegue |
| La que nombre `api_key_ref` (p. ej. `VERIDICUS_ANTHROPIC_API_KEY`) | Clave del proveedor, solo en la CLI; nunca en `semantic-agent` (NFR10.2) |
| `VERIDICUS_LOCAL_BASE_URL_<PAPEL>` | `base_url` del servidor local; debe ser privada (NFR1.6) |

## 4. Calidad del código (NFR2, NFR13, NFR14)

- **NFR2:** niveles 0 y 1 en CPU y sin red (NFR2.1); el perfil GPU no lo usa ninguna prueba de U11.
- **NFR13:** cobertura de NFR13.1–NFR13.3; mypy estricto y Ruff con reglas `S`.
- **NFR14:** identificadores en inglés con el glosario; mensajes de la CLI, errores y comentarios en español.
  Los campos del contrato común del TG (`hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones`) conservan su
  nombre sin alias (CD-05).

## 5. Dependencias

| Paquete | Uso | Paquete de U11 |
|---|---|---|
| `veridicus_contracts` (U1) | Esquemas, cargador YAML, JCS, límites | Todos |
| `jsonschema` | Validación | `incoherence_analyzer`, `execution_profiles` |
| `httpx` | Adaptador local y cliente de C21 | `model_gateway` |
| `libs-anonymizer` (U10) | Solo extra `cli` | `incoherence_analyzer[cli]` |
| `pytest`, `pytest-cov`, `hypothesis`, `pytest-socket`, `import-linter` | Pruebas | Desarrollo |

Todas fijadas en `uv.lock` con *hashes*; `pip-audit` en la CI (NFR10.14). La wheelhouse de ZINE se arma con
`uv export --frozen` desde esos lockfiles.

## 6. Comandos de verificación (AUTONOMIA-02)

| Comprobación | Comando | Umbral |
|---|---|---|
| Lint y tipos | `uv run ruff check libs/ && uv run mypy --strict libs/incoherence_analyzer libs/model_gateway libs/execution_profiles libs/integrity_policy` | 0 errores |
| Pruebas y cobertura | `uv run pytest libs/ --cov --cov-branch --cov-fail-under=80` | ≥ 80 % de líneas; 100 % de ramas en guardias (NFR13.2) |
| Fronteras | `uv run lint-imports` | 0 contratos rotos |
| Perfiles | `uv run python scripts/check-profiles.py config/profiles.yaml` | 0 hallazgos (NFR1.7) |
| Conjunto | `uv run python scripts/check-dataset.py evaluation/synthetic/manifest.yaml` | 0 hallazgos (NFR4.11) |
| Secretos y datos | `gitleaks detect --source libs/ && gitleaks detect --source evaluation/` | 0 hallazgos |
| Dependencias | `uv run pip-audit` | 0 `HIGH`/`CRITICAL` con corrección |
| Nivel 2 | `veridicus evaluate evaluation/synthetic --perfil evaluacion-comercial --salida resultados-locales/eval` | Código 0; reporte adjunto al PR |

## 7. Riesgos

| Riesgo | Tratamiento |
|---|---|
| `llama-server` cambia su API compatible con OpenAI | Versión fijada por digest y respuestas grabadas en la prueba de contrato (BR10.2) |
| El juez Qwen cuantizado de `todo-local` no cabe en la RAM del clúster | Lo resuelve Infrastructure Design de U2; si no cabe, `todo-local` queda solo para ZINE y la demo usa `comercial-piloto` |
| La evaluación en CPU tarda más de 6 h (NFR2.2) | Partir por muestras; nunca bajar umbrales |
