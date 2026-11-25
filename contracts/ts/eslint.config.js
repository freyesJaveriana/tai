import js from "@eslint/js";
import tseslint from "typescript-eslint";

// `yaml` solo se importa en src/loaders.ts (D5): un solo punto crea el lector, igual que loaders.py.
const IMPORTAR_YAML_FUERA_DE_LOADERS = {
  paths: [
    {
      name: "yaml",
      message: "Solo src/loaders.ts importa `yaml` (D5, clave repetida es un error).",
    },
  ],
  patterns: [
    {
      group: ["yaml/*"],
      message: "Solo src/loaders.ts importa `yaml` (D5, clave repetida es un error).",
    },
  ],
};

export default tseslint.config(
  { ignores: ["node_modules/**", "coverage/**", "generated/**"] },
  js.configs.recommended,
  ...tseslint.configs.strict,
  {
    files: ["src/**/*.ts", "test/**/*.ts", "vitest.config.ts"],
    rules: {
      "no-restricted-imports": ["error", IMPORTAR_YAML_FUERA_DE_LOADERS],
    },
  },
  {
    files: ["src/loaders.ts"],
    rules: { "no-restricted-imports": "off" },
  },
  {
    files: ["scripts/**/*.mjs"],
    languageOptions: {
      globals: { process: "readonly", console: "readonly", URL: "readonly" },
    },
  },
);
