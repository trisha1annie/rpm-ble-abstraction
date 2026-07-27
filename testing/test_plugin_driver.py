from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from ble_plugin.models import DecodedPayload
from ble_plugin.plugin_driver import DriverMeasurement, PluginDriver


class CompleteDriver:
    device_id = "AA:BB:CC:DD:EE:FF"

    async def start(self, on_measurement):
        return None

    async def stop(self):
        return None


class IncompleteDriver:
    device_id = "AA:BB:CC:DD:EE:FF"


def test_driver_measurement_preserves_boundary_values():
    payload = DecodedPayload(values={}, status_flags={})
    received_at = datetime(2026, 7, 28, tzinfo=timezone.utc)
    measurement = DriverMeasurement(
        device_id="AA:BB:CC:DD:EE:FF",
        service_uuid="00001810-0000-1000-8000-00805f9b34fb",
        characteristic_uuid="00002a35-0000-1000-8000-00805f9b34fb",
        payload=payload,
        received_at=received_at,
    )

    assert measurement.payload is payload
    assert measurement.received_at is received_at
    assert measurement.quality == {}


def test_driver_measurement_is_shallowly_frozen():
    measurement = DriverMeasurement(
        device_id="AA:BB:CC:DD:EE:FF",
        service_uuid="00001810-0000-1000-8000-00805f9b34fb",
        characteristic_uuid="00002a35-0000-1000-8000-00805f9b34fb",
        payload=DecodedPayload(values={}, status_flags={}),
        received_at=datetime.now(timezone.utc),
    )

    with pytest.raises(FrozenInstanceError):
        measurement.device_id = "other"


def test_runtime_protocol_accepts_complete_driver():
    assert isinstance(CompleteDriver(), PluginDriver)


def test_runtime_protocol_rejects_incomplete_driver():
    assert not isinstance(IncompleteDriver(), PluginDriver)
