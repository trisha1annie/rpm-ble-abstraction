from datetime import datetime, timezone
from pathlib import Path

import pytest

from ble_plugin.models import DecodedPayload, DecodedValue, SfloatSpecialValue
from ble_plugin.plugin_driver import DriverMeasurement
from ble_plugin.schema import normalise_uuid
from fhir_mapping import (
    FhirMappingRegistry,
    FhirNormalisationError,
    FhirNormaliser,
    NormalisationContext,
    UnsupportedFhirMappingError,
)


MAPPING_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "src" / "fhir_mapping"
)
RECEIVED_AT = datetime(2026, 9, 15, 6, 30, tzinfo=timezone.utc)


def make_normaliser() -> FhirNormaliser:
    return FhirNormaliser(
        FhirMappingRegistry.from_directory(MAPPING_DIRECTORY)
    )


def decoded(value, unit):
    return DecodedValue(
        raw_value=value,
        physical_value=value,
        unit=unit,
    )


def measurement(service_uuid, characteristic_uuid, values, status_flags=None):
    return DriverMeasurement(
        device_id="AA:BB:CC:DD:EE:FF",
        service_uuid=normalise_uuid(service_uuid),
        characteristic_uuid=normalise_uuid(characteristic_uuid),
        payload=DecodedPayload(
            values=values,
            status_flags=status_flags or {},
        ),
        received_at=RECEIVED_AT,
    )


def coding_codes(resource):
    return {coding["code"] for coding in resource["code"]["coding"]}


def component(resource, loinc_code):
    return next(
        item
        for item in resource["component"]
        if item["code"]["coding"][0]["code"] == loinc_code
    )


def test_valid_blood_pressure_produces_panel_observation():
    result = make_normaliser().normalise(
        measurement(
            "1810",
            "2A35",
            {
                "systolic": decoded(120.0, "mmHg"),
                "diastolic": decoded(80.0, "mmHg"),
                "mean_arterial_pressure": decoded(90.0, "mmHg"),
            },
        ),
        NormalisationContext(
            patient_reference="Patient/123",
            device_reference="Device/bp-monitor",
        ),
    )

    assert len(result) == 1
    observation = result[0]
    assert observation["resourceType"] == "Observation"
    assert observation["meta"]["profile"] == [
        "http://hl7.org/fhir/StructureDefinition/bp"
    ]
    assert observation["status"] == "final"
    assert observation["subject"] == {"reference": "Patient/123"}
    assert observation["device"] == {"reference": "Device/bp-monitor"}
    assert observation["effectiveDateTime"] == RECEIVED_AT.isoformat()
    assert "identifier" not in observation
    assert component(observation, "8480-6")["valueQuantity"]["value"] == 120.0
    assert component(observation, "8462-4")["valueQuantity"]["value"] == 80.0
    assert component(observation, "8478-0")["valueQuantity"]["value"] == 90.0


def test_blood_pressure_converts_kpa_to_mmhg():
    observation = make_normaliser().normalise(
        measurement(
            "1810",
            "2A35",
            {
                "systolic": decoded(16.0, "kPa"),
                "diastolic": decoded(10.0, "kPa"),
                "mean_arterial_pressure": decoded(
                    SfloatSpecialValue.NaN,
                    "kPa",
                ),
            },
        ),
        NormalisationContext("Patient/123"),
    )[0]

    systolic = component(observation, "8480-6")["valueQuantity"]
    diastolic = component(observation, "8462-4")["valueQuantity"]
    assert systolic["value"] == pytest.approx(120.00992)
    assert diastolic["value"] == pytest.approx(75.0062)
    assert systolic["code"] == "mm[Hg]"
    assert "8478-0" not in {
        item["code"]["coding"][0]["code"]
        for item in observation["component"]
    }


def test_blood_pressure_requires_systolic_and_diastolic():
    with pytest.raises(FhirNormalisationError, match="diastolic"):
        make_normaliser().normalise(
            measurement(
                "1810",
                "2A35",
                {"systolic": decoded(120.0, "mmHg")},
            ),
            NormalisationContext("Patient/123"),
        )


def test_valid_plx_emits_independent_spo2_and_heart_rate_observations():
    result = make_normaliser().normalise(
        measurement(
            "1822",
            "2A5E",
            {
                "spo2pr_spot_check_spo2": decoded(98.0, "Percentage"),
                "spo2pr_spot_check_pr": decoded(72.0, "bpm"),
            },
        ),
        NormalisationContext("Patient/123"),
    )

    assert len(result) == 2
    assert "2708-6" in coding_codes(result[0])
    assert result[0]["valueQuantity"] == {
        "value": 98.0,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%",
    }
    assert "8867-4" in coding_codes(result[1])
    assert result[1]["valueQuantity"]["value"] == 72.0
    assert result[1]["valueQuantity"]["code"] == "/min"


@pytest.mark.parametrize(
    ("spo2", "pulse_rate", "expected_code"),
    [
        (decoded(98.0, "Percentage"), None, "2708-6"),
        (None, decoded(72.0, "bpm"), "8867-4"),
        (
            decoded(98.0, "Percentage"),
            decoded(SfloatSpecialValue.NaN, "bpm"),
            "2708-6",
        ),
        (
            decoded(SfloatSpecialValue.NaN, "Percentage"),
            decoded(72.0, "bpm"),
            "8867-4",
        ),
    ],
)
def test_plx_emits_valid_partial_output(spo2, pulse_rate, expected_code):
    values = {}
    if spo2 is not None:
        values["spo2pr_spot_check_spo2"] = spo2
    if pulse_rate is not None:
        values["spo2pr_spot_check_pr"] = pulse_rate

    result = make_normaliser().normalise(
        measurement("1822", "2A5E", values),
        NormalisationContext("Patient/123"),
    )

    assert len(result) == 1
    assert expected_code in coding_codes(result[0])


