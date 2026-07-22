from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Optional

from .schema import normalize_uuid


@dataclass(frozen=True)
class DiscoveredDevice:
    """
    Information available from BLE scanning, before a GATT connection.

    ``device_id`` is the backend transport address

    All UUIDs in ``advertised_service_uuids`` and ``service_data`` keys are
    normalised into lower-case 128-bit strings.
    """
    device_id: str
    name: Optional[str]
    rssi: Optional[int]
    advertised_service_uuids: frozenset[str]
    # Mapping keys are company identifiers (uint16); values are raw bytes.
    manufacturer_data: Mapping[int, bytes]
    # Keys are normalised 128-bit UUID strings; values are raw bytes.
    service_data: Mapping[str, bytes]


@dataclass(frozen=True)
class DiscoveredCharacteristic:
    """A single GATT characteristic as seen after connecting."""
    uuid: str  # Lower-case normalised 128-bit UUID
    properties: frozenset[str]  # e.g. frozenset({"notify", "read"})


@dataclass(frozen=True)
class DiscoveredService:
    """A single GATT service as seen after connecting."""
    uuid: str  # Lower-case normalised 128-bit UUID
    characteristics: tuple[DiscoveredCharacteristic, ...]


@dataclass(frozen=True)
class DiscoveredGatt:
    """Full GATT topology of a connected device."""
    device_id: str
    services: tuple[DiscoveredService, ...]
