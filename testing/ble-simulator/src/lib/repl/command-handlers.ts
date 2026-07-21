import chalk from "chalk";
import fs from "fs";
import yaml from "js-yaml";
import { registry } from "../registry";
import { getEncoder } from "../encoder-registry";
import { getCurrentConfig } from "../peripheral";
import type { Command } from "./types";
import type { FuzzyMatcher } from "./fuzzy-matcher";
import type { CharHandle, DeviceConfig } from "../../types";

export class CommandHandlers {
  constructor(
    private fuzzyMatcher: FuzzyMatcher,
    private getAvailableConfigs: () => Map<string, string>,
    private getConfigByNumber: () => Map<number, string>,
    private loadConfigs: () => void
  ) {}

  showHelp(): void {
    console.log(chalk.bold("\n📖 Available Commands:"));

    const commands = this.getCommands();
    const maxCmdLength = Math.max(
      ...Object.entries(commands).map(
        ([name, cmd]) => (cmd.usage || name).length
      )
    );

    for (const [name, cmd] of Object.entries(commands)) {
      const usage = cmd.usage || name;
      const padding = " ".repeat(maxCmdLength - usage.length + 2);
      console.log(`  ${chalk.cyan(usage)}${padding}${cmd.description}`);
    }
  }

  listCharacteristics(): void {
    const names = Object.keys(registry);
    if (names.length === 0) {
      console.log(chalk.yellow("⚠️  No characteristics registered."));
      console.log(chalk.gray("   Use 'switch' to load a device configuration"));
      return;
    }

    console.log(chalk.bold("\n📋 Characteristics:"));

    for (const name of names) {
      const handle = registry[name];
      const props = handle.config.properties.join(", ");
      const encoderInfo = handle.config.encoder
        ? chalk.gray(` [encoder: ${handle.config.encoder.type}]`)
        : "";
      console.log(
        `  ${chalk.cyan(name.padEnd(20))} ${chalk.gray(
          `[${props}]`
        )} = ${chalk.green(`"${handle.value.toString()}"`)}${encoderInfo}`
      );
    }
  }

  readCharacteristic(name: string): void {
    const handle = this.checkCharacteristic(name);
    if (!handle) return;

    console.log(
      chalk.yellow(
        `⚠️  Reading raw value for '${name}' may not be human-readable.`
      )
    );

    console.log(
      `${chalk.green("✅")} ${chalk.cyan(name)} = ${chalk.green(
        `"${handle.value.toString()}"`
      )}`
    );
  }

  writeCharacteristic(name: string, values: string[]): void {
    const handle = this.checkCharacteristic(name);
    if (!handle) return;

    const encoderType = handle.config.encoder?.type;
    this.writeUpdateCharacteristic(name, values, encoderType, handle, false);
  }

  /**
   * Send a notification for a characteristic
   */
  notifyCharacteristic(name: string, values: string[]): void {
    const handle = this.checkCharacteristic(name);
    if (!handle) return;

    if (!handle.updateValueCallback) {
      console.log(chalk.yellow(`⚠️  No clients subscribed to ${name}`));
      console.log(
        chalk.gray(`   Connect a BLE client first to receive notifications`)
      );
      return;
    }

    const encoderType = handle.config.encoder?.type;
    this.writeUpdateCharacteristic(name, values, encoderType, handle, true);
  }

  private checkCharacteristic(name: string): CharHandle | null {
    const handle = registry[name];
    if (!handle) {
      console.log(chalk.red(`❌ No such characteristic: ${name}`));
      const suggestions = this.fuzzyMatcher.findSimilarCharacteristics(
        name,
        Object.keys(registry)
      );
      if (suggestions.length > 0) {
        console.log(chalk.gray(`   Did you mean: ${suggestions.join(", ")}?`));
      }
      console.log(chalk.gray(`   Use 'list' to see all characteristics`));
      return null;
    }

    return handle;
  }

  private writeUpdateCharacteristic(
    name: string,
    values: string[],
    encoderType: string | undefined,
    handle: CharHandle,
    update = false
  ): void {
    let buffer: Buffer;

    if (encoderType) {
      const encoder = getEncoder(encoderType);
      if (!encoder) {
        console.log(chalk.red(`❌ Encoder '${encoderType}' not found`));
        return;
      }
      try {
        const args = this.parseEncoderArgs(encoderType, values);
        buffer = encoder.encode(...args);
        handle.value = buffer;
        if (update && handle.updateValueCallback) {
          handle.updateValueCallback(buffer);
        }
        console.log(
          `${chalk.green(`✅ ${update ? "Notify" : "Write"}:`)} ${chalk.cyan(
            name
          )} = ${chalk.yellow(values.join(" "))} ${chalk.gray(
            `(encoded with ${encoderType})`
          )}`
        );
      } catch (err) {
        console.log(
          chalk.red(`❌ Error encoding value: ${(err as Error).message}`)
        );
        console.log(chalk.gray(`   Expected format: ${encoder.example}`));
        return;
      }
    } else {
      buffer = Buffer.from(values.join(" "));
      handle.value = buffer;
      if (update && handle.updateValueCallback) {
        handle.updateValueCallback(buffer);
      }
      console.log(
        `${chalk.green(`✅ ${update ? "Notify" : "Write"}:`)} ${chalk.cyan(
          name
        )} = ${chalk.yellow(`"${values.join(" ")}"`)}`
      );
    }
  }

