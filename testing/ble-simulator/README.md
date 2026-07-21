# BLE Peripheral Simulator

A flexible Bluetooth Low Energy (BLE) peripheral simulator that allows you to simulate various medical and IoT devices using YAML configuration files.

## Features

- 🎛️ **YAML-based Configuration**: Define devices, services, and characteristics in simple YAML files
- 🔄 **Runtime Device Switching**: Switch between different device configurations without restarting
- 🎨 **Automatic Data Encoding**: Built-in encoders for common BLE profiles (Blood Pressure, Pulse Oximeter, Weight Scale, etc.)
- 🧪 **Interactive REPL**: Test and control devices with an interactive command-line interface
- 🔌 **Extensible**: Easy to add custom encoders and device configurations
- 📱 **Multi-Device Support**: Simulate multiple device types from a single application

## Quick Start

### Installation

```bash
# Install dependencies
pnpm install

# Build the project (optional)
pnpm build
```

### Running the Simulator

Start the simulator by passing a config to use when the app first starts.

```bash
# Development mode
pnpm dev ./configs/yk-oximeter.yaml

# Or after building
pnpm start ./configs/yk-oximeter.yaml
```

### Basic Usage

Once the simulator is running, you'll have an interactive REPL where you can:

```bash
# List all available characteristics
> list

# Write data to a characteristic (auto-encoded)
> write oxi 98 72

# Send a notification
> notify oxi 98 72

# Switch to a different device
> devices
> switch 1

# Get help
> help

# Exit
> exit
```

## Device Configurations

The simulator comes with three pre-configured medical devices:

### 1. **YK Pulse Oximeter** (`yk-oximeter`)

- Measures SpO2 (blood oxygen saturation) and pulse rate
- Custom proprietary protocol format

**Example Usage:**

```bash
> notify oxi 98 72    # SpO2: 98%, Pulse: 72 bpm
```

### 2. **A&D UA-651 Blood Pressure Monitor** (`and-ua651-blood-pressure`)

- Measures systolic, diastolic blood pressure and pulse rate
- Follows IEEE-11073 SFLOAT encoding standard

**Example Usage:**

```bash
> write bp 120 80 72  # Systolic: 120, Diastolic: 80, Pulse: 72
```

### 3. **A&D UC-352 Weight Scale** (`and-uc352-weight-scale`)

- Measures weight in kg or lb
- Follows BLE Weight Scale profile

**Example Usage:**

```bash
> notify weight 75.5 kg    # 75.5 kg
> notify weight 165 lb     # 165 lb
```

## REPL Commands

| Command                     | Description                                        | Example              |
| --------------------------- | -------------------------------------------------- | -------------------- |
| `help`                      | Show all available commands                        | `help`               |
| `list`                      | List all characteristics with their current values | `list`               |
| `read <char>`               | Read a characteristic value                        | `read battery-level` |
| `write <char> <values...>`  | Write to a characteristic                          | `write bp 120 80 72` |
| `notify <char> <values...>` | Send a notification to subscribed clients          | `notify oxi 98 72`   |
| `devices`                   | List all available device configurations           | `devices`            |
| `switch <device>`           | Switch to a different device (by name or number)   | `switch 2`           |
| `exit`                      | Exit the simulator                                 | `exit`               |

## Creating Custom Devices

### 1. Create a YAML Configuration File

See [Creating Device Configurations](docs/EXTENDING.md/#creating-device-configurations) for more information.

## Available Encoders

The simulator includes several built-in encoders for common BLE data formats:

| Encoder          | Description                      | Example Usage            |
| ---------------- | -------------------------------- | ------------------------ |
| `blood-pressure` | IEEE-11073 SFLOAT blood pressure | `write bp 120 80 72`     |
| `pulse-oximeter` | YK oximeter proprietary format   | `notify oxi 98 72`       |
| `weight-scale`   | BLE Weight Scale profile         | `notify weight 75.5 kg`  |
| `battery-level`  | Battery percentage (0-100)       | `write battery-level 85` |
| `uint8`          | 8-bit unsigned integer (0-255)   | `write value 42`         |
| `uint16`         | 16-bit unsigned integer          | `write value 1234`       |
| `uint32`         | 32-bit unsigned integer          | `write value 12345`      |
| `text`           | Plain UTF-8 text                 | `write name "Hello"`     |

For detailed encoder specifications, see [ENCODERS.md](docs/ENCODERS.md).

## Creating Custom Encoders

See [Creating Custom Encoders](docs/ENCODERS.md/#creating-custom-encoders) for more information.

## Project Structure

```
ble-simulator/
├── configs/                    # Device configuration files
│   ├── and-ua651-blood-pressure.yaml
│   ├── and-uc352-weight-scale.yaml
│   └── yk-oximeter.yaml
├── docs/                       # Documentation
│   ├── ENCODERS.md            # Encoder specifications
│   └── MULTI-DEVICE.md        # Multi-device usage guide
├── src/
│   ├── index.ts               # Entry point
│   ├── types.ts               # TypeScript type definitions
│   └── lib/
│       ├── characteristic.ts  # BLE characteristic implementation
│       ├── encoder-registry.ts # Data encoders
│       ├── peripheral.ts      # BLE peripheral management
│       ├── registry.ts        # Characteristic registry
│       ├── service.ts         # BLE service implementation
│       ├── utils.ts           # Utility functions
│       └── repl/              # Interactive REPL
│           ├── index.ts
│           ├── command-handlers.ts
│           ├── device-manager.ts
│           ├── autocomplete.ts
│           └── fuzzy-matcher.ts
├── package.json
└── tsconfig.json
```

## Requirements

- **Node.js**: v18 or higher (for ES modules support)
- **macOS**: This repo has **not** been tested on Linux, only on macOS. That being said, it should work with little intervention.
- **Bluetooth Hardware**: Built-in or USB Bluetooth adapter

## Troubleshooting

### Permission Denied

**Error**: `Operation not permitted`

**Solution**: On Linux, you may need to run with sudo or grant capabilities:

```bash
sudo setcap cap_net_raw+eip $(eval readlink -f `which node`)
```

### Device Name Too Long

Device names are truncated by the library during advertising, so if you are relying on matching the name to connect to a device, this may be the culprit.
