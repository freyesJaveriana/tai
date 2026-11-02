**Collaborator:** aidlc-quality-agent

## Contribution

Ángulo: comprobabilidad de los criterios (segunda pasada, cambio 01). El borrador es sólido: casi todos
los criterios son Given/When/Then con nivel, los rechazos fijan estado HTTP y «0 filas», y los escáneres
llevan control negativo. Propongo cambios concretos, sin reabrir las respuestas 1–14.

### A. AUTONOMIA-04/05: huecos de prueba (bloqueantes)

1. **US11.3: falta la prueba del *payload* saliente** que exige `team.md` (Mandated AUTONOMIA-04).
   AC11.3.1 prueba la salida del anonimizador, no lo que recibe el proveedor. Nuevo **AC11.3.7**: Given un
   perfil comercial y el conjunto sintético con entidades sembradas, When corre el analizador (juez y
   verificador), Then el `ModelGateway` *fake* captura cada mensaje saliente y ninguno contiene una entidad
   sembrada (0 fugas), y todos contienen marcas `[PERSONA_n]`; control negativo: con el anonimizador
   puenteado en un *fixture*, la prueba falla. `[N0]`. Debe correr en la biblioteca, para cubrir CLI y
   servicio a la vez (pregunta 10).
2. **US11.3: fallo cerrado también en N1**, como pide el nivel 1 de `team.md`. Nuevo **AC11.3.8**: Given
   `semantic-agent` con el anonimizador detenido y un servidor de proveedor *fake* en contenedor, When se
   analiza un turno, Then el servidor registra 0 peticiones y el tramo queda en `error`. `[N1]`.
   AC11.3.3 debe sumar el caso (c) *timeout* del anonimizador.
3. **AC11.3.3 / FR4.2: falta el `codigo`.** FR4.2 no tiene un código para el fallo del anonimizador, así
   que la aserción «termina en `error`» queda abierta. Propongo una fila en la tabla de precisiones:
   código estable `anonimizador` (o el que fije Contract Design). AC3.2.1 suma el caso (h).
4. **AC11.3.4: más bordes de marca.** Además de una marca alterada: (a) una marca inventada
   (`[PERSONA_9]` inexistente) y (b) una cita que pierde una marca, ambas invalidan; control positivo: la
   cita restaurada se verifica contra el turno **original**, no contra el seudonimizado.
5. **US3.4: la regla del piloto necesita controles negativos explícitos.** «Solo se normalizan
   espacios» debe probar que **no** se normaliza nada más. AC3.4.2 suma: (d) mayúsculas o minúsculas
   distintas, (e) una tilde quitada, (f) comillas o puntuación cambiadas, (g) fragmentos unidos con
   « […] » que vienen de **turnos distintos**, (h) un turno inexistente (`n` fuera de rango). Todos se
   rechazan. AC3.4.3 (Hypothesis) debe tener su propiedad inversa: insertar o cambiar un carácter que no
   sea espacio en una subcadena válida ⇒ se rechaza.
6. **AC3.4.5 (N2) con un perfil comercial**, además de `todo-local`. Así el 100 % de citas verificadas
   cubre también la restauración antes de verificar (mapa 05, niveles 0, 1 y 2).

### B. Aserciones ambiguas o no medibles (AUTONOMIA-02)

7. **AC2.7.3** «la consola responde y veo su avance» es una opinión. Reescribir como AC2.2.2: Given un
   *fake* que bloquea el modo final, When pido `GET` de la sesión y `POST` de una decisión, Then `200`
   antes de liberarlo, y el avance muestra «k de n ventanas». `[N1]` + `[N0]` Vitest.
8. **AC2.7.2** «mismo par de citas»: definir la identidad como el par {(turno, texto normalizado en
   espacios)} **sin importar el orden**, igual que NFR4. Borde nuevo: un hallazgo del incremental ya
   `aceptada` que el modo final repite **conserva su estado y su historial** y no vuelve a `pendiente`.
   `[N1]`.
9. **US2.7: concurrencia del lanzamiento.** Nuevo AC2.7.6: con un modo final «En cola» o «Procesando»,
   lanzar otro responde `409`; dos `POST` simultáneos ⇒ exactamente un `202`. `[N1]`. Para la
   consolidación (AC6.1.2) y el rótulo del reporte cuenta **el último** modo final.
10. **AC2.6.2 contradice la convención:** usa `422` para «no es JSON válido», pero la convención reserva
    `415` para el formato. Fijar: tipo de contenido que no es JSON ⇒ `415`; JSON mal formado o fuera del
    esquema ⇒ `422`. Ampliar los casos de esquema en `[N0]` (uno por campo obligatorio, `origen` distinto
    de `corpus`, `turnos` vacío, `pagina_fin < pagina`, `estado` fuera del enum); el conteo `[N1]` basta
    con un caso.
11. **AC2.6.1** «tal como vienen»: la aserción es que los turnos persistidos, leídos por la API, son
    iguales campo a campo al archivo de entrada. **AC2.6.3**: un caso en el límite y otro en límite + 1
    para **cada uno** de los tres límites.
12. **AC14.1.4: la comparación falla siempre.** La salida del contrato lleva `fecha` y fechas por llamada,
    así que los SHA-256 nunca coinciden. Comparar la salida sin `fecha` ni las fechas del registro de
    modelos, como AC12.2.2.
13. **US14.1, regla común `[ZINE]`.** Cada criterio registra en el reporte el comando exacto (con `-p`,
    `-n` y `-t` en `llama-bench`), el ID del trabajo SLURM, el nodo y el SHA-256 del modelo. Un resultado
    «no medible», con su motivo y su salida, también cierra el criterio: es una historia de medición.
    AC14.1.2 clasifica cada parámetro como aceptado, rechazado o **aceptado sin efecto**. AC14.1.5 instala
    con `pip install --no-index --find-links <paquete>` y adjunta el log sin descargas.
