import fs from "fs";
import yaml from "js-yaml";
import path from "path";
import chalk from "chalk";
import type { DeviceConfig } from "../../types";
import {
  stopPeripheral,
  startPeripheral,
  getCurrentConfig,
} from "../peripheral";

export class DeviceManager {
  private availableConfigs = new Map<string, string>();
  private configByNumber = new Map<number, string>();

  loadConfigs(): void {
    this.availableConfigs.clear();
    this.configByNumber.clear();

    const configsDir = path.join(process.cwd(), "configs");
    if (!fs.existsSync(configsDir)) return;

    const files = fs
      .readdirSync(configsDir)
      .filter((f) => f.endsWith(".yaml") || f.endsWith(".yml"))
      .sort();

    let index = 1;
    for (const file of files) {
      const fullPath = path.join(configsDir, file);
      const key = file.replace(/\.(yaml|yml)$/, "");
      this.availableConfigs.set(key, fullPath);
      this.configByNumber.set(index++, key);
    }
  }

  getAvailableConfigs(): Map<string, string> {
    return this.availableConfigs;
  }

  getConfigByNumber(): Map<number, string> {
    return this.configByNumber;
  }

  async switchDevice(deviceKey: string): Promise<void> {
    const configPath = this.availableConfigs.get(deviceKey);
    if (!configPath) {
      console.log(chalk.red(`❌ Device '${deviceKey}' not found`));
      console.log(chalk.gray("   Use 'devices' to see available devices"));
      return;
    }

    try {
      const content = fs.readFileSync(configPath, "utf8");
      const config = yaml.load(content) as DeviceConfig;

      console.log(
        chalk.yellow(`⏳ Switching to ${config.displayName || config.name}...`)
      );

      stopPeripheral();
      console.log(chalk.gray("   Stopped current device"));
      console.log(chalk.gray("   Starting new device..."));

      await new Promise<void>((resolve, reject) => {
        const t = setTimeout(
          () => reject(new Error("Timeout waiting for peripheral to start")),
          15000
        );

        startPeripheral(config, () => {
          clearTimeout(t);
          console.log(
            chalk.green(
              `✅ Device switched successfully to ${
                config.displayName || config.name
              }`
            )
          );
          console.log(
            chalk.gray(`   Use 'list' to see available characteristics`)
          );
          resolve();
        });
      });
    } catch (err) {
      console.log(
        chalk.red(`❌ Failed to switch device: ${(err as Error).message}`)
      );
    }
  }

  getCurrentDevice(): DeviceConfig | null {
    return getCurrentConfig();
  }
}
