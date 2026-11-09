# U0X-T0N: <título corto de la tarea>

> **Plantilla.** El orquestador la copia a `docs/loop/tareas/U0X-T0N-<slug>.md` y la llena a partir del `code-generation-plan.md` aprobado; el humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es el mundo entero del codificador.** No va a leer el PRD.

**Unidad:** U0X: `<nombre de la unidad>`   **Bolt:** Bn   **Rama base:** `<tipo>/<slug-del-bolt>`
**Pasos del plan que cubre:** Step N–M de `<ruta del code-generation-plan.md>`
**Historias que implementa:** USx.y (según la trazabilidad del plan)
**Depende de:** `<U0X-T0M, o ninguna>`

---

## Alcance

**Dentro** (una línea, concreta):

> <qué se construye en esta tarea>

**Fuera** (lo que el codificador debe rechazar aunque lo vea roto):

- <cosa que parece relacionada y no lo es>
- <pasos del plan que pertenecen a otra tarea>

---

## Archivos de contexto

Rutas, no contenido:

- `<intent>/construction/<unidad>/code-generation/code-generation-plan.md` (pasos citados y Testing Contract)
- `<intent>/construction/<unidad>/code-generation/unit-test-instructions.md`
- `<intent>/construction/<unidad>/functional-design/…` (solo los archivos que la tarea necesite)
- `<intent>/inception/contract-design/contract-summary.md` (si toca un contrato)
- `<cualquier otro archivo que el codificador necesite leer>`

---

## Criterios de aceptación

Cada uno con **su comando**, tomado de la `Verificación:` del paso del plan o de `unit-test-instructions.md`. El revisor los corre él mismo.

- [ ] **CA-1**: <qué debe ser cierto>
  ```bash
  <comando exacto, acotado a la unidad>
  ```
  Esperado: <qué salida demuestra que pasa>

- [ ] **CA-2**: <qué debe ser cierto>
  ```bash
  <comando exacto>
  ```
  Esperado: <qué salida demuestra que pasa>

> **Sin comando, la tarea no está lista.** Si el comportamiento cambia estado, el criterio nombra la **lectura de vuelta con la herramienta real**.

---

## Plan de pruebas

Qué pruebas se escriben **en esta tarea**, y en qué orden según el Testing Contract:

- <prueba que va primero y se ve fallar (guardias, contratos de datos)>
- <prueba de la capa, después de implementarla>

---

## Reglas de la app que aplican

- <IDs de `team.md` que toca la tarea, p. ej. AUTONOMIA-04 o AUTONOMIA-05, con la prueba que las demuestra>
- Solo datos sintéticos.

---

## Notas

- Archivos que se **modifican en su sitio**: `<lista>`.
- <trampas conocidas o decisiones ya tomadas>
