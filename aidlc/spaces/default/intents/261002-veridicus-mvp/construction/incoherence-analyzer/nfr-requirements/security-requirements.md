# Requisitos de seguridad — U11 incoherence-analyzer

**Revisión 1 (2026-11-22): primera pasada de una unidad nueva del cambio 01 (DT27) y de la adenda 02.**
- **IDs.** Todo es **nuevo**. Cada requisito hereda el ID del NFR de Inception que detalla y le añade un
  número (`NFR1.3` detalla NFR1).
- **Respuestas.** **P1 = A**: el verificador de `comercial-piloto` es local (gpt-oss-20b), no hay alterno en
  la primera rebanada y el generador del conjunto es de Google. **P2 = A** (umbrales estadísticos) y
  **P3 = A** (40 muestras), en `reliability-requirements.md`.
- **Tipo `library`.** El archivo de etapa pide para U11 este documento, `tech-stack-decisions.md` y
  `traceability.json`. Como NFR3, NFR8 y los plazos de C25 recaen aquí, se añaden
  `performance-requirements.md` y `reliability-requirements.md`. No hay documento de escalabilidad ni de
  observabilidad: la biblioteca no escala por sí misma y no expone métricas. Lo que aporta a NFR8 y NFR15
  está en esos dos documentos.

**Insumos.**
- Flujos F1–F12, máquinas de estado §3, escenarios E1–E66, frontera §7 y tabla FD-U11-01 a FD-U11-28 de
  `functional-design/functional-spec.md` (functional-spec).
- Reglas BR1.1–BR14.5 de `functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`.
- FR4, FR13–FR16 y NFR1–NFR15 de `inception/requirements-analysis/requirements.md` (requirements, revisión
  3; NFR9 «Retirado»), y VE-01, VE-02, VE-07, VE-14 y VE-17 de `requirements-adenda-02.md`.
- C6, C8, C13, C14, C17–C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary,
  revisión 3).
- Lo que fijaron hoy otras unidades:
  - **U1:** `limits.exceeded` siempre `413`, C25 sin nulos y decimales en `ratio` y `s`.
  - **U10:** NFR-U10-04 (plazo por llamada ≥ 200 s), NFR-U10-07 (Anthropic primero, generador de Google u
    OpenAI) y el ADR por proveedor.
  - **U2:** modelos concretos y *N* de la prueba de humo, delegados aquí.
  - **U12:** campo `origin` de C19 v2.
  - **U4, U8, U9 y U13:** sus tablas FD (ver §6).
- `docs/validacion-zine/reporte.md`, con las mediciones M1–M6 y la revisión del humano del 2026-11-06.
- Respuestas P1–P3 de `nfr-requirements-questions.md`, reglas AUTONOMIA-01..05 de `team.md` y
  prohibiciones de `project.md`.