  listDevices(): void {
    this.loadConfigs();
    const configs = this.getAvailableConfigs();
    const configByNumber = this.getConfigByNumber();

    if (configs.size === 0) {
      console.log(
        chalk.yellow("⚠️  No device configs found in ./configs directory")
      );
      console.log(
        chalk.gray("   Create YAML config files in the configs/ directory")
      );
      return;
    }

    const current = getCurrentConfig();
    console.log(chalk.bold("\n📱 Available devices:"));

    const sorted = Array.from(configByNumber.entries()).sort(
      (a, b) => a[0] - b[0]
    );

    for (const [num, name] of sorted) {
      const configPath = configs.get(name)!;
      try {
        const content = fs.readFileSync(configPath, "utf8");
        const config = yaml.load(content) as DeviceConfig;
        const isCurrent =
          current && current.name === config.name
            ? chalk.green(" ← current")
            : "";
        const servicesCount = chalk.gray(
          ` (${config.services.length} service${
            config.services.length !== 1 ? "s" : ""
          })`
        );
        console.log(
          `  ${chalk.cyan(String(num).padStart(2) + ".")} ${
            config.displayName || config.name
          } [${chalk.gray(name)}]${servicesCount}${isCurrent}`
        );
      } catch {
        console.log(
          `  ${chalk.cyan(String(num).padStart(2) + ".")} ${name} ${chalk.red(
            "(error loading)"
          )}`
        );
      }
    }

    console.log(chalk.gray("\n   Switch using: switch <number|name>"));
  }

  resolveDeviceArg(arg: string): string | null {
    if (!arg) {
      console.log(chalk.red("❌ Missing argument: device name or number"));
      console.log(chalk.gray("   Usage: switch <device>"));
      console.log(chalk.gray("   Use 'devices' to see available devices"));
      return null;
    }

    const configs = this.getAvailableConfigs();
    const configByNumber = this.getConfigByNumber();

    const maybeNum = Number(arg);
    if (Number.isInteger(maybeNum) && configByNumber.has(maybeNum)) {
      return configByNumber.get(maybeNum)!;
    }
    if (configs.has(arg)) return arg;

    console.log(chalk.red(`❌ Unknown device '${arg}'`));
    const suggestions = this.fuzzyMatcher.findSimilarDevices(
      arg,
      Array.from(configs.keys())
    );
    if (suggestions.length > 0) {
      console.log(chalk.gray(`   Did you mean: ${suggestions.join(", ")}?`));
    }
    console.log(chalk.gray("   Use 'devices' to list all available devices"));
    return null;
  }

  private parseEncoderArgs(encoderType: string, values: string[]): any[] {
    switch (encoderType) {
      case "blood-pressure":
        // Expect: systolic diastolic pulse
        if (values.length < 3) {
          throw new Error(
            "Blood pressure requires 3 values: systolic diastolic pulse"
          );
        }
        return [parseInt(values[0]), parseInt(values[1]), parseInt(values[2])];

      case "pulse-oximeter":
        // Expect: spo2 pulse
        if (values.length < 2) {
          throw new Error(
            "Pulse oximeter requires at least 2 values: spo2% pulse"
          );
        }
        return [
          parseInt(values[0]),
          parseInt(values[1]),
          values[2] ? parseFloat(values[2]) : undefined,
        ];

      case "weight-scale":
        // bmi and height are supported but not used
        // Expect: weight [unit]
        if (values.length < 1) {
          throw new Error(
            "Weight scale requires at least 1 value: weight [kg|lb]"
          );
        }
        return [
          parseFloat(values[0]),
          values[1] === "lb" || values[1] === "kg" ? values[1] : "kg",
          values[2] ? parseFloat(values[2]) : undefined,
          values[3] ? parseFloat(values[3]) : undefined,
        ];

      case "battery-level":
      case "uint8":
        return [parseInt(values[0])];

      case "uint16":
        return [parseInt(values[0])];

      case "uint32":
        return [parseInt(values[0])];

      case "heart-rate":
        return [parseInt(values[0])];

      case "text":
        return [values.join(" ")];

      default:
        return values.map((v) => {
          const num = parseFloat(v);
          return isNaN(num) ? v : num;
        });
    }
  }

  private getCommands(): Record<string, Command> {
    return {
      help: {
        description: "Show available commandsaaaaa",
      },
      list: {
        description: "List all characteristics currently registered",
      },
      read: {
        description: "Read a characteristic value",
        usage: "read <char>",
      },
      write: {
        description: "Write to a characteristic (uses encoder if configured)",
        usage: "write <char> <values...>",
      },
      notify: {
        description: "Send a notification (uses encoder if configured)",
        usage: "notify <char> <values...>",
      },
      devices: {
        description: "List available device configs found in ./configs",
      },
      switch: {
        description:
          "Switch to a different device (interactive or by name/number)",
        usage: "switch [device]",
      },
      exit: {
        description: "Exit the simulator",
      },
    };
  }
}
