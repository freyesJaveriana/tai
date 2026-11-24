// Registro de esquemas de los contratos con ajv (functional-spec §4.2, BR1.9, BR12.3; §4.14).
//
// Espejo de registry.py: recorre los `*.schema.json` y todo `.yaml`, `.yml` o `.json` cuyo documento
// raíz declare `$schema` y `$id` (fuera de `fixtures/` y `tests/`) y registra cada uno bajo
// `https://veridicus.invalid/` más su `$id`, sin tocar el archivo (el ajv recibe una copia). Toda
// referencia entre esquemas usa el `$id` del destino como ruta absoluta. El dominio `.invalid` está
// reservado y ajv no tiene cargador de URI: una referencia que el registro no tiene falla al compilar,
// sin red (NFR10.4, NFR10.5).
//
// `vendor/` no se registra: los meta-esquemas de 2020-12 ya vienen dentro de `Ajv2020` y registrarlos
// repetiría su `$id` (P-T20-3).
import { Ajv2020, type ValidateFunction } from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { VERIDICUS_EXTENSIONS } from "../generated/auth-surface";
import { LoadError, loadFile } from "./loaders";

export const BASE_URI = "https://veridicus.invalid/";
export const CONTRACTS_ROOT = fileURLToPath(new URL("../../", import.meta.url));
// Los directorios de datos del paquete (`pyproject.toml`, `tool.hatch.build.targets.wheel.include`),
// sin `vendor/` (P-T20-3).
export const DATA_DIRS: readonly string[] = [
  "analyzer",
  "api",
  "cli",
  "errors",
  "format",
  "health",
  "integrity",
  "metrics",
  "model_calls",
  "profiles",
  "queues",
  "transcript",
  "ui",
];
const DIRECTORIOS_SALTADOS = new Set(["fixtures", "tests"]);
const SUFIJOS_DE_DATOS = [".yaml", ".yml", ".json"];
const SUFIJO_DE_ESQUEMA = ".schema.json";

/** Las extensiones `x-veridicus-*` de §4.6, y ninguna más (NFRD-U1-03). */
export const EXTENSIONS: readonly string[] = VERIDICUS_EXTENSIONS;

export interface Registry {
  readonly ajv: Ajv2020;
  /** URI absoluta de cada esquema registrado, en orden de archivo. */
  readonly uris: string[];
  /** URI de cada documento (OpenAPI, AsyncAPI) registrado para validar por puntero. */
  readonly documentos: Set<string>;
}

/** Un ajv 2020-12 estricto, con formatos y solo las extensiones de §4.6. */
export function createAjv(): Ajv2020 {
  const ajv = new Ajv2020({
    strict: true,
    // E-37 (2026-11-24): `strict: true` activa también `strictRequired` y `strictTypes`, que rechazan
    // JSON Schema 2020-12 válido y aceptado por Python: un `required` dentro de `then` o `not` cuyas
    // `properties` están en el esquema padre (C6, C7, C19) y un `required` sin `type` en el mismo
    // nivel (C18). Los dos se apagan; siguen activos `strictSchema` (palabra clave desconocida),
    // `strictNumbers`, `strictTuples` y la lista cerrada de extensiones `x-veridicus-*` (BR1.9).
    strictRequired: false,
    strictTypes: false,
    allErrors: false,
    unicodeRegExp: true,
    validateFormats: true,
  });
  addFormats(ajv);
  // Anotaciones sin validación: sus valores los comprueban las guardias de la mitad Python.
  for (const keyword of EXTENSIONS) ajv.addKeyword({ keyword });
  return ajv;
}

function* archivosDeDatos(carpeta: string): Generator<string> {
  const entradas = readdirSync(carpeta, { withFileTypes: true }).sort((a, b) =>
    a.name < b.name ? -1 : 1,
  );
  for (const entrada of entradas) {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) {
      if (!DIRECTORIOS_SALTADOS.has(entrada.name)) yield* archivosDeDatos(ruta);
    } else if (SUFIJOS_DE_DATOS.some((sufijo) => entrada.name.endsWith(sufijo))) {
      yield ruta;
    }
  }
}

type Objeto = Record<string, unknown>;
const esObjeto = (valor: unknown): valor is Objeto =>
  typeof valor === "object" && valor !== null && !Array.isArray(valor);

/** Un documento cuya raíz declara `$schema` y `$id` es un esquema (BR12.3). */
const declaraEsquema = (contenido: unknown): boolean =>
  esObjeto(contenido) && "$schema" in contenido && "$id" in contenido;

