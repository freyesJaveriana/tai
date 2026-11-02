**Collaborator:** aidlc-developer-agent

## Contribution

Segunda pasada (cambio 01). Ángulo: implementabilidad y tamaño (INVEST), dependencias y ruta crítica,
realizabilidad con la pila (Python 3.12, FastAPI, React/TS, PostgreSQL + CNPG, Redis Streams,
llama.cpp) y factibilidad de US14.1 en el clúster Ing. Sistemas. No reabro las respuestas 1–14.

### 1. US14.1 tiene un ciclo con el alto de Domain Design (bloqueante)

AC14.1.5 instala «la CLI» y la tabla de dependencias la hace depender de US12.1 y US14.2; pero US12.1 se
construye en Construction, **después** de Domain Design, y Domain Design no empieza hasta revisar el
reporte de US14.1 (respuesta 14). Tal como está escrita, US14.1 no puede terminar nunca. Lo mismo, en
menor grado, AC14.1.4 («dos análisis idénticos»: aún no hay analizador). Propuesta:

- **AC14.1.5 (reescrito)** Given un SL250s sin internet y una *wheelhouse* armada en un trabajo en
  `hpchead02` (`pip download` con el conjunto de dependencias previsto de la biblioteca: p. ej.
  `pydantic`, `httpx`, `jsonschema` y un paquete de prueba mínimo con un *entry point*), When otro trabajo
  en el SL250s instala con `pip install --no-index --find-links` en el entorno conda propio y ejecuta el
  *entry point*, Then termina con código 0 y registra las versiones instaladas. `[ZINE]`
- **AC14.2.5 (nuevo, Construction)** el criterio actual de AC14.1.5 (instalar la CLI real desde el
  paquete y analizar una transcripción sintética contra el servidor local) pasa a US14.2, que sí depende
  de US12.1. Corregir la fila «US14.1 (AC14.1.5) | US12.1 y US14.2» de la tabla de dependencias: US14.1
  no depende de código.
- **AC14.1.4 (precisado)** «dos peticiones idénticas a `llama-server`» (mismo *prompt* sintético, `seed`,
  `--threads`, `--parallel 1` y `cache_prompt` igual en ambas), no «dos análisis»; registra si los SHA-256
  coinciden y, si no, el primer *token* que difiere.

### 2. US14.1: factibilidad en el clúster (precisiones, no reabren la respuesta 14)

- **Competencia por los SL250s.** La 4L usa `--exclusive` y 12 grupos para 8 nodos: tras lanzar el resto
  del arreglo no queda ningún SL250s libre durante días, y los trabajos de AC14.1.2/.4/.5/.6 esperan en
  cola. Añadir a la historia: los trabajos de medición se lanzan **mientras solo corre `--array=8`** (7
  nodos libres) y antes del resto del arreglo, o con dependencia explícita; el humano decide el orden.
- **Un solo `llama-server` para AC14.1.2 y AC14.1.4.** Copiar 36,9 GB a `/tmp` y cargarlos cuesta; un
  trabajo de sondeo en un SL250s que levanta el servidor una vez y corre ambas pruebas reduce el tiempo de
  nodo. En AC14.1.2 registrar también si la salida forzada por esquema funciona **con el razonamiento de
  Qwen encendido y apagado**: la gramática restringe toda la salida, incluido el bloque de razonamiento, y
  eso decide el diseño del adaptador local (US13.6).
- **AC14.1.3 sin cargar el modelo.** `llama-tokenize` carga solo el vocabulario del GGUF y puede correr en
  `hpchead02` como trabajo; no hace falta levantar `/tokenize` en un SL250s. Precisar además **qué
  entrevistas**: el paquete de la 4L trae 3 (118, 176, 673); si «la más larga» de las 10 no está ahí, el
  trabajo debe recibirla por el mismo canal (`scp` al directorio del proyecto, nunca a Git) y el reporte
  lo dice.
