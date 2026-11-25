# veridicus-anonymizer

Anonimizador de Veridicus (C20, unidad U10, versión 0.1.0). Es un módulo de Python que se usa dentro del
mismo proceso: recibe una petición para un proveedor externo, **seudonimiza** el texto, llama al
proveedor **una sola vez**, **restaura** la respuesta y devuelve el resultado, o **falla cerrado** sin
haber enviado nada (AUTONOMIA-04). Todo lo que sale del clúster pasa por él.

Esta es la entrega mínima B10a. Lo que todavía no hace está en [Qué no hace todavía](#qué-no-hace-todavía).

## Qué hace

1. **Comprueba el destino** antes de tocar el texto: el destino debe ser externo, el proveedor debe tener
   adaptador, el dominio debe estar en la lista permitida y usar el puerto 443, el modelo debe estar en
   la tabla de capacidades y la variable de la clave debe existir. Si algo falla, lanza
   `AnonymizerUnavailable`, sin ninguna petición y sin `ModelCall`.
2. **Seudonimiza** cada texto del mensaje con reglas (`google-re2`), las cadenas con forma de marca y una
   red de seguridad que también marca toda palabra con mayúscula inicial que abre oración, no está
   clasificada y no está en la lista de palabras permitidas. Las marcas son consistentes dentro de la
   llamada (`[ENTIDAD_1]`, `[LUGAR_1]`, `[IDENTIFICADOR_1]`).
3. **Llama una vez** al adaptador nativo del proveedor, con `httpx` directo, sin reintentos y sin seguir
   redirecciones. Solo Anthropic tiene adaptador en B10a.
4. **Restaura** las marcas de la respuesta antes de devolverla y vacía la tabla de correspondencia en
   todos los finales. Las marcas que el proveedor alteró se informan en `altered_markers`.
5. **Registra** solo identificadores y cifras; nunca texto, claves ni dominios en los mensajes de error.

La garantía de «fuga cero» no la da la demostración sino las pruebas de las guardias
(`tests/guards/test_autonomia_04_payload.py`, `test_autonomia_04_fail_closed.py` y
`test_autonomia_04_no_leak.py`).

## Cómo lo construye la CLI de B11a

La CLI no construye el módulo a mano: llama `build_anonymizer(env, transport=None)` con su entorno.

```python
from veridicus_anonymizer import build_anonymizer

anonymizer = build_anonymizer(env)  # env: Mapping[str, str], por ejemplo os.environ
result = anonymizer.generate(request)  # request: veridicus_contracts.model_calls.GenerateRequest
```

- La firma no tiene ningún parámetro para saltarse la seudonimización, ni para cambiar los catálogos ni el
  reloj (PD-7).
- Sin `transport`, usa el transporte de producción: TLS 1.2 o superior con verificación de certificado y de
  nombre, `retries=0`, `follow_redirects=False` y sin leer el entorno del proceso (`trust_env=False`).
  Con un `FakeTransport` (`veridicus_anonymizer.testing.fake_transport`) corre sin red.
- Lanza `ConfigInvalidProfileError` si una lista o la tabla de capacidades no es válida, y
  `ConfigInvalidLimitError` si una cifra de límite lo es (ambas de `veridicus_errors`), antes de cualquier
  llamada.
- La clave se comprueba en `generate`, contra `request.destination.api_key_ref`; su ausencia es
  `AnonymizerUnavailable`.

## Variables de entorno

Solo nombres `VERIDICUS_*`. Los valores los crea el humano en un `Secret` o en un `.env` no versionado.

| Variable | Qué es |
|---|---|
| `VERIDICUS_ANTHROPIC_API_KEY` | La clave del adaptador de Anthropic. El nombre lo fija `api_key_ref` del destino del perfil; el módulo solo lee esa variable del entorno recibido y nunca la guarda ni la registra. |
| `VERIDICUS_LIMIT_<NOMBRE>` | Baja una cifra del catálogo `contracts/limits.v1.yaml`; nunca la sube. Las que usa el módulo son `anonymizer_response_max_bytes`, `anonymizer_masking_budget_ratio` y `model_call_timeout_s`. |

## Plazos y registros

- El plazo de `httpx` es **por operación** (conexión, escritura, lectura), no total: el tiempo de una
  llamada puede acercarse a **dos veces** `timeout_s` de la petición (F-06). El tope de `model_call_timeout_s`
  se aplica a cada operación.
- `build_client` ya no cambia el nivel de los *loggers* `httpx` y `httpcore` (F-10). Su línea informativa
  lleva solo método, URL constante y estado, nunca la clave ni texto, pero quien use la biblioteca puede
  silenciarla si quiere:

```python
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
```

## Qué no hace todavía

Queda diferido a **B10b (DP-03)**; ninguna de estas piezas está en esta versión:

- el **NER**: la detección usa solo reglas, formas de marca y la red de seguridad ampliada (PD-2);
- el **proxy** del anonimizador y su despliegue en el clúster;
- los adaptadores de **OpenAI y Google**: sus dominios están en la lista, pero un destino `openai` o
  `google` falla cerrado con `AnonymizerUnavailable` hasta B10b;
- el Corefile de CoreDNS y la comprobación de la `NetworkPolicy` en el clúster (verificación manual).

## Límite declarado (PD-2)

Sin NER, **un apodo escrito todo en minúscula no lo detecta ninguna regla** y saldría tal cual. Una prueba
documenta el límite y no lo cuenta como fuga del conjunto sembrado. La red de seguridad enmascara de más a
propósito (falla del lado seguro): una palabra con mayúscula inicial que abre oración y no está en la lista
de palabras permitidas sale como `[ENTIDAD_n]`, aunque sea común. La lista de palabras permitidas se amplía
por PR y **nunca** contiene un nombre de pila.

## Demostración

```bash
uv run --frozen --offline --directory libs/anonymizer python examples/demo_fake.py
```

Corre con el `FakeTransport` y una transcripción sintética. Imprime el cuerpo que saldría (solo marcas), la
respuesta restaurada y, con un destino `openai`, la línea `AnonymizerUnavailable` con `peticiones=0`. Es
evidencia, no garantía.

## Verificación

Desde la raíz del repositorio:

```bash
timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest --cov=veridicus_anonymizer --cov-branch --cov-report=json --cov-fail-under=80
timeout 60 uv run --frozen --offline --directory libs/anonymizer python -m veridicus_anonymizer.testing.coverage_gate coverage.json
timeout 300 uv run --frozen --offline --directory libs/anonymizer mypy --strict src tests
timeout 120 uv run --frozen --offline --directory libs/anonymizer lint-imports
```

La compuerta exige el 100 % de ramas en `domain/`, `application/`, `api.py`, `providers/` y
`testing/fake_transport.py`, y el 80 % de líneas en el paquete. La etiqueta `anonymizer-v0.1.0` la pone el
humano al fusionar el PR del Bolt.
