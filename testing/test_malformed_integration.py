import pytest

from ble_plugin.standard_plugin_driver import StandardPluginDriver


SERVICE_UUID = "00001810-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "00002a35-0000-1000-8000-00805f9b34fb"


class FakeBleClient:
    def __init__(self):
        self.device_id = "test-bp-device"


@pytest.mark.asyncio
async def test_real_malformed_payload_recovery(caplog):
    client = FakeBleClient()
    driver = StandardPluginDriver(client)

    measurements = []

    async def on_measurement(measurement):
        measurements.append(measurement)

    # Register the characteristic and measurement callback.
    # This bypasses BLE transport, but not decoding.
    driver._subscriptions[CHAR_UUID] = SERVICE_UUID
    driver._on_measurement = on_measurement

    # Blood Pressure Measurement:
    # Flags = 0x00
    # Systolic = 100 (SFLOAT)
    # Diastolic = 80 (SFLOAT)
    # MAP = 90 (SFLOAT)
    valid_payload = bytes.fromhex("00 64 00 50 00 5A 00")

    # Missing required measurement bytes
    malformed_payload = bytes.fromhex("00 64 00")

    # Valid notification
    await driver._notification_callback(CHAR_UUID, valid_payload)

    # Malformed notification
    await driver._notification_callback(CHAR_UUID, malformed_payload)

    #Valid notification after malformed one
    await driver._notification_callback(CHAR_UUID, valid_payload)

    # Valid measurements should be forwarded.
    assert len(measurements) == 2

    assert measurements[0].device_id == "test-bp-device"
    assert measurements[1].device_id == "test-bp-device"

    assert measurements[0].characteristic_uuid == CHAR_UUID
    assert measurements[1].characteristic_uuid == CHAR_UUID

    # Confirm the actual decoded values.
    first_payload = measurements[0].payload

    assert first_payload.values["systolic"].physical_value == 100
    assert first_payload.values["diastolic"].physical_value == 80

    # Confirm the malformed notification was logged
    assert "Payload rejected due to critical quality flags" in caplog.text