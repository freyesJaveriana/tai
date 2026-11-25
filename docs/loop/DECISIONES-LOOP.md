# Decisiones del loop de agentes

Entregable del módulo 6 (cambio 04, DT30). Responde las preguntas de la guía (§13) y una quinta del TG.
Se llena a medida que corre el loop; nada del piloto del TG entra aquí (el repositorio es público).

Datos de U1 `contracts` (Bolt B1, 2026-11-23 a 2026-11-25):
- 82 pasos de plan;
- 33 tareas del plan y 12 correctivas, en los PR #5 a #41;
- cerca de 39 h de reloj.

Las decisiones citadas (E-*, P-*) están en `aidlc/…/construction/contracts/code-generation/decisiones-humano.md`.

## 1. Un empujón de vuelta arbitrado

**U01-T29**, que extiende a todo el repositorio la guardia de identificadores del clúster.

**El empujón.** El codificador se detuvo dos veces sin tocar nada, como mandaba la tarea:
- **Primera parada:** la guardia ampliada saltaba sobre informes de `docs/loop/revisiones/`, que son copias literales. La tarea no le permitía editarlos ni eximir una carpeta.
- **Segunda parada, en la ronda 2:** la regla corregida detectaba las sondas inventadas que el revisor había escrito tal cual en su informe de la ronda 1.

**El arbitraje.** Sin reabrir la tarea:
- **P-T29-1.** El orquestador abrevió los dos restos reales de los informes, con una nota, y añadió `hpchead99` a la lista cerrada de nombres inventados.
- **P-T29-2.** Los informes persistidos describen con palabras las sondas que la guardia detecta, y desde entonces los encargos al revisor piden citar cada sonda por el nombre de su caso.

En los dos casos se mantuvo la regla de no eximir ninguna carpeta.

**Después.** El mismo patrón se repitió en U01-T30 y se resolvió con el mismo criterio (P-T30-2):
- se eximieron números inventados exactos, no archivos;
- la sigla `CC` quedó restringida a palabra suelta, para no saltar en las URL de `uv.lock`.

## 2. La tarea de más rondas y su defecto de especificación

**U01-T15** (guardias de C1 y de los límites) necesitó **5 rondas**, como T12 y T13. El defecto no estaba en el código del codificador sino en la especificación.
- Las guardias, escritas en rojo primero, encontraron defectos reales en contratos ya fusionados. El más grave: C2 llevaba el texto de los turnos sin tope, a través de C6 (ronda 2, F-01).
- El plan suponía que esos contratos estaban bien y que T15 solo los vigilaría.

El humano decidió E-10 a E-18. Dos tareas correctivas de contrato los arreglaron:
- **T15b:** C1, C5, C19 y C25;
- **T15c:** el tope de C2.

T15 rebasó sobre cada una. La lección para el modo liviano: una guardia que se escribe en rojo después de los contratos que vigila debe planearse junto con una ronda de corrección de esos contratos.

## 3. Un hallazgo del revisor que el autor no habría visto

