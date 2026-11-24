// Registro de esquemas y carga estricta con ajv (BR1.9, BR12.3, §4.6, §4.14).
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { VERIDICUS_EXTENSIONS } from "../generated/auth-surface";
import { CONTRACTS_ROOT, cargarLoaders, cargarRegistry } from "./support";

const BASE = "https://veridicus.invalid/";
const creadas: string[] = [];

/** Una raíz temporal con `datos/<archivo>` por cada entrada; se borra al terminar. */
function raizCon(archivos: Record<string, string>): string {
  const raiz = mkdtempSync(join(tmpdir(), "veridicus-ts-"));
  creadas.push(raiz);
  for (const [nombre, texto] of Object.entries(archivos)) {
    const destino = join(raiz, "datos", nombre);
    mkdirSync(dirname(destino), { recursive: true });
    writeFileSync(destino, texto, "utf-8");
  }
  return raiz;
}

afterAll(() => {
  for (const raiz of creadas) rmSync(raiz, { recursive: true, force: true });
});

const ESQUEMA = (id: string, resto = ""): string =>
  `{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "${id}", "type": "object"${resto}}`;

describe("registry.ts: los contratos reales", () => {
  it("registra los esquemas del paquete bajo la base .invalid, sin red", async () => {
    const { buildRegistry } = await cargarRegistry();
    const registro = buildRegistry();
    expect(registro.uris.length).toBeGreaterThanOrEqual(9);
    expect(registro.uris.every((uri) => uri.startsWith(BASE))).toBe(true);
    expect(registro.uris).toContain(`${BASE}veridicus/contracts/analyzer/v1/salida`);
    expect(registro.uris).toContain(`${BASE}veridicus/contracts/integrity/review-suggestion/v2`);
  });

  it("BR1.9: cada esquema de contracts/ compila con ajv strict", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const registro = buildRegistry();
    const fallos: string[] = [];
    for (const uri of registro.uris) {
      try {
        validatorFor(registro, uri);
      } catch (error) {
        fallos.push(`${uri}: ${String(error)}`);
      }
    }
    expect(fallos).toEqual([]);
  });

  it("una referencia entre esquemas se resuelve por el $id del destino (BR12.3)", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const registro = buildRegistry();
    const validar = validatorFor(registro, `${BASE}veridicus/contracts/integrity/review-suggestion/v2`);
    // Un objeto vacío no cumple el esquema, y la resolución de `salida#/$defs/cita` no lanza.
    expect(validar({})).toBe(false);
  });
});

describe("registry.ts: carga estricta (BR1.9)", () => {
  it("control negativo: una palabra clave desconocida falla al compilar", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({ "a.schema.json": ESQUEMA("veridicus/t/a", ', "palabraInventada": 1') });
    const registro = buildRegistry(raiz, ["datos"]);
    expect(() => validatorFor(registro, `${BASE}veridicus/t/a`)).toThrow(/unknown keyword/);
  });

  it("una `description` mal escrita deja una clave suelta y falla", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({ "a.schema.json": ESQUEMA("veridicus/t/a", ', "descripton": "texto"') });
    const registro = buildRegistry(raiz, ["datos"]);
    expect(() => validatorFor(registro, `${BASE}veridicus/t/a`)).toThrow(/unknown keyword/);
  });

  it("el esquema bien formado del control compila (el rojo era por la palabra clave)", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({ "a.schema.json": ESQUEMA("veridicus/t/a", ', "description": "texto"') });
    const registro = buildRegistry(raiz, ["datos"]);
    expect(validatorFor(registro, `${BASE}veridicus/t/a`)({})).toBe(true);
  });

  it("unicodeRegExp: un patrón con propiedades Unicode se evalúa como Unicode", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({
      "a.schema.json": `{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "veridicus/t/a", "type": "string", "pattern": "^\\\\p{L}+$"}`,
    });
    const validar = validatorFor(buildRegistry(raiz, ["datos"]), `${BASE}veridicus/t/a`);
    expect(validar("ñandú")).toBe(true);
    expect(validar("a1")).toBe(false);
  });

  it("los formatos date-time y uuid se comprueban (ajv-formats)", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({
      "f.schema.json": `{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "veridicus/t/f", "type": "object", "properties": {"t": {"type": "string", "format": "date-time"}, "u": {"type": "string", "format": "uuid"}}}`,
    });
    const validar = validatorFor(buildRegistry(raiz, ["datos"]), `${BASE}veridicus/t/f`);
    expect(validar({ t: "2026-11-24T10:00:00Z", u: "123e4567-e89b-12d3-a456-426614174000" })).toBe(true);
    expect(validar({ t: "ayer" })).toBe(false);
    expect(validar({ u: "no-es-uuid" })).toBe(false);
  });

  it("allErrors es falso: la validación se detiene en el primer error", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({
      "e.schema.json": `{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "veridicus/t/e", "type": "object", "properties": {"a": true, "b": true}, "required": ["a", "b"]}`,
    });
    const validar = validatorFor(buildRegistry(raiz, ["datos"]), `${BASE}veridicus/t/e`);
    expect(validar({})).toBe(false);
    expect(validar.errors).toHaveLength(1);
  });
});

