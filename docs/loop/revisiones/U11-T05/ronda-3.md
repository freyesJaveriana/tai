# Ronda 3: U11-T05

**Veredicto:** VERDE. Lo dio `revisor` con opus sobre `15103b7`.

El revisor corrió él mismo, completos, los criterios CA-1 a CA-8, y todos pasaron. Los resultados:

- **CA-1:** 82 pruebas, con `composition.py` al 100 % de ramas. Aparte, 76 pruebas y `cli/` al 98,28 % de líneas.
- **CA-2:** el único cambio es el de P-T04-1.
- **CA-3:** 111 pruebas.
- **CA-4:** las fronteras siguen KEPT en los 5 paquetes, con 58 pruebas.
- **CA-5:** 4 pruebas de punta a punta. La prueba manual se recolecta (2), pero la corrida por defecto la deja fuera.
- **CA-6:** 235 y 161 pruebas al 100 %, y 459 en el anonimizador.
- **CA-7 y CA-8:** limpios.

## Correcciones de la ronda 2

- **F-01 (cerrado).** La sonda `_SignalingProvider(SIGTERM, at=…)` en tres casos no deja nunca en disco la salida de la corrida interrumpida. El revisor quitó cada uno de los dos chequeos de la bandera, uno por vez, y en cada caso falló su propia prueba.
- **F-02 (cerrado).** La cuenta del README ya es 1 + 2N llamadas.
- **F-03 (cerrado).** El mutante que quita la entrada `api` hace fallar la prueba nueva.
- **F-04 (cerrado).** Se actualizaron los comentarios.

## Hallazgos que no bloquean

| ID | Severidad | Lugar | Hallazgo | Arbitraje |
|---|---|---|---|---|
| A-01 | AMARILLO | `README.md:38-42` | Los 3300 s son por entrevista y el comando manual corre dos. El peor caso es de unos 6600 s, así que `timeout 3600` lo corta. | **Va a T06.** Recomendar `timeout 7200`. Hasta entonces, el orquestador se lo indica al humano para la corrida del viernes. |
| A-02 | AMARILLO | `cli/main.py:258-264` | Si una señal llega a la vez que un incidente de anonimización, el incidente queda tapado: sale el código 5 y no se escribe la salida en error. No sale ninguna llamada nueva. | **Precisión para la tabla de la unidad.** Hay que decidir si el incidente tiene prioridad sobre la señal. Queda como candidata para T06. |
| A-03 | AMARILLO | `cli/messages.py:54` | Si la señal llega cuando ya se escribió la última salida, el mensaje dice «la corrida en curso quedó sin salida». | **Va a T06.** Usar un mensaje distinto para ese caso. |

## Tareas candidatas

- A-02: precisar en el diseño qué tiene prioridad entre un incidente y una señal (NFRD-U11-10).
- BR11.6 no cubre `evaluation/zine/paquete/` (US14).
- El `grep` de `sk-` en CA-8 debe excluir los controles de B10a en las tareas que siguen.