**U01-T29, ronda 1, F-01 (ROJO).** La regla nueva del destino de `scp` terminaba en `:(?![\\/])` para no confundir una unidad de Windows (`C:\`) con un host. Esa misma exclusión descartaba todo `host:/ruta`, que es la forma más común de un destino `scp`.

El control negativo del codificador solo probaba destinos relativos (`host:base/`), así que pasaba en verde. El revisor lo encontró con sus propias sondas, `c-f06-abs`, `c-f06-usuario-abs` y `c-f06-otro-ps1-abs`, todas con nombres inventados.

En la misma ronda encontró que un host escrito como IP tampoco se detectaba (F-02). La ronda 2 corrigió las dos cosas.

Un caso parecido es **U01-T30, ronda 1, F-01**: un número inventado de la lista de exentos tapaba a un número vecino, por un cuantificador perezoso. Las pruebas del autor no tenían dos números seguidos.

## 4. Costo en tokens de una ola en paralelo frente a la serie

Medición del humano en el host, 2026-11-25 (cambio 06, §1):

```
python 03-desarrollo\medir_uso.py veridicus --desde 2026-11-23T17:00
  opus-5-5     salida   2.75 M  entrada+caché    690.7 M  USD      313
  sonnet-5-5   salida   3.21 M  entrada+caché    901.2 M  USD      188
  Total USD equivalentes: 501   horas con actividad: 34
```

**Totales de U1.** Unos 501 USD equivalentes y 34 horas con actividad para 45 tareas (33 del plan y 12 correctivas), con unas 2,4 rondas por tarea:
- ≈ 11 USD por tarea;
- ≈ 6 USD por paso del plan (82 pasos);
- ≈ 0,4 h por paso.

**La herramienta no separa olas.** Mide por modelo y por intervalo, no por ola, así que la comparación es indirecta.
- **Tokens.** Una tarea cuesta lo mismo despachada en paralelo que en serie: el codificador lee el mismo archivo de tarea, el mismo plan y el mismo código, y el revisor corre los mismos criterios. Los tokens dependen de la tarea y de sus rondas, no de cuántas corren a la vez.
- **Reloj.** Las olas de 3 (por ejemplo, T08–T10 y T16–T18) sí acortaron el reloj: las 45 tareas cupieron en unas 34 h con actividad, cuando en serie habrían pedido varias más.
- **El costo de paralelizar.** Fueron las paradas cruzadas. T17 esperó a T17b y T18 a T18b y T18c. Esas esperas, y los rebases que siguieron, añadieron rondas, y cada ronda vuelve a leer el contexto, que es la parte cara: la entrada y la caché son ~1.592 M de tokens, frente a ~6 M de salida.

**Conclusión para el modo liviano (DT31).**
- Paralelizar sirve cuando las tareas de la ola no dependen entre sí. Si una tarea de la ola depende de otra que todavía no se ha fusionado, se gastan tokens en rebases y rondas repetidas.
- El ahorro grande no está en el paralelismo. Está en menos rondas (ML-5), menos tareas por Bolt (ML-3) y menos contexto por ronda (ML-7), porque casi todo el costo es entrada y caché.

## 5. Puntos H1–H5 con AI-DLC 2.10

Se comprobaron con la primera tarea de U1, despachada sola (`docs/loop/README.md` §6), y durante el resto del Bolt.

| # | Qué | Resultado | Ajuste |
|---|---|---|---|
| H1 | El guardia de aprobación del plan deja despachar al `codificador` | Pasa. Con `Approve Plan` registrado, U01-T01 se despachó y escribió en su worktree. Cada cambio del plan (E-1, E-2, E-5, E-6) pidió un nuevo `Approve Plan` antes de seguir | Ninguno |
| H2 | El *hook* de reglas por etapa añade las reglas al despacho del codificador | Pasa en la práctica. Los codificadores aplicaron sin que el encargo las repitiera las reglas de `team.md` y `project.md`: AUTONOMIA, rojo primero, Conventional Commits en español y nada del piloto | Los encargos siguen repitiendo las dos líneas de las reglas comunes (idioma y Bash), porque esas no llegan por el *hook* |
| H3 | `source-manifest.json` declara todo lo que cambió, incluido `docs/loop/` | Pasa, con un ajuste. `source-manifest.json` de U1 declara `docs/loop/`, `.claude/agents/`, las guardias de `scripts/` y los demás archivos del diff de B1 (20a8cc4..eb9d851), salvo `aidlc/`, que es el registro. Se escribió a mano en el cierre, porque el loop no lo genera | En el modo liviano, el orquestador escribe `source-manifest.json` al cerrar cada Bolt, a partir de `git diff --name-only` contra la base |
| H4 | `.worktrees/` no ensucia el árbol | Pasa: `.gitignore:100` ignora `.worktrees/`, y `git status` de la raíz no mostró ningún worktree en 45 tareas | Ninguno |
| H5 | El guardia de alcance del revisor de AI-DLC no toca al `revisor` del loop | Pasa: el `revisor` corrió más de 80 rondas de solo lectura sobre los worktrees sin que el guardia lo bloqueara | Ninguno |
