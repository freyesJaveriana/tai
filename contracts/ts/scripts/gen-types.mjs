// Tipos de C1 y comprobación de los generados (D9, §4.14).
//
// Sin argumentos genera `generated/console.ts` con `openapi-typescript` desde `api/console.v2.yaml` y
// deja que `gen_ts` escriba las constantes. Con `--check` no escribe nada: corre `gen_ts --check` y
// compara en memoria la salida de `openapi-typescript` con el archivo versionado. Sale con código
// distinto de 0 si algo difiere o falta.
//
// Los contratos se refieren a otros esquemas por su `$id` como ruta absoluta (`/veridicus/contracts/...`,
// BR12.3), que `openapi-typescript` leería como una ruta del disco. Antes de generar, el script copia
// los contratos a una carpeta temporal y sustituye cada una por la ruta relativa del archivo que
// declara ese `$id`. Los archivos del repositorio no cambian (P-T20-7).
import { spawnSync } from "node:child_process";
import {
  existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, posix, relative } from "node:path";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";

const CARPETA_TS = fileURLToPath(new URL("..", import.meta.url));
const CONTRACTS = fileURLToPath(new URL("../../", import.meta.url));
const DESTINO = fileURLToPath(new URL("../generated/console.ts", import.meta.url));
const C1 = "api/console.v2.yaml";
// Los directorios de datos de contracts/ que C1 puede referenciar (los de `DATA_DIRS` de src/registry.ts).
const DIRECTORIOS = [
  "analyzer", "cli", "errors", "format", "health", "integrity", "metrics", "model_calls",
  "profiles", "queues", "transcript", "ui",
];
const SALTADOS = new Set(["fixtures", "tests"]);

/** Cada archivo de datos de los directorios, como ruta relativa a contracts/ con `/`. */
function archivosDeDatos() {
  const salida = [C1];
  const recorrer = (carpeta) => {
    for (const entrada of readdirSync(carpeta, { withFileTypes: true })) {
      const ruta = join(carpeta, entrada.name);
      if (entrada.isDirectory()) {
        if (!SALTADOS.has(entrada.name)) recorrer(ruta);
      } else if (/\.(ya?ml|json)$/.test(entrada.name)) {
        salida.push(relative(CONTRACTS, ruta).replaceAll("\\", "/"));
      }
    }
  };
  for (const directorio of DIRECTORIOS) recorrer(join(CONTRACTS, directorio));
  return salida.sort();
}

/** Copia los contratos a `raiz` con cada `$ref` por `$id` reescrita como ruta relativa de archivo. */
function copiarConReferenciasDeArchivo(raiz) {
  const archivos = archivosDeDatos();
  const textos = new Map(archivos.map((a) => [a, readFileSync(join(CONTRACTS, a), "utf-8")]));
  const ids = new Map();
  for (const [archivo, texto] of textos) {
    const encontrado = /^\s*"?\$id"?:\s*["']?([^"'\s,]+)/m.exec(texto);
    if (encontrado && archivo !== C1) ids.set(encontrado[1], archivo);
  }
  for (const [archivo, texto] of textos) {
    const reescrito = texto.replace(/\/(veridicus\/contracts\/[A-Za-z0-9._/-]+)/g, (completo, id) => {
      const objetivo = ids.get(id);
      return objetivo === undefined ? completo : posix.relative(posix.dirname(archivo), objetivo);
    });
    const destino = join(raiz, archivo);
    mkdirSync(dirname(destino), { recursive: true });
    writeFileSync(destino, reescrito, "utf-8");
  }
}

async function tiposDeC1() {
  const raiz = mkdtempSync(join(tmpdir(), "veridicus-gen-"));
  try {
    copiarConReferenciasDeArchivo(raiz);
    const fuente = new URL(`file://${join(raiz, C1)}`);
    return astToString(await openapiTS(fuente));
  } finally {
    rmSync(raiz, { recursive: true, force: true });
  }
}

const comprobar = process.argv.includes("--check");

// Las constantes del catálogo, los rótulos, C8 y las listas de §4.6 las genera `gen_ts` (T19).
const gen = spawnSync(
  "uv",
  [
    "run", "--frozen", "--offline", "--directory", "..",
    "python", "-m", "veridicus_contracts.tools.gen_ts",
    ...(comprobar ? ["--check"] : []),
  ],
  { cwd: CARPETA_TS, stdio: "inherit" },
);
if (gen.status !== 0) {
  console.error(`gen:check: gen_ts terminó con código ${String(gen.status)}`);
  process.exit(gen.status ?? 1);
}

const generado = await tiposDeC1();

if (!comprobar) {
  writeFileSync(DESTINO, generado, "utf-8");
  console.log("gen: escrito generated/console.ts");
} else if (!existsSync(DESTINO)) {
  console.error("gen:check: falta generated/console.ts; corra `npm run gen`");
  process.exit(1);
} else if (readFileSync(DESTINO, "utf-8") !== generado) {
  console.error("gen:check: generated/console.ts difiere de lo que genera openapi-typescript");
  process.exit(1);
} else {
  console.log("gen:check: generated/console.ts al día");
}
