# Diseño de fiabilidad y calidad de la IA — U11 incoherence-analyzer

**Revisión 1 (2026-11-22): primera pasada.**
- **Por qué existe.** U11 es `library` y el archivo de etapa no pide este documento para ese tipo. Se añade
  porque `reliability-requirements.md` existe: el fallo cerrado de AUTONOMIA-05, los plazos y reintentos,
  la CLI sin archivos a medias, los umbrales de NFR4 y la cobertura son de U11.
- **Sin disyuntor ni mamparo.** La biblioteca hace una llamada a la vez, sin estado entre corridas, y cada
  error termina la corrida. Un disyuntor solo añadiría estado compartido (mismo criterio que U10).

**Insumos.** `nfr-requirements/reliability-requirements.md` (reliability-requirements: NFR4, NFR6,
NFR10.4, NFR10.10–NFR10.13, NFR10.15 y NFR13), `security-requirements.md` y `tech-stack-decisions.md` de esta
unidad; BR5–BR8, BR10–BR13, F7, F8, F10 y §3 de `functional-design/functional-spec.md` (functional-spec) y
`functional-design/rules.md`; C6, C13 (tabla de reintentos), C17, C19 v2 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); NFRD-U10-10 y NFRD-U10-17 de U10;
mediciones M4 y M5 del reporte de ZINE.

## 1. Fallo cerrado de la corrida (NFR10.10; AUTONOMIA-05)

`domain/run_state.py` es una máquina de estados pura (la de functional-spec §3.1) que recibe eventos y
devuelve el siguiente estado; `application/analyze.py` solo la conduce. Todo error de `model_calls` pasa por
una sola función:

| Evento | Estado | `error.codigo` |
|---|---|---|
| `InvalidOutput`, candidato mal formado, salida que no valida contra C6, *prompt* con otra huella | `failed` | `salida_invalida` |
| `ContentBlocked` sin alterno o en la ranura `fallback` | `failed` | `bloqueo_contenido` |
| `Timeout` o plazo agotado | `failed` | `tiempo_agotado` |
| `ProviderError` | `failed` | `proveedor` |
| `AnonymizerUnavailable` | `failed` | `anonimizador_no_disponible` |
| Llamada externa con `anonymized: false` (precede a cualquier otro) | `aborted_incident` | `incidente_anonimizacion` |
| `cancelled()` verdadero | `cancelled` | — (lanza `Cancelled`, sin `Salida`) |
| Excepción que no es de `model_calls` | — | — (se propaga; CLI 5) |

```python
def fail(run: RunState, code: ErrorCode) -> Salida:
    out = base_output(run, estado="error", codigo=code)     # hallazgos y descartes vacíos
    out.registro.llamadas = list(run.calls)                  # lo que alcanzó a llamar
    out.registro.fragmentado = run.chunking                  # también en error (BR8.5)
    return validate_or_raise(out)                            # contra C6; si no, error del código
```

**Pruebas.** Una por código con cada salida validada contra C6, `hallazgos == []`, `descartes == []` y sin
`observaciones_conductor` (NFR-U11-12 la amplía cuando entre U8). 100 % de ramas en `run_state.py` y en
`output.py`.

## 2. Verificación de citas y filtro (NFR4.1, NFR4.12; AUTONOMIA-05)

- **Orden fijo del filtro** (BR5.2): marca alterada, campo solo con espacios, verificación de las dos citas
  contra su turno, tramo incremental y vocabulario prohibido. El primer fallo descarta con su motivo, sin
  texto.
- **Regla del piloto** (`project.md`; BR5.5–BR5.7): solo se normalizan espacios; « […] » une fragmentos del
  mismo turno en orden; ENT y plegados se aceptan con aviso. La función `verify_quote(turn_text, quote) ->
  QuoteCheck` es pura y vive en `domain/quotes.py`.
- **Restauración antes de verificar.** Con un destino externo, el módulo de U10 (o el proxy) devuelve el
  contenido ya restaurado y las rutas de `altered_markers`; el filtro descarta con `marca_alterada` antes de
  verificar (BR5.3), y un puntero que no cae en ningún candidato da `salida_invalida`.
