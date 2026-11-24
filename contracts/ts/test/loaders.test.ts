// Carga estricta de YAML y JSON (D5, BR1.9; espejo de tests/test_loaders.py).
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { CONTRACTS_ROOT, cargarLoaders, leerTexto } from "./support";

const ruta = (relativa: string): string => join(CONTRACTS_ROOT, relativa);

describe("loaders.ts: YAML", () => {
  it("lee un documento YAML 1.2 con anidamiento, listas y escalares", async () => {
    const { loadYamlText } = await cargarLoaders();
    const valor = loadYamlText("a: 1\nb: [x, y]\nc:\n  d: true\n  e: ~\n");
    expect(valor).toEqual({ a: 1, b: ["x", "y"], c: { d: true, e: null } });
  });

  it("una clave repetida es un error que nombra la clave", async () => {
    const { loadYamlText, LoadError } = await cargarLoaders();
    expect(() => loadYamlText("a: 1\na: 2\n")).toThrow(LoadError);
    expect(() => loadYamlText("a: 1\na: 2\n")).toThrow(/a/);
  });

  it("una clave repetida en un nivel anidado también es un error", async () => {
    const { loadYamlText, LoadError } = await cargarLoaders();
    expect(() => loadYamlText("x:\n  k: 1\n  k: 2\n")).toThrow(LoadError);
  });

  it("una etiqueta de objeto desconocida se rechaza", async () => {
    const { loadYamlText, LoadError } = await cargarLoaders();
    expect(() => loadYamlText("a: !!python/object:os.system x\n")).toThrow(LoadError);
  });

  it("una clave que no es texto se rechaza", async () => {
    const { loadYamlText, LoadError } = await cargarLoaders();
    expect(() => loadYamlText("1: uno\n")).toThrow(LoadError);
  });

  it("un YAML mal formado es un LoadError y no otra excepción", async () => {
    const { loadYamlText, LoadError } = await cargarLoaders();
    expect(() => loadYamlText("a: [1, 2\n")).toThrow(LoadError);
  });
});

describe("loaders.ts: JSON", () => {
  it("lee un documento JSON", async () => {
    const { loadJsonText } = await cargarLoaders();
    expect(loadJsonText('{"a": [1, 2.5, null, "z"]}')).toEqual({ a: [1, 2.5, null, "z"] });
  });

  it("conserva el menos cero que escribe un fixture (K-62)", async () => {
    const { loadJsonText } = await cargarLoaders();
    const valor = loadJsonText('{"limite": -0.0}') as { limite: number };
    expect(Object.is(valor.limite, -0)).toBe(true);
  });

  it("una clave repetida en JSON es un error", async () => {
    const { loadJsonText, LoadError } = await cargarLoaders();
    expect(() => loadJsonText('{"a": 1, "a": 2}')).toThrow(LoadError);
  });

  it("NaN e Infinity no son JSON y se rechazan", async () => {
    const { loadJsonText, LoadError } = await cargarLoaders();
    expect(() => loadJsonText('{"a": NaN}')).toThrow(LoadError);
    expect(() => loadJsonText('{"a": Infinity}')).toThrow(LoadError);
  });

  it("un JSON mal formado es un LoadError", async () => {
    const { loadJsonText, LoadError } = await cargarLoaders();
    expect(() => loadJsonText("{")).toThrow(LoadError);
  });
});

describe("loaders.ts: archivos", () => {
  it("lee un archivo YAML y uno JSON de contracts/ por su sufijo", async () => {
    const { loadFile } = await cargarLoaders();
    const yaml = loadFile(ruta("limits.v1.yaml")) as Record<string, unknown>;
    expect(typeof yaml).toBe("object");
    const json = loadFile(ruta("security-surface.json")) as Record<string, unknown>;
    expect(typeof json).toBe("object");
  });

  it("un sufijo que no es .yaml, .yml ni .json es un error", async () => {
    const { loadFile, LoadError } = await cargarLoaders();
    expect(() => loadFile(ruta("vendor/SHA256SUMS"))).toThrow(LoadError);
  });

  it("un archivo ausente es un LoadError con su ruta", async () => {
    const { loadFile, LoadError } = await cargarLoaders();
    expect(() => loadFile(ruta("no-existe.yaml"))).toThrow(LoadError);
  });
});

describe("loaders.ts: C8 (vocabulario prohibido)", () => {
  it("el vocabulario del paquete se carga y no repite términos", async () => {
    const { loadFile } = await cargarLoaders();
    const c8 = loadFile(ruta("integrity/forbidden-vocabulary.v2.yaml")) as { terms: string[] };
    expect(c8.terms.length).toBeGreaterThan(0);
    expect(new Set(c8.terms).size).toBe(c8.terms.length);
  });

  it("un vocabulario con la clave `terms` repetida se rechaza (clave repetida en loaders.ts)", async () => {
    const { loadYamlText, LoadError } = await cargarLoaders();
    const texto = leerTexto("integrity/forbidden-vocabulary.v2.yaml");
    expect(() => loadYamlText(`${texto}\nterms:\n  - mentiroso\n`)).toThrow(LoadError);
  });
});