- **AC14.1.6.** `llama-bench` debe correr en un SL250s (`hpchead02` no tiene AVX y sus cifras no
  sirven); añadir que el modelo elegido sea de licencia compatible (DT10), Q8_0 o BF16 (FR16.2) y quepa
  en un nodo (≤ ~50 GB de pesos con la caché), y que el reporte nombre la familia.
- **AC14.1.1 y el alto.** Las horas de `--array=8` (la 118, ~1–1,5 días estimados, hasta 14 de `--time`)
  atan el inicio de Domain Design a una corrida que puede cortarse. Proponer que el reporte se pueda
  revisar con la medición **en curso** (llamadas, *tokens* y segundos de `registro_4L_8.csv` y del log del
  servidor) si no termina en un plazo que fije el humano; la decisión de esperar sigue siendo suya.
- **Normas del clúster.** Añadir a la historia: todo paso es un `.sbatch` (en el nodo de entrada solo
  `scp`, `sbatch`, `squeue`/`sacct`); `HOME` y cachés dentro de la carpeta del proyecto (`comun.sh`);
  entorno conda propio con `-p`, sin Apptainer; cada medición escribe solo bajo un subdirectorio propio
  (p. ej. `/zine/HPC02S1/freyes/tg4L/validacion/`) para no mezclarse con `corridas/` de la 4L.
- **Dónde viven los `.sbatch` y el reporte.** El reporte `evaluation/zine/…` y los scripts entrarían por
  PR (zona de código), pero la configuración de GitHub es tarea previa al desarrollo. Proponer que el
  reporte vaya a `docs/` (commit directo) o que la historia diga que su PR es el primero del repositorio.
- **Traza.** AC14.1.3 procesa entrevistas del piloto en el clúster y NFR12 dice «solo en la máquina
  local»; la respuesta 11 lo permite para ZINE. Añadir NFR12 a la fila de la respuesta 11 en la tabla de
  decisiones que precisan `requirements.md`.

### 3. Primera rebanada: ruta crítica incompleta y US11.3 demasiado grande

- **Ruta crítica.** La rebanada de la respuesta 10 (biblioteca + CLI + anonimizador + proveedor
  comercial) no puede correr sin US13.2 (perfil y `config_sha256`), US13.6 (al menos un adaptador
  comercial), US3.6 (esquema del contrato), US3.2 (error ⇒ vacío, AUTONOMIA-05) y US3.5 (verificador).
  Propuesta: US12.2 → US3.6 → US3.4 → US3.2 → US13.2 → US13.6 (un comercial + compatible con OpenAI) →
  US11.3 → US13.3 → US3.5 → US12.1 → US12.3. Añadir a la tabla: US12.1 y US13.3 dependen de US13.2.
- **Partir US11.3** (6 criterios que mezclan biblioteca y servicio):
  - **US11.3 (biblioteca, primera rebanada)**: AC11.3.1–AC11.3.4, AC11.3.6 y AC11.3.5 en `[N0]` (el
    *canary* se busca en los logs capturados y en los archivos que escribe la CLI; no hay PostgreSQL ni
    Redis en la CLI, así que `[N1]` no aplica).
  - **US11.6 (nueva, plataforma) — El anonimizador es el único punto de salida en el clúster.** Con la
    `NetworkPolicy` de US9.1, `semantic-agent` no puede llamar al proveedor: sus adaptadores comerciales
    deben ir a través de `anonymizer-proxy`. Criterios: `semantic-agent` con un destino externo y sin la
    URL del anonimizador no arranca `[N0]`; la tabla de correspondencia vive solo en el proceso que
    restaura `[N1]`. El dónde se seudonimiza (biblioteca dentro de `semantic-agent` o el *proxy*) lo
    decide Domain Design; la historia solo fija la frontera.
- **Falta la prueba de *payload* saliente (AUTONOMIA-04, mandato de `team.md`).** AC11.3.1 prueba la
  salida del anonimizador, no lo que envía el adaptador. **AC11.3.7 (nuevo)** Given un transporte HTTP
  *fake* que captura el cuerpo de cada petición de cada adaptador comercial, When se analiza una
  transcripción sintética con entidades sembradas, Then 0 entidades sembradas en los cuerpos capturados.
  `[N0]`
