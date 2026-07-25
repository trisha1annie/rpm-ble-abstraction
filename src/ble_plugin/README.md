# BLE Transport Plugin

The `ble_plugin` transport layer provides a interface for discovering BLE physiological sensors, reading GATT topologies, and subscribing to live measurement notifications.

---

## 3 Quick CLI Commands

### 1. Scan Nearby Bluetooth Devices
Scan the airwaves for 10 seconds to discover nearby device names and addresses (`device_id`):

```powershell
python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10
```

---

### 2. Connect & Print GATT Topology
Connect to a device by its address to list all available GATT services and characteristics:

```powershell
python -m ble_plugin.tools.inspect_ble_device --device-id AA:BB:CC:DD:EE:FF
```

---

### 3. Subscribe & Stream Live Notifications
Subscribe to a specific characteristic to stream incoming raw hex measurement packets with UTC timestamps for 30 seconds:

```powershell
python -m ble_plugin.tools.inspect_ble_device `
    --device-id AA:BB:CC:DD:EE:FF `
    --characteristic cdeacd81-5235-4c07-8846-93a37ee6b86d `
    --listen-seconds 30
```
