// Sin red (NFR10.4, NFR10.5, §4.14): el setup de Vitest sustituye cada salida a la red por una
// función que lanza; esta prueba de control intenta usarlas y espera el error del setup.
import dns from "node:dns";
import http from "node:http";
import https from "node:https";
import net from "node:net";
import { describe, expect, it } from "vitest";
import config from "../vitest.config";
import { MENSAJE_SIN_RED } from "./sin-red";

// Esta prueba NO importa el setup: solo ve el bloqueo si `setupFiles` lo carga (F-01).
describe("sin red", () => {
  it("vitest.config.ts carga el setup sin red en setupFiles", () => {
    expect(config.test?.setupFiles).toContain("test/setup-no-network.ts");
  });

  it("un fetch de control lanza el error del setup", async () => {
    await expect(async () => fetch("https://veridicus.invalid/")).rejects.toThrow(MENSAJE_SIN_RED);
  });

  it.each([
    ["net.connect", () => net.connect(80, "veridicus.invalid")],
    ["net.createConnection", () => net.createConnection(80, "veridicus.invalid")],
    ["http.request", () => http.request("http://veridicus.invalid/")],
    ["https.request", () => https.request("https://veridicus.invalid/")],
    ["dns.lookup", () => dns.lookup("veridicus.invalid", () => undefined)],
  ])("%s lanza el error del setup", (_nombre, usar) => {
    expect(usar).toThrow(MENSAJE_SIN_RED);
  });
});