describe("registry.ts: extensiones x-veridicus-* (§4.6)", () => {
  it("registra exactamente las nueve extensiones de §4.6, ni una más", async () => {
    const { EXTENSIONS, createAjv } = await cargarRegistry();
    expect([...EXTENSIONS].sort()).toEqual([...VERIDICUS_EXTENSIONS].sort());
    const ajv = createAjv();
    for (const nombre of VERIDICUS_EXTENSIONS) expect(ajv.getKeyword(nombre)).not.toBe(false);
    expect(ajv.getKeyword("x-veridicus-version")).toBe(false);
    expect(ajv.getKeyword("x-veridicus-otra")).toBe(false);
  });

  it("un esquema con una extensión de la lista compila", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({ "a.schema.json": ESQUEMA("veridicus/t/a", ', "x-veridicus-limit": "turn_max_chars"') });
    expect(validatorFor(buildRegistry(raiz, ["datos"]), `${BASE}veridicus/t/a`)({})).toBe(true);
  });

  it("un esquema con una extensión que no está en §4.6 falla al compilar", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({ "a.schema.json": ESQUEMA("veridicus/t/a", ', "x-veridicus-otra": true') });
    const registro = buildRegistry(raiz, ["datos"]);
    expect(() => validatorFor(registro, `${BASE}veridicus/t/a`)).toThrow(/x-veridicus-otra/);
  });

  it("E-30: x-veridicus-version solo se admite en la raíz del esquema", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const enRaiz = raizCon({ "a.schema.json": ESQUEMA("veridicus/t/a", ', "x-veridicus-version": "1.0.0"') });
    expect(validatorFor(buildRegistry(enRaiz, ["datos"]), `${BASE}veridicus/t/a`)({})).toBe(true);
    const anidada = raizCon({
      "a.schema.json": ESQUEMA("veridicus/t/a", ', "properties": {"p": {"x-veridicus-version": "1.0.0"}}'),
    });
    const registro = buildRegistry(anidada, ["datos"]);
    expect(() => validatorFor(registro, `${BASE}veridicus/t/a`)).toThrow(/x-veridicus-version/);
  });
});

