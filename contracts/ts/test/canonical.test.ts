// Huella JCS (RFC 8785) igual que en Python (NFR10.15, BR9.7, K-62).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { CONTRACTS_ROOT, cargarCanonical, cargarLoaders } from "./support";

interface Vector {
  id: string;
  sha256: string;
  value: unknown;
}

async function vectores(): Promise<Vector[]> {
  const { loadFile } = await cargarLoaders();
  const documento = loadFile(join(CONTRACTS_ROOT, "fixtures", "jcs-vectors.json")) as {
    vectors: Vector[];
  };
  return documento.vectors;
}

describe("canonical.ts: vectores JCS de fixtures/jcs-vectors.json", () => {
  it("son 200 y cada huella recalculada coincide con la esperada", async () => {
    const { sha256Jcs } = await cargarCanonical();
    const lista = await vectores();
    expect(lista).toHaveLength(200);
    const distintos = lista
      .filter((vector) => sha256Jcs(vector.value) !== vector.sha256)
      .map((vector) => vector.id);
    expect(distintos).toEqual([]);
  });

  it("K-62: el vector con menos cero conserva -0 al leerse y da la misma huella que Python", async () => {
    const { sha256Jcs, canonicalString } = await cargarCanonical();
    const vector = (await vectores()).find((v) => v.id === "vec-002");
    expect(vector).toBeDefined();
    const valor = (vector as Vector).value as { limite: number };
    // Sin esta comprobación la prueba pasaría en vacío si el lector hubiera perdido el signo.
    expect(Object.is(valor.limite, -0)).toBe(true);
    expect(canonicalString(valor)).toBe('{"limite":0}');
    expect(sha256Jcs(valor)).toBe(
      "b17af95d767166786c64f5af90f8efbc58a4febcba17955356c3a85964bfbc27",
    );
  });

  it("cada número límite del fixture está presente (1e21, -0, 5e-324, 0.1)", async () => {
    const texto = JSON.stringify(await vectores(), (_, v: unknown) => (Object.is(v, -0) ? "-0" : v));
    for (const marca of ["1e+21", '"-0"', "5e-324", "0.1"]) {
      expect(texto).toContain(marca);
    }
  });
});

describe("canonical.ts: configuración efectiva (BR9.7)", () => {
  it("la huella del payload es la de effective-config.valid.sha256 y la del perfil es profile_sha256", async () => {
    const { sha256Jcs } = await cargarCanonical();
    const { loadFile } = await cargarLoaders();
    const fixture = loadFile(
      join(CONTRACTS_ROOT, "profiles", "fixtures", "effective-config.valid.json"),
    ) as { payload: { profile: unknown; profile_sha256: string } };
    const esperada = readFileSync(
      join(CONTRACTS_ROOT, "profiles", "fixtures", "effective-config.valid.sha256"),
      "utf-8",
    ).trim();
    expect(sha256Jcs(fixture.payload)).toBe(esperada);
    expect(sha256Jcs(fixture.payload.profile)).toBe(fixture.payload.profile_sha256);
  });
});

describe("canonical.ts: forma canónica", () => {
  it("ordena las claves por unidades UTF-16 y no deja espacios", async () => {
    const { canonicalString } = await cargarCanonical();
    expect(canonicalString({ b: 1, a: [true, null], "é": "x" })).toBe('{"a":[true,null],"b":1,"é":"x"}');
  });

  it("escribe los números como RFC 8785", async () => {
    const { canonicalString } = await cargarCanonical();
    expect(canonicalString([1e21, 5e-324, 0.1, 100, 1.5])).toBe("[1e+21,5e-324,0.1,100,1.5]");
  });

  it("rechaza lo que JSON no tiene: NaN, Infinity y undefined", async () => {
    const { canonicalString } = await cargarCanonical();
    expect(() => canonicalString({ a: Number.NaN })).toThrow(/finito/);
    expect(() => canonicalString([Number.POSITIVE_INFINITY])).toThrow(/finito/);
    expect(() => canonicalString(undefined)).toThrow(/JSON/);
  });

  it("la huella es SHA-256 en hexadecimal minúscula de 64 caracteres", async () => {
    const { sha256Jcs } = await cargarCanonical();
    expect(sha256Jcs({})).toMatch(/^[0-9a-f]{64}$/);
  });
});
