import pytest
from types import SimpleNamespace

from ble_plugin.schema import (
    FieldSchema,
    PayloadSchema,
    CharacteristicSchema,
    GattServiceSchema,
    LoadedDeviceSchema,
)
from ble_plugin.decoder import decode
from ble_plugin.exceptions import InvalidPayloadError
from fault_handling.quality_handler import handle_payload


BP_CHAR_UUID = "00002a35-0000-1000-8000-00805f9b34fb"
BP_SERVICE_UUID = "00001810-0000-1000-8000-00805f9b34fb"

from fault_handling.quality_handler import payload_quality


def make_schema(required_fields, optional_fields=None):
    """Create a mock payload schema."""
    optional_fields = optional_fields or []

    fields = [
        SimpleNamespace(name=name, required=True)
        for name in required_fields
    ]

    fields += [
        SimpleNamespace(name=name, required=False)
        for name in optional_fields
    ]

    return SimpleNamespace(fields=fields)


def make_payload(values, quality_flags=None):
    """Create a mock decoded payload."""
    return SimpleNamespace(
        values=values,
        quality_flags=quality_flags or {}
    )


def test_valid_payload():
    schema = make_schema(
        required_fields=["systolic", "diastolic"],
        optional_fields=["timestamp"]
    )

    payload = make_payload(
        values={
            "systolic": 120,
            "diastolic": 80,
            "timestamp": "2026-10-12"
        }
    )

    assert payload_quality(payload, schema) == ("VALID PAYLOAD", set())


def test_missing_required_field():
    schema = make_schema(
        required_fields=["systolic", "diastolic"],
        optional_fields=["timestamp"]
    )

    payload = make_payload(
        values={"systolic": 120},
        quality_flags={"truncated_payload": True}
    )

    assert payload_quality(payload, schema) == (
        "INVALID", {"diastolic"}
    )


def test_multiple_missing_required_fields():
    schema = make_schema(
        required_fields=["systolic", "diastolic"],
        optional_fields=["timestamp"]
    )

    payload = make_payload(
        values={},
        quality_flags={"truncated_payload": True}
    )

    assert payload_quality(payload, schema) == (
        "INVALID", {"systolic", "diastolic"}
    )


def test_truncated_optional_field_is_usable():
    """Required fields exist, but optional data is truncated."""
    schema = make_schema(
        required_fields=["systolic", "diastolic"],
        optional_fields=["timestamp"]
    )

    payload = make_payload(
        values={
            "systolic": 120,
            "diastolic": 80
        },
        quality_flags={"truncated_payload": True}
    )

    assert payload_quality(payload, schema) == ("USABLE", set())


def test_trailing_bytes_is_usable():
    schema = make_schema(
        required_fields=["systolic", "diastolic"]
    )

    payload = make_payload(
        values={
            "systolic": 120,
            "diastolic": 80
        },
        quality_flags={"trailing_bytes": True}
    )

    assert payload_quality(payload, schema) == ("USABLE", set())


def test_missing_optional_field_without_truncation():
    """An absent optional field is not automatically malformed."""
    schema = make_schema(
        required_fields=["systolic", "diastolic"],
        optional_fields=["timestamp"]
    )

    payload = make_payload(
        values={
            "systolic": 120,
            "diastolic": 80
        }
    )

    assert payload_quality(payload, schema) == ("VALID PAYLOAD", set())


def test_required_fields_take_priority_over_quality_flags():
    """Missing required fields must be invalid, even with other flags."""
    schema = make_schema(
        required_fields=["systolic", "diastolic"]
    )

    payload = make_payload(
        values={"systolic": 120},
        quality_flags={"trailing_bytes": True}
    )

    assert payload_quality(payload, schema) == (
        "INVALID", {"diastolic"}
    )


def test_handle_valid_payload():
    payload = SimpleNamespace(
        values={"systolic": 120, "diastolic": 80},
        quality_flags={}
    )

    assert handle_payload(payload, "VALID PAYLOAD") is payload


def test_handle_invalid_payload():
    payload = SimpleNamespace(
        values={"systolic": 120},
        quality_flags={"truncated_payload": True}
    )

    assert handle_payload(payload, "INVALID") is None


def test_handle_usable_truncated_payload():
    payload = SimpleNamespace(
        values={"systolic": 120, "diastolic": 80},
        quality_flags={"truncated_payload": True}
    )

    assert handle_payload(payload, "USABLE") is payload


def test_handle_usable_trailing_bytes():
    payload = SimpleNamespace(
        values={"systolic": 120, "diastolic": 80},
        quality_flags={"trailing_bytes": True}
    )

    assert handle_payload(payload, "USABLE") is payload


@pytest.fixture
def bp_schema():
    payload_schema = PayloadSchema(
        fields=(
            FieldSchema(
                name="systolic",
                type_name="uint16",
                required=True,
            ),
            FieldSchema(
                name="diastolic",
                type_name="uint16",
                required=True,
            ),
            FieldSchema(
                name="timestamp",
                type_name="uint32",
                required=False,
            ),
        )
    )

    return LoadedDeviceSchema(
        device_type="test_bp_sensor",
        service=GattServiceSchema(
            uuid=BP_SERVICE_UUID,
            name="Blood Pressure",
        ),
        characteristics=(
            CharacteristicSchema(
                uuid=BP_CHAR_UUID,
                name="Blood Pressure Measurement",
                access=("notify",),
                payload_schema=payload_schema,
            ),
        ),
    )


def test_valid_payload(bp_schema):
    # systolic=120, diastolic=80, timestamp=1000
    payload = bytes.fromhex("78005000e8030000")

    result = decode(bp_schema, BP_CHAR_UUID, payload)

    assert result.values["systolic"].physical_value == 120
    assert result.values["diastolic"].physical_value == 80
    assert result.values["timestamp"].physical_value == 1000
    assert not result.quality_flags.get("truncated_payload", False)


def test_truncated_optional_field_is_accepted(bp_schema):
    # Both required measurements are complete.
    # Only the optional timestamp is truncated.
    payload = bytes.fromhex("78005000e803")

    result = decode(bp_schema, BP_CHAR_UUID, payload)

    assert result.values["systolic"].physical_value == 120
    assert result.values["diastolic"].physical_value == 80
    assert "timestamp" not in result.values
    assert result.quality_flags["truncated_payload"] is True


def test_truncated_required_field_is_rejected(bp_schema):
    # Systolic is complete, but diastolic is incomplete.
    payload = bytes.fromhex("780050")

    with pytest.raises(InvalidPayloadError):
        decode(bp_schema, BP_CHAR_UUID, payload)


def test_missing_all_required_fields_is_rejected(bp_schema):
    with pytest.raises(InvalidPayloadError):
        decode(bp_schema, BP_CHAR_UUID, b"")


def test_trailing_bytes_are_accepted_with_warning(bp_schema):
    # Complete payload plus one unexpected byte.
    payload = bytes.fromhex("78005000e8030000ff")

    result = decode(bp_schema, BP_CHAR_UUID, payload)

    assert result.quality_flags["trailing_bytes"] is True
    assert result.values["systolic"].physical_value == 120
    assert result.values["diastolic"].physical_value == 80

def test_unknown_quality_flag_is_invalid():
    schema = make_schema(
        required_fields=["systolic", "diastolic"]
    )

    payload = make_payload(
        values={"systolic": 120, "diastolic": 80},
        quality_flags={"invalid_encoding": True}
    )

    assert payload_quality(payload, schema) == ("INVALID", set())