14. **AC14.1.7** «deja constancia»: fijar dónde. Una línea de revisión firmada (quién, fecha, decisión)
    en el reporte, en un commit `aidlc(...)`, y el evento de inicio de Domain Design en la auditoría con
    hora posterior. `[Manual]`.
15. **AC12.3.4: la compuerta N2 no es binaria.** Para que bloquee el PR: la CLI de evaluación termina con
    código ≠ 0 si una métrica no alcanza su umbral, y el JSON trae `pasa` por métrica. AC12.3.2 registra el
    SHA-256 del conjunto, no solo su versión. AC12.3.1 suma bordes: una muestra coherente sin esperadas (sin
    división por cero), un mismo par emitido dos veces cuenta una sola vez, y un acierto de par con tipo
    distinto cuenta como acierto y como desacuerdo de tipo.
16. **AC6.1.1** junta cinco condiciones. Pedir una prueba por motivo y fijar qué se muestra si se dan
    varias (todas, en un orden fijo). Bordes nuevos: (a) una sesión con 0 hallazgos se consolida, y el
    reporte dice «Sin sugerencias de revisión»; (b) un hallazgo incremental que llega entre abrir el
    diálogo y confirmar hace que la API responda `409` al confirmar. **AC6.1.3**: comparar el Markdown con
    un archivo dorado de una sesión *fixture* con reloj fijo, además de comprobar cada sección.
17. **AC5.5.2: la exclusión puede servir de puerta trasera.** Controles nuevos: (a) observaciones con
    «miente» entre «» que **no** es ninguna de las dos citas ⇒ el escaneo falla; (b) una reformulación del
    analista con «miente» no lo hace fallar y el reporte la muestra en el bloque del analista
    (Seguimiento 4).
18. **AC13.3.1: falta el control positivo.** Por cada caso, el mismo archivo corregido arranca y pasa la
    sonda. «Sin su valor» se prueba con un valor *canary* que no aparece en el log.
19. **AC13.2.1:** reordenar claves o cambiar el formato del YAML no cambia `config_sha256` (forma
    canónica), y el valor de una clave de API nunca entra en la huella.
20. **AC10.8.1:** el «25 % + 1» no tiene denominador. Fijar el *fixture* (p. ej., 5 de 20 descartados no
    alerta, 6 de 20 alerta) cuando NFR Requirements fije la ventana.
21. **AC12.1.3** suma (d): un directorio de salida no escribible ⇒ código ≠ 0.

### C. Contradicción entre requisitos (va a la tabla de precisiones)

22. **NFR12** dice que «las entrevistas del piloto solo se procesan en la máquina local». La pregunta 11,
    FR16.2 y AC14.1.3 las llevan al clúster ZINE. Hay que añadir NFR12 a la fila de la pregunta 11 de la
    tabla de precisiones («el piloto también se procesa en ZINE, empaquetado fuera de Git; solo salen
    cifras»), para no arrastrar la contradicción (`phases/inception.md`).

### D. traceability.json

23. Destinos que faltan: **NFR4** + US10.5 (permutación y consistencia); **NFR10** + US8.1 (*hash*),
    US11.3 (tabla de correspondencia, AC11.3.5) y US9.1 (AC9.1.4, logs); **NFR12** + US14.1 (AC14.1.3);
    **FR1.3** + US2.1, US2.7 y US6.1 (actor y hora de cada acción). **NFR13** sigue como Deferred, con la
    nota «parcial en AC3.4.4 y AC11.3.3 (100 % de ramas)». No hay ningún FR/NFR sin destino, y los
    retirados están bien marcados N/A.

## Positions

- AGREE: el formato general, los niveles [N0]..[N3]/[Manual]/[ZINE] y la convención de rechazos con «0 filas» hacen comprobables casi todos los criterios.
- AGREE: separar las variantes deterministas y `[N2]` de cada criterio que depende de un modelo (AC3.3.1, AC3.4.5, AC10.5.1).
- AGREE: US14.1 como historia de medición sin umbrales; los umbrales los fija NFR Requirements.
- OBJECT: US11.3 no tiene la prueba del *payload* saliente ni el fallo cerrado en N1 que exige AUTONOMIA-04 (puntos 1–2); es bloqueante.
- OBJECT: AC11.3.3 y AC3.2.1 no tienen `codigo` para el fallo del anonimizador, así que «termina en error» queda abierto (punto 3).
- OBJECT: US3.4 no prueba que la regla del piloto rechace lo que no son espacios (mayúsculas, tildes, puntuación, « […] » entre turnos) (punto 5).
- OBJECT: AC2.7.3 es una opinión sin umbral (AUTONOMIA-02), y AC2.7.2 no protege la decisión humana cuando el modo final repite un hallazgo ya decidido (puntos 7–8).
- OBJECT: AC14.1.4 compara SHA-256 de salidas que incluyen `fecha` y nunca coincidirá (punto 12).
- OBJECT: AC12.3.4 no da una compuerta binaria (código de salida y `pasa` por métrica), así que el nivel 2 no puede bloquear el PR (punto 15).
- OBJECT: NFR12 contradice la pregunta 11, FR16.2 y AC14.1.3 sobre procesar el piloto en ZINE; hay que registrarlo en la tabla de precisiones (punto 22).
- OBJECT: AC2.6.2 usa `422` donde la convención fija `415` para el formato (punto 10).
