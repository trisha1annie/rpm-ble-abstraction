# Extending the BLE Simulator

This guide explains how to extend the BLE simulator with custom functionality, including new encoders, REPL commands, and device features.

## Table of Contents

- [Creating Device Configurations](#creating-device-configurations)
- [Adding REPL Commands](#adding-repl-commands)

## Creating Device Configurations

### Basic Device Configuration

Create a YAML file in `configs/`:

```yaml
name: "ShortName" # BLE advertised name (≤10 chars recommended)
displayName: "Full Device Name" # Display name for menus

services:
  - uuid: "0000180d-0000-1000-8000-00805f9b34fb" # Service UUID
    characteristics:
      - uuid: "00002a37-0000-1000-8000-00805f9b34fb" # Characteristic UUID
        name: "heart-rate" # Name for REPL commands
        properties: ["notify"] # BLE properties
        initial: "60" # Optional initial value
        encoder:
          type: "uint8" # Encoder type
```

> [!TIP]
> Keep the characteristic names short for easier typing and use in the REPL.

### Device Configuration Fields

| Field         | Required | Description                                      |
| ------------- | -------- | ------------------------------------------------ |
| `name`        | Yes      | BLE advertised name (keep short for advertising) |
| `displayName` | No       | Human-readable name shown in menus               |
| `services`    | Yes      | Array of BLE services                            |

### Service Fields

| Field             | Required | Description                               |
| ----------------- | -------- | ----------------------------------------- |
| `uuid`            | Yes      | 128-bit service UUID (standard or custom) |
| `characteristics` | Yes      | Array of characteristics                  |

### Characteristic Fields

| Field        | Required | Description                                                          |
| ------------ | -------- | -------------------------------------------------------------------- |
| `uuid`       | Yes      | 128-bit characteristic UUID                                          |
| `name`       | Yes      | Unique name for REPL commands                                        |
| `properties` | Yes      | Array: `read`, `write`, `writeWithoutResponse`, `notify`, `indicate` |
| `initial`    | No       | Initial value (string or numeric)                                    |
| `encoder`    | No       | Encoder configuration                                                |

## Adding REPL Commands

### Step 1: Define Command Handler

Edit `src/lib/repl/index.ts` in the `initializeCommands()` method:

```typescript
private initializeCommands(): Record<string, Command> {
  return {
    // ... existing commands ...

    mycommand: {
      description: "My custom command",
      usage: "mycommand <arg>",
      handler: async (args) => this.handleMyCommand(args),
    },
  };
}
```

### Step 2: Implement Handler

Add the handler method in the same file:

```typescript
private async handleMyCommand(args: string[]): Promise<void> {
  if (args.length === 0) {
    console.log(chalk.red("❌ Missing argument"));
    console.log(chalk.gray("   Usage: mycommand <arg>"));
    return;
  }

  const arg = args[0];
  console.log(chalk.green(`✅ Executed with: ${arg}`));

  // Your command logic here
}
```

### Step 3: Add Autocomplete (Optional)

Edit `src/lib/repl/autocomplete.ts`:

```typescript
private getCommandCompletions(line: string): readline.CompleterResult {
  const commands = Object.keys(this.commands);
  const hits = commands.filter((cmd) => cmd.startsWith(line));
  return [hits.length ? hits : commands, line];
}
```
