import { registry } from "../registry";
import type { Command } from "./types";

export class AutocompleteHandler {
  constructor(
    private commands: Record<string, Command>,
    private getAvailableConfigs: () => Map<string, string>
  ) {}

  complete(line: string): [string[], string] {
    const parts = line.trim().split(/\s+/);
    const commandName = parts[0];
    const argIndex = parts.length - 1;

    if (parts.length === 1) {
      return this.completeCommand(commandName);
    }

    return this.completeArgument(commandName, argIndex, parts[argIndex] || "");
  }

  private completeCommand(partial: string): [string[], string] {
    const commandNames = Object.keys(this.commands);
    const hits = commandNames.filter((c) => c.startsWith(partial));
    return [hits.length ? hits : commandNames, partial];
  }

  private completeArgument(
    commandName: string,
    argIndex: number,
    currentArg: string
  ): [string[], string] {
    const cmd = this.commands[commandName];
    if (!cmd) return [[], currentArg];

    if (["read", "write", "notify"].includes(commandName) && argIndex === 1) {
      return this.completeCharacteristic(currentArg);
    }

    if (commandName === "switch" && argIndex === 1) {
      return this.completeDevice(currentArg);
    }

    return [[], currentArg];
  }

  private completeCharacteristic(partial: string): [string[], string] {
    const charNames = Object.keys(registry);
    const hits = charNames.filter((c) => c.startsWith(partial));
    return [hits.length ? hits : charNames, partial];
  }

  private completeDevice(partial: string): [string[], string] {
    const deviceNames = Array.from(this.getAvailableConfigs().keys());

    const hits = deviceNames.filter((d) => d.startsWith(partial));
    return [hits.length ? hits : deviceNames, partial];
  }
}
