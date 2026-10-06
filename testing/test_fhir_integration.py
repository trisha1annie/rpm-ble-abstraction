from datetime import datetime, timezone
from pathlib import Path

import pytest

from ble_plugin.decoder import decode
from ble_plugin.plugin_driver import DriverMeasurement
from ble_plugin.schema import normalise_uuid
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
