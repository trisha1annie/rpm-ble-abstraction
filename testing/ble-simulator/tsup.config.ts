import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  target: "node24",
  clean: true,
  sourcemap: true,
  dts: false,
  shims: true,
  esbuildOptions(options) {
    options.banner = {
      js: "#!/usr/bin/env node",
    };
  },
  outExtension() {
    return {
      js: ".js",
    };
  },
});
