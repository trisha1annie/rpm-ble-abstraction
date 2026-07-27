"""Common driver boundary for a single live BLE device session."""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from .models import DecodedPayload


@dataclass(frozen=True)
class DriverMeasurement:
    """A decoded measurement emitted by a device driver."""

    device_id: str
    service_uuid: str
    characteristic_uuid: str
    payload: DecodedPayload
    received_at: datetime
    quality: Mapping[str, Any] = field(default_factory=dict)


MeasurementCallback = Callable[[DriverMeasurement], Awaitable[None] | None]


@runtime_checkable
class PluginDriver(Protocol):
    """Device-independent lifecycle boundary for a live BLE session."""

    @property
    def device_id(self) -> str:
        """Transport-specific identity of the live device."""
        ...

    async def start(self, on_measurement: MeasurementCallback) -> None:
        """Connect, subscribe, and begin emitting decoded measurements."""
        ...

    async def stop(self) -> None:
        """End subscriptions and close the device session."""
        ...
