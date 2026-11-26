# veridicus-incoherence-analyzer

Biblioteca y línea de comandos `veridicus` del analizador de incoherencias (U11). Este archivo lo
completa U11-T06 (uso, tabla de la frontera de datos, versión 0.1.0); por ahora solo trae lo que la
demostración necesita.

## Uso

```bash
veridicus analyze <archivo.json | directorio> --perfil demo-anthropic [--salida <directorio>]
```

Códigos de salida: `0` todas las corridas terminaron (aunque alguna tenga `estado: error`); `2`
argumento, archivo, consentimiento, límite o directorio; `3` perfil, anonimizador, clave,
transferencia o aviso; `4` incidente de anonimización; `5` error inesperado, escritura fallida o
interrupción. Sin `--salida`, la salida va a `resultados-locales/<fecha>-analyze`, que Git ignora.

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
timeout 1800 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/manual -m manual --no-cov --force-enable-socket -q
```

- `--extra cli` instala el anonimizador, sin el cual un destino externo no arranca (código 3). Con un
  entorno que ya lo tiene instalado da lo mismo.
- El peor caso pasa de 900 s: dos entrevistas, hasta tres llamadas cada una y 300 s por llamada
  (`VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300`) son unos 1800 s. Con `timeout 900` el humano podría ver
  un corte sin que el proveedor haya fallado.
- La prueba falla si la corrida termina en `estado: error` (por ejemplo, una clave inválida) o sin
  ninguna llamada, y si la entrevista con la contradicción sembrada no produce ningún hallazgo.

El resultado queda en `libs/incoherence_analyzer/resultados-locales/manual-real-provider/` y no se
versiona.
