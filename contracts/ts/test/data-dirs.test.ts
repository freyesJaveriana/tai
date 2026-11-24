// F-05: los directorios de datos que registra TypeScript son los del `include` de la rueda de Python.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { CONTRACTS_ROOT, cargarRegistry } from "./support";

/** Los grupos de captura de cada coincidencia, como texto. */
function nombres(texto: string, patron: RegExp): string[] {
  return [...texto.matchAll(patron)].flatMap((m) => (m[1] === undefined ? [] : [m[1]]));
}

/** Entradas `"/nombre"` del `include` de `[tool.hatch.build.targets.wheel]`, sin `vendor`. */
function incluidosDePyproject(): string[] {
  const texto = readFileSync(join(CONTRACTS_ROOT, "pyproject.toml"), "utf-8");
  const bloque = /\[tool\.hatch\.build\.targets\.wheel\]\s*\ninclude = \[([^\]]*)\]/.exec(texto);
  expect(bloque, "no se encontró el include de la rueda en pyproject.toml").not.toBeNull();
  return nombres(bloque?.[1] ?? "", /"\/([a-z_]+)"/g)
    .filter((nombre) => nombre !== "vendor")
    .sort();
}

describe("directorios de datos frente a pyproject.toml", () => {
  it("DATA_DIRS de registry.ts es el include de la rueda sin vendor ni src", async () => {
    const { DATA_DIRS } = await cargarRegistry();
    const esperados = incluidosDePyproject().filter((nombre) => nombre !== "src");
    expect(esperados.length).toBeGreaterThan(10);
    expect([...DATA_DIRS].sort()).toEqual(esperados);
  });

  it("DIRECTORIOS de gen-types.mjs es DATA_DIRS sin api (C1 se añade aparte)", async () => {
    const { DATA_DIRS } = await cargarRegistry();
    const script = readFileSync(join(CONTRACTS_ROOT, "ts", "scripts", "gen-types.mjs"), "utf-8");
    const bloque = /const DIRECTORIOS = \[([^\]]*)\]/.exec(script);
    expect(bloque, "no se encontró DIRECTORIOS en gen-types.mjs").not.toBeNull();
    const lista = nombres(bloque?.[1] ?? "", /"([a-z_]+)"/g).sort();
    expect(lista).toEqual([...DATA_DIRS].filter((d) => d !== "api").sort());
  });
});
