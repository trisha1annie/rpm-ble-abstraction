"""Default driver for BLE route resolution."""
from __future__ import annotations

import inspect
import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from .ble_client import BleClient
from .models import DecodedPayload
from .plugin_driver import DriverMeasurement, MeasurementCallback, PluginDriver
from .schema import normalise_uuid

_log = logging.getLogger(__name__)


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
        self._client.set_disconnected_callback(self._handle_unexpected_disconnect)
        try:
            await self._client.connect()
            gatt = await self._client.discover_gatt()
            for service in gatt.services:
                service_uuid = normalise_uuid(service.uuid)
                if service_uuid in _SKIP_SERVICE_UUIDS:
                    continue
                for characteristic in service.characteristics:
                    if not {"notify", "indicate"}.intersection(characteristic.properties):
                        continue
                    characteristic_uuid = normalise_uuid(characteristic.uuid)
                    if characteristic_uuid in _SKIP_CHARACTERISTIC_UUIDS:
                        continue
                    if not _supports_route(service_uuid, characteristic_uuid):
                        continue
                    if characteristic_uuid in self._subscriptions:
                        raise DriverLifecycleError(
                            "A notification characteristic UUID occurs in multiple "
                            f"services: {characteristic_uuid}"
                        )
                    await self._client.subscribe(
                        characteristic_uuid,
                        self._notification_callback,
                    )
                    self._subscriptions[characteristic_uuid] = service_uuid
            self._started = True
        except Exception:
            await self.stop()
            raise

    async def stop(self) -> None:
        subscriptions = tuple(self._subscriptions)
        self._subscriptions.clear()
        self._started = False
        self._on_measurement = None
        self._client.set_disconnected_callback(None)

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

        try:
            decoded = _decode_notification(service_uuid, normalised_uuid, payload)
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
        self._subscriptions.clear()
        self._started = False
        self._on_measurement = None
