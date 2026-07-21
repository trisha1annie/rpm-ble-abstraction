import readline from "readline";
import chalk from "chalk";
import { registry } from "../registry";
import { getEncoder } from "../encoder-registry";
import type { Command } from "./types";
import { FuzzyMatcher } from "./fuzzy-matcher";
import { AutocompleteHandler } from "./autocomplete";
import { CommandHandlers } from "./command-handlers";
import { DeviceManager } from "./device-manager";

export class REPL {
  private rl?: readline.Interface;
  private fuzzyMatcher: FuzzyMatcher;
  private deviceManager: DeviceManager;
  private commandHandlers: CommandHandlers;
  private autocompleteHandler: AutocompleteHandler;
  private commands: Record<string, Command>;

  constructor() {
    this.fuzzyMatcher = new FuzzyMatcher();
    this.deviceManager = new DeviceManager();

    this.commandHandlers = new CommandHandlers(
      this.fuzzyMatcher,
      () => this.deviceManager.getAvailableConfigs(),
      () => this.deviceManager.getConfigByNumber(),
      () => this.deviceManager.loadConfigs()
    );

    this.commands = this.initializeCommands();

    this.autocompleteHandler = new AutocompleteHandler(this.commands, () =>
      this.deviceManager.getAvailableConfigs()
    );
  }

  private initializeCommands(): Record<string, Command> {
    return {
      help: {
        description: "Show available commands",
        handler: () => this.commandHandlers.showHelp(),
      },
      list: {
        description: "List all characteristics currently registered",
        handler: () => this.commandHandlers.listCharacteristics(),
      },
      read: {
        description: "Read a characteristic value",
        usage: "read <char>",
        handler: async (args) => this.handleRead(args),
      },
      write: {
        description: "Write to a characteristic (uses encoder if configured)",
        usage: "write <char> <values...>",
        handler: async (args) => this.handleWrite(args),
      },
      notify: {
        description: "Send a notification (uses encoder if configured)",
        usage: "notify <char> <values...>",
        handler: async (args) => this.handleNotify(args),
      },
      devices: {
        description: "List available device configs found in ./configs",
        handler: () => this.commandHandlers.listDevices(),
      },
      switch: {
        description:
          "Switch to a different device (interactive or by name/number)",
        usage: "switch <device>",
        handler: async (args) => this.handleSwitch(args),
      },
      exit: {
        description: "Exit the simulator",
        handler: () => this.exit(),
      },
    };
  }

  private handleRead(args: string[]): void {
    const names = Object.keys(registry);

    if (names.length === 0) {
      console.log(chalk.yellow("⚠️  No characteristics registered."));
      console.log(
        chalk.gray("   Use 'switch' to load a device configuration.")
      );
      return;
    }

    if (args.length === 0) {
      console.log(chalk.red("❌ Missing argument: characteristic name"));
      console.log(chalk.gray("   Usage: read <char>"));
      console.log(
        chalk.gray(`   Available characteristics: ${names.join(", ")}`)
      );
      return;
    }

    this.commandHandlers.readCharacteristic(args[0]);
  }

  private handleWrite(args: string[]): void {
    const names = Object.keys(registry);

    if (names.length === 0) {
      console.log(chalk.yellow("⚠️  No characteristics registered."));
      console.log(
        chalk.gray("   Use 'switch' to load a device configuration.")
      );
      return;
    }

    if (args.length === 0) {
      console.log(chalk.red("❌ Missing argument: characteristic name"));
      console.log(chalk.gray("   Usage: write <char> <values...>"));
      console.log(
        chalk.gray(`   Available characteristics: ${names.join(", ")}`)
      );
      return;
    }

    const char = args[0];
    const values = args.slice(1);

    if (values.length === 0) {
      const handle = registry[char];
      if (handle && handle.config.encoder) {
        const encoder = getEncoder(handle.config.encoder.type);
        if (encoder) {
          console.log(chalk.red("❌ Missing values for characteristic"));
          console.log(chalk.gray(`   Usage: write ${char} ${encoder.example}`));
          return;
        }
      }
      console.log(chalk.red("❌ Missing values for characteristic"));
      console.log(chalk.gray(`   Usage: write ${char} <values...>`));
      return;
    }

    this.commandHandlers.writeCharacteristic(char, values);
  }

  private handleNotify(args: string[]): void {
    const names = Object.keys(registry);
    if (names.length === 0) {
      console.log(chalk.yellow("⚠️  No characteristics registered."));
      console.log(
        chalk.gray("   Use 'switch' to load a device configuration.")
      );
      return;
    }

    if (args.length === 0) {
      console.log(chalk.red("❌ Missing argument: characteristic name"));
      console.log(chalk.gray("   Usage: notify <char> <values...>"));
      console.log(
        chalk.gray(`   Available characteristics: ${names.join(", ")}`)
      );
      return;
    }

    const char = args[0];
    const values = args.slice(1);

    if (values.length === 0) {
      const handle = registry[char];
      if (handle && handle.config.encoder) {
        const encoder = getEncoder(handle.config.encoder.type);
        if (encoder) {
          console.log(chalk.red("❌ Missing values for characteristic"));
          console.log(
            chalk.gray(`   Usage: notify ${char} ${encoder.example}`)
          );
          return;
        }
      }
      console.log(chalk.red("❌ Missing values for characteristic"));
      console.log(chalk.gray(`   Usage: notify ${char} <values...>`));
      return;
    }

    this.commandHandlers.notifyCharacteristic(char, values);
  }

  private async handleSwitch(args: string[]): Promise<void> {
    const deviceKey = this.commandHandlers.resolveDeviceArg(args[0]);
    if (deviceKey) {
      await this.deviceManager.switchDevice(deviceKey);
    }
  }

  private async processCommand(input: string): Promise<void> {
    const parts = input.split(/\s+/);
    const cmdName = parts[0].toLowerCase();
    const args = parts.slice(1);

    const command = this.commands[cmdName];
    if (!command) {
      console.log(chalk.red(`❌ Unknown command: ${cmdName}`));

      const commandNames = Object.keys(this.commands);
      const suggestions = this.fuzzyMatcher.findSimilarCommands(
        cmdName,
        commandNames
      );

      if (suggestions.length > 0) {
        console.log(chalk.gray(`   Did you mean: ${suggestions.join(", ")}?`));
      }
      console.log(chalk.gray("   Type 'help' for available commands"));
    } else if (command.handler) {
      await command.handler(args);
    }

    console.log();
  }

  start(): void {
    process.stdin.setRawMode?.(false);

    this.deviceManager.loadConfigs();

    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: chalk.blue("> "),
      terminal: true,
      completer: (line: string) => this.autocompleteHandler.complete(line),
    });

    console.log(chalk.green("🎮 BLE Simulator REPL"));
    console.log(chalk.gray("Type 'help' for commands.\n"));

    setImmediate(() => {
      this.rl?.prompt();
    });

    this.rl.on("line", (line: string) => {
      const input = line.trim();

      if (!input) {
        this.rl?.prompt();
        return;
      }

      (async () => {
        try {
          await this.processCommand(input);
        } catch (err: any) {
          console.error(chalk.red("❌ Error:"), err.message);
        }

        setImmediate(() => {
          this.rl?.prompt();
        });
      })();
    });

    this.rl.on("close", () => {
      console.log(chalk.cyan("\n👋 Goodbye!"));
      process.exit(0);
    });

    this.rl.on("SIGINT", () => {
      this.rl?.close();
      process.exit(0);
    });
  }

  private exit(): void {
    this.rl?.close();
  }
}

export function startREPL(): void {
  const repl = new REPL();
  repl.start();
}