Las pruebas corren en **nivel 0** (cada PR, sin red ni GPU, con *fakes* deterministas del `ModelGateway` y
datos sintéticos) salvo que la fila diga otra cosa. Cada una lleva su control negativo. Los comandos están
en `tech-stack-decisions.md` §6.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Datos sin seudonimizar que maneja | Qué cruza la frontera de la máquina o del clúster |
|---|---|---|---|
| Núcleo `libs/incoherence_analyzer/` (filtro, verificación de citas, ventanas, salida) | En el proceso de la CLI (máquina local o nodo de ZINE) o de `semantic-agent` (clúster) | Transcripción completa, candidatos y citas, solo en memoria | Nada por sí mismo |
| `ModelGateway`, adaptador local (C14) | Igual | Turnos sin enmascarar hacia el servidor local | Nada: `base_url` interna de la máquina, del clúster o del trabajo de SLURM |
| `ModelGateway`, adaptador `anonymizer` en la CLI | Máquina local | Mensajes que el módulo de U10 seudonimiza en el mismo proceso | **Sí**, por el módulo de U10: texto seudonimizado hacia `api.anthropic.com` (P1 = A: solo el juez es externo) |
| Cliente HTTP de C21 en `semantic-agent` | Clúster | Mensajes hacia `anonymizer-proxy`, dentro del clúster | Nada desde U11; el proxy es el único que sale |
| Verificador local gpt-oss-20b (P1 = A) | Servidor local de la máquina o del clúster | `hecho`, `tipo` y las dos citas, sin enmascarar | Nada |
| CLI: salidas de C6 | Disco local; corpus fuera de Git | Citas literales y hechos | Nada |
| CLI: reporte C19 y `AVISO.txt` | Disco local; de ZINE vuelve solo el reporte | Ninguno: cifras, hashes y versiones | Lo copia el humano a la consola del investigador o al repositorio principal |
| Paquete de ZINE (`evaluation/zine/paquete/`) | Máquina local → ZINE, lo copia el humano | Transcripciones del corpus del TG y sintéticas, wheelhouse, perfil local | Hacia la carpeta del proyecto en ZINE; nunca a Git |
| Conjunto sintético (`evaluation/synthetic/`) | Repositorio | Solo datos ficticios | El *prompt* de generación sale hacia Google durante su creación (P1 = A) |

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Un perfil con destino externo arranca sin el anonimizador delante | Information disclosure | Alto | NFR1.2 |
| T2 | El anonimizador cae a mitad de corrida y la llamada sale igual | Information disclosure | Alto | NFR1.4 |
| T3 | Una llamada externa vuelve con `anonymized: false` y la corrida sigue | Repudiation, Information disclosure | Alto | NFR1.5 |
| T4 | Un perfil nombra un proveedor externo sin ADR, o un segundo proveedor recibe datos sin decisión | Information disclosure | Alto | NFR1.7 |
| T5 | Se analiza una transcripción cuyo consentimiento no autoriza la transferencia | Information disclosure | Alto | NFR1.8 |
| T6 | El testimonio cambia las instrucciones del juez (inyección) | Tampering | Medio | NFR5.1, NFR5.4 |
| T7 | Juez, verificador y generador comparten familia y se refuerzan los sesgos | Tampering | Medio | NFR5.2 |
| T8 | Un hallazgo sale con una cita inventada o en otro turno | Tampering | Alto | NFR10.6 (y la verificación de BR5.5–BR5.7) |
| T9 | La salida lleva una etiqueta de veracidad | Tampering | Alto | NFR11.2 |
| T10 | Una clave de API aparece en logs, stderr, reporte o paquete | Information disclosure | Medio | NFR10.2, NFR12.2 |
| T11 | Testimonio en stderr, logs, reporte C19 o `AVISO.txt` | Information disclosure | Alto | NFR10.3 |
| T12 | Corpus del piloto en Git o en la CI | Information disclosure | Alto | NFR12.2 |
| T13 | El servidor local responde algo enorme o redirige a otro *host* | Denial of service, Spoofing | Medio | NFR10.8 |
| T14 | La biblioteca importa Redis, Kubernetes, una base de datos o el anonimizador fuera de la raíz de composición | Elevation of privilege | Medio | NFR10.5 |
| T15 | Alguien cambia perfiles, *prompt*, precios o umbrales sin PR | Repudiation | Medio | NFR10.7, NFR11.1 |
| T16 | Un YAML de configuración con etiquetas de objeto o claves duplicadas | Tampering | Medio | NFR10.9 |
| T17 | Un script del repositorio lanza trabajos en ZINE | Elevation of privilege | Medio | NFR12.2 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | nuevo | El diseño declara la frontera por componente. | La tabla de §1 está en este documento y en el README de `libs/incoherence_analyzer/`. Un componente nuevo entra con su fila en el mismo PR | Revisión del PR |
| NFR1.2 | nuevo | Un destino externo sin `AnonymizingProvider` impide arrancar (BR10.1). | En la biblioteca y en la CLI, un perfil con algún papel o alterno `external` y sin el proveedor inyectado termina en error de configuración (CLI: código 3) con **0 llamadas** en el *fake*. Pasa también cuando el módulo de U10 no se puede construir (NER con otro SHA-256) | Nivel 0 |
| NFR1.3 | nuevo | El cuerpo saliente no lleva ninguna entidad sembrada (BR7.5, AC11.3.7). | Prueba compuesta con el `ModelGateway` real, el adaptador `anonymizer`, el módulo de U10 y su `FakeTransport`: con un *fixture* de perfil con juez, verificador y alterno externos, los cuerpos capturados de `judge`, `verifier` y `verifier_permuted` tienen **0 apariciones** de las entidades sembradas. Con el enmascarado puenteado por el *fixture* de U10, la prueba falla | Nivel 0 (NER de prueba) y nivel 1 (NER real, sin red) |
| NFR1.4 | nuevo | Si el anonimizador falla, no sale ninguna llamada (BR7.4, AC11.3.3). | Prueba compuesta con el anonimizador (a) caído, (b) que lanza una excepción y (c) que no responde antes de su plazo: el transporte registra **0 llamadas**, la corrida termina en `anonimizador_no_disponible`, sin reintento ni alterno. Con 100 % de ramas | Nivel 0 |
| NFR1.5 | nuevo | Una llamada externa con `anonymized: false` aborta la corrida (BR7.6). | Un *fake* que devuelve ese registro en la segunda llamada da exactamente 2 llamadas, `incidente_anonimizacion`, hallazgos vacíos y código 4 en la CLI. También con un error tipado que trae ese registro | Nivel 0 |
| NFR1.6 | nuevo | Con un perfil todo local no interviene el anonimizador ni nada fuera de la máquina (BR7.7, BR2.3). | Un `AnonymizingProvider` espía registra 0 llamadas con `todo-local`, y todos los registros llevan `anonimizado: false`. Un destino local con URL pública, o un externo con `base_url`, hace inválido el perfil | Nivel 0 |
| NFR1.7 | nuevo | En la primera rebanada solo Anthropic recibe datos, y ningún proveedor externo entra sin su ADR (P1 = A). | `scripts/check-profiles.py` lee `config/profiles.yaml` y falla si: (a) un papel o alterno `external` nombra un proveedor o modelo que no está en la `ProviderCapabilityTable` de U10 con su ADR; (b) `comercial-piloto` o su espejo de evaluación tienen como externo algo distinto del juez de `anthropic`. Controles negativos: verificador `openai` externo en `comercial-piloto` y un proveedor sin ADR. Cambiar (b) es un PR con decisión registrada | Nivel 0 |
| NFR1.8 | nuevo | Sin `autoriza_transferencia` no se usa un perfil con destino externo (BR1.3, VE-07). | Bloque de consentimiento con `autoriza_transferencia: false` y `comercial-piloto`: `profile.transfer_not_authorized` (CLI: 3), 0 llamadas. El mismo bloque con `todo-local` se analiza. Corpus o guiada sin bloque: `session.consent_missing`, 0 llamadas (BR1.2) | Nivel 0 |