- **Doble comprobación en nivel 2.** `evaluate` vuelve a verificar con la misma función cada cita emitida;
  una sola que no verifica en cualquiera de las 3 corridas hace fallar `verified_quotes` (E54).
- **Pruebas.** Hypothesis genera turnos y citas con espacios dobles, saltos de línea, tildes compuestas y
  descompuestas y « […] » en orden e invertido; propiedades: una cita tomada del turno con espacios cambiados
  verifica, una con un carácter cambiado no, y una cita de otro turno da `cita_en_otro_turno`.

## 3. Plazos, cancelación y reintentos (NFR10.4, NFR10.11)

**Plazo de cada llamada.** Antes de cada `generate`, `application/deadline.py` calcula con el reloj inyectado:

| Destino | `timeout_s` | Si el restante no alcanza |
|---|---|---|
| Local, o externo por el módulo en proceso (CLI) | `min(model_call_timeout_s, deadline − ahora)` | `tiempo_agotado` sin llamar |
| Externo por el cliente de C21 (`semantic-agent`) | `min(model_call_timeout_s, deadline − ahora − 10 s)`; el cliente espera `timeout_s` + 10 s | Restante ≤ 10 s: `tiempo_agotado` sin llamar (NFRD-U11-04) |

**Reintentos** (BR10.3, tabla de C13; una prueba por fila con reloj simulado):

| Adaptador | Respuesta | Qué hace |
|---|---|---|
| Local | Conexión rechazada, `502`, `503`, `504` | Hasta 2 reintentos, a los 2 s y 6 s, solo si `deadline − ahora` alcanza para la espera más un intento; si no, `ProviderError` |
| Local | *Timeout* o salida inválida | Sin reintento: `Timeout` o `InvalidOutput` |
| Local | `3xx` o respuesta sobre el tope | Sin reintento: `ProviderError` con su `ModelCall` |
| `anonymizer` (módulo o C21) | Cualquier error | Sin reintento; el alterno solo ante `ContentBlocked` en `primary` (BR7.3) |
| Cliente de C21 | `409`, `413`, `422`, `503`, `3xx`, sin conexión | `AnonymizerUnavailable` (NFRD-U11-05) |

**Cancelación.** `cancelled()` se consulta antes de cada llamada y entre ventanas (BR7.2). En la CLI la
alimenta el manejador de señales (§4); en `semantic-agent`, U4 (clave de Redis, CD-06).

## 4. CLI sin archivos a medias, señales y códigos (NFR10.12, NFR10.13)

- **Validación previa completa** antes de la primera llamada (BR11.2): argumentos, cada archivo, nombres de
  salida repetidos, perfil, aviso, gateway, directorio y regla del corpus. Si falla, 2 o 3 y **0 archivos**,
  ni siquiera `AVISO.txt`; el directorio de salida se crea solo después.
- **Escritura atómica** (`cli/io_atomic.py`): `tempfile.NamedTemporaryFile(dir=destino, delete=False)`,
  `write`, `flush`, `os.fsync`, `os.replace` y `fsync` del directorio. Si algo falla, se borra el temporal en
  `finally` y la CLI termina con 5. Prueba con un sistema de archivos *fake* que falla en `write`, en `fsync` y
  en `replace`: no queda archivo final ni temporal.
- **Señales** (NFRD-U11-10): SIGINT y SIGTERM marcan la cancelación y lanzan `CliInterrupted` en el hilo
  principal; la corrida en curso queda sin salida, el reporte se escribe con las hechas y el código es 5. Una
  segunda señal durante el cierre termina con 5 sin reporte.
- **Códigos.** 0, 2, 3, 4, 5 y 6 con una prueba cada uno (BR11.3). Con 4, el lote se detiene, se escriben la
  salida de esa corrida y el reporte de lo hecho.
- **Reporte.** `reporte.json` se valida contra C19 v2 antes de escribirse; si no valida, código 5 y no se
  escribe (NFR4.13).

## 5. Arranque con configuración incompleta (NFR10.15)

