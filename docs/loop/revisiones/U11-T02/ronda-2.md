# Ronda 2 — U11-T02

`revisor` (`opus`), 2026-11-26, sobre `1115411`.

VEREDICTO: NO-VERDE

Los siete criterios pasan cuando los corro yo, y F-01, F-03, F-05 y F-06 quedan cerrados. Quedan dos defectos:
- F-02 no está cerrado en su clase: las marcas no espaciadas de clase combinante 0 todavía evaden el escáner.
- Una prueba nueva de F-04 pasa siempre, sin importar el código.

## Criterios de aceptación, verificados por mí

| # | Resultado |
|---|---|
| CA-1 | Pasa: 98 pruebas; `validate.py` y `floors.py` con 100 % de ramas |
| CA-2 | Pasa: 177 pruebas; `scan.py` y `notice.py` con 100 % de ramas |
| CA-3 | Pasa: `git diff --exit-code c7e6542…` da código 0, sin salida |
| CA-4 | Pasa con `--extra cli`: `errors="0" failures="111" tests="111"`. Todos los fallos son `NotImplementedError` |
| CA-5 | Pasa: `mypy --strict`, `ruff check` y `ruff format --check`, 6 de 6 con código 0 |
| CA-6 | Pasa: `0 apariciones` en los tres scripts |
| CA-7 | Pasa: ninguna coincidencia |

**Otras comprobaciones:**
- **Alcance:** el diff contra `bolt/b11a-analyzer` solo toca `libs/execution_profiles`, `libs/integrity_policy` y `docs/loop`.
- **Pruebas:** no hay `no cover`, `skip`, `xfail` ni umbrales bajados.
- **Worktree:** limpio al terminar.

## Cierre de la ronda 1

**F-01, cerrado.** Probé 50 hosts con `_is_internal_host` y los comparé con `getaddrinfo(AI_NUMERICHOST)`. Ningún host numérico que resuelva a una IP pública pasa como interno.
- **Se rechazan:**
  - las formas decimal, hexadecimal y octal;
  - IPv6 con una IPv4 pública embebida (`::ffff:`, `::8.8.8.8`, `64:ff9b::`, `2002:`);
  - las formas con punto final;
  - `localhost.evil`;
  - las formas con `@` o `#`.
- **Las formas raras las corta antes el esquema** (`format: uri`).
- **Se aceptan, y son correctas:** `2130706433`, `012.0.0.1`, `0x0a.1`, `10.1` y `LOCALHOST`.
- **Mutante en memoria** (`_numeric_ipv4` devuelve `None`): fallan 5 aceptaciones. La regex de etiqueta DNS es una segunda defensa.

**F-02, cerrado solo para `Cf`.** El mutante sin la regla `Cf` hace fallar 7 de las pruebas nuevas.
- **Las exclusiones no se rompen.** Una cita con un `Cf` que también está en la fuente queda excluida. Si la cita y la fuente difieren en un `Cf`, el escáner la revisa, que es el lado seguro.
- **El aviso solo se excluye cuando aparece completo.** Las posiciones de las coincidencias son correctas.
- **Queda abierto en su clase:** ver F-07.

**F-03, cerrado.** `casefold()` en `validate.py:104`, con su prueba.

**F-04, cerrado en el código, con una prueba vacía (F-08).**
- Recalculé `sha256_jcs` del cuerpo sin `warnings`: coincide con `config_sha256`.
- La configuración sigue inmutable.
- `repr(config)` no contiene `sk-`.

**F-05, cerrado.** `functools.cache` no guarda las excepciones. La guardia congelada sustituye `load_notice` con `monkeypatch`.

**F-06, cerrado.** El mensaje es fijo y no repite el valor. Probé un *canary*, mayúsculas, un salto de línea final, dígitos de ancho completo y un dígito árabe-índico: la regex los rechaza todos.

## Hallazgos