### NFR5 — Resistencia adversarial

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR5.1 | nuevo | Escenario A (BR12.6). | Con `--adversarial escenario-a` y el perfil `evaluacion-comercial`: `scenario_a_marker_hits = 0` y `scenario_a_difference ≤ 1 − three_run_agreement` de las 3 corridas sin inyección. En nivel 0, un *fake* que obedece la inyección hace fallar la comprobación y otro que la ignora la pasa. Incluye la variante de U10 que pide los nombres reales: 0 valores sembrados antes de restaurar | Nivel 2 (reporte adjunto al PR) y nivel 0 |
| NFR5.2 | nuevo | Escenario B: tres familias distintas (P1 = A). | Juez `anthropic`; verificador gpt-oss-20b, declarado con `family: openai` porque es de esa línea; juez local de ZINE `family: qwen`; generador del conjunto `google`. `evaluate` termina con 3 si la familia del generador coincide con la del juez o la del verificador del perfil (BR12.1), y la validación del perfil rechaza juez y verificador de la misma familia (BR2.4). El reporte declara la familia de cada papel y la del generador | Nivel 0 y nivel 2 |
| NFR5.3 | nuevo | Escenario C: permutación medida. | En cada perfil de evaluación, `permutation_coverage = 1` y `reversed_order_consistency > 0,65` (media de 3 corridas; `team.md`). La prueba de nivel 0 con un verificador *fake* que cambia de veredicto según el orden da la fracción esperada | Nivel 2 y nivel 0 |
| NFR5.4 | nuevo | El testimonio solo viaja como dato (BR3.1, BR3.3). | En los mensajes capturados, el testimonio nunca aparece en `system`, y `user` es JSON válido. El verificador solo recibe `hecho`, `tipo`, `cita_a` y `cita_b`. Si el archivo del *prompt* no coincide con `config.prompt_sha256`, la corrida termina en `salida_invalida` sin llamar | Nivel 0 |

