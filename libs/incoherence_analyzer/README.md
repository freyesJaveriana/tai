# veridicus-incoherence-analyzer

Biblioteca y línea de comandos `veridicus` del analizador de incoherencias (U11, Bolt B11a, versión
`0.1.0`). Lee una transcripción **sintética** (el objeto `transcripcion` del contrato común C6), busca
contradicciones internas del relato sobre hechos centrales y escribe una salida C6 con **sugerencias de
revisión**: cada hallazgo lleva sus dos citas literales, verificadas en su turno. Nunca emite un veredicto
de veracidad (AUTONOMIA-03) ni un hallazgo con una cita alterada (AUTONOMIA-05). La etiqueta
`analyzer-v0.1.0` la pone el humano; la CI solo la comprueba.

## Demostración sin red

Corre la CLI con el `FakeTransport` de B10a sobre una entrevista inventada, desde la raíz del repositorio:

```bash
uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli python examples/demo_fake.py
```

Imprime el nombre del archivo `.salida.json`, el estado y el número de hallazgos (1). El directorio de
trabajo es temporal y se borra al terminar.

## Uso

```bash
veridicus analyze <archivo.json | directorio> --perfil demo-anthropic [--salida <directorio>]
```

Por cada entrada escribe `<nombre>.salida.json`, y en el directorio de salida un `AVISO.txt` con los
avisos (propósito limitado, VE-01, y `same_family`). No escribe `reporte.json` en B11a.

Códigos de salida: `0` todas las corridas terminaron (aunque alguna tenga `estado: error`); `2`
argumento, archivo, consentimiento, límite o directorio; `3` perfil, anonimizador, clave,
transferencia o aviso; `4` incidente de anonimización; `5` error inesperado, escritura fallida o
interrupción. Sin `--salida`, la salida va a `resultados-locales/<fecha>-analyze`, que Git ignora. Una
transcripción de origen `corpus` solo se analiza si Git no puede rastrear el directorio de salida.

Si una señal (`SIGINT` o `SIGTERM`) llega a mitad de una corrida, esa corrida queda sin salida y el código
es `5`; las salidas ya escritas se conservan, y ninguna llamada nueva sale.

## Variables de entorno

| Variable | Qué hace |
|---|---|
| `VERIDICUS_ANTHROPIC_API_KEY` | La clave del proveedor. La crea el humano; nunca se versiona. Sin ella, el código es `3` y no sale ninguna llamada |
| `VERIDICUS_LIMIT_<NOMBRE>` | Baja un límite del catálogo `contracts/limits.v1.yaml`; nunca lo sube |
| `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S` | Plazo de cada llamada al modelo. El perfil comercial exige al menos 270 s; la demostración y la prueba manual usan `300` |

## El perfil único y su aviso de una sola familia

B11a trae un solo perfil, `demo-anthropic`: el juez y el verificador son Anthropic (`claude-sonnet-5-5`),
con `purpose: demonstration` y `same_family_declared: true`. Todo destino externo pasa por el `Anonymizer`
de B10a: si no está o falla, el código es `3` o `4` y no sale ninguna llamada (AUTONOMIA-04). Como juez y
verificador son de la misma familia, la CLI imprime el aviso `same_family` en stderr y lo escribe en
`AVISO.txt`. **Nunca es un perfil de evaluación**: no sirve para medir.

## Prueba manual con el proveedor real

La lanza el humano, **desde la raíz del repositorio** (las rutas `--directory` son relativas a ella),
con una entrevista **sintética** y su clave en `VERIDICUS_ANTHROPIC_API_KEY`. No corre en la suite por
defecto; sale por la red y por eso lleva `--force-enable-socket`.

Comando del plan (R-04), literal:

```bash
timeout 900 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/manual -m manual --no-cov --force-enable-socket -q
```

Variante recomendada, con `--extra cli` y un plazo mayor:

```bash
timeout 7200 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/manual -m manual --no-cov --force-enable-socket -q
```

- `--extra cli` instala el anonimizador, sin el cual un destino externo no arranca (código 3). Con un
  entorno que ya lo tiene instalado da lo mismo.
- El peor caso es **por comando**, no por entrevista, y pasa de 900 s. Una entrevista hace 1 + 2N llamadas
  (el juez y, por cada uno de los N candidatos que sobreviven al filtro, el verificador y el verificador
  permutado), con hasta 300 s por llamada. El comando corre dos entrevistas: 2 × (1 + 2N) llamadas. Con
  N = 5 son 22 llamadas, unos 6600 s. `timeout 7200` es una cota práctica, **no un máximo garantizado**:
  N no tiene tope en esta prueba. Con un plazo menor el humano podría ver un corte sin que el proveedor
  haya fallado.
- La prueba falla si la corrida termina en `estado: error` (por ejemplo, una clave inválida) o sin
  ninguna llamada, y si la entrevista con la contradicción sembrada no produce ningún hallazgo.

El resultado queda en `libs/incoherence_analyzer/resultados-locales/manual-real-provider/` y no se
versiona.

## Límites declarados

- **Plazo de 2× (PD-10).** El *timeout* de `httpx` de B10a es por operación, así que una llamada puede
  pasarse del plazo restante. `application/deadline.py` comprueba el plazo antes y después de cada llamada
  y da `tiempo_agotado` si se pasó, pero el exceso posible de una llamada no se corta a la mitad.
- **Una sola familia de modelos.** Juez y verificador de la misma familia pueden compartir sesgos; por eso
  el perfil es de demostración y lleva el aviso (BR2.5).
- **Solo el modo final, un solo destino.** Sin modo incremental, sin modo fragmentado ni alterno, y sin
  adaptadores local, OpenAI o Google.
- **Sin garantía de recuperación total.** El analizador propone sugerencias de revisión; un humano decide.

## Diferido a B11b

El modo fragmentado y el alterno, el modo incremental (BR1.5, BR5.8), `reporte.json` con costo y métricas
(C19, `kind: run`), el perfil `comercial-piloto` con verificador local, el nivel 2 de evaluación con su
*workflow* `analyzer-level2-gate.yml`, y las reglas BR11.8 y BR12 a BR14. Los casos `rule: clarification`
de `scan-cases.v1.yaml` pasan a U8.

## CI

`.github/workflows/analyzer-level0.yml` corre un *job* por paquete (`incoherence_analyzer`,
`model_gateway`, `execution_profiles` e `integrity_policy`) y, al final, la compuerta de cobertura:
`python -m veridicus_incoherence_analyzer.testing.coverage_gate` con los cuatro `coverage.json` (100 % de
ramas en los 9 módulos guardia y 80 % de líneas por paquete).
