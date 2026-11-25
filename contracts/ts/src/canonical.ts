// Huella JCS (RFC 8785) de un objeto JSON (D14, NFR10.15; espejo de canonical.py).
//
// `canonicalize` serializa con la forma de números de RFC 8785 (la de `JSON.stringify` de ECMAScript).
// `JSON.parse` lee menos cero como -0 y JCS lo escribe como `0`, igual que `rfc8785` en Python.
import canonicalize from "canonicalize";
import { createHash } from "node:crypto";

/** Rechaza lo que JCS no puede escribir (NaN, Infinity), como `rfc8785` en Python. */
function comprobarFinitos(valor: unknown): void {
  if (typeof valor === "number" && !Number.isFinite(valor)) {
    throw new TypeError("JCS solo admite números finitos");
  }
  if (Array.isArray(valor)) valor.forEach(comprobarFinitos);
  else if (typeof valor === "object" && valor !== null) Object.values(valor).forEach(comprobarFinitos);
}

/** Serialización canónica JCS del objeto, como texto. */
export function canonicalString(objeto: unknown): string {
  comprobarFinitos(objeto);
  const texto = canonicalize(objeto);
  if (texto === undefined) throw new TypeError("el valor no es JSON: no tiene forma canónica");
  return texto;
}

/** SHA-256, en hexadecimal, de la serialización canónica del objeto (UTF-8). */
export function sha256Jcs(objeto: unknown): string {
  return createHash("sha256").update(canonicalString(objeto), "utf-8").digest("hex");
}
