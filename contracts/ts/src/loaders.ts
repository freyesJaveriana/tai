// Carga de YAML y JSON de los contratos (D5; espejo de loaders.py).
//
// Este módulo es el único punto del paquete que importa `yaml` (regla de ESLint
// `no-restricted-imports`): YAML 1.2, sin claves repetidas, sin etiquetas de objetos y con claves de
// texto. Todo valor leído es compatible con JSON.
import { readFileSync } from "node:fs";
import { basename } from "node:path";
import { isScalar, parseDocument, visit } from "yaml";

export class LoadError extends Error {
  constructor(mensaje: string) {
    super(mensaje);
    this.name = "LoadError";
  }
}

const DECODIFICADOR = new TextDecoder("utf-8", { fatal: true });

/** Primer problema que `yaml` informa al leer el texto (error o aviso), o `undefined` si no hay. */
function problemaDe(documento: ReturnType<typeof parseDocument>): string | undefined {
  const problema = documento.errors[0] ?? documento.warnings[0];
  return problema?.message.split("\n")[0];
}

/** Lee un documento YAML 1.2; rechaza claves repetidas, etiquetas de objetos y claves que no son texto. */
export function loadYamlText(texto: string): unknown {
  const documento = parseDocument(texto, { version: "1.2", uniqueKeys: true, merge: false });
  const problema = problemaDe(documento);
  if (problema !== undefined) {
    throw new LoadError(`YAML no válido (clave repetida, etiqueta no permitida o sintaxis): ${problema}`);
  }
  visit(documento, {
    Pair(_clave, par) {
      if (!isScalar(par.key) || typeof par.key.value !== "string") {
        throw new LoadError(`clave que no es texto en YAML: ${JSON.stringify(par.key)}`);
      }
    },
  });
  return documento.toJS() as unknown;
}

/** Lee un documento JSON; rechaza claves repetidas y NaN o Infinity. Conserva el menos cero. */
export function loadJsonText(texto: string): unknown {
  let valor: unknown;
  try {
    valor = JSON.parse(texto) as unknown;
  } catch (error) {
    throw new LoadError(`JSON no válido: ${(error as Error).message}`);
  }
  // `JSON.parse` calla ante una clave repetida y se queda con la última: el lector de YAML 1.2 las ve.
  const documento = parseDocument(texto, { version: "1.2", uniqueKeys: true });
  if (documento.errors.some((error) => error.code === "DUPLICATE_KEY")) {
    throw new LoadError("clave repetida en JSON");
  }
  return valor;
}

/** Lee un archivo `.yaml`, `.yml` o `.json` según su sufijo. */
export function loadFile(ruta: string): unknown {
  const nombre = basename(ruta);
  let texto: string;
  try {
    texto = DECODIFICADOR.decode(readFileSync(ruta));
  } catch (error) {
    const motivo = error instanceof TypeError ? "no es texto UTF-8" : "no se pudo leer";
    throw new LoadError(`${nombre}: ${motivo}`);
  }
  if (nombre.endsWith(".yaml") || nombre.endsWith(".yml")) return loadYamlText(texto);
  if (nombre.endsWith(".json")) return loadJsonText(texto);
  throw new LoadError(`sufijo no admitido en ${nombre}: use .yaml, .yml o .json`);
}
