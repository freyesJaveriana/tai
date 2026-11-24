## Resumen

<!-- Qué cambia y por qué, en pocas líneas. Cita la tarea (U0X-T0N) y el Bolt. -->

## Evidencia

<!-- team.md: el código y la infraestructura entran solo por PR con evidencia. Pega la salida del
comando de verificación de cada tarea, producida en esta rama y sin recortar. -->

| Tarea o criterio | comando de verificación | Resultado |
|---|---|---|
| | | |

## Cambios en `contracts/security-surface.json`

<!-- La huella de seguridad la regenera un humano con --write; la CI nunca la escribe (AUTONOMIA-01).
Si este PR no la toca, escribe «Sin cambios». Si la toca, justifica cada diferencia: -->

- [ ] Sin cambios en `contracts/security-surface.json`.
- [ ] La huella cambió y cada diferencia está justificada abajo (sección afectada, qué cambió, por qué es seguro).

Justificación:

## Reglas de la app

- [ ] Ningún dato del piloto del TG: solo transcripciones sintéticas.
- [ ] Ningún valor de `Secret`, `.env`, `kubeconfig` ni clave privada.
- [ ] Ningún comando de este PR aplica cambios al clúster (AUTONOMIA-01).
- [ ] Ningún umbral (cobertura, rendimiento, configuración de pruebas) se bajó para que una compuerta pase.

## Revisión

<!-- Apruebas tú, apoyado en la revisión del agente y en la evidencia de arriba. -->