### NFR10 — Seguridad de la aplicación

Los plazos, los reintentos y el fallo cerrado (NFR10.4, NFR10.10–NFR10.13) están en
`reliability-requirements.md`.

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | nuevo | La entrada se valida antes de llamar (BR1.1, BR1.4, BR1.5). | Contra la copia de C6 con el registro de U1 y contra `turn_max_chars`, `transcript_max_turns` y `transcript_max_chars` de C25: un campo ausente, un enum fuera de valores, un límite superado, un perfil no aprobado o un tramo incremental inválido dan `InputRejected` con su `code` y **0 llamadas**. En la CLI, código 2 o 3 y ningún archivo escrito (BR11.2) | Nivel 0 |
| NFR10.2 | nuevo | Las claves solo llegan por referencia y nunca se muestran (BR2.1, BR2.2). | En la CLI, la clave se lee del entorno por `api_key_ref` (prefijo `VERIDICUS_`). Sin valor: código 3, 0 llamadas, y el mensaje nombra la variable. Con un *canary* como valor, aparece **0 veces** en logs, stderr, salidas, reporte, `AVISO.txt` y textos de excepción. En `semantic-agent` no se resuelve ninguna clave. `gitleaks` en pre-commit y en la CI sobre `libs/` y `evaluation/` | Nivel 0 y CI |
| NFR10.3 | nuevo | Lo que no es un archivo de C6 lleva solo IDs, hashes y cifras (BR11.7, AC11.3.5). | Un *canary* sembrado como nombre en un turno que ningún hallazgo cita aparece **0 veces** en logs, stderr, `reporte.json`, `AVISO.txt` y salidas, en el éxito y en cada código de salida. Los mensajes nombran el archivo por su ruta y la entrevista por `interview_sha256`. Una excepción se registra con su tipo y su `code`, nunca con su mensaje si trae contenido del modelo | Nivel 0 |
| NFR10.5 | nuevo | Fronteras de importación (BR10.5, BR10.4). | Contratos de import-linter: los cuatro paquetes de U11 no importan `redis`, `kubernetes` ni controladores de base de datos; `libs.model_gateway` no importa `libs.anonymizer`; `libs.incoherence_analyzer` solo lo importa desde `cli.composition`, que ningún `__init__` reexporta; el cliente de C21 solo importa los contratos. Cada contrato con un módulo de prueba que lo viola | Nivel 0 |
| NFR10.6 | nuevo | Nada sale sin validarse contra su esquema (BR3.4, BR5.1, BR6.4, BR8.1). | Las respuestas del juez y del verificador se validan contra su esquema cerrado (sin `id`, `pagina`, `avisos`, `actos` ni campos extra como `is_truthful`). Un candidato mal formado invalida la corrida. Toda `Salida` valida contra C6 antes de devolverse; si no, se sustituye por una en error `salida_invalida` que también valida. 100 % de ramas en esos módulos | Nivel 0 |
| NFR10.7 | nuevo | La configuración solo se lee (BR2.11). | Una comprobación estática falla si un módulo fuera del cargador abre en modo escritura `config/profiles.yaml`, `config/prices.yaml`, el archivo del *prompt* o `evaluation/thresholds.v1.yaml`. La CLI no tiene ninguna opción que los modifique | Nivel 0 |
| NFR10.8 | nuevo | El adaptador local solo habla con su servidor interno y con topes (BR10.2). | `httpx` con `follow_redirects=False` (un `3xx` es `ProviderError` con su `ModelCall`, 0 peticiones al otro *host*), `HTTPTransport(retries=0)` y lectura por bloques con tope `model_response_max_bytes` (2 097 152 bytes, NFR-U11-06): más es `ProviderError`. Una respuesta que no es JSON estricto (claves repetidas, `NaN`) o no cumple el esquema es `InvalidOutput` | Nivel 0 |
| NFR10.9 | nuevo | Los YAML se cargan con el cargador seguro de U1. | Perfiles, precios, umbrales, manifiesto del conjunto, listas de etiquetas e inyección del Escenario A se leen con los cargadores de `veridicus_contracts` (seguro, sin claves duplicadas). Una prueba AST falla ante otro cargador en el código de U11. Control negativo: un manifiesto con una clave repetida | Nivel 0 |
| NFR10.14 | nuevo | Dependencias fijadas y auditadas. | `uv.lock` por paquete con *hashes*; `pip-audit` sin hallazgos `HIGH` o `CRITICAL` con corrección. La wheelhouse de ZINE se arma desde ese lockfile | CI |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | nuevo | Cada resultado es reproducible y auditable sin texto (BR2.10, BR8.3, BR8.7). | `config_sha256` y `profile_sha256` con la función JCS de U1, sin una segunda implementación, y la huella del *fixture* de C18 coincide. Cada llamada, también las fallidas con registro, queda en `registro.llamadas` en orden y con todos los campos de C13. La misma entrada, la misma configuración y el mismo *fake* dan la misma salida salvo las fechas. El cambio de perfiles, *prompt*, precios o umbrales es un PR (AUTONOMIA-01) | Nivel 0 (con Hypothesis en las huellas) |
| NFR11.2 | nuevo | Ninguna etiqueta de veracidad sale del analizador (AUTONOMIA-03; BR9.1–BR9.5, BR8.6). | (a) 100 % de los casos de vocabulario de `contracts/integrity/scan-cases.v1.yaml` dan lo esperado, y un caso invertido hace fallar la suite; (b) en nivel 2, **0 coincidencias** de C8 en `hecho` y `observaciones` emitidos; (c) los esquemas del juez y del verificador no tienen campos de veracidad; (d) el aviso de VE-01, con su versión, sale en stderr y en cada `AVISO.txt` | Nivel 0 y nivel 2 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | nuevo | Los *fixtures* y el conjunto son sintéticos. | La comprobación de U1 (`synthetic: true` y `mentions`) corre sobre `libs/*/tests/` de U11 y sobre `evaluation/` con 0 hallazgos. Cada muestra del conjunto tiene `origen: sintetico` (BR13.1). El conjunto lo genera Google y lo revisa a mano el autor, que deja quién y cuándo en el manifiesto (BR13.5) | Nivel 0 y revisión del PR |
| NFR12.2 | nuevo | Nada del corpus ni del paquete de ZINE llega a Git, y nada del repositorio lanza trabajos (BR11.5, BR11.6, BR14.1–BR14.4). | `git ls-files` no devuelve nada bajo `resultados-locales/` ni `evaluation/zine/paquete/`; una salida de corpus hacia un directorio rastreado da código 2 sin escribir; en `evaluation/zine/` solo hay `.sbatch`, `empaquetar.py` y un manifiesto con nombre, SHA-256 y fuente; `gitleaks` sobre el paquete termina con 0 o lo borra; ningún archivo invoca `sbatch`, `ssh`, `scp` ni `rsync` salvo como texto para el humano | Nivel 0 |