`cli/composition.py` (y la raíz de U4 en `semantic-agent`) construye en este orden y se detiene en el primer
fallo, con un mensaje que nombra el ajuste o el archivo, nunca un valor:

1. `limits.load(os.environ)` de U1 sobre el catálogo empaquetado; una `VERIDICUS_LIMIT_<NOMBRE>` que sube un
   techo, que no existe o que rompe una relación de C25 es error (NFRD-U11-02).
2. `config/profiles.yaml` y `config/prices.yaml` (o las rutas de `VERIDICUS_PROFILES_PATH` y
   `VERIDICUS_PRICES_PATH`) con el cargador seguro y `profiles.validate(..., key_prefix="VERIDICUS_")`.
3. El perfil pedido existe y está aprobado.
4. SHA-256 del *prompt* igual al de la configuración.
5. Aviso de VE-01 legible con versión.
6. Gateway (`security-design.md` §2), con el piso de 270 s si hay un papel externo.

Cada paso con su prueba: CLI 3 y 0 llamadas; en `semantic-agent`, U4 no construye el gateway.

## 6. Cobertura y módulos guardia (NFR13.1, NFR13.2, NFR13.3)

| Módulo | Reglas | Ramas |
|---|---|---|
| `libs/incoherence_analyzer/domain/quotes.py` | BR5.5–BR5.7 | 100 % |
| `libs/incoherence_analyzer/domain/filter.py` | BR5.1–BR5.4, BR5.8, BR6.1–BR6.4 | 100 % |
| `libs/incoherence_analyzer/domain/run_state.py` | BR7.1–BR7.3, BR7.6 | 100 % |
| `libs/incoherence_analyzer/domain/output.py` | BR8.1 | 100 % |
| `libs/model_gateway/adapters/anonymizing.py` | BR7.4–BR7.6 | 100 % |
| `libs/integrity_policy/scan.py` | BR9.1–BR9.3 | 100 % |
| `libs/execution_profiles/validate.py` | BR2 | 100 % |

- **Cómo se exige.** `pytest --cov --cov-branch --cov-fail-under=80` por paquete y, además,
  `scripts/check-guard-coverage.py` lee `coverage.json` y falla si alguno de esos archivos tiene una rama sin
  cubrir. La lista de archivos guardia vive en ese script y cambia por PR.
- **Primero en rojo** (`team.md`, Ordering): las pruebas de estos módulos y de los contratos (C6, C13, C18,
  C19, C21) se escriben antes y se ejecutan en rojo; el plan de tareas de B11 lo cita.
- **Exclusiones.** Solo el arnés de `evaluation/` y el código generado, en `[tool.coverage.run] omit` de cada
  `pyproject.toml`; cada exclusión nueva se justifica en su PR.

## 7. Calidad de la IA en nivel 2 (NFR4.1–NFR4.10)

- **Umbrales.** `evaluation/thresholds.v1.yaml`, cargado con el cargador seguro; su SHA-256 va al reporte. Cada
  métrica declara `threshold`, `comparison` (`eq`, `ge`, `gt`) y `blocking_profiles` (`all` o una lista).
  Una prueba de nivel 0 compara el archivo con la tabla de NFR4: un umbral más bajo hace fallar la suite.

```yaml
schema_version: 1.0.0
metrics:
  verified_quotes:            { threshold: 1,    comparison: eq, blocking_profiles: all }
  precision:                  { threshold: 0.70, comparison: ge, blocking_profiles: [evaluacion-comercial] }
  reversed_order_consistency: { threshold: 0.65, comparison: gt, blocking_profiles: all }
```

- **Cálculo.** Precisión, sensibilidad y acuerdo entre 3 corridas por su media (P2 = A); acierto por par no
  ordenado (BR12.2); consistencia al invertir el orden con los booleanos del envoltorio del gateway (BR12.4);
  cobertura de la permutación; fugas del anonimizador desde el gancho de U10; acuerdo de tipo y sensibilidad
  por tramo de distancia (NFR-U11-09) sin umbral.
