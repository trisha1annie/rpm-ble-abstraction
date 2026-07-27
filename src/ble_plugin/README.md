# BLE Transport Plugin

The `ble_plugin` transport layer provides an interface for discovering BLE physiological sensors, reading GATT topologies, and subscribing to measurement notifications.

---

## CLI Inspection Commands

Use [inspect_ble_device.py](file:///home/sunnymug/Desktop/uni/rpm-ble-abstraction/src/ble_plugin/tools/inspect_ble_device.py) to scan, connect, and stream notifications.

### 1. Scan Nearby Devices
```bash
python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10
```

### 2. Connect and Print GATT Topology
```bash
python -m ble_plugin.tools.inspect_ble_device --device-id <MAC_ADDRESS>
```

### 3. Subscribe and Stream Live Data
```bash
python -m ble_plugin.tools.inspect_ble_device \
    --device-id <MAC_ADDRESS> \
    --characteristic cdeacd81-5235-4c07-8846-93a37ee6b86d \
    --listen-seconds 20
```

---

## Local Testing with BLE Simulator


### Linux (Requires Dual Adapters)

Linux requires two Bluetooth radios (e.g. internal adapter `hci1` and USB dongle `hci0`).

1. **Terminal 1: Start Simulator on `hci1`**
   ```bash
   sudo systemctl start bluetooth
   sudo hciconfig hci1 down
   cd testing/ble-simulator
   sudo BLENO_HCI_DEVICE_ID=1 HCI_CHANNEL_USER=1 node dist/index.js ./configs/oxi.yaml
   ```

2. **Terminal 2: Scan & Connect via Python**
   ```bash
   source .venv/bin/activate
   python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10
   ```

3. **Stream Notifications**
   Run the inspect command with the `BleModuleA` MAC address, then in Terminal 1 REPL type `notify oxi 98 72`.

---

### macOS (Single Adapter)

macOS natively shares a single Bluetooth adapter.

1. **Terminal 1: Start Simulator**
   ```bash
   cd testing/ble-simulator
   pnpm start ./configs/oxi.yaml
   ```

2. **Terminal 2: Scan & Connect**
   ```bash
   source .venv/bin/activate
   python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10
   ```