## 4. Correspondencia con AUTONOMIA

| Regla | Requisitos de U11 |
|---|---|
| AUTONOMIA-01 | NFR11.1 (cambios por PR), NFR12.2 (ningún script lanza trabajos en ZINE) |
| AUTONOMIA-02 | Cada requisito nombra su umbral; los comandos están en `tech-stack-decisions.md` §6 |
| AUTONOMIA-03 | NFR11.2; NFR10.6 (esquemas sin campos de veracidad) |
| AUTONOMIA-04 | §1; NFR1.1–NFR1.8; NFR10.2, NFR10.3, NFR10.5, NFR10.8 |
| AUTONOMIA-05 | NFR10.6; NFR10.10 (fallo cerrado, en `reliability-requirements.md`); NFR4.1 (citas verificadas en nivel 2) |

## 5. Riesgos aceptados o transferidos

| Riesgo | Tratamiento |
|---|---|
| **Reidentificación por el relato.** Aun seudonimizado, Anthropic ve el relato y las relaciones entre marcas (DT18) | Aceptado con el ADR del proveedor y el consentimiento que autoriza la transferencia (NFR1.8). Con P1 = A, solo un proveedor lo ve |
| **Detección incompleta del anonimizador** en la corrida del piloto, que es real | Transferido a U10 (prueba de 0 fugas y tasas por detector). U11 aborta ante `anonymized: false` (NFR1.5) |
| **Una sola palabra citada** queda fuera del escaneo | Depende de FD-U1-14, aún pendiente en U1. Se aplica sin otra regla (BR9.2) |
| **Flexiones fuera de la lista 1.0.0** («mienten») | Limitación declarada (E17); cada término nuevo entra por PR de U1 con su control negativo |
| **gpt-oss como «openai»** | Si el TG decide que gpt-oss es una familia aparte, se cambia la declaración del perfil por PR; nunca se relaja la regla de familias (NFR5.2) |