- **Bloqueo.** `blocking` es verdadero solo con `evaluacion-comercial` (NFR-U11-14). `evaluate` termina con
  6 si una métrica que bloquea con el perfil usado no alcanza; con los demás perfiles, `passes` por métrica y
  código 0 si pasan las absolutas.
- **Reproducibilidad del reporte.** `dataset_version`, `dataset_sha256`, `prompt_sha256`, `profile_sha256`,
  `config_sha256`, modelo por llamada, `origin` y SHA-256 de los umbrales.

## 8. Conjunto sintético y repetibilidad (NFR4.11–NFR4.14)

- **`scripts/check-dataset.py`** comprueba la composición de NFR4.11 sobre
  `evaluation/synthetic/manifest.v1.yaml` y que cada muestra valida contra C6 y cada contradicción esperada
  trae dos citas que verifican con `verify_quote` (NFR4.12). Control negativo: un manifiesto con 2 muestras de
  un tipo.
- **Repetibilidad local (NFR4.14).** `evaluacion-local-zine` fija `seed` y `temperature: 0`; el adaptador local
  manda `seed` solo si el servidor la admite (BR8.3). La prueba de nivel 2 en ZINE compara dos corridas de la
  misma muestra: mismo conjunto de pares (M5 lo midió en 4/4). Con modelos comerciales lo mide NFR4.8.

## 9. Calificación a ciegas (NFR6.1)

`evaluate --export-likert <dir>` (NFRD-U11-09):
1. Solo con `--conjunto` igual al conjunto sintético del manifiesto; otra entrada da 2 sin escribir.
2. Toma los hallazgos emitidos de la primera corrida, les asigna identificadores opacos y los baraja con una
   semilla que imprime en stderr.
3. Escribe `<dir>/muestras/<id>.json` con `hecho`, las dos citas y `observaciones`, sin perfil, modelo,
   proveedor, muestra ni corrida, y `<dir>/clave.json` con la correspondencia.
4. Prueba de nivel 0: ningún archivo de `muestras/` contiene el nombre del perfil, del modelo ni de la muestra.
   La calificación ≥ 4,5/5 de dos evaluadores es manual, antes de la sustentación.

## 10. Quién recupera qué

| Falla | Alcance | Recuperación |
|---|---|---|
| Error de modelo o del anonimizador | Esa corrida (`estado: error`) | El humano relanza; en el producto, `/runs/{id}/retry` de U4 |
| Incidente de anonimización | El lote de la CLI se detiene; la sesión del producto se bloquea (U4) | Revisión humana; nunca automática |
| Plazo agotado | Esa corrida | Cambiar plazo o perfil por PR |
| Escritura que falla | El archivo en curso; CLI 5 | Relanzar; ningún archivo a medias que limpiar |
| Señal | La corrida en curso | Relanzar; las hechas ya están escritas |
| Evaluación interrumpida | Las muestras pendientes | Reanudar con el mismo `--salida` (`performance-design.md` §6) |

## 11. Decisiones

| # | Decisión | Alternativas descartadas | Consecuencias |
|---|---|---|---|
| DR1 | Máquina de estados pura con una sola función de fallo | Manejo de errores repartido | 100 % de ramas medible y una salida en error idéntica para cada código |
| DR2 | Sin disyuntor ni reintento de corridas | Disyuntor por proveedor | Sin estado entre corridas; a cambio, un proveedor caído hace fallar cada corrida hasta que el humano actúe |
| DR3 | Reintentos solo locales, con el plazo como techo | Reintentar también hacia el anonimizador | Nada sale dos veces del clúster por un reintento (C13) |
| DR4 | Escritura con `fsync` y `os.replace` | Escribir directo | Nunca un archivo a medias; a cambio, un `fsync` por archivo |
| DR5 | Umbrales en archivo con prueba que impide bajarlos | Umbrales en código | Cambian solo por PR y se citan en el reporte |
| DR6 | Lista de módulos guardia en un script que lee `coverage.json` | Un solo `--cov-fail-under` global | El 100 % de ramas se exige donde importa sin subir el 80 % del resto |
