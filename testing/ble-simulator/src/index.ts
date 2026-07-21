import fs from "fs";
import yaml from "js-yaml";
import { startPeripheral } from "./lib/peripheral";
import { startREPL } from "./lib/repl";
import type { DeviceConfig } from "./types";

function main() {
  if (process.argv.length < 3) {
    console.log("Usage: ble-sim <config.yaml>");
    process.exit(1);
  }

  const configPath = process.argv[2];

  let config: DeviceConfig;
  try {
    const fileContents = fs.readFileSync(configPath, "utf8");
    config = yaml.load(fileContents) as DeviceConfig;
  } catch (err) {
    console.error("Error loading config:", (err as Error).message);
    process.exit(1);
  }

  startPeripheral(config, () => {
    console.log("✅ BLE Peripheral running.");
    console.log(`📡 Advertising as: ${config.name}`);
    console.log("");

    // Start interactive REPL
    startREPL();
  });
}

main();