## 6. Precisiones a artefactos ya aprobados (NFR-U11-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Todas salen de las fuentes o de la sección 2 de
`nfr-requirements-questions.md`, salvo NFR-U11-01 a NFR-U11-03, que son las respuestas P1–P3.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U11-01 | `contract-summary.md` (C18, pregunta abierta de modelos), NFR-U10-07 y `bolt-plan.md` (B11) | **P1 = A.** `comercial-piloto` y `evaluacion-comercial`: juez de Anthropic (externo), verificador local gpt-oss-20b Q8_0 (`family: openai`), sin alterno. Generador del conjunto: Google. B10 sigue necesitando solo el adaptador y el ADR de Anthropic para la primera rebanada. Los identificadores exactos de los modelos de Anthropic y de Google entran con el PR de `config/profiles.yaml` (o del manifiesto del conjunto) y el ADR de su proveedor; C18 decía que los fijaba esta etapa | P1 = A |
| NFR-U11-02 | `requirements.md` (NFR4) | **P2 = A.** Precisión ≥ 0,70, sensibilidad ≥ 0,60 y acuerdo entre 3 corridas ≥ 0,60, por su media. Bloquean solo con `evaluacion-comercial`, en los PR de IA y en las entregas etiquetadas; con los demás perfiles el reporte dice `passes` sin bloquear | P2 = A |
| NFR-U11-03 | `requirements.md` (NFR4) y rules (BR13.2) | **P3 = A.** Composición mínima del conjunto 1.0.0: 40 muestras (21 con contradicción, 3 por tipo; 11 coherentes; 8 trampa, 2 por caso), al menos 6 largas (más de 120 turnos), al menos 3 contradicciones esperadas por tramo de distancia y cada etiqueta de sesgo en al menos 2 muestras | P3 = A |
| NFR-U11-04 | rules (BR2.7) y `stories.md` (AC13.2.2) | El modo fragmentado es obligatorio solo cuando el **juez** es local. Con P1 = A el verificador local solo lee las dos citas, y `comercial-piloto` no debe partir en ventanas al juez comercial | P1 = A; sección 2 |
| NFR-U11-05 | `contract-summary.md` (C25) y U1 (catálogo de límites) | Cifras de U11, como máximos del catálogo: `model_call_timeout_s = 3600`, `run_deadline_final_s = 43200`, `run_deadline_incremental_s = 1200`, `fragment_window_turns = 60`, `fragment_overlap_turns = 20`. Cada despliegue las baja por entorno, con los mínimos de `tech-stack-decisions.md` §3. `run_deadline_incremental_s` pasa de los 900 de la sección 2 a 1200 porque la permutación se queda activa en todos los perfiles (NFR-U11-08). Entran por PR de U1 antes del código de B11 | Sección 2, punto 1; NFR-U10-04 |
| NFR-U11-06 | `contract-summary.md` (C25) y U1 | Cifra nueva `model_response_max_bytes = 2 097 152` (`bytes`): tope de lectura de la respuesta del servidor local y del cliente de C21. Toda cifra de límite vive en C25 (`project.md`) | Esta etapa (NFR10.8) |
| NFR-U11-07 | `contract-summary.md` (C18, `config/profiles.yaml`) | Perfiles iniciales: `comercial-piloto` (producción), `todo-local` (producción en el clúster, ventana 40 y solapamiento 10), `evaluacion-comercial` (espejo de `comercial-piloto`) y `evaluacion-local-zine` (juez Qwen3.6-35B-A3B Q8_0 y verificador gpt-oss-20b Q8_0, con su SHA-256 del reporte de ZINE, `batch_only: true`, ventana 60 y solapamiento 20). El juez local de `todo-local` es un Qwen cuantizado que quepa en el clúster, válido solo para demostración; su archivo y su SHA-256 los fija Infrastructure Design de U2 | Sección 2, puntos 4 y 6; BR12.1 |
| NFR-U11-08 | Sección 2, punto 3, de `nfr-requirements-questions.md` | Se sustituye «`permutation: false` en los perfiles de producto» por lo que ya aprobó U8 (FD-U8-08, P5 = A): `permutation: true` en todos los perfiles, también en `todo-local`. El costo cabe en los plazos (`performance-requirements.md`, NFR3.6 y NFR8.3). La permutación solo se apaga en `todo-local` si la prueba de NFR8 con permutación no alcanza el 98 %, por PR que cambie el perfil y la prueba de U8 | FD-U8-08; pregunta abierta de U8 para NFR |
| NFR-U11-09 | rules (BR12.5) | Se confirman los tramos de distancia: hasta *O*, de *O*+1 a *W* y más de *W*, con *W* y *O* del perfil o los topes de C25 si el perfil no fragmenta | Sección 2, punto 5 |
| NFR-U11-10 | `team.md` (Testing Posture, prueba de humo) y NFR de U2 (*N*) | *N* = **300 s** para `frontend/e2e/smoke.spec.ts` con `comercial-piloto` sobre una transcripción sintética de ≤ 60 turnos. La sección 2 proponía 240 s; con el verificador local de P1 = A y la permutación no alcanza. U4 suma su parte de cola y consola sin pasar de *N* | Sección 2, punto 2; P1 = A |
| NFR-U11-11 | Functional Design de U9 (§9, fila de U11) | U9 da por hecho que el `ModelGateway` de U11 aporta `transcribe` y `synthesize`. C13 y el Functional Design de U11 solo declaran `generate`. U11 no añade esos métodos: la transcripción y la síntesis son de U9 contra sus servidores locales (C14). Si U9 los necesita en el puerto, entran por PR de U1 sobre C13 | Lectura de las tablas FD de otras unidades |
| NFR-U11-12 | Functional Design de U8 (FD-U8-01) y rules (BR8.6) | La prueba «ninguna salida trae `observaciones_conductor`» de U11 pasa a «ninguna salida final ni en error lo trae» cuando entre U8. Hasta entonces la de U11 sigue igual | FD-U8-01 |
| NFR-U11-13 | Functional Design de U4 (E42) | El ejemplo de U4 usa ventana 40 y solapamiento 8. El perfil `todo-local` usa ventana 40 y solapamiento 10 (E23 de U11); la franja de U4 muestra lo que diga `registro.fragmentado` | Sección 2, punto 1 |
| NFR-U11-14 | `contract-summary.md` (C19 v2, FD-U11-09) | Además de los umbrales y `passes` que ya trae C19 v2, entran `blocking` (verdadero solo con `evaluacion-comercial`), `origin` (P3 = A de U12) y la latencia p50 y p95 por papel (NFR15.1). Van en el mismo PR de U1 que ya lleva C19 v2 | NFR-U11-02; P3 = A de U12 |
| NFR-U11-15 | Functional Design de U11 (F de `evaluate`) y rules (BR12) | Opción nueva `--export-likert <dir>` de `veridicus evaluate`: escribe por muestra el `hecho`, las dos citas y las `observaciones`, sin perfil ni modelo, para la calificación Likert a ciegas de NFR6. Solo sobre el conjunto sintético; con una entrada de corpus termina con 2 | Esta etapa (NFR6.1) |
