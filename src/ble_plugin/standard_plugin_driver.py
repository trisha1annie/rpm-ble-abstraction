"""Default driver for BLE route resolution."""
from __future__ import annotations

import inspect
import logging
import asyncio
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from .ble_client import BleClient
from .exceptions import UnexpectedFieldValueError
from .models import DecodedPayload
from .plugin_driver import DriverMeasurement, MeasurementCallback, PluginDriver
from .schema import normalise_uuid
from fault_handling.stream_handler import StreamHandler

_log = logging.getLogger(__name__)

_GENERIC_ATTRIBUTE_SERVICE_UUID = normalise_uuid("1801")
_SERVICE_CHANGED_CHARACTERISTIC_UUID = normalise_uuid("2A05")
_SKIP_SERVICE_UUIDS = frozenset({_GENERIC_ATTRIBUTE_SERVICE_UUID})
_SKIP_CHARACTERISTIC_UUIDS = frozenset({_SERVICE_CHANGED_CHARACTERISTIC_UUID})


class DriverLifecycleError(RuntimeError):
    pass


def _decode_notification(
    service_uuid: str,
    characteristic_uuid: str,
    payload: bytes,
) -> DecodedPayload:
    from routing.router import router

    return router(service_uuid, characteristic_uuid, payload)


def _supports_route(service_uuid: str, characteristic_uuid: str) -> bool:
    from routing.router import supports_route

    return supports_route(service_uuid, characteristic_uuid)


class StandardPluginDriver:
    def __init__(
        self,
        client: BleClient,
        quality: Mapping[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._quality = dict(quality or {})
        self._on_measurement: MeasurementCallback | None = None
        self._subscriptions: dict[str, str] = {}
        self._started = False
        self._stream_handlers: dict[str, StreamHandler] = {}
        self._dropout_task: asyncio.Task | None = None

    @property
    def device_id(self) -> str:
        return self._client.device_id

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def subscribed_characteristics(self) -> frozenset[str]:
        return frozenset(self._subscriptions)

    
    async def start(self, on_measurement: MeasurementCallback) -> None:
        if self._started:
            raise DriverLifecycleError("Driver has already started")

        self._on_measurement = on_measurement
        self._client.set_disconnected_callback(
            self._handle_unexpected_disconnect
        )

        try:
            await self._client.connect()
            gatt = await self._client.discover_gatt()

            for service in gatt.services:
                service_uuid = normalise_uuid(service.uuid)

                for characteristic in service.characteristics:
                    if not {"notify", "indicate"}.intersection(
                        characteristic.properties
                    ):
                        continue

                    characteristic_uuid = normalise_uuid(
                        characteristic.uuid
                    )

                    if not _supports_route(
                        service_uuid, characteristic_uuid
                    ):
                        continue

                    if characteristic_uuid in self._subscriptions:
                        raise DriverLifecycleError(
                            "A notification characteristic UUID occurs "
                            "in multiple services: "
                            f"{characteristic_uuid}"
                        )

                    # Register timing state before subscribing
                    self._stream_handlers[characteristic_uuid] = StreamHandler()
                    self._subscriptions[characteristic_uuid] = service_uuid

                    await self._client.subscribe(
                        characteristic_uuid,
                        self._notification_callback,
                    )

            self._started = True

            if self._stream_handlers:
                self._dropout_task = asyncio.create_task(
                    self._monitor_dropouts()
                )

        except Exception:
            await self.stop()
            raise


    async def stop(self) -> None:
        subscriptions = tuple(self._subscriptions)
        self._subscriptions.clear()
        self._started = False
        self._on_measurement = None
        self._client.set_disconnected_callback(None)

        if self._dropout_task is not None:
            self._dropout_task.cancel()

            try:
                await self._dropout_task
            except asyncio.CancelledError:
                pass

            self._dropout_task = None

        self._stream_handlers.clear()

        for characteristic_uuid in subscriptions:
            await self._client.unsubscribe(characteristic_uuid)
        await self._client.disconnect()

    async def _notification_callback(
        self,
        characteristic_uuid: str,
        payload: bytes,
    ) -> None:
        normalised_uuid = normalise_uuid(characteristic_uuid)
        service_uuid = self._subscriptions.get(normalised_uuid)
        callback = self._on_measurement
        if service_uuid is None or callback is None:
            return
        
        self._process_notification_timing(normalised_uuid)

        try:
            decoded = _decode_notification(service_uuid, normalised_uuid, payload)
        except UnexpectedFieldValueError as exc:
            # Devices can interleave other frame types (e.g. waveform data) on a
            # measurement characteristic, so mismatches are routine, not faults.
            _log.debug(
                "Ignoring notification from %s service %s characteristic %s "
                "that does not match its schema: %s",
                self.device_id,
                service_uuid,
                normalised_uuid,
                exc,
            )
            return
        except Exception as exc:
            _log.warning(
                "Unable to decode notification from %s service %s "
                "characteristic %s: %s",
                self.device_id,
                service_uuid,
                normalised_uuid,
                exc,
            )
            return

        result = callback(
            DriverMeasurement(
                device_id=self.device_id,
                service_uuid=service_uuid,
                characteristic_uuid=normalised_uuid,
                payload=decoded,
                received_at=datetime.now(timezone.utc),
                quality=self._quality,
            )
        )
        if inspect.isawaitable(result):
            await result

    async def _handle_unexpected_disconnect(self) -> None:
        task = self._dropout_task
        self._dropout_task = None

        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._stream_handlers.clear()
        self._subscriptions.clear()
        self._started = False
        self._on_measurement = None
    
    def _process_notification_timing(
        self,
        characteristic_uuid: str,
    ) -> None:
        handler = self._stream_handlers.get(characteristic_uuid)

        if handler is None:
            return

        was_dropout = handler.dropout_active
        interval = handler.check_notification(time.monotonic())

        if was_dropout:
            _log.info(
                "Notification stream recovered: %s",
                characteristic_uuid,
            )

        if interval is None:
            return

        if handler.baseline is None:
            baseline = handler.establish_baseline(sample_size=10)

            if baseline is not None:
                _log.info(
                    "Timing baseline established for %s: %.2f ms",
                    characteristic_uuid,
                    baseline[0] * 1000,
                )
            return

        rate_changed = handler.detect_rate_change(interval)

        if rate_changed:
            _log.warning(
                "Notification rate changed for %s: %.2f Hz",
                characteristic_uuid,
                1 / handler.baseline[0],
            )

        else:
            if handler.detect_anomaly(interval, handler.baseline):
                _log.warning(
                    "Timing anomaly detected for %s",
                    characteristic_uuid,
                )

        jitter = handler.calculate_jitter_window(size=10)

        if jitter is not None and handler.detect_jitter(
            jitter, threshold=0.03
        ):
            _log.warning(
                "High jitter for %s: %.2f ms",
                characteristic_uuid,
                jitter * 1000,
            )
    
    async def _monitor_dropouts(self) -> None:
        while True:
            await asyncio.sleep(0.1)

            current_time = time.monotonic()

            for characteristic_uuid, handler in self._stream_handlers.items():
                if handler.baseline is None:
                    continue

                median_interval, mad = handler.baseline
                timeout = 3 * median_interval

                event = handler.monitor_dropout(
                    current_time,
                    timeout,
                )

                if event == "dropout_detected":
                    _log.warning(
                        "Notification dropout detected for %s",
                        characteristic_uuid,
                    )
