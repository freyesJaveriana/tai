// Sin red (NFR10.4, NFR10.5, §4.14): ninguna prueba abre una conexión. Cada punto de salida a la red
// se sustituye por una función que lanza el mismo error; una prueba de control lo comprueba.
import dns from "node:dns";
import http from "node:http";
import https from "node:https";
import net from "node:net";

import { MENSAJE_SIN_RED } from "./sin-red";

function bloqueada(): never {
  throw new Error(MENSAJE_SIN_RED);
}

// Los módulos de Node se sustituyen en el objeto compartido (CommonJS), de modo que lo vea
// también el código que los importe después.
const modificables = [
  [net, "connect"],
  [net, "createConnection"],
  [http, "request"],
  [https, "request"],
  [dns, "lookup"],
] as const;

for (const [modulo, nombre] of modificables) {
  Object.defineProperty(modulo, nombre, { value: bloqueada, configurable: true, writable: true });
}
Object.defineProperty(globalThis, "fetch", { value: bloqueada, configurable: true, writable: true });
