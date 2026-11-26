# Ronda 1 — U11-T02

`revisor` (`opus`), 2026-11-26.

VEREDICTO: NO-VERDE

Los siete criterios pasan cuando los corro yo, pero encontré dos fallos de seguridad:
- **ROJO:** una forma de saltarse BR2.3 con una dirección IPv4 escrita en decimal o en hexadecimal.
- **NARANJA:** una forma de evadir el escáner con caracteres invisibles dentro de una palabra.

## Criterios de aceptación, verificados por mí

Todo se corrió sobre `58df79f`, con `--directory` en ruta absoluta.

| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U11-T02/libs/execution_profiles pytest --cov=veridicus_execution_profiles.validate --cov=veridicus_execution_profiles.floors --cov-branch --cov-fail-under=100 --cov-report=term-missing` | Pasa: 70 pruebas, con 100 % de ramas en `validate.py` (32) y en `floors.py`. `test_profile_contract.py` (14) está en verde y los cinco pares quedan cubiertos. |
| CA-2 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U11-T02/libs/integrity_policy pytest --cov=veridicus_integrity_policy.scan --cov=veridicus_integrity_policy.notice --cov-branch --cov-fail-under=100 --cov-report=term-missing` | Pasa: 162 pruebas, con 100 % de ramas en `scan.py` (24) y en `notice.py` (6). `tests/guards` (20) está en verde. |
| CA-3 | `git -C /workspace/.worktrees/U11-T02 diff --exit-code c7e6542… -- <las 6 rutas>` | Pasa: código 0. |
| CA-4 | El mismo comando con `--extra cli` (decisión del orquestador), `-rE --tb=no -q --rojo` | `111 failed` y 0 ERROR. Todas fallan por el `NotImplementedError` de `analyze`, `load_response_schema`, `build` o `run`. |
| CA-5 | `mypy --strict src tests`, `ruff check .` y `ruff format --check .` en los dos paquetes | Pasa: 6 de 6 con código 0. |
| CA-6 | Los tres `check-no-*.sh` | Pasa: `0 apariciones` en los tres. |
| CA-7 | `grep -rnP "sk-\|api_key\s*:" …/libs/execution_profiles/config` | Pasa: no hay coincidencias. |

**Otras comprobaciones**

- **Rueda:** la construí con `uv build --wheel --offline --no-build-isolation`. Incluye `veridicus_execution_profiles/config/profiles.yaml`, así que el `force-include` es correcto.
- **Worktree:** quedó limpio al terminar.
- **Fuga de la clave:** puse un *canary* `sk-…` en `api_key_ref`. El error dice «ajuste api_key_ref: no cumple la forma exigida» y no repite el valor.

## Hallazgos

### F-01 · ROJO · `libs/execution_profiles/src/veridicus_execution_profiles/validate.py:46` · BR2.3 se salta con una IPv4 en decimal o en hexadecimal

**El fallo.** `_is_internal_host` toma como «servicio del clúster» todo host sin punto. Pero `134744072`, `0x8080808` y `0` son direcciones IPv4 que glibc acepta. `ipaddress` no las reconoce como direcciones, y por eso caen en esa rama.

**Evidencia.**
- `validate_profile`, con `scope: local`, acepta `http://134744072:8080` y `http://0x8080808:8080` sin ningún aviso.
- `socket.getaddrinfo('134744072', 80, …, socket.AI_NUMERICHOST)` resuelve las dos a `('8.8.8.8', 80)`, sin pasar por DNS.

**Consecuencia.** Un destino `local` no pasa por el anonimizador, y aun así puede apuntar a una IP pública. La transcripción saldría sin seudonimizar, lo que viola AUTONOMIA-04. La CLI corre en la anfitriona, donde no hay `NetworkPolicy` que la frene.

**Corrección.**
1. Si `socket.inet_aton(host)` tiene éxito, tratar el host como `IPv4Address(inet_aton(host))` y aplicarle la regla de loopback o de red privada.
2. Exigir que un nombre sin punto sea una etiqueta DNS que empiece por letra: `^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$`.
3. Probar los casos `134744072`, `0x8080808`, `0` y `2130706433`. Este último es 127.0.0.1 y debe aceptarse como loopback.

### F-02 · NARANJA · `libs/integrity_policy/src/veridicus_integrity_policy/scan.py:45-56` · Los caracteres invisibles dentro de una palabra evaden el escáner

