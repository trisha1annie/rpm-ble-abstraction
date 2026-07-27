"""Route BLE payloads to their respective decoding schemas."""

from pathlib import Path

from .uuid_normalizer import normalize_uuid
from .numbers_lookup import BluetoothNumbersLookup

from ble_plugin.decoder import decode
from ble_plugin.exceptions import SchemaLoadError
from ble_plugin.models import DecodedPayload
from ble_plugin.yaml_loader import load_schema

BLUETOOTH_BASE_UUID_SUFFIX = "-0000-1000-8000-00805F9B34FB"


class RoutingError(Exception):
    """Raised when the router cannot find a suitable decoding schema."""


def router(
    service_uuid: str,
    characteristic_uuid: str,
    payload: bytes,
) -> DecodedPayload:
    """Find the matching schema and decode a BLE payload."""

    normalized_service_uuid = normalize_uuid(service_uuid)
    normalized_characteristic_uuid = normalize_uuid(characteristic_uuid)

    project_root = Path(__file__).resolve().parents[1]
    lookup = BluetoothNumbersLookup()

    if lookup.is_sig_pair(
        normalized_service_uuid,
        normalized_characteristic_uuid,
    ):
        schema_directory = (
            project_root
            / "gatt_registry"
            / "decode_registry"
        )
    else:
        schema_directory = (
            project_root
            / "wot"
        )

    if not schema_directory.is_dir():
        raise RoutingError(
            f"Schema directory does not exist: {schema_directory}"
        )

    schema_paths = list(schema_directory.rglob("*.yaml"))

    for schema_path in schema_paths:
        try:
            schema = load_schema(str(schema_path))
        except SchemaLoadError:
            continue

        normalized_schema_service_uuid = normalize_uuid(
            schema.service.uuid
        )

        if normalized_schema_service_uuid != normalized_service_uuid:
            continue

        matching_characteristic = any(
            normalize_uuid(schema_characteristic.uuid)
            == normalized_characteristic_uuid
            for schema_characteristic in schema.characteristics
        )

        if not matching_characteristic:
            continue
        
        full_characteristic_uuid = (
            f"0000{normalized_characteristic_uuid}"
            f"{BLUETOOTH_BASE_UUID_SUFFIX}"
        )

        return decode(
            schema=schema,
            characteristic_uuid=full_characteristic_uuid,
            payload=payload,
        )

    raise RoutingError(
        "No matching schema found for "
        f"service {normalized_service_uuid} and "
        f"characteristic {normalized_characteristic_uuid}"
    )

if __name__ == "__main__":
    result = router(
        service_uuid="1810",
        characteristic_uuid="2A35",
        payload=bytes.fromhex("00800050005D00"),
    )
