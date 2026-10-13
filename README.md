# rpm-ble-abstraction

A sensor abstraction layer for heterogeneous BLE healthcare devices. It enables configuration-driven integration of physiological sensors through WoT Thing Descriptions, plugin drivers, and FHIR-based interoperability while providing built-in fault handling and extensibility.

# End-to-End Testing Guide

Guide for testing the `StandardPluginDriver` end-to-end using either real hardware devices or the BLE simulator.

---

## Real Devices Guide

### MAC Addresses

- **Weight Scale:** `64:69:4E:92:20:0D`
- **Pulse Oximeter:** `63:31:61:38:36:66`

### 1. Scan for Nearby Real Devices

Ensure the physical device is turned on and advertising, then run:

```bash
python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10
```

### 2. Run the Plugin Driver for Real Devices

Connect `StandardPluginDriver` to the target device using its MAC address:

#### Real Weight Scale
```bash
python -m ble_plugin.tools.inspect_driver --device-id 64:69:4E:92:20:0D --scan-timeout 5
```
*Take a measurement on the scale (e.g. step onto the platform) to transmit weight data.*

#### Real Pulse Oximeter
```bash
python -m ble_plugin.tools.inspect_driver --device-id 63:31:61:38:36:66 --scan-timeout 5
```
*Place a finger into the pulse oximeter sensor to measure and transmit SpO2 and pulse rate data.*

---

## BLE Simulator Guide

### 1. Start the BLE Simulator

#### Linux (Dual Adapters)

Requires two Bluetooth adapters (e.g. internal `hci1` for simulator, USB dongle `hci0` for scanner).

```bash
cd testing/ble-simulator
sudo systemctl start bluetooth
sudo hciconfig hci1 down
sudo BLENO_HCI_DEVICE_ID=1 HCI_CHANNEL_USER=1 node dist/index.js ./configs/bp.yaml
```

_(For weight scale, replace `./configs/bp.yaml` with `./configs/weight.yaml`)._

#### macOS (Single Adapter)

```bash
cd testing/ble-simulator
pnpm start ./configs/bp.yaml
```

---

### 2. Scan for the Device MAC Address

In a second terminal:

```bash
source .venv/bin/activate
python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10
```

Note the `BleModuleA` / `A&D_UA-651BLE` address (`<SIMULATOR_MAC>`).

---

### 3. Validate Raw Transport (Optional)

```bash
python -m ble_plugin.tools.inspect_ble_device \
  --device-id <SIMULATOR_MAC> \
  --characteristic 2A35 \
  --listen-seconds 30
```

In the simulator REPL, trigger a notification: `notify bp 120 80 72`.

---

### 4. Run the Plugin Driver

Test full route discovery, notification subscription, and payload decoding using `ble_plugin/tools/inspect_driver.py`:

```bash
python -m ble_plugin.tools.inspect_driver --device-id <SIMULATOR_MAC>
```

To also print FHIR Observations for supported routes:

```bash
python -m ble_plugin.tools.inspect_driver \
    --device-id <SIMULATOR_MAC> \
    --fhir --patient-reference Patient/example
```

In the simulator REPL, send notifications:

- Blood Pressure: `notify bp 120 80 72`
- Weight Scale: `notify weight 75.5 kg`

Press `Ctrl+C` to stop and disconnect. Use `--fhir` with the blood pressure, weight, or pulse-oximeter simulator. The pulse-oximeter simulator uses the proprietary YK route, which `src/fhir_mapping/yk_oximeter.yaml` maps to SpO2 and heart rate Observations.

The YK pulse oximeter is described by `src/wot/td/oxi.yaml` and `src/wot/bdo/oxi.yaml`. Only its 15-byte `0x81` measurement frames are decoded (SpO2, pulse rate, raw perfusion index). The real device also sends `0x80` waveform frames on the same characteristic. These fail the schema's `expected_value` check and are dropped, so add `--verbose` to see them.
