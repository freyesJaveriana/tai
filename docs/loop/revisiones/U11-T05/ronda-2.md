# Ronda 2 — U11-T05

**Veredicto:** NO-VERDE. Revisor: `revisor` con opus, sobre `3826d03`.

## Lo que se cerró en esta ronda

Los criterios CA-1 a CA-8 pasan con las corridas del revisor. Comprobó cada corrección de la ronda 1 con mutantes en memoria o con sondas:

- **F-01, F-02 y F-03:** cerrados.
- **F-07:** cierto lo que dijo el codificador. Import-linter ya detectaba `domain -> api` de forma indirecta.
- **Comando manual del viernes:** sirve si se lanza desde la raíz. La salida cae en `libs/incoherence_analyzer/resultados-locales/manual-real-provider/`, que Git ignora.

## Hallazgos

| ID | Severidad | Lugar | Hallazgo | Arbitraje |
|---|---|---|---|---|
| F-01 | NARANJA | `cli/main.py:251-266` | Si la señal llega durante la última llamada de una corrida, `analyze` termina y `_write` escribe `<nombre>.salida.json`. Aun así, la CLI sale con 5 y dice «la corrida en curso quedó sin salida». Esto va contra NFRD-U11-10. La prueba solo mira el código. | **Corregir:** revisar la bandera entre `analyze` y `_write`; si está puesta, no escribir y lanzar `CancelledError`. La prueba debe afirmar que el archivo no existe. Hay que conservar el chequeo después del bucle. |
| F-02 | AMARILLO | `README.md:38-40` y bitácora | El peor caso es 1 + 2N llamadas por entrevista, no 3, y `timeout 1800` no deja margen. | **Corregir:** rehacer la cuenta en el README y en la bitácora. Recomendar `timeout 3600` como cota práctica y aclarar que lo es. |
| F-03 | AMARILLO | `tests/boundaries/test_import_contracts.py:82-87` | El caso negativo `domain->api` pasa también sin la entrada nueva. | **Corregir:** afirmar en stdout la ruta directa a `veridicus_incoherence_analyzer.api`, o usar un `api` sin dependencias, y comprobar con el mutante que la prueba distingue. |
| F-04 | AMARILLO | `tests/manual/test_real_provider.py:7-11` y `tests/cli/test_exit_codes.py:344` | Comentarios desactualizados después de F-03, F-04 y F-05. | **Corregir.** |

## Tareas candidatas

- BR11.6 sigue sin cubrir `evaluation/zine/paquete/`. Queda para US14.
- El `grep` de `sk-` de CA-8 encuentra controles de B10a en `libs/anonymizer/tests`. Las tareas que vengan deben excluirlos de forma explícita en el criterio.
