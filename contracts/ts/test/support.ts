// Ayudas comunes de las pruebas de la mitad TypeScript (espejo de tests/helpers.py).
//
// Un módulo de `src/` que aún no existe es un fallo con su motivo, no un error de importación sin
// capturar (mismo criterio que `importar_o_fallar` de la mitad Python): el rojo dice qué falta.
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { expect } from "vitest";

export const CONTRACTS_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

export async function importarOFallar<T>(nombre: string, importar: () => Promise<T>): Promise<T> {
  try {
    return await importar();
  } catch (error) {
    return expect.fail(`módulo ausente o roto: src/${nombre}.ts: ${String(error)}`);
  }
}

export const cargarLoaders = () => importarOFallar("loaders", () => import("../src/loaders"));
export const cargarRegistry = () => importarOFallar("registry", () => import("../src/registry"));
export const cargarCanonical = () => importarOFallar("canonical", () => import("../src/canonical"));

export function leerTexto(relativa: string): string {
  return readFileSync(join(CONTRACTS_ROOT, relativa), "utf-8");
}

// Directorios que no son contratos del paquete (checks/_recorrido.py: DIRECTORIOS_SALTADOS).
const SALTADOS = new Set([
  "vendor",
  "ts",
  "node_modules",
  ".venv",
  "build",
  "__pycache__",
  ".mypy_cache",
  ".ruff_cache",
  ".pytest_cache",
  ".hypothesis",
]);
const SUFIJOS = [".yaml", ".yml", ".json"];

/** Cada archivo de datos bajo una carpeta `fixtures/` de `contracts/`, como ruta relativa con `/`. */
export function archivosDeFixtures(): string[] {
  const salida: string[] = [];
  const recorrer = (carpeta: string): void => {
    for (const entrada of readdirSync(carpeta, { withFileTypes: true }).sort((a, b) =>
      a.name < b.name ? -1 : 1,
    )) {
      const ruta = join(carpeta, entrada.name);
      if (entrada.isDirectory()) {
        if (!SALTADOS.has(entrada.name)) recorrer(ruta);
      } else if (SUFIJOS.some((sufijo) => entrada.name.endsWith(sufijo))) {
        const partes = relative(CONTRACTS_ROOT, ruta).split(sep);
        if (partes.slice(0, -1).includes("fixtures")) salida.push(partes.join("/"));
      }
    }
  };
  recorrer(CONTRACTS_ROOT);
  return salida;
}
