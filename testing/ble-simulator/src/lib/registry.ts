import type { Registry } from "../types";

export const registry: Registry = {};

export function clearRegistry() {
  for (const key in registry) {
    delete registry[key];
  }
}
