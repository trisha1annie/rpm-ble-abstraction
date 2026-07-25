"""
Hardware-free unit tests for the Bleak transport adapter.

All tests inject fake Bleak-like objects through BleakBleClient._backend or
by monkey-patching BleakScanner.discover.  No real BLE adapter is required.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ble_plugin.bleak_client import BleakBleClient, BleakScannerAdapter, _device_from_adv
from ble_plugin.discovery_models import DiscoveredDevice
from ble_plugin.exceptions import (
    BleNotConnectedError,
    BleSubscriptionError,
    BleTransportError,
)
from ble_plugin.schema import normalise_uuid


# ---------------------------------------------------------------------------
# Fake Bleak data structures
# ---------------------------------------------------------------------------

class FakeBLEDevice:
    """Minimal stand-in for bleak.backends.device.BLEDevice."""
    def __init__(self, address: str, name: str | None = None):
        self.address = address
        self.name = name


class FakeAdvertisementData:
    """Minimal stand-in for bleak.backends.scanner.AdvertisementData."""
    def __init__(
        self,
        local_name: str | None = None,
        rssi: int | None = None,
        service_uuids: list[str] | None = None,
        manufacturer_data: dict[int, bytes] | None = None,
        service_data: dict[str, bytes] | None = None,
    ):
        self.local_name = local_name
        self.rssi = rssi
        self.service_uuids = service_uuids or []
        self.manufacturer_data = manufacturer_data or {}
        self.service_data = service_data or {}


def fake_discover_result(*pairs) -> dict[str, tuple[FakeBLEDevice, FakeAdvertisementData]]:
    """
    Build a Mapping[address, (BLEDevice, AdvertisementData)] like
    BleakScanner.discover(return_adv=True) produces.
    """
    return {dev.address: (dev, adv) for dev, adv in pairs}


# ---------------------------------------------------------------------------
# Fake GATT backend
# ---------------------------------------------------------------------------

class FakeChar:
    def __init__(self, uuid: str, properties: list[str]):
        self.uuid = uuid
        self.properties = properties


class FakeService:
    def __init__(self, uuid: str, chars: list[FakeChar]):
        self.uuid = uuid
        self.characteristics = chars


class FakeBleakBackend:
    """Minimal async stand-in for bleak.BleakClient."""

    def __init__(self, services=None, connect_raises=None, start_notify_raises=None):
        self._connected = False
        self._services = services or []
        self._connect_raises = connect_raises
        self._start_notify_raises = start_notify_raises
        self._notifiers: dict[str, Any] = {}
        self.services = []  # populated after connect

    async def connect(self):
        if self._connect_raises:
            raise self._connect_raises
        self._connected = True
        self.services = self._services

    async def disconnect(self):
        self._connected = False

    async def start_notify(self, uuid, callback):
        if self._start_notify_raises:
            raise self._start_notify_raises
        self._notifiers[uuid] = callback

    async def stop_notify(self, uuid):
        self._notifiers.pop(uuid, None)

    def fire(self, uuid, data: bytes):
        """Trigger a notification for testing."""
        if uuid in self._notifiers:
            self._notifiers[uuid](None, bytearray(data))


# Scanner tests (tests 1-4): exercise the return_adv=True code path

@pytest.mark.asyncio
async def test_scanner_16bit_and_128bit_uuid_normalisation():
    """16-bit and full 128-bit advertised UUIDs must both be normalised."""
    dev = FakeBLEDevice("AA:BB:CC:DD:EE:FF", "Scale")
    adv = FakeAdvertisementData(
        local_name="Scale",
        service_uuids=["181D", "00002a9d-0000-1000-8000-00805f9b34fb"],
    )
    result = fake_discover_result((dev, adv))

    with patch(
        "ble_plugin.bleak_client.BleakScanner.discover",
        new=AsyncMock(return_value=result),
    ):
        scanner = BleakScannerAdapter()
        devices = await scanner.scan(timeout_seconds=5.0)

    assert len(devices) == 1
    assert normalise_uuid("181D") in devices[0].advertised_service_uuids
    assert normalise_uuid("2a9d") in devices[0].advertised_service_uuids


@pytest.mark.asyncio
async def test_scanner_name_priority_and_absent():
    """adv.local_name takes priority over ble_device.name; both absent -> None."""
    # Case A: local_name is set
    dev_a = FakeBLEDevice("AA:00:00:00:00:01", name="device-name")
    adv_a = FakeAdvertisementData(local_name="adv-name")

    # Case B: only ble_device.name
    dev_b = FakeBLEDevice("AA:00:00:00:00:02", name="fallback-name")
    adv_b = FakeAdvertisementData(local_name=None)

    # Case C: neither name
    dev_c = FakeBLEDevice("AA:00:00:00:00:03", name=None)
    adv_c = FakeAdvertisementData(local_name=None)

    result = fake_discover_result((dev_a, adv_a), (dev_b, adv_b), (dev_c, adv_c))

    with patch(
        "ble_plugin.bleak_client.BleakScanner.discover",
        new=AsyncMock(return_value=result),
    ):
        devices = {d.device_id: d for d in await BleakScannerAdapter().scan(5.0)}

    assert devices["AA:00:00:00:00:01"].name == "adv-name"
    assert devices["AA:00:00:00:00:02"].name == "fallback-name"
    assert devices["AA:00:00:00:00:03"].name is None


@pytest.mark.asyncio
async def test_scanner_rssi_present_and_absent():
    """RSSI is taken from adv_data.rssi; None when absent."""
    dev_a = FakeBLEDevice("BB:00:00:00:00:01")
    adv_a = FakeAdvertisementData(rssi=-65)

    dev_b = FakeBLEDevice("BB:00:00:00:00:02")
    adv_b = FakeAdvertisementData(rssi=None)

    result = fake_discover_result((dev_a, adv_a), (dev_b, adv_b))

    with patch(
        "ble_plugin.bleak_client.BleakScanner.discover",
        new=AsyncMock(return_value=result),
    ):
        devices = {d.device_id: d for d in await BleakScannerAdapter().scan(5.0)}

    assert devices["BB:00:00:00:00:01"].rssi == -65
    assert devices["BB:00:00:00:00:02"].rssi is None


@pytest.mark.asyncio
async def test_scanner_service_data_keys_normalised_and_manufacturer_data_copied():
    """service_data keys are normalised; manufacturer_data is copied."""
    dev = FakeBLEDevice("CC:00:00:00:00:01")
    adv = FakeAdvertisementData(
        service_data={"181D": b"\x01\x02"},
        manufacturer_data={0x0075: b"\xAA\xBB"},
    )
    result = fake_discover_result((dev, adv))

    with patch(
        "ble_plugin.bleak_client.BleakScanner.discover",
        new=AsyncMock(return_value=result),
    ):
        devices = await BleakScannerAdapter().scan(5.0)

    d = devices[0]
    assert normalise_uuid("181D") in d.service_data
    assert d.service_data[normalise_uuid("181D")] == b"\x01\x02"
    assert d.manufacturer_data[0x0075] == b"\xAA\xBB"


# ---------------------------------------------------------------------------
# GATT mapping tests (tests 5-7)
# ---------------------------------------------------------------------------

def make_backend_with_services():
    return FakeBleakBackend(services=[
        FakeService("1810", [
            FakeChar("2A35", ["Indicate", "Read"]),
        ]),
    ])


@pytest.mark.asyncio
async def test_gatt_service_uuid_is_normalised():
    client = BleakBleClient("DD:00:00:00:00:01", _backend=make_backend_with_services())
    await client.connect()
    gatt = await client.discover_gatt()
    assert gatt.services[0].uuid == normalise_uuid("1810")


@pytest.mark.asyncio
async def test_gatt_characteristic_uuid_is_normalised():
    client = BleakBleClient("DD:00:00:00:00:02", _backend=make_backend_with_services())
    await client.connect()
    gatt = await client.discover_gatt()
    assert gatt.services[0].characteristics[0].uuid == normalise_uuid("2A35")


@pytest.mark.asyncio
async def test_gatt_properties_are_lowercase():
    client = BleakBleClient("DD:00:00:00:00:03", _backend=make_backend_with_services())
    await client.connect()
    gatt = await client.discover_gatt()
    props = gatt.services[0].characteristics[0].properties
    assert props == frozenset({"indicate", "read"})


# ---------------------------------------------------------------------------
# Pre-connection guard tests (tests 8-9)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discover_gatt_before_connect_raises():
    client = BleakBleClient("EE:00:00:00:00:01", _backend=FakeBleakBackend())
    with pytest.raises(BleNotConnectedError):
        await client.discover_gatt()


@pytest.mark.asyncio
async def test_subscribe_before_connect_raises():
    client = BleakBleClient("EE:00:00:00:00:02", _backend=FakeBleakBackend())
    with pytest.raises(BleNotConnectedError):
        await client.subscribe("2a35", lambda u, d: None)


# ---------------------------------------------------------------------------
# Notification callback tests (tests 10-11)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sync_callback_receives_normalised_uuid_and_exact_bytes():
    backend = FakeBleakBackend(services=[
        FakeService("1810", [FakeChar("2A35", ["indicate"])]),
    ])
    client = BleakBleClient("FF:00:00:00:00:01", _backend=backend)
    await client.connect()

    received = []

    def cb(uuid, data):
        received.append((uuid, data))

    await client.subscribe("2A35", cb)
    raw = b"\x00\x78\x00\x50\x00\x5A\x00"
    backend.fire(normalise_uuid("2A35"), raw)

    assert len(received) == 1
    assert received[0][0] == normalise_uuid("2A35")
    assert received[0][1] == raw



@pytest.mark.asyncio
async def test_async_callback_is_awaited():
    backend = FakeBleakBackend(services=[
        FakeService("1810", [FakeChar("2A35", ["indicate"])]),
    ])
    client = BleakBleClient("FF:00:00:00:00:02", _backend=backend)
    await client.connect()

    awaited = []

    async def async_cb(uuid, data):
        awaited.append((uuid, data))

    await client.subscribe("2A35", async_cb)
    backend.fire(normalise_uuid("2A35"), b"\x01\x02")

    # Yield to the event loop so ensure_future can run the coroutine.
    await asyncio.sleep(0)

    assert len(awaited) == 1
    assert awaited[0][1] == b"\x01\x02"


# ---------------------------------------------------------------------------
# State management tests (tests 12–13)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disconnect_clears_connection_and_subscription_state():
    backend = FakeBleakBackend(services=[
        FakeService("1810", [FakeChar("2A35", ["indicate"])]),
    ])
    client = BleakBleClient("FF:00:00:00:00:03", _backend=backend)
    await client.connect()
    await client.subscribe("2A35", lambda u, d: None)

    assert client.is_connected
    assert normalise_uuid("2A35") in client._subscriptions

    await client.disconnect()

    assert not client.is_connected
    assert client._subscriptions == {}


@pytest.mark.asyncio
async def test_backend_connect_error_wrapped_as_ble_transport_error():
    backend = FakeBleakBackend(connect_raises=OSError("adapter off"))
    client = BleakBleClient("FF:00:00:00:00:04", _backend=backend)

    with pytest.raises(BleTransportError) as exc_info:
        await client.connect()

    assert "FF:00:00:00:00:04" in str(exc_info.value)
    assert not client.is_connected