- **US13.6** pide cuatro adaptadores en una historia. Partir: el comercial elegido para la rebanada y el
  compatible con OpenAI (MUST, primera rebanada); los otros dos comerciales en AC separados o en otra
  historia, para que la rebanada cierre sin esperarlos.
- **AC12.2.2** (CLI frente a `semantic-agent`, `[N1]`) depende de la consola: impide cerrar US12.2 en la
  rebanada. Moverlo a una historia del trabajador (p. ej. AC2.2.6) y dejar en US12.2 solo import-linter.

### 4. Criterios no realizables tal como están

- **AC3.3.1 `[N2]`** «no cambia el conjunto de hallazgos» no se puede cumplir con modelos comerciales
  (sin semilla fiable, dos corridas sin inyección ya difieren). Reescribir: la inyección del Escenario A
  pide una salida reconocible (p. ej. un hallazgo con un `hecho` marcador o una etiqueta prohibida) y la
  evaluación comprueba 0 apariciones; y la diferencia con y sin inyección no supera el desacuerdo entre 3
  corridas sin inyección.
- **AC2.7.2 y AC3.6.3** «mismo par de citas»: fijar la clave de deduplicación para que sea probable:
  par **no ordenado** de (turno, cita normalizada por espacios). Dos citas casi iguales del mismo par de
  turnos aparecen dos veces; dejarlo escrito como límite.
- **AC12.4.1** «sin directorio de salida explícito para el corpus»: decir cómo se reconoce el corpus
  (`origen: corpus` del contrato) y, como guardia barata, que la CLI rechace con código ≠ 0 escribir una
  salida de `origen: corpus` en una ruta que `git check-ignore` no cubra. `[N0]`

### 5. Lo que es implementable sin cambios

US2.2 (Redis Streams con grupo de consumidores y `XAUTOCLAIM`, idempotente por ID de corrida), US6.1
AC6.1.6 (`SELECT … FOR UPDATE` sobre la sesión), US8.4 (permisos `INSERT`-only más `NOT NULL`), US13.2
(SHA-256 de JSON canónico) y US3.4 (verificación determinista con Hypothesis) son pequeñas y realizables
con la pila. US10.5 duplica llamadas: de acuerdo con contarlo en Delivery Planning.

## Positions

- OBJECT: US14.1 AC14.1.5 (y la fila de dependencias) exige la CLI de US12.1, que solo existe después del alto de Domain Design que US14.1 libera; ciclo sin salida.
- OBJECT: AC14.1.4 habla de «análisis» sin analizador todavía; debe medir peticiones idénticas a `llama-server` con `--parallel 1`.
- OBJECT: US14.1 no prevé la competencia por los 8 SL250s con la 4L en `--exclusive`; sin fijar el orden de lanzamiento, las mediciones quedan días en cola.
- OBJECT: La ruta crítica de la primera rebanada omite US13.2, US13.6, US3.6, US3.2 y US3.5, sin las cuales la CLI no puede correr con un proveedor comercial.
- OBJECT: Falta la prueba de *payload* saliente de los adaptadores que manda AUTONOMIA-04 (AC11.3.7), y US11.3 mezcla biblioteca y servicio sin fijar que el *proxy* sea la única salida.
- OBJECT: AC3.3.1 `[N2]` («no cambia el conjunto de hallazgos») no es realizable con modelos no deterministas.
- AGREE: Tratar US14.1 como historia de medición que registra cifras sin umbrales (AUTONOMIA-02 se cumple con comando y dato).
- AGREE: Respuestas 10–13 aplicadas en US2.3, US2.6, US2.7, US6.1 y US13.3 son implementables con la pila.
- AGREE: Separar US3.4 (verificación) de US3.1 (presentación) y US3.5 de US3.6.
- AGREE: Mover a `[N0]` el *canary* de la CLI y fijar la clave de deduplicación son ajustes que un experto resuelve sin ronda 2.