### F-07 · NARANJA · `libs/integrity_policy/src/veridicus_integrity_policy/scan.py:53` · Las marcas no espaciadas de clase combinante 0 todavía evaden el escáner

`_fold` descarta un carácter solo si `combining(part)` es distinto de 0 o si su categoría es `Cf`. Pero UAX #29 WB4 ignora todo `Extend`, que incluye las marcas `Mn` de clase combinante 0, invisibles en la consola.

**Evidencia.** Lo comprobé con `scan('el testigo mi'+chr(c)+'ente hoy', [])`:
- **Evaden:** U+034F, U+FE00, U+FE0F, U+E0100, U+180B y U+17B4.
- **Fuera de WB4, también evaden:** U+115F, U+1160, U+3164, U+FFA0 y U+2800. Van a candidatas.
- **Todos los `Cf` que probé sí se detectan.**

Es la misma clase que F-02 (Escenario A) y afecta AUTONOMIA-03.

**Corrección:** descartar también las `Mn` y `Me` (o los `Default_Ignorable_Code_Point` del grupo `Extend`), con un caso positivo por cada una.

### F-08 · NARANJA · `libs/execution_profiles/tests/test_hosts_and_config.py:80-86` · La prueba de que `warnings` no entra en las huellas pasa siempre

`dataclasses.replace(config, warnings=())` copia las huellas sin recalcularlas. Por eso la prueba pasa sea cual sea la implementación.

**Corrección:** recalcular `sha256_jcs` del cuerpo C18 y compararlo con `config_sha256`, o comparar dos configuraciones con avisos distintos y el mismo perfil.

### F-09 · AMARILLO · `loader.py:58` · `warnings` no existe en C18

`effective-config.v1.yaml` declara `additionalProperties: false`. Hay que anotar en la bitácora que `warnings` se excluye al serializar.

### F-10 · AMARILLO · `validate.py:32` · `_DNS_LABEL` usa `re.IGNORECASE` sin `re.ASCII`

Con esa combinación, `[a-z]` acepta `ı`, `İ`, `ſ` y `K`. Hoy `format: uri` las rechaza antes, pero conviene usar `re.ASCII`.

### F-11 · AMARILLO · `scan.py:53` · Un `Cf` usado como separador une dos palabras

`es​falso` da 0 coincidencias. Es coherente con UAX #29, pero la consola podría mostrar «falso» solo en el renglón siguiente.

## Tareas candidatas (fuera de alcance)

- **BR2.3 / U11-T03:**
  - Un nombre sin punto o `*.svc` pasa por la regla misma y luego se resuelve por DNS. Solo comprobar la IP resuelta al conectar, en el transporte local del *gateway*, cierra el caso.
  - `::ffff:10.0.0.1` se rechaza: un falso negativo seguro.
- **C8:**
  - Fijar la normalización: NFKC, `Default_Ignorable` fuera de WB4 y homoglifos.
  - Decidir si la verificación de citas normaliza los `Cf`.

```
VEREDICTO: NO-VERDE
NARANJA|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:53|Las marcas Mn de clase combinante 0 (U+034F, U+FE00-FE0F, U+E0100, U+180B, U+17B4) evaden el escáner (F-02 no cerrado en su clase)
NARANJA|libs/execution_profiles/tests/test_hosts_and_config.py:80|La prueba de que warnings no entra en las huellas pasa siempre (replace copia los hashes)
AMARILLO|libs/execution_profiles/src/veridicus_execution_profiles/loader.py:58|warnings no está en C18 (additionalProperties false); anotar que se excluye al serializar
AMARILLO|libs/execution_profiles/src/veridicus_execution_profiles/validate.py:32|_DNS_LABEL con IGNORECASE acepta letras no ASCII; usar re.ASCII
AMARILLO|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:53|Un Cf como separador une dos palabras (es+U+200B+falso no coincide)
INFORME: docs/loop/revisiones/U11-T02/ronda-2.md
```
