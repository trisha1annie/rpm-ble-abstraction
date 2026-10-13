"""Route BLE payloads to their respective decoding schemas."""

from pathlib import Path

from .numbers_lookup import BluetoothNumbersLookup
from ble_plugin.td_loader import load_wot_schema
from .uuid_normalizer import normalize_uuid
from ble_plugin.decoder import decode
from ble_plugin.exceptions import SchemaLoadError
from ble_plugin.models import DecodedPayload
from ble_plugin.yaml_loader import load_schema

project_root = Path(__file__).resolve().parents[1]


class RoutingError(Exception):
    """Error when the router cannot find a suitable decoding schema."""


def _find_route(service_uuid: str, characteristic_uuid: str):
    normalized_service_uuid = normalize_uuid(service_uuid)
    normalized_characteristic_uuid = normalize_uuid(characteristic_uuid)

    lookup = BluetoothNumbersLookup()
    if lookup.is_sig_pair(
        normalized_service_uuid,
        normalized_characteristic_uuid,
    ):
        schema_directory = project_root / "gatt_registry" / "decode_registry"
        schema_loader = load_schema
    else:
        schema_directory = project_root / "wot" / "td"
        schema_loader = load_wot_schema

    if not schema_directory.is_dir():
        raise RoutingError(
            "The driver does not support this device. Schema directory does not "
            f"exist: {schema_directory}"
        )

    for schema_path in schema_directory.rglob("*.yaml"):
        try:
            schema = schema_loader(str(schema_path))
        except SchemaLoadError:
            continue

        if normalize_uuid(schema.service.uuid) != normalized_service_uuid:
            continue

        matching_characteristic = next(
            (
                schema_characteristic
                for schema_characteristic in schema.characteristics
                if normalize_uuid(schema_characteristic.uuid)
                == normalized_characteristic_uuid
            ),
            None,
        )
        if matching_characteristic is not None:
            return schema, matching_characteristic

    return None


def supports_route(service_uuid: str, characteristic_uuid: str) -> bool:
    """Return whether a decoding schema supports the given GATT route."""
    return _find_route(service_uuid, characteristic_uuid) is not None


def router(
    service_uuid: str,
    characteristic_uuid: str,
    payload: bytes,
) -> DecodedPayload:
    """Check if the given UUIDs are standard or proprietary, find the matching schema, and decode a BLE payload."""

    normalized_service_uuid = normalize_uuid(service_uuid)
    normalized_characteristic_uuid = normalize_uuid(characteristic_uuid)
    route = _find_route(normalized_service_uuid, normalized_characteristic_uuid)
    if route is not None:
        schema, matching_characteristic = route
        return decode(
            schema=schema,
            characteristic_uuid=matching_characteristic.uuid,
            payload=payload,
        )

    raise RoutingError(
        "No matching schema found for "
        f"service {normalized_service_uuid} and "
        f"characteristic {normalized_characteristic_uuid}"
    )