describe("registry.ts: sin red y URI cerradas (NFR10.4, NFR10.5)", () => {
  it("una referencia a una URI que el registro no tiene falla sin consultar la red", async () => {
    const { buildRegistry, validatorFor } = await cargarRegistry();
    const raiz = raizCon({
      "a.schema.json": ESQUEMA("veridicus/t/a", ', "properties": {"p": {"$ref": "https://example.com/ajeno"}}'),
    });
    const registro = buildRegistry(raiz, ["datos"]);
    expect(() => validatorFor(registro, `${BASE}veridicus/t/a`)).toThrow(/can't resolve reference|ajeno/);
  });
});

describe("registry.ts: reglas del $id (espejo de registry.py)", () => {
  it("una URI repetida es un error que nombra los dos archivos", async () => {
    const { buildRegistry } = await cargarRegistry();
    const { LoadError } = await cargarLoaders();
    const raiz = raizCon({
      "a.schema.json": ESQUEMA("veridicus/t/a"),
      "b.schema.json": ESQUEMA("/veridicus/t/a"),
    });
    expect(() => buildRegistry(raiz, ["datos"])).toThrow(LoadError);
    expect(() => buildRegistry(raiz, ["datos"])).toThrow(/a\.schema\.json.*b\.schema\.json/);
  });

  it.each([
    ["absoluto", "https://otro.example/x"],
    ["con fragmento", "veridicus/t/a#x"],
    ["con consulta", "veridicus/t/a?x=1"],
    ["vacío", ""],
    ["que sale de la base", "../fuera"],
  ])("un $id %s se rechaza", async (_nombre, id) => {
    const { buildRegistry } = await cargarRegistry();
    const { LoadError } = await cargarLoaders();
    const raiz = raizCon({ "a.schema.json": ESQUEMA(id) });
    expect(() => buildRegistry(raiz, ["datos"])).toThrow(LoadError);
  });

  it("un *.schema.json sin $id es un error", async () => {
    const { buildRegistry } = await cargarRegistry();
    const { LoadError } = await cargarLoaders();
    const raiz = raizCon({ "a.schema.json": '{"type": "object"}' });
    expect(() => buildRegistry(raiz, ["datos"])).toThrow(LoadError);
  });

  it("un YAML sin $schema y $id no es un esquema y se ignora; con los dos, sí", async () => {
    const { buildRegistry } = await cargarRegistry();
    const raiz = raizCon({
      "datos.yaml": "a: 1\n",
      "esquema.yaml": "$schema: https://json-schema.org/draft/2020-12/schema\n$id: veridicus/t/y\ntype: object\n",
    });
    expect(buildRegistry(raiz, ["datos"]).uris).toEqual([`${BASE}veridicus/t/y`]);
  });

  it("salta fixtures/ y tests/", async () => {
    const { buildRegistry } = await cargarRegistry();
    const raiz = raizCon({
      "fixtures/a.schema.json": ESQUEMA("veridicus/t/a"),
      "tests/b.schema.json": ESQUEMA("veridicus/t/b"),
      "c.schema.json": ESQUEMA("veridicus/t/c"),
    });
    expect(buildRegistry(raiz, ["datos"]).uris).toEqual([`${BASE}veridicus/t/c`]);
  });

  it("un directorio de datos ausente es un error y no se salta en silencio", async () => {
    const { buildRegistry } = await cargarRegistry();
    const raiz = raizCon({});
    expect(() => buildRegistry(raiz, ["datos"])).toThrow(/datos/);
  });
});

describe("registry.ts: documentos OpenAPI y AsyncAPI por puntero", () => {
  it("valida un mensaje de cola por el puntero a su carga, con referencias a esquemas", async () => {
    const { buildRegistry, registerFragment, validatorFor } = await cargarRegistry();
    const { loadFile } = await cargarLoaders();
    const registro = buildRegistry();
    const documento = loadFile(join(CONTRACTS_ROOT, "queues", "runs.v2.yaml"));
    const puntero = "#/components/messages/RunRequested/payload";
    const uri = registerFragment(registro, "queues/runs.v2.yaml", documento, puntero);
    expect(uri).toBe(`${BASE}_documentos/queues/runs.v2.yaml/components/messages/RunRequested/payload`);
    expect(registerFragment(registro, "queues/runs.v2.yaml", documento, puntero)).toBe(uri);
    expect(validatorFor(registro, uri)({})).toBe(false);
  });

  it("un puntero que no existe o que no apunta a un esquema es un error", async () => {
    const { buildRegistry, registerFragment } = await cargarRegistry();
    const { LoadError } = await cargarLoaders();
    const registro = buildRegistry();
    const documento = { a: { b: [1] } };
    expect(() => registerFragment(registro, "x.yaml", documento, "#/a/c")).toThrow(LoadError);
    expect(() => registerFragment(registro, "x.yaml", documento, "#/a/b")).toThrow(LoadError);
    expect(() => registerFragment(registro, "x.yaml", documento, "a/b")).toThrow(LoadError);
  });
});
