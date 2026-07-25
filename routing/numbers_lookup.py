"""Lookup utilities for the vendored Bluetooth Numbers Database."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from routing.uuid_normalizer import normalize_uuid


class BluetoothNumbersLookup:
    """Load and query Bluetooth service definitions"""

    def __init__(self, database_directory: Path | None = None) -> None:
        if database_directory is None:
            project_root = Path(__file__).resolve().parents[1]

            database_directory = (
                project_root
                / "gatt_registry"
                / "vendor"
                / "bluetooth-numbers-database"
                / "v1"
            )

        self.database_directory = database_directory

        self._services = self._load_file(
            database_directory / "service_uuids.json"
        )

        self._characteristics = self._load_file(
            database_directory / "characteristic_uuids.json"
        )

    @staticmethod
    def _load_file(path: Path) -> dict[str, dict[str, Any]]:
        """Load a UUID JSON file and index each entry"""
        if not path.is_file():
            raise FileNotFoundError(
                f"Bluetooth Numbers Database file not found: {path}"
            )

        with path.open("r", encoding="utf-8") as file:
            entries = json.load(file)

        if not isinstance(entries, list):
            raise ValueError(
                f"Expected a JSON list in {path}, "
                f"but received {type(entries).__name__}."
            )

        index: dict[str, dict[str, Any]] = {}

        for entry in entries:
            uuid = normalize_uuid(entry["uuid"])
            index[uuid] = entry

        return index

    def get_service(self, uuid: str) -> dict[str, Any] | None:
        """Return service metadata, or None if the UUID is unknown."""
        return self._services.get(normalize_uuid(uuid))

    def get_characteristic(self, uuid: str) -> dict[str, Any] | None:
        """Return characteristic metadata, or None if unknown."""
        return self._characteristics.get(normalize_uuid(uuid))

    def has_service(self, uuid: str) -> bool:
        """Return True if the service exists anywhere in the database."""
        return self.get_service(uuid) is not None

    def has_characteristic(self, uuid: str) -> bool:
        """Return True if the characteristic exists in the database."""
        return self.get_characteristic(uuid) is not None

    def is_sig_service(self, uuid: str) -> bool:
        """Return True if the service is Bluetooth SIG-defined."""
        service = self.get_service(uuid)

        return (
            service is not None
            and service.get("source", "").casefold() == "gss"
        )

    def is_sig_characteristic(self, uuid: str) -> bool:
        """Return True if the characteristic is Bluetooth SIG-defined."""
        characteristic = self.get_characteristic(uuid)

        return (
            characteristic is not None
            and characteristic.get("source", "").casefold() == "gss"
        )

    def is_sig_pair(
        self,
        service_uuid: str,
        characteristic_uuid: str,
    ) -> bool:
        """Return True if both UUIDs are Bluetooth SIG-defined."""
        return (
            self.is_sig_service(service_uuid)
            and self.is_sig_characteristic(characteristic_uuid)
        )


if __name__ == "__main__":
    lookup = BluetoothNumbersLookup()

    print("Blood Pressure service:")
    print(lookup.get_service("1810"))

    print("\nBlood Pressure Measurement characteristic:")
    print(lookup.get_characteristic("2A35"))

    print("\nSIG-defined pair:")
    print(lookup.is_sig_pair("1810", "2A35"))