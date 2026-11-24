import { defineConfig } from "vitest/config";

// Umbral de 80 % de líneas (team.md, Testing Posture). Los tipos generados y el
// archivo de arranque no cuentan: son código generado y andamiaje de la prueba.
export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    setupFiles: ["test/setup-no-network.ts"],
    environment: "node",
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      reporter: ["text", "json-summary"],
      thresholds: { lines: 80 },
    },
  },
});
