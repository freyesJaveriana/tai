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

La lanza el humano, con una entrevista **sintética** y su clave en `VERIDICUS_ANTHROPIC_API_KEY`. No
corre en la suite por defecto; sale por la red y por eso lleva `--force-enable-socket`:

```bash
timeout 900 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/manual -m manual --no-cov --force-enable-socket -q
```

`--extra cli` instala el anonimizador, sin el cual un destino externo no arranca (código 3). El
comando del plan (R-04) no lo trae; con un entorno que ya lo tiene instalado da lo mismo.

El resultado queda en `libs/incoherence_analyzer/resultados-locales/manual-real-provider/` y no se
versiona.
