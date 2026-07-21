# BLE Data Encoders

This document explains the encoder system in the BLE simulator, including available encoders, their formats, and how to create custom encoders.

## Table of Contents

- [Available Encoders](#available-encoders)
  - [`blood-pressure`](#blood-pressure)
  - [`pulse-oximeter`](#pulse-oximeter)
  - [`weight-scale`](#weight-scale)
  - [`battery-level`](#battery-level)
  - [`text`](#text)
  - [`uint8`](#uint8)
  - [`uint16`](#uint16)
  - [`uint32`](#uint32)
- [Using Encoders in YAML](#using-encoders-in-yaml)
- [Using Encoders in REPL](#using-encoders-in-repl)
- [Creating Custom Encoders](#creating-custom-encoders)
- [Buffer Utilities](#buffer-utilities)
- [References](#references)

## Available Encoders

### `blood-pressure`

Encodes blood pressure measurements with systolic, diastolic, and pulse rate values using the IEEE-11073 SFLOAT format.

**Binary Format:**

- Byte 0: Flags (0x04 = pulse rate present)
- Bytes 1-2: Systolic pressure (IEEE-11073 SFLOAT)
- Bytes 3-4: Diastolic pressure (IEEE-11073 SFLOAT)
- Bytes 5-6: Pulse rate (IEEE-11073 SFLOAT)

**YAML Configuration:**

```yaml
- uuid: "00002a35-0000-1000-8000-00805f9b34fb"
  name: "bp"
  properties: ["indicate"]
  encoder:
    type: "blood-pressure"
```

**REPL Usage:**

```bash
write bp 120 80 72       # Systolic: 120 mmHg, Diastolic: 80 mmHg, Pulse: 72 bpm
notify bp 130 85 75      # Send as notification
```

**Arguments:** `<systolic> <diastolic> <pulse>`

---

### `pulse-oximeter`

Encodes pulse oximeter measurements with SpO2 percentage and pulse rate. Uses YK oximeter proprietary format.

**Binary Format:**

- Byte 0: Flag (0x81)
- Byte 1: SpO2 percentage
- Byte 2: Pulse rate
- Byte 4: Reserved (0x00)
- Byte 9: Reserved (0x00)
- Total: 10 bytes

**YAML Configuration:**

```yaml
- uuid: "cdeacd81-5235-4c07-8846-93a37ee6b86d"
  name: "oxi"
  properties: ["notify", "read"]
  encoder:
    type: "pulse-oximeter"
```

**REPL Usage:**

```bash
notify oxi 98 72         # SpO2: 98%, Pulse: 72 bpm
write oxi 95 80          # SpO2: 95%, Pulse: 80 bpm
```

**Arguments:** `<spo2> <pulse>`

---

### `weight-scale`

Encodes weight measurements according to BLE Weight Scale Profile (0x2A9D).

**Binary Format:**

- Byte 0: Flags (0x00 = kg, 0x01 = lb)
- Bytes 1-2: Weight encoded (kg: weight × 200, lb: weight × 100)

**YAML Configuration:**

```yaml
- uuid: "00002a9d-0000-1000-8000-00805f9b34fb"
  name: "weight"
  properties: ["indicate"]
  encoder:
    type: "weight-scale"
```

**REPL Usage:**

```bash
notify weight 75.5 kg    # 75.5 kilograms (default)
notify weight 165 lb     # 165 pounds
write weight 80          # 80 kg (unit defaults to kg)
```

**Arguments:** `<weight> [unit]` where unit is `kg` or `lb` (defaults to `kg`)

---

### `battery-level`

Encodes battery level as a percentage (0-100) according to BLE Battery Service (0x2A19).

**Binary Format:**

- Byte 0: Battery percentage (0-100)

**YAML Configuration:**

```yaml
- uuid: "00002a19-0000-1000-8000-00805f9b34fb"
  name: "battery-level"
  properties: ["read", "notify"]
  encoder:
    type: "battery-level"
```

**REPL Usage:**

```bash
write battery-level 85   # Set to 85%
notify battery-level 50  # Send notification with 50%
```

**Arguments:** `<percentage>` (0-100)

---

### `text`

Plain UTF-8 text encoding for string values.

**Binary Format:**

- UTF-8 encoded string bytes

**YAML Configuration:**

```yaml
- uuid: "00002a23-0000-1000-8000-00805f9b34fb"
  name: "system-id"
  properties: ["read"]
  encoder:
    type: "text"
```

**REPL Usage:**

```bash
write system-id "MyDevice"
write name "Hello World"
```

**Arguments:** `<text>` (any string, spaces allowed)

---

### `uint8`

Unsigned 8-bit integer encoding (0-255).

**Binary Format:**

- Byte 0: Value (0-255)

**YAML Configuration:**

```yaml
encoder:
  type: "uint8"
```

**REPL Usage:**

```bash
write value 42
write status 255
```

**Arguments:** `<value>` (0-255)

---

### `uint16`

Unsigned 16-bit integer encoding (0-65535).

**Binary Format:**

- Bytes 0-1: Value in little-endian format

**YAML Configuration:**

```yaml
encoder:
  type: "uint16"
```

**REPL Usage:**

```bash
write value 1234
write counter 65000
```

**Arguments:** `<value>` (0-65535)

---

### `uint32`

Unsigned 32-bit integer encoding (0-4294967295).

**Binary Format:**

- Bytes 0-3: Value in little-endian format

**YAML Configuration:**

```yaml
- uuid: "00002a49-0000-1000-8000-00805f9b34fb"
  name: "bp-feature"
  properties: ["read"]
  encoder:
    type: "uint32"
```

**REPL Usage:**

```bash
write feature 12345
write counter 1000000
```

**Arguments:** `<value>` (0-4294967295)

**Arguments:** `<value>` (0-4294967295)

---

## Using Encoders in YAML

To use an encoder, add an `encoder` section to any characteristic:

```yaml
characteristics:
  - uuid: "00002a35-0000-1000-8000-00805f9b34fb"
    name: "bp"
    properties: ["indicate"]
    encoder:
      type: "blood-pressure" # Required: encoder type
```

### Optional: Initial Values

You can specify an initial value that will be set when the device starts:

```yaml
- uuid: "00002a19-0000-1000-8000-00805f9b34fb"
  name: "battery-level"
  properties: ["read", "notify"]
  initial: "100" # Initial battery at 100%
  encoder:
    type: "battery-level"
```

## Using Encoders in REPL

### Write Command

Write to a characteristic using its encoder.

```bash
write <characteristic> <values...>
```

Examples:

```bash
write bp 120 80 72           # Blood pressure with pulse
write battery-level 85       # Battery percentage
write oxi 98 72              # Pulse oximeter
write weight 75.5 kg         # Weight in kg
```

### Notify Command

Send a notification to subscribed clients. For the most part, this will be the command to use when testing
a subscription based connection.

> [!IMPORTANT]
> The notify command will only work if there is at least one client listening for that particular characteristic.

```bash
notify <characteristic> <values...>
```

Examples:

```bash
notify oxi 98 72             # Notify SpO2 and pulse
notify battery-level 50      # Notify low battery
notify weight 165 lb         # Notify weight in pounds
```

## Creating Custom Encoders

To add a new encoder, edit `src/lib/encoder-registry.ts`:

### Step 1: Define the Encoder

```typescript
export const encoders: EncoderRegistry = {
  // ... existing encoders ...

  "my-custom-encoder": {
    encode: (value1: number, value2: string) => {
      // Allocate buffer (adjust size as needed)
      const buffer = Buffer.alloc(4);

      // Write your data
      buffer.writeUInt16LE(value1, 0);
      buffer.writeUInt8(value2 === "on" ? 1 : 0, 2);

      return buffer;
    },
    description: "My custom encoder - value and on/off state",
    example: "123 on",
  },
};
```

### Step 2: Add Argument Parsing

If your encoder needs custom argument parsing, update the `parseEncoderArgs` method in `src/lib/repl/command-handlers.ts`:

```typescript
private parseEncoderArgs(encoderType: string, values: string[]): any[] {
  switch (encoderType) {
    // ... existing cases ...

    case "my-custom-encoder":
      if (values.length < 2) {
        throw new Error("Requires: <value> <on|off>");
      }
      return [parseInt(values[0]), values[1]];

    default:
      return values.map((v) => {
        const num = parseFloat(v);
        return isNaN(num) ? v : num;
      });
  }
}
```

### Step 3: Use in YAML

```yaml
- uuid: "12345678-1234-1234-1234-123456789abc"
  name: "my-char"
  properties: ["read", "write", "notify"]
  encoder:
    type: "my-custom-encoder"
```

## Buffer Utilities

The simulator provides utility functions in `src/lib/utils.ts`:

### `encodeSFloat(value: number): number`

Encodes a number as IEEE-11073 SFLOAT (16-bit).

```typescript
const encoded = encodeSFloat(120.5); // For blood pressure
buffer.writeUInt16LE(encoded, 0);
```

## References

- [Bluetooth GATT Specifications](https://www.bluetooth.com/specifications/specs/)
- [IEEE 11073-20601 Health Informatics](https://standards.ieee.org/standard/11073-20601-2008.html)
- [Node.js Buffer Documentation](https://nodejs.org/api/buffer.html)
