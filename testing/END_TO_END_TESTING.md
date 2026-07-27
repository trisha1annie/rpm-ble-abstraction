# End-to-End Testing Guide

Guide for testing the StandardPluginDriver end-to-end with ble-simulator

---

## 1. Start the BLE Simulator

### Linux (Dual Adapters)

Requires two Bluetooth adapters (e.g. internal `hci1` for simulator, USB dongle `hci0` for scanner).

```bash
cd testing/ble-simulator
sudo systemctl start bluetooth
sudo hciconfig hci1 down
sudo BLENO_HCI_DEVICE_ID=1 HCI_CHANNEL_USER=1 node dist/index.js ./configs/bp.yaml
```
*(For weight scale, replace `./configs/bp.yaml` with `./configs/weight.yaml`).*

### macOS (Single Adapter)

```bash
cd testing/ble-simulator
pnpm start ./configs/bp.yaml
```

---

## 2. Scan for the Device MAC Address

In a second terminal:

```bash
source .venv/bin/activate
python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10
```

Note the `BleModuleA` / `A&D_UA-651BLE` address (`<SIMULATOR_MAC>`).

---

## 3. Validate Raw Transport (Optional)

```bash
python -m ble_plugin.tools.inspect_ble_device \
  --device-id <SIMULATOR_MAC> \
  --characteristic 2A35 \
  --listen-seconds 30
```

In the simulator REPL, trigger a notification: `notify bp 120 80 72`.

---

## 4. Run the Plugin Driver

Test full route discovery, notification subscription, and payload decoding using ble_plugin/tools/inspect_driver.py

```bash
python -m ble_plugin.tools.inspect_driver --device-id <SIMULATOR_MAC>
```

In the simulator REPL, send notifications:
- Blood Pressure: `notify bp 120 80 72`
- Weight Scale: `notify weight 75.5 kg`

Press `Ctrl+C` to stop and disconnect.
