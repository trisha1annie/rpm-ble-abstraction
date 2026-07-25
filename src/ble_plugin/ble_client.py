"""
BLE Interface - other test scripts interact with BLE client here
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from .discovery_models import DiscoveredDevice, DiscoveredGatt

# Notification callback receives (normalised_uuid, raw_bytes).
NotificationCallback = Callable[[str, bytes], Awaitable[None] | None]


@runtime_checkable
class BleScanner(Protocol):
    """Protocol for transport-level BLE scanning."""

    async def scan(self, timeout_seconds: float) -> tuple[DiscoveredDevice, ...]:
        """
        Scan for BLE advertisements for ``timeout_seconds`` and return one
        ``DiscoveredDevice`` per unique backend address observed.
        """
        ...


@runtime_checkable
class BleClient(Protocol):
    """
    Protocol for a transport-level BLE client managing a single device connection.
    """

    @property
    def device_id(self) -> str:
        """BLE Address."""
        ...

    @property
    def is_connected(self) -> bool:
        """True when an active GATT connection is held."""
        ...

    async def connect(self) -> None:
        """
        Establish a GATT connection to the device.

        Raises ``BleTransportError`` (or a subclass) on failure.
        """
        ...

    async def disconnect(self) -> None:
        """
        Close the GATT connection if one is active.

        Safe to call after a failed ``connect()`` or when already disconnected.
        """
        ...

    async def discover_gatt(self) -> DiscoveredGatt:
        """
        Read the GATT service/characteristic topology of the connected device.

        Raises ``BleNotConnectedError`` if not connected.
        Raises ``BleDiscoveryError`` on backend failure.
        """
        ...

    async def subscribe(
        self,
        characteristic_uuid: str,
        callback: NotificationCallback,
    ) -> None:
        """
        Start notifications or indications for ``characteristic_uuid``.

        The callback will receive ``(normalised_uuid, bytes)`` for each packet.

        Raises ``BleNotConnectedError`` if not connected.
        Raises ``BleSubscriptionError`` if the UUID is already subscribed or
        if the backend rejects the request.
        """
        ...

    async def unsubscribe(self, characteristic_uuid: str) -> None:
        """
        Stop notifications or indications for ``characteristic_uuid``.
        """
        ...
