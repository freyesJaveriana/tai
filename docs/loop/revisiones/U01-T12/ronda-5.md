# Ronda 5: U01-T12

VEREDICTO: VERDE

Revisión de 4a4e47f contra f513f64. El código y las pruebas son los de c012dcd.

- Los seis criterios de aceptación pasan:
  - CA-1: 347 passed.
  - CA-3: 348 sentencias y 190 ramas, todas cubiertas (100 %).
  - CA-5: `mypy --strict` y `ruff` limpios.
  - CA-6: 0 apariciones.
- F-01 queda cerrado. Los dos rojos de la bitácora se reproducen igual:
  - 10 fallos y 333 aprobados, con el código de f513f64 y las pruebas de c012dcd;
  - 63 fallos y 260 aprobados, con las pruebas de f513f64 contra 105adac.
- Mutación de la lógica nueva: mueren los 9 mutantes, así que F-02 y F-04 quedan cerrados.
- Sin regresiones de H-02 ni de H-03.

## AMARILLO

- `test_report_closed.py:1640-1648` es la prueba de la limitación de ReDoS. Fija una debilidad conocida y busca un comentario en el código, así que es decorativa y falla si alguien endurece la regla. Se propone pasarla a `xfail(strict=True)` o quitar la aserción. No bloquea; la limitación queda registrada en K-24.

## Candidatas

Ya registradas: K-22 y K-23.