**El fallo.** Con fuente `[]`, `scan` devuelve `[]` para estas tres formas de «miente»:
- `'mi­ente'` (guion blando);
- `'mi​ente'` (espacio de ancho cero);
- la forma de ancho completo.

La consola muestra las dos primeras como «miente». BR9.1 pide «límites de palabra Unicode», y UAX #29 (WB4) ignora los caracteres de formato (`Cf`) dentro de la palabra. Un *prompt* inyectado (Escenario A) podría pedir justo esa forma.

**Lo que sí funciona:** las mayúsculas (`MiÉnte`), la tilde descompuesta y `FALSO.`.

**Corrección.**
- En `_fold`, descartar los caracteres de categoría `Cf` (U+00AD, U+200B a U+200D, U+2060 y U+FEFF), igual que se descartan los combinantes.
- Probarlo con un caso positivo por cada uno.

La forma de ancho completo (NFKC) cambia la semántica de C8, así que va a candidatas.

### F-03 · AMARILLO · `validate.py:83` · La regla de familias es parcial y no distingue mayúsculas

Una familia ausente no cuenta, y `Claude` y `claude` cuentan como dos familias distintas. BR2.4 está diferido a B11b (plan:497), así que no bloquea.

**Sugerencia:** comparar con `casefold()`.

### F-04 · AMARILLO · `loader.py:99` · `load_config` descarta los avisos

`load_config` no conserva los avisos que devuelve `validate_profile`, por ejemplo `same_family`. T05 tendría que validar otra vez para mostrar el aviso de BR2.5.

**Sugerencia:** devolver los avisos junto a la `EffectiveConfig`, o dejarlo anotado como supuesto de firma.

### F-05 · AMARILLO · `scan.py:114` · El aviso se relee en cada llamada

`_notice_spans` lee `notice.v1.yaml` en cada `scan`.

**Sugerencia:** guardarlo en caché, como `_vocabulary`.

### F-06 · AMARILLO · `loader.py:88` · `prompt_sha256` no se valida

El valor por defecto falla cerrado: 64 ceros nunca coinciden con un SHA-256 real. Esa garantía depende de T04. Lo que falta es validar la forma de un valor pasado a mano, por ejemplo `""`.

**Sugerencia:** comprobar `^[0-9a-f]{64}$`.

### Sin hallazgo en lo que se pidió revisar

- **El perfil** solo usa campos de `profile-base` y del analizador, y valida con `profiles.validate` real.
- **La validación no se salta** en estos casos:
  - una `base_url` en un destino externo se rechaza;
  - el piso de 270 s se aplica a todo papel externo;
  - una clave ausente o en blanco se rechaza, y el mensaje nombra la variable;
  - la `EffectiveConfig` es inmutable a fondo.
- **El escáner:**
  - escanea un término suelto entre «…»;
  - escanea un tramo «…» que no está en ninguna fuente o que difiere en mayúsculas;
  - no excluye un fragmento del aviso;
  - excluye el aviso aunque tenga otros espacios.
- **Las pruebas** no tienen `no cover`, `skip` ni exclusiones. El control negativo de `scan-cases` falla de verdad.
- **BR2.4, BR2.6, BR2.7 y BR2.9** quedan diferidas a B11b (plan:497), y ninguna hacía falta en B11a.

## Tareas candidatas (fuera de alcance)

- **C8:** definir la normalización de compatibilidad (NFKC, ancho completo) y de los caracteres que se ignoran por defecto, para que U8 y U11 escaneen igual.
- **U1, `profile-base.schema.v1`:** que `base_url` rechace por patrón los hosts IPv4 numéricos sin puntos.

```
VEREDICTO: NO-VERDE
ROJO|libs/execution_profiles/src/veridicus_execution_profiles/validate.py:46|BR2.3 se salta con una IPv4 en decimal o hexadecimal (134744072 resuelve a 8.8.8.8)
NARANJA|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:45-56|Caracteres invisibles (U+00AD, U+200B) dentro de una palabra evaden el escáner
AMARILLO|libs/execution_profiles/src/veridicus_execution_profiles/validate.py:83|La regla de familias es parcial y no distingue mayúsculas (BR2.4 diferido)
AMARILLO|libs/execution_profiles/src/veridicus_execution_profiles/loader.py:99|load_config descarta los avisos (same_family)
AMARILLO|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:114|El aviso se relee en cada llamada al escáner
AMARILLO|libs/execution_profiles/src/veridicus_execution_profiles/loader.py:88|prompt_sha256 sin validar su forma
INFORME: docs/loop/revisiones/U11-T02/ronda-1.md
```
