"""
Bleak-backed BLE transport adapter.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .ble_client import BleClient, BleScanner, NotificationCallback
from .discovery_models import (
    DiscoveredCharacteristic,
    DiscoveredDevice,
    DiscoveredGatt,
    DiscoveredService,
)
from .exceptions import (
    BleDiscoveryError,
    BleNotConnectedError,
    BleSubscriptionError,
    BleTransportError,
)
from .schema import normalize_uuid

_log = logging.getLogger(__name__)


def _device_from_adv(ble_device: BLEDevice, adv_data: AdvertisementData) -> DiscoveredDevice:
    """Convert a Bleak (BLEDevice, AdvertisementData) pair to a DiscoveredDevice."""
    service_uuids = frozenset(
        normalize_uuid(u) for u in (adv_data.service_uuids or [])
    )
    service_data = {
        normalize_uuid(k): bytes(v)
        for k, v in (adv_data.service_data or {}).items()
    }
    # Copy mutable manufacturer_data into a plain dict with immutable values.
    manufacturer_data = {
        company_id: bytes(payload)
        for company_id, payload in (adv_data.manufacturer_data or {}).items()
    }
    return DiscoveredDevice(
        device_id=ble_device.address,
        name=adv_data.local_name or ble_device.name or None,
        rssi=adv_data.rssi if adv_data.rssi is not None else None,
        advertised_service_uuids=service_uuids,
        manufacturer_data=manufacturer_data,
        service_data=service_data,
    )


class BleakScannerAdapter:
    """
    ``BleScanner`` implementation backed by Bleak.

    Uses ``BleakScanner.discover(return_adv=True)`` so that each result
    includes the paired ``AdvertisementData``.  Plain ``discover()`` returns
    only ``BLEDevice`` objects, which carry none of the advertisement payload.
    """

    async def scan(self, timeout_seconds: float) -> tuple[DiscoveredDevice, ...]:
        """
        Scan for BLE devices for ``timeout_seconds``.

        Returns one ``DiscoveredDevice`` per unique backend address.
        """
        if timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be positive, got {timeout_seconds}")

        try:
            results: dict[str, tuple[BLEDevice, AdvertisementData]] = (
                await BleakScanner.discover(
                    timeout=timeout_seconds,
                    return_adv=True,
                )
            )
        except Exception as exc:
            raise BleTransportError(
                f"BLE scan failed: {exc}", operation="scan"
            ) from exc

        devices = []
        for _address, (ble_device, adv_data) in results.items():
            try:
                devices.append(_device_from_adv(ble_device, adv_data))
            except Exception as exc:
                # Log and skip malformed advertisement data rather than
                # discarding the entire scan result.
                _log.warning("Skipping device %s: %s", ble_device.address, exc)

        return tuple(devices)


class BleakBleClient:
    """
    ``BleClient`` implementation backed by Bleak.

    Parameters
    device_id:
        The opaque backend address supplied by ``BleakScannerAdapter.scan()``.
    _backend:
        Private parameter for injecting a pre-constructed ``BleakClient`` in
        unit tests.
    """

    def __init__(self, device_id: str, _backend: Optional[BleakClient] = None) -> None:
        self._device_id = device_id
        # Test-only
        self._backend = _backend
        self._connected = False
        # Tracks active subscriptions: normalised UUID -> Bleak callback wrapper.
        self._subscriptions: dict[str, Any] = {}

    # --- BleClient protocol ---

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Connect to the device. Wraps Bleak errors as ``BleTransportError``."""
        if self._backend is None:
            self._backend = BleakClient(self._device_id)
        try:
            await self._backend.connect()
            self._connected = True
            _log.debug("Connected to %s", self._device_id)
        except Exception as exc:
            self._connected = False
            raise BleTransportError(
                f"Failed to connect: {exc}",
                device_id=self._device_id,
                operation="connect",
            ) from exc

    async def disconnect(self) -> None:
        """
        Disconnect from the device.  Safe to call after a failed connect or
        when already disconnected.
        """
        self._connected = False
        self._subscriptions.clear()
        if self._backend is not None:
            try:
                await self._backend.disconnect()
            except Exception as exc:
                # Only raise for genuine transport errors, not for "already
                # disconnected" states which are routine on teardown.
                _log.warning("Disconnect for %s raised: %s", self._device_id, exc)
                raise BleTransportError(
                    f"Error during disconnect: {exc}",
                    device_id=self._device_id,
                    operation="disconnect",
                ) from exc

    async def discover_gatt(self) -> DiscoveredGatt:
        """
        Read GATT services and characteristics from the connected device.

        Raises ``BleNotConnectedError`` if no connection is active.
        Raises ``BleDiscoveryError`` on backend failure.
        """
        if not self._connected:
            raise BleNotConnectedError(
                "discover_gatt() requires an active connection",
                device_id=self._device_id,
                operation="discover_gatt",
            )
        try:
            services = self._backend.services
        except Exception as exc:
            raise BleDiscoveryError(
                f"GATT discovery failed: {exc}",
                device_id=self._device_id,
                operation="discover_gatt",
            ) from exc

        discovered_services = []
        for service in services:
            chars = []
            for char in service.characteristics:
                chars.append(
                    DiscoveredCharacteristic(
                        uuid=normalize_uuid(str(char.uuid)),
                        properties=frozenset(p.lower() for p in char.properties),
                    )
                )
            discovered_services.append(
                DiscoveredService(
                    uuid=normalize_uuid(str(service.uuid)),
                    characteristics=tuple(chars),
                )
            )

        return DiscoveredGatt(
            device_id=self._device_id,
            services=tuple(discovered_services),
        )

    async def subscribe(
        self,
        characteristic_uuid: str,
        callback: NotificationCallback,
    ) -> None:
        """
        Start notifications/indications for ``characteristic_uuid``.

        The callback receives ``(normalised_uuid, bytes)`` for every packet.
        Awaitable callbacks are scheduled on the running event loop via
        ``asyncio.ensure_future``.

        Raises ``BleNotConnectedError`` if not connected.
        Raises ``BleSubscriptionError`` if the UUID is already subscribed.
        """
        if not self._connected:
            raise BleNotConnectedError(
                "subscribe() requires an active connection",
                device_id=self._device_id,
                operation="subscribe",
            )

        normalised = normalize_uuid(characteristic_uuid)

        if normalised in self._subscriptions:
            raise BleSubscriptionError(
                f"UUID {normalised} already has an active subscription",
                device_id=self._device_id,
                operation="subscribe",
            )

        def _bleak_callback(_sender: Any, data: bytearray) -> None:
            result = callback(normalised, bytes(data))
            if asyncio.iscoroutine(result):
                asyncio.ensure_future(result)

        try:
            await self._backend.start_notify(normalised, _bleak_callback)
            self._subscriptions[normalised] = _bleak_callback
            _log.debug("Subscribed to %s on %s", normalised, self._device_id)
        except Exception as exc:
            raise BleSubscriptionError(
                f"Failed to subscribe to {normalised}: {exc}",
                device_id=self._device_id,
                operation="subscribe",
            ) from exc

    async def unsubscribe(self, characteristic_uuid: str) -> None:
        """
        Stop notifications/indications for ``characteristic_uuid``.
        does nothing if the UUID is not currently subscribed.
        """
        normalised = normalize_uuid(characteristic_uuid)
        if normalised not in self._subscriptions:
            return

        try:
            await self._backend.stop_notify(normalised)
        except Exception as exc:
            _log.warning("stop_notify for %s raised: %s", normalised, exc)
        finally:
            self._subscriptions.pop(normalised, None)

