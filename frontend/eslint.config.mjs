import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // These are Node.js CLI utilities, not browser-source modules. They use
    // CommonJS deliberately and are verified by their dedicated commands.
    "fallback-server.cjs",
    "scripts/**/*.cjs",
  ]),
]);

export default eslintConfig;
