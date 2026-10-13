from datetime import datetime, timezone
from pathlib import Path

import pytest

from ble_plugin.decoder import decode
from ble_plugin.plugin_driver import DriverMeasurement
from ble_plugin.schema import normalise_uuid
from ble_plugin.td_loader import load_wot_schema
from ble_plugin.yaml_loader import load_schema
from fhir_mapping import (
    FhirMappingRegistry,
    FhirNormalisationError,
    FhirNormaliser,
    NormalisationContext,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_decoded_blood_pressure_normalises_to_fhir_json():
    schema = load_schema(
        PROJECT_ROOT
        / "src"
        / "gatt_registry"
        / "decode_registry"
        / "blood_pressure.yaml"
    )
    characteristic_uuid = normalise_uuid("2A35")
    decoded = decode(
        schema,
        characteristic_uuid,
        b"\x00\x78\x00\x50\x00\x5A\x00",
    )
    measurement = DriverMeasurement(
        device_id="AA:BB:CC:DD:EE:FF",
        service_uuid=normalise_uuid("1810"),
        characteristic_uuid=characteristic_uuid,
        payload=decoded,
        received_at=datetime(2026, 9, 15, 6, 30, tzinfo=timezone.utc),
    )
    normaliser = FhirNormaliser(
        FhirMappingRegistry.from_directory(
            PROJECT_ROOT / "src" / "fhir_mapping"
        )
    )

    observations = normaliser.normalise(
        measurement,
        NormalisationContext("Patient/example"),
    )

    assert len(observations) == 1
    assert observations[0]["resourceType"] == "Observation"
    assert observations[0]["code"]["coding"][0]["code"] == "85354-9"
    assert [
        item["valueQuantity"]["value"]
        for item in observations[0]["component"]
    ] == [120.0, 80.0, 90.0]


def test_decoded_invalid_pulse_oximeter_reading_is_rejected():
    schema = load_schema(
        PROJECT_ROOT
        / "src"
        / "gatt_registry"
        / "decode_registry"
        / "pulse_oximeter.yaml"
    )
    characteristic_uuid = normalise_uuid("2A5E")
    # Status present, and the invalid-measurement bit set.
    decoded = decode(
        schema,
        characteristic_uuid,
        b"\x02\x62\x00\x48\x00\x00\x80",
    )
    measurement = DriverMeasurement(
        device_id="AA:BB:CC:DD:EE:FF",
        service_uuid=normalise_uuid("1822"),
        characteristic_uuid=characteristic_uuid,
        payload=decoded,
        received_at=datetime(2026, 9, 15, 6, 30, tzinfo=timezone.utc),
    )
    normaliser = FhirNormaliser(
        FhirMappingRegistry.from_directory(
            PROJECT_ROOT / "src" / "fhir_mapping"
        )
    )

    with pytest.raises(FhirNormalisationError, match="invalid_measurement_detected"):
        normaliser.normalise(
            measurement,
            NormalisationContext("Patient/example"),
        )


def yk_oximeter_measurement(hex_payload):
    schema = load_wot_schema(PROJECT_ROOT / "src" / "wot" / "td" / "oxi.yaml")
    characteristic_uuid = normalise_uuid("cdeacd81-5235-4c07-8846-93a37ee6b86d")
    return DriverMeasurement(
        device_id="63:31:61:38:36:66",
        service_uuid=normalise_uuid("cdeacd80-5235-4c07-8846-93a37ee6b86d"),
        characteristic_uuid=characteristic_uuid,
        payload=decode(schema, characteristic_uuid, bytes.fromhex(hex_payload)),
        received_at=datetime(2026, 10, 6, 11, 20, tzinfo=timezone.utc),
    )


def test_decoded_yk_oximeter_reading_normalises_to_fhir_json():
    normaliser = FhirNormaliser(
        FhirMappingRegistry.from_directory(
            PROJECT_ROOT / "src" / "fhir_mapping"
        )
    )

    observations = normaliser.normalise(
        yk_oximeter_measurement("816148a00000000000000000000000"),
        NormalisationContext("Patient/example"),
    )

    assert [
        observation["valueQuantity"]["value"] for observation in observations
    ] == [97, 72]
    assert observations[0]["code"]["coding"][1]["code"] == "59408-5"
    assert observations[1]["code"]["coding"][0]["code"] == "8867-4"


def test_decoded_yk_oximeter_no_finger_reading_is_rejected():
    normaliser = FhirNormaliser(
        FhirMappingRegistry.from_directory(
            PROJECT_ROOT / "src" / "fhir_mapping"
        )
    )

    with pytest.raises(FhirNormalisationError, match="rejected value 0"):
        normaliser.normalise(
            yk_oximeter_measurement("810000000000000000000000000000"),
            NormalisationContext("Patient/example"),
        )
