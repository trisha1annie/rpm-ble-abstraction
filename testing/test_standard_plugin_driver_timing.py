import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ble_plugin.standard_plugin_driver import StandardPluginDriver
from ble_plugin.schema import normalise_uuid


SERVICE_UUID = normalise_uuid("1810")
CHARACTERISTIC_UUID = normalise_uuid("2A35")
SECOND_CHARACTERISTIC_UUID = normalise_uuid("2A36")

DRIVER_MODULE = "ble_plugin.standard_plugin_driver"


class MockBleClient:
    def __init__(self, characteristics=None):
        if characteristics is None:
            characteristics = [CHARACTERISTIC_UUID]

        self.device_id = "test-device"
        self.connected = False
        self.disconnected_callback = None
        self.notification_callbacks = {}

        self.gatt = SimpleNamespace(
            services=[
                SimpleNamespace(
                    uuid=SERVICE_UUID,
                    characteristics=[
                        SimpleNamespace(
                            uuid=uuid,
                            properties={"notify"},
                        )
                        for uuid in characteristics
                    ],
                )
            ]
        )

    def set_disconnected_callback(self, callback):
        self.disconnected_callback = callback

    async def connect(self):
        self.connected = True

    async def discover_gatt(self):
        return self.gatt

    async def subscribe(self, characteristic_uuid, callback):
        self.notification_callbacks[characteristic_uuid] = callback

    async def unsubscribe(self, characteristic_uuid):
        self.notification_callbacks.pop(characteristic_uuid, None)

    async def disconnect(self):
        self.connected = False

    async def emit(self, characteristic_uuid, payload=b"\x00"):
        callback = self.notification_callbacks[characteristic_uuid]
        await callback(characteristic_uuid, payload)


@pytest.fixture
def mock_client():
    return MockBleClient()


@pytest.fixture
def measurement_callback():
    return AsyncMock()


async def start_driver(client, measurement_callback):
    driver = StandardPluginDriver(client)

    with patch(
        f"{DRIVER_MODULE}._supports_route",
        return_value=True,
    ):
        await driver.start(measurement_callback)

    return driver


"""Test timing integration without waiting."""
def send_timestamps(driver, characteristic_uuid, timestamps):
    for timestamp in timestamps:
        with patch(
            f"{DRIVER_MODULE}.time.monotonic",
            return_value=timestamp,
        ):
            driver._process_notification_timing(characteristic_uuid)


# Handler creation
@pytest.mark.asyncio
async def test_creates_stream_handler_for_each_characteristic(
    measurement_callback,
):
    client = MockBleClient(
        characteristics=[
            CHARACTERISTIC_UUID,
            SECOND_CHARACTERISTIC_UUID,
        ]
    )

    driver = await start_driver(client, measurement_callback)

    try:
        assert driver.is_started is True

        assert CHARACTERISTIC_UUID in driver._stream_handlers
        assert SECOND_CHARACTERISTIC_UUID in driver._stream_handlers

        assert (
            driver._stream_handlers[CHARACTERISTIC_UUID]
            is not driver._stream_handlers[SECOND_CHARACTERISTIC_UUID]
        )

    finally:
        await driver.stop()


