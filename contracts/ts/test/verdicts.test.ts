// Mismos veredictos que Python sobre los mismos fixtures (NFR10.16, §4.14, T16).
//
// Las dos mitades recorren `contracts/**/fixtures/` y comparan su resultado con el `expectation` que
// declara cada fixture; si las dos coinciden con lo declarado, coinciden entre sí. Un fixture que esta
// mitad no sabe validar es un fallo, no un salto.
import { describe, expect, it } from "vitest";
import { join } from "node:path";
import {
  CONTRACTS_ROOT,
  archivosDeFixtures,
  cargarLoaders,
  cargarRegistry,
} from "./support";

const BASE = "https://veridicus.invalid/";

// Contrato del fixture -> (archivo del paquete, puntero dentro de él). Es la tabla `ESQUEMAS` de
// checks/fixture_coverage.py: una tabla en cada mitad, y la prueba de abajo falla si un fixture nombra
// un contrato que esta tabla no tiene (P-T20-6).
const ESQUEMAS: Record<string, readonly [string, string]> = {
  "C6.entrada": ["analyzer/v1/entrada.schema.json", ""],
  "C6.salida": ["analyzer/v1/salida.schema.json", ""],
  C7: ["integrity/review-suggestion.v2.json", ""],
  "C18.effective-config": ["profiles/effective-config.v1.yaml", ""],
  "C18.profile-base": ["profiles/profile-base.schema.v1.yaml", ""],
  "C18.profiles": ["profiles/profiles.schema.v1.yaml", ""],
  C19: ["cli/report.schema.v2.yaml", ""],
  "model-call": ["model_calls/model-call.v1.yaml", ""],
  "C21.request": [
    "api/anonymizer-proxy.v1.yaml",
    "#/paths/~1v1~1generate/post/requestBody/content/application~1json/schema",
  ],
};
// Familia de mensajes de cola -> AsyncAPI que los declara.
const COLAS: Record<string, string> = {
  C2: "queues/runs.v2.yaml",
  C3: "queues/results.v2.yaml",
  C5: "queues/speech.v2.yaml",
};

// Fixtures que solo valida Python, por su forma YAML, con su motivo. Hoy ninguno lo necesita: todo
// fixture lleva un `payload` compatible con JSON. Un fixture nuevo de forma YAML se anota aquí con su
// motivo y su prueba en Python; no se omite sin más.
const SOLO_PYTHON: Record<string, string> = {};

// Archivos de `fixtures/` que no son fixtures de contrato (no llevan `contract` y `expectation`).
const NO_SON_FIXTURES = new Set(["fixtures/synthetic-names.yaml", "fixtures/jcs-vectors.json"]);

const RECUENTO_DE_PYTHON = 67;

interface Fixture {
  fixture_id: string;
  contract: string;
  synthetic: boolean;
  expectation: "accept" | "reject";
  reject_reason?: string;
  payload: unknown;
}

const esFixture = (documento: unknown): documento is Fixture =>
  typeof documento === "object" &&
  documento !== null &&
  "contract" in documento &&
  "expectation" in documento;

async function leer(archivo: string): Promise<unknown> {
  const { loadFile } = await cargarLoaders();
  return loadFile(join(CONTRACTS_ROOT, archivo));
}

type Memo = Awaited<ReturnType<typeof montar>>;
let memo: Promise<Memo> | undefined;

async function montar() {
  const modulo = await cargarRegistry();
  return { modulo, registro: modulo.buildRegistry(), uris: new Map<string, string>() };
}

async function validadorDe(contrato: string) {
  const { modulo, registro, uris } = await (memo ??= montar());
  const familia = contrato.split(".")[0] ?? contrato;
  let archivo: string;
  let puntero: string;
  if (contrato in ESQUEMAS) {
    [archivo, puntero] = ESQUEMAS[contrato] as readonly [string, string];
  } else if (familia in COLAS && contrato.includes(".")) {
    archivo = COLAS[familia] as string;
    puntero = `#/components/messages/${contrato.split(".").slice(1).join(".")}/payload`;
  } else {
    return expect.fail(`contrato desconocido para esta mitad: ${contrato}`);
  }
  const clave = `${archivo}${puntero}`;
  if (!uris.has(clave)) {
    const documento = await leer(archivo);
    const id =
      typeof documento === "object" && documento !== null && "$id" in documento
        ? (documento as { $id: unknown }).$id
        : undefined;
    // Un esquema con `$id` ya está en el registro; un OpenAPI o AsyncAPI se valida por su puntero.
    uris.set(
      clave,
      typeof id === "string"
        ? new URL(id, BASE).href
        : modulo.registerFragment(registro, archivo, documento, puntero),
    );
  }
  return modulo.validatorFor(registro, uris.get(clave) as string);
}

const archivos = archivosDeFixtures();

describe("verdicts: la lista de fixtures", () => {
  it("hay fixtures, y cada archivo de fixtures/ es un fixture o está nombrado como no-fixture", async () => {
    expect(archivos.length).toBeGreaterThan(0);
    const sueltos: string[] = [];
    let fixtures = 0;
    for (const archivo of archivos) {
      if (esFixture(await leer(archivo))) fixtures += 1;
      else if (!NO_SON_FIXTURES.has(archivo)) sueltos.push(archivo);
    }
    expect(sueltos).toEqual([]);
    // F-04: recuento de Python (`fixtures(Path('.'))` de checks/fixture_coverage.py) fijado a mano; un
    // fixture nuevo exige subirlo aquí y que Python lo cuente igual.
    expect(fixtures).toBe(RECUENTO_DE_PYTHON);
    expect(archivos).toHaveLength(RECUENTO_DE_PYTHON + NO_SON_FIXTURES.size);
    // El recuento de esta mitad se compara a mano con el de Python en la bitácora (CA-3).
    console.info(`verdicts: ${fixtures} fixtures de contrato en ${archivos.length} archivos`);
  });

  it("la lista de fixtures que solo valida Python está vacía o cada entrada lleva su motivo", () => {
    for (const [archivo, motivo] of Object.entries(SOLO_PYTHON)) {
      expect(archivos, archivo).toContain(archivo);
      expect(motivo.length, archivo).toBeGreaterThan(10);
    }
  });
});

describe("verdicts: cada fixture se acepta o se rechaza como declara", () => {
  const propios = archivos.filter((a) => !(a in SOLO_PYTHON) && !NO_SON_FIXTURES.has(a));

  it.each(propios)("%s", async (archivo) => {
    const fixture = await leer(archivo);
    expect(esFixture(fixture), `${archivo}: no tiene la forma de un fixture`).toBe(true);
    const f = fixture as Fixture;
    expect(f.synthetic, `${archivo}: synthetic debe ser true`).toBe(true);
    expect(["accept", "reject"]).toContain(f.expectation);
    if (f.expectation === "reject") expect(f.reject_reason, `${archivo}: falta reject_reason`).toBeTruthy();
    const validar = await validadorDe(f.contract);
    const valido = validar(f.payload);
    const detalle = JSON.stringify(validar.errors?.slice(0, 2) ?? []);
    expect(valido, `${archivo}: esperado ${f.expectation} (${f.reject_reason ?? "sin razón"}) ${detalle}`).toBe(
      f.expectation === "accept",
    );
  });
});
