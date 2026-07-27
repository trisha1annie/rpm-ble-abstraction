import asyncio
import logging
from collections.abc import Awaitable, Callable
from unittest.mock import Mock

import pytest

from ble_plugin.discovery_models import (
    DiscoveredCharacteristic,
    DiscoveredGatt,
    DiscoveredService,
)
from ble_plugin.models import DecodedPayload, DecodedValue
from ble_plugin.plugin_driver import PluginDriver
from ble_plugin.schema import normalise_uuid
from ble_plugin import standard_plugin_driver
from ble_plugin.standard_plugin_driver import (
    DriverLifecycleError,
    StandardPluginDriver,
)


class FakeBleClient:
    def __init__(self, gatt: DiscoveredGatt) -> None:
        self._gatt = gatt
        self.connected = False
        self.subscriptions: dict[
            str, Callable[[str, bytes], Awaitable[None] | None]
        ] = {}
        self.unsubscribed: list[str] = []
        self.disconnected_callback = None

    @property
    def device_id(self) -> str:
        return self._gatt.device_id

    @property
    def is_connected(self) -> bool:
        return self.connected

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False
        self.subscriptions.clear()

    async def discover_gatt(self) -> DiscoveredGatt:
        return self._gatt

    async def subscribe(self, characteristic_uuid, callback) -> None:
        self.subscriptions[normalise_uuid(characteristic_uuid)] = callback

    async def unsubscribe(self, characteristic_uuid) -> None:
        normalised_uuid = normalise_uuid(characteristic_uuid)
        self.unsubscribed.append(normalised_uuid)
        self.subscriptions.pop(normalised_uuid, None)

    def set_disconnected_callback(self, callback) -> None:
        self.disconnected_callback = callback

    async def fire(self, characteristic_uuid: str, payload: bytes) -> None:
        normalised_uuid = normalise_uuid(characteristic_uuid)
        callback = self.subscriptions[normalised_uuid]
        result = callback(normalised_uuid, payload)
        if result is not None:
            await result

    async def disconnect_unexpectedly(self) -> None:
        self.connected = False
        self.subscriptions.clear()
        if self.disconnected_callback is not None:
            result = self.disconnected_callback()
            if result is not None:
                await result


def make_gatt() -> DiscoveredGatt:
    return DiscoveredGatt(
        device_id="AA:BB:CC:DD:EE:FF",
        services=(
            DiscoveredService(
                uuid=normalise_uuid("181D"),
                characteristics=(
                    DiscoveredCharacteristic(
                        uuid=normalise_uuid("2A9D"),
                        properties=frozenset({"indicate"}),
                    ),
                    DiscoveredCharacteristic(
                        uuid=normalise_uuid("2A9E"),
                        properties=frozenset({"read"}),
                    ),
                ),
            ),
            DiscoveredService(
                uuid=normalise_uuid("180F"),
                characteristics=(
                    DiscoveredCharacteristic(
                        uuid=normalise_uuid("2A19"),
                        properties=frozenset({"notify"}),
                    ),
                ),
            ),
        ),
    )


def make_single_measurement_gatt(
    service_uuid: str,
    characteristic_uuid: str,
) -> DiscoveredGatt:
    return DiscoveredGatt(
        device_id="AA:BB:CC:DD:EE:FF",
        services=(
            DiscoveredService(
                uuid=normalise_uuid(service_uuid),
                characteristics=(
                    DiscoveredCharacteristic(
                        uuid=normalise_uuid(characteristic_uuid),
                        properties=frozenset({"indicate"}),
                    ),
                ),
            ),
        ),
    )


def test_driver_subscribes_to_all_notifiable_characteristics_and_emits(
    monkeypatch,
):
    async def exercise():
        client = FakeBleClient(make_gatt())
        driver = StandardPluginDriver(client)
        measurements = []
        decode_notification = Mock(
            return_value=DecodedPayload(
                values={"weight": DecodedValue(15100, 75.5, "kg")},
                status_flags={},
            )
        )
        monkeypatch.setattr(
            standard_plugin_driver,
            "_decode_notification",
            decode_notification,
        )

        await driver.start(measurements.append)
        await client.fire("2A9D", b"\x00\xFC\x3A")

        assert isinstance(driver, PluginDriver)
        assert driver.subscribed_characteristics == {
            normalise_uuid("2A9D"),
            normalise_uuid("2A19"),
        }
        assert len(measurements) == 1
        assert measurements[0].service_uuid == normalise_uuid("181D")
        assert measurements[0].characteristic_uuid == normalise_uuid("2A9D")
        assert measurements[0].payload.values["weight"].physical_value == 75.5
        decode_notification.assert_called_once_with(
            normalise_uuid("181D"),
            normalise_uuid("2A9D"),
            b"\x00\xFC\x3A",
        )

    asyncio.run(exercise())


def test_driver_stop_unsubscribes_and_disconnects():
    async def exercise():
        client = FakeBleClient(make_gatt())
        driver = StandardPluginDriver(client)

        await driver.start(lambda measurement: None)
        await driver.stop()

        assert not driver.is_started
        assert not client.connected
        assert client.unsubscribed == [normalise_uuid("2A9D"), normalise_uuid("2A19")]
        assert driver.subscribed_characteristics == frozenset()

    asyncio.run(exercise())


def test_driver_rejects_duplicate_start():
    async def exercise():
        client = FakeBleClient(make_gatt())
        driver = StandardPluginDriver(client)

        await driver.start(lambda measurement: None)

        with pytest.raises(DriverLifecycleError):
            await driver.start(lambda measurement: None)

    asyncio.run(exercise())


def test_driver_cleans_state_after_unexpected_disconnect():
    async def exercise():
        client = FakeBleClient(make_gatt())
        driver = StandardPluginDriver(client)

        await driver.start(lambda measurement: None)
        await client.disconnect_unexpectedly()

        assert not driver.is_started
        assert driver.subscribed_characteristics == frozenset()

    asyncio.run(exercise())


def test_driver_continues_after_router_error(monkeypatch, caplog):
    async def exercise():
        client = FakeBleClient(make_single_measurement_gatt("181D", "2A9D"))
        driver = StandardPluginDriver(client)
        measurements = []
        monkeypatch.setattr(
            standard_plugin_driver,
            "_decode_notification",
            Mock(side_effect=ValueError("unsupported payload")),
        )

        await driver.start(measurements.append)
        await client.fire("2A9D", b"\x00\xFC\x3A")

        assert measurements == []
        assert driver.is_started
        assert driver.subscribed_characteristics == {normalise_uuid("2A9D")}

    caplog.set_level(logging.WARNING, logger="ble_plugin.standard_plugin_driver")
    asyncio.run(exercise())
    assert "Unable to decode notification" in caplog.text