# Dropout monitor startup
@pytest.mark.asyncio
async def test_dropout_monitor_starts(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        assert driver._dropout_task is not None
        assert driver._dropout_task.done() is False

    finally:
        await driver.stop()


# Baseline establishment
@pytest.mark.asyncio
async def test_baseline_established_after_fifty_intervals(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        # 51 notifications produce 50 intervals at 5 Hz
        timestamps = [i * 0.2 for i in range(51)]

        send_timestamps(
            driver,
            CHARACTERISTIC_UUID,
            timestamps,
        )

        handler = driver._stream_handlers[CHARACTERISTIC_UUID]

        assert len(handler.intervals) == 50
        assert handler.baseline is not None

        median_interval, mad = handler.baseline

        assert median_interval == pytest.approx(0.2)
        assert mad == pytest.approx(0.0)

    finally:
        await driver.stop()


# Malformed notifications still count for timing
@pytest.mark.asyncio
async def test_malformed_notification_still_updates_timing(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        with patch(
            f"{DRIVER_MODULE}.time.monotonic",
            side_effect=[0.0, 0.2],
        ), patch(
            f"{DRIVER_MODULE}._decode_notification",
            side_effect=ValueError("Malformed payload"),
        ):
            await mock_client.emit(CHARACTERISTIC_UUID)
            await mock_client.emit(CHARACTERISTIC_UUID)

        handler = driver._stream_handlers[CHARACTERISTIC_UUID]

        assert handler.intervals == pytest.approx([0.2])

        measurement_callback.assert_not_awaited()

    finally:
        await driver.stop()


# Missed dropout from arrival gap
@pytest.mark.asyncio
async def test_missed_dropout_detected_from_arrival_gap(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        handler = driver._stream_handlers[CHARACTERISTIC_UUID]
        handler.baseline = (0.2, 0.01)

        send_timestamps(
            driver,
            CHARACTERISTIC_UUID,
            [0.0, 0.2, 0.85, 1.05],
        )

        assert handler.last_notification_dropout is True
        assert handler.pending_long_gap is False
        assert handler.dropout_active is False

        assert handler.jitter_intervals == pytest.approx([0.2])

    finally:
        await driver.stop()


# Sustained rate change
@pytest.mark.asyncio
async def test_rate_change_updates_baseline(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        handler = driver._stream_handlers[CHARACTERISTIC_UUID]

        # Begin with a 5 Hz baseline
        handler.baseline = (0.2, 0.01)

        # Start at t=0, then send five 500 ms intervals
        timestamps = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

        send_timestamps(
            driver,
            CHARACTERISTIC_UUID,
            timestamps,
        )

        # New frequency is 2 Hz
        assert handler.baseline[0] == pytest.approx(0.5)

        assert handler.rate_change_window == []
        assert handler.jitter_intervals == []

    finally:
        await driver.stop()


# Known slowdown edge case
@pytest.mark.asyncio
async def test_large_slowdown_updates_baseline(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        handler = driver._stream_handlers[CHARACTERISTIC_UUID]

        # Original frequency: 10 Hz.
        handler.baseline = (0.1, 0.005)

        # New frequency: 2 Hz.
        timestamps = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

        send_timestamps(
            driver,
            CHARACTERISTIC_UUID,
            timestamps,
        )

        assert handler.baseline[0] == pytest.approx(0.5)

    finally:
        await driver.stop()


# Stop cleanup
@pytest.mark.asyncio
async def test_stop_cleans_up_monitoring(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    task = driver._dropout_task

    await driver.stop()

    assert driver.is_started is False
    assert driver._dropout_task is None
    assert task.done() is True

    assert driver._stream_handlers == {}
    assert driver._subscriptions == {}

    assert mock_client.connected is False


#Unexpected disconnect cleanup
@pytest.mark.asyncio
async def test_unexpected_disconnect_cleans_up_monitoring(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    task = driver._dropout_task

    await driver._handle_unexpected_disconnect()

    assert driver.is_started is False
    assert driver._dropout_task is None
    assert task.done() is True

    assert driver._stream_handlers == {}
    assert driver._subscriptions == {}

@pytest.mark.asyncio
async def test_realtime_slowdown_with_dropout_monitor(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        handler = driver._stream_handlers[CHARACTERISTIC_UUID]

        # Start with established 10 Hz baseline
        handler.baseline = (0.1, 0.005)

        # Establish the first notification timestamp using a background dropout monitor.
        driver._process_notification_timing(CHARACTERISTIC_UUID)

        # Simulate a sustained transition to 2 Hz
        # Each notification arrives approximately every 500 ms
        for _ in range(6):
            await asyncio.sleep(0.5)
            driver._process_notification_timing(CHARACTERISTIC_UUID)

        # The handler should eventually recognise 2 Hz
        assert handler.baseline[0] == pytest.approx(0.5, abs=0.08)

        # The stream should reset a dropout state
        assert handler.dropout_active is False

    finally:
        await driver.stop()
    

@pytest.mark.asyncio
async def test_realtime_dropout_and_recovery(
    mock_client,
    measurement_callback,
):
    driver = await start_driver(mock_client, measurement_callback)

    try:
        handler = driver._stream_handlers[CHARACTERISTIC_UUID]

        # Establish a 5 Hz baseline
        handler.baseline = (0.2, 0.01)

        driver._process_notification_timing(CHARACTERISTIC_UUID)

        # Stop notifications to exceed the 600 ms dropout timeout
        await asyncio.sleep(0.8)
        assert handler.dropout_active is True

        # First notification after interruption.
        driver._process_notification_timing(CHARACTERISTIC_UUID)

        # The stream is active again but the gap is classified
        assert handler.dropout_active is False
        assert handler.pending_long_gap is False
        assert handler.last_notification_dropout is False

        # Wait for a normal interval
        await asyncio.sleep(0.2)

        driver._process_notification_timing(CHARACTERISTIC_UUID)

        # Normal notifications resume after the detected dropout
        assert handler.last_notification_dropout is False
        assert handler.pending_long_gap is False
        assert handler.dropout_active is False

        # The recovery gap does not contaminate the jitter calculation.
        assert len(handler.jitter_intervals) == 1
        assert handler.jitter_intervals[0] == pytest.approx(
            0.2,
            abs=0.05,
        )

    finally:
        await driver.stop()