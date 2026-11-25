// Mensaje del error de «sin red». Vive aparte del setup a propósito: importarlo no sustituye nada,
// así que una prueba que lo use solo ve el bloqueo si `setupFiles` de vitest.config.ts carga el setup.
export const MENSAJE_SIN_RED = "red bloqueada por el setup de las pruebas (NFR10.4)";