function uriDe(nombre: string, contenido: unknown): string {
  const identificador = esObjeto(contenido) ? contenido["$id"] : undefined;
  if (typeof identificador !== "string") {
    throw new LoadError(`${nombre}: el esquema no tiene $id de texto`);
  }
  if (!identificador || identificador.includes("#") || identificador.includes("?")) {
    throw new LoadError(
      `${nombre}: el $id no puede ser vacío, con fragmento o con consulta: ${JSON.stringify(identificador)}`,
    );
  }
  if (/^[a-z][a-z0-9+.-]*:/i.test(identificador)) {
    throw new LoadError(`${nombre}: un $id absoluto no se admite fuera de vendor/: ${identificador}`);
  }
  if (identificador.startsWith("//") || identificador.split("/").includes("..")) {
    throw new LoadError(`${nombre}: el $id relativo sale de la base: ${identificador}`);
  }
  return new URL(identificador, BASE_URI).href;
}

/** Registro con todos los esquemas bajo `raiz` (por defecto, los de `contracts/`). */
export function buildRegistry(
  raiz: string = CONTRACTS_ROOT,
  directorios: readonly string[] = DATA_DIRS,
): Registry {
  const ajv = createAjv();
  const uris: string[] = [];
  const origen = new Map<string, string>();
  for (const directorio of directorios) {
    const carpeta = join(raiz, directorio);
    if (!existsSync(carpeta)) throw new LoadError(`falta el directorio de datos ${directorio}`);
    for (const archivo of archivosDeDatos(carpeta)) {
      const nombre = archivo.split(/[\\/]/).at(-1) as string;
      const contenido = loadFile(archivo);
      if (!nombre.endsWith(SUFIJO_DE_ESQUEMA) && !declaraEsquema(contenido)) continue;
      const uri = uriDe(nombre, contenido);
      const previo = origen.get(uri);
      if (previo !== undefined) {
        throw new LoadError(`URI repetida ${uri}: la declaran ${previo} y ${nombre}`);
      }
      origen.set(uri, nombre);
      // Copia con el `$id` absoluto: las referencias de ruta absoluta (`/veridicus/...`) se
      // resuelven contra la base. El archivo no cambia. BR1.1 (E-29, E-30): `x-veridicus-version` es
      // una anotación que solo se admite en la raíz del esquema; sale de la copia y, anidada, falla.
      const esquema: Objeto = { ...(contenido as Objeto), $id: uri };
      delete esquema["x-veridicus-version"];
      ajv.addSchema(esquema, uri);
      uris.push(uri);
    }
  }
  return { ajv, uris, documentos: new Set() };
}

/** El valor al que apunta un puntero JSON `#/a/b` (RFC 6901) dentro de un documento. */
function porPuntero(documento: unknown, puntero: string): unknown {
  if (!puntero.startsWith("#/")) throw new LoadError(`puntero no válido: ${puntero}`);
  let actual: unknown = documento;
  for (const segmento of puntero.slice(2).split("/")) {
    const clave = decodeURIComponent(segmento).replaceAll("~1", "/").replaceAll("~0", "~");
    if (!esObjeto(actual) || !(clave in actual)) throw new LoadError(`el puntero ${puntero} no existe`);
    actual = actual[clave];
  }
  return actual;
}

/**
 * Registra, como esquema propio, el fragmento de un documento OpenAPI o AsyncAPI al que apunta un
 * puntero (la carga de un mensaje, el cuerpo de una operación) y devuelve su URI.
 *
 * Un documento OpenAPI o AsyncAPI no es un esquema: ajv compila la raíz entera del documento que
 * contiene el fragmento y falla por `openapi` o `asyncapi`. Se registra solo el fragmento, con la URI
 * del documento más el puntero como `$id`; sus referencias de ruta absoluta (`/veridicus/...`) se
 * resuelven contra la base como en el resto del registro (P-T20-5).
 */
export function registerFragment(
  registro: Registry,
  relativa: string,
  documento: unknown,
  puntero: string,
): string {
  const uri = `${BASE_URI}_documentos/${relativa}/${puntero.slice(2)}`;
  if (!registro.documentos.has(uri)) {
    const fragmento = porPuntero(documento, puntero);
    if (!esObjeto(fragmento)) throw new LoadError(`el puntero ${puntero} no apunta a un esquema`);
    registro.ajv.addSchema({ ...fragmento, $id: uri }, uri);
    registro.documentos.add(uri);
  }
  return uri;
}

/** El validador del esquema registrado bajo `uri` (y de un puntero `#/...` dentro de él). */
export function validatorFor(registro: Registry, uri: string, puntero = ""): ValidateFunction {
  return registro.ajv.compile({ $ref: uri + puntero });
}
