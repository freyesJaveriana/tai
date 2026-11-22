# Requisitos de escalabilidad — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR3, por la lista y la consola).
- **Alcance.** El MVP corre en una sola máquina con una réplica de `session-api` y un solo investigador
  (supuesto de requirements §5). Aquí se fijan el volumen esperado, los topes que lo acotan y qué hacer si
  se superan. No hay autoescalado para U12.

**Insumos.** Preguntas abiertas 1 y 2 del Functional Design (§11); BR2.2, BR2.3 y BR6.5 de rules; C1, C19 y
C25 de contract-summary; NFR-U11-03 (40 muestras), NFR-U11-07 (perfiles) y `performance-requirements.md` de
U11 (llamadas por corrida y modo fragmentado).

## 1. Dimensionamiento de los topes de C25

El tamaño de un reporte C19 lo dominan las llamadas: cada una ocupa unos 280 bytes en JSON compacto y unos
450 con sangría. Son estimaciones de esta etapa; NFR3.11 las comprueba con los *fixtures*.

| Caso | Corridas | Llamadas por corrida | Tamaño estimado |
|---|---|---|---|
| Evaluación de B11 (40 muestras × 3 corridas, `evaluacion-comercial`) | 120 | ~15 (juez y 2 por candidato con permutación) | ~0,8 MB |
| Evaluación con el Escenario A (el doble de corridas) en modo fragmentado (`evaluacion-local-zine`, ventana 60 y solapamiento 20) | 240 | ~30 (hasta 7 ventanas y los candidatos) | **~3,3 MB** (peor caso estimado) |
| Corrida sobre las 10 entrevistas del piloto, modo fragmentado (hasta unas 15 ventanas en la más larga) | 10 | ~55 | ~0,3 MB |

| Cifra | Valor | Por qué |
|---|---|---|
| `research_report_max_bytes` | **8 388 608** (8 MiB) | 2,5 veces el peor caso estimado, para no rechazar una evaluación más grande del conjunto 1.1.0 o una corrida de ZINE sobre más entrevistas. Cabe en la memoria de NFR3.8 |
| `research_report_max_json_depth` | **8** niveles | La profundidad natural de C19 v2 es 5 (raíz → `runs` → corrida → `calls` → llamada). Deja margen para un objeto más en una versión menor sin abrir la puerta a un anidamiento patológico |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR3.9 | nuevo | Volumen de reportes sin paginación. | La lista sin paginar (C1 no pagina) cumple NFR3.4 con **1 000** reportes. El volumen esperado en el TG es de decenas a pocos cientos (evaluaciones de B11, corridas de ZINE y comparaciones de perfiles). Si se pasa de 1 000, la paginación entra por PR de U1 sobre C1 antes del reporte 1 001; mientras tanto, la lista sigue completa y no se trunca en silencio | `perf`, nivel 1 (NFR3.4); consulta de conteo en la revisión de B12 |
| NFR3.10 | nuevo | Concurrencia. | Dos subidas simultáneas del mismo archivo dejan exactamente 1 fila (E8, NFR11.6). Dos subidas simultáneas de archivos distintos de tamaño máximo terminan las dos en `201` dentro de 2 × el p95 de NFR3.2 y dentro de NFR3.8. Una subida en curso no aumenta en más de 200 ms el p95 de `GET /sessions/{id}` con `since` de U4 (NFR3.3 de U4), porque la API y el trabajador son procesos distintos (D11 de U4) | Nivel 1 |
| NFR3.11 | nuevo | Crecimiento del almacenamiento. | El espacio que ocupa un reporte guardado (fila y tablas hijas, con índices, medido como diferencia de `pg_total_relation_size`) es **≤ 1,5 ×** `source_bytes`. Con 1 000 reportes del tamaño típico, la tabla ocupa ≤ 1,5 GiB; Infrastructure Design lo suma al volumen de PostgreSQL. El *fixture* del peor caso estimado mide ≤ 4 MiB (comprueba la estimación de §1) | Nivel 1 |

## 3. Qué se degrada primero

| Señal | Qué pasa | Qué se hace |
|---|---|---|
| Más de 1 000 reportes | La lista tarda más que NFR3.4 | Paginación por PR de U1 (NFR3.9) |
| Un reporte legítimo de más de 8 MiB | `413` `limits.exceeded` | Se sube la cifra por PR de U1 tras medir la memoria (NFR3.8); una variable de entorno solo puede bajarla |
| La memoria del proceso de la API se acerca a su límite | Riesgo de `OOMKilled` durante una subida | Hallazgo que se corrige por PR (NFR3.8); nunca se sube el límite en silencio |
