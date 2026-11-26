# Ronda 1 — U11-T06

**Veredicto:** VERDE. Lo dio `revisor` con sonnet sobre `25b0bd9`.

El revisor corrió él mismo CA-1 a CA-7 y la demostración, y todo terminó con salida 0:

- **CA-1:** 79 pruebas de *workflows* pasan y la guardia de clúster da `0 apariciones`.
- **CA-2:** la compuerta pasa con los `coverage.json` reales y tiene 20 pruebas.
- **CA-3:** las suites pasan, con la cobertura de cada paquete:

  | Paquete | Pruebas | Cobertura |
  |---|---|---|
  | analizador | 566 | 99,25 % |
  | gateway | 31 | 100 % |
  | perfiles | 100 | 98,97 % |
  | política | 195 | 100 % |
  | anonimizador | 459 | 99,54 % |
  | errores | 14 | — |

  mypy, ruff y las guardias salen limpios.
- **CA-4:** `demo_fake.py` termina con 1 hallazgo.
- **CA-6:** las rutas congeladas siguen intactas.
- **CA-7:** los cuatro paquetes están en 0.1.0.

Además comprobó lo siguiente:

- **Mutantes de la compuerta:** quitar cualquiera de los 9 guardias la hace fallar. También falla si se baja una rama en cualquiera de los 8 guardias que tienen ramas, o si las líneas de un paquete quedan por debajo del 80 %.
- **`pip-audit`:** bloquea de verdad.
- **Acciones de los *workflows*:** quedan fijadas por los mismos SHA que en `anonymizer-level0.yml`.
- **Hallazgos A-01 y A-03 de U11-T05:** quedaron cerrados.

## Hallazgos

| ID | Severidad | Lugar | Hallazgo | Arbitraje |
|---|---|---|---|---|
| F-01 | AMARILLO | `docs/loop/bitacoras/U11-T06.md:31` | El `grep` de CA-7 encuentra el prefijo `sk-ant-api03-` citado en prosa. Ya estaba en la bitácora de U10-T06. | **Aceptado:** es prosa y no una clave. En las próximas tareas, CA-7 debe excluir `docs/loop/bitacoras`. |
| F-02 | AMARILLO | `testing/coverage_gate.py:85` | Un guardia sin ramas pasa en vacío. Es el caso de `anonymizing.py`, con 0 ramas de 0. | **Candidata para B11b:** exigir el 100 % de líneas en los guardias. El plan no lo pide. |
| F-03 | AMARILLO | `analyzer-level0.yml:236-280` | El *job* `coverage-gate` repite las 4 suites porque no hay un SHA aprobado de `upload-artifact`. | **Candidata:** si el humano aprueba esa acción, se cambia. |

## Tareas candidatas

- **A-02:** decidir si el incidente de anonimización tiene prioridad sobre la señal (NFRD-U11-10).
- **F-02 y F-03:** las dos candidatas de la tabla.
- **Cierre de B11a:** quitar las aristas temporales de CG-U11-11 y abrir el PR del Bolt. La etiqueta `analyzer-v0.1.0` la pone el humano.