@pytest.mark.parametrize(
    "flag_name",
    ["invalid_measurement_detected", "measurement_unavailable"],
)
def test_plx_rejects_flagged_status(flag_name):
    with pytest.raises(FhirNormalisationError, match=flag_name):
        make_normaliser().normalise(
            measurement(
                "1822",
                "2A5E",
                {
                    "spo2pr_spot_check_spo2": decoded(98.0, "Percentage"),
                    "spo2pr_spot_check_pr": decoded(72.0, "bpm"),
                },
                status_flags={flag_name: True},
            ),
            NormalisationContext("Patient/123"),
        )


def test_plx_keeps_reading_for_other_status_flags():
    result = make_normaliser().normalise(
        measurement(
            "1822",
            "2A5E",
            {"spo2pr_spot_check_spo2": decoded(98.0, "Percentage")},
            status_flags={"questionable_measurement_detected": True},
        ),
        NormalisationContext("Patient/123"),
    )

    assert len(result) == 1
    assert result[0]["valueQuantity"]["value"] == 98.0


def test_plx_rejects_when_neither_output_is_usable():
    with pytest.raises(FhirNormalisationError, match="at least 1"):
        make_normaliser().normalise(
            measurement(
                "1822",
                "2A5E",
                {
                    "spo2pr_spot_check_spo2": decoded(
                        SfloatSpecialValue.NaN,
                        "Percentage",
                    ),
                    "spo2pr_spot_check_pr": decoded(
                        SfloatSpecialValue.NOT_AT_THIS_RESOLUTION,
                        "bpm",
                    ),
                },
            ),
            NormalisationContext("Patient/123"),
        )


def test_weight_only_preserves_kilograms_and_omits_device():
    result = make_normaliser().normalise(
        measurement(
            "181D",
            "2A9D",
            {"weight": decoded(75.5, "kg")},
        ),
        NormalisationContext("Patient/123"),
    )

    assert len(result) == 1
    assert result[0]["valueQuantity"]["value"] == 75.5
    assert result[0]["valueQuantity"]["code"] == "kg"
    assert "device" not in result[0]


def test_weight_emits_height_and_bmi_and_converts_metres_to_cm():
    result = make_normaliser().normalise(
        measurement(
            "181D",
            "2A9D",
            {
                "weight": decoded(75.5, "kg"),
                "height": decoded(1.82, "m"),
                "bmi": decoded(22.8, "kg/m^2"),
            },
        ),
        NormalisationContext("Patient/123"),
    )

    assert len(result) == 3
    assert result[1]["valueQuantity"]["value"] == pytest.approx(182.0)
    assert result[1]["valueQuantity"]["code"] == "cm"
    assert result[2]["valueQuantity"]["value"] == 22.8
    assert result[2]["valueQuantity"]["code"] == "kg/m2"


def test_weight_preserves_profile_permitted_imperial_units():
    result = make_normaliser().normalise(
        measurement(
            "181D",
            "2A9D",
            {
                "weight": decoded(165.0, "lb"),
                "height": decoded(71.5, "in"),
            },
        ),
        NormalisationContext("Patient/123"),
    )

    assert result[0]["valueQuantity"]["value"] == 165.0
    assert result[0]["valueQuantity"]["code"] == "[lb_av]"
    assert result[1]["valueQuantity"]["value"] == 71.5
    assert result[1]["valueQuantity"]["code"] == "[in_i]"


def test_weight_rejects_bmi_without_finite_height():
    for height in (
        None,
        decoded(SfloatSpecialValue.NaN, "m"),
    ):
        values = {
            "weight": decoded(75.5, "kg"),
            "bmi": decoded(22.8, "kg/m^2"),
        }
        if height is not None:
            values["height"] = height

        with pytest.raises(FhirNormalisationError, match="requires.*height"):
            make_normaliser().normalise(
                measurement("181D", "2A9D", values),
                NormalisationContext("Patient/123"),
            )


def test_required_weight_special_value_is_rejected():
    with pytest.raises(FhirNormalisationError, match="weight"):
        make_normaliser().normalise(
            measurement(
                "181D",
                "2A9D",
                {
                    "weight": decoded(
                        SfloatSpecialValue.NOT_AT_THIS_RESOLUTION,
                        "kg",
                    )
                },
            ),
            NormalisationContext("Patient/123"),
        )


def test_patient_reference_is_required():
    with pytest.raises(FhirNormalisationError, match="patient_reference"):
        make_normaliser().normalise(
            measurement(
                "181D",
                "2A9D",
                {"weight": decoded(75.5, "kg")},
            ),
            NormalisationContext(""),
        )


def test_unsupported_route_is_explicit():
    with pytest.raises(UnsupportedFhirMappingError, match="No FHIR mapping"):
        make_normaliser().normalise(
            measurement(
                "1822",
                "2A5F",
                {
                    "spo2pr_normal_spo2": decoded(98.0, "Percentage"),
                    "spo2pr_normal_pr": decoded(72.0, "bpm"),
                },
            ),
            NormalisationContext("Patient/123"),
        )
