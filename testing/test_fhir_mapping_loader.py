from dataclasses import replace
from pathlib import Path

import pytest

from ble_plugin.schema import normalise_uuid
from fhir_mapping.loader import (
    FhirMappingLoadError,
    FhirMappingRegistry,
    load_fhir_mapping,
)


MAPPING_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "src" / "fhir_mapping"
)


def test_corrected_mappings_load_and_are_indexed():
    registry = FhirMappingRegistry.from_directory(MAPPING_DIRECTORY)

    assert registry.get("1810", "2A35").mapping_id == (
        "blood_pressure_observation"
    )
    assert registry.get("181D", "2A9D").mapping_id == "weight_observation"
    assert registry.get("1822", "2A5E").mapping_id == (
        "pulse_oximeter_observation"
    )
    assert registry.get(
        "cdeacd80-5235-4c07-8846-93a37ee6b86d",
        "cdeacd81-5235-4c07-8846-93a37ee6b86d",
    ).mapping_id == "yk_oximeter_observation"


def test_registry_matches_canonical_driver_uuids():
    registry = FhirMappingRegistry.from_directory(MAPPING_DIRECTORY)

    mapping = registry.get(
        normalise_uuid("1810"),
        normalise_uuid("2A35"),
    )

    assert mapping is not None
    assert mapping.characteristic_name == "blood_pressure_measurement"


def test_loader_reports_invalid_yaml(tmp_path):
    mapping_path = tmp_path / "invalid.yaml"
    mapping_path.write_text("mapping_id: [", encoding="utf-8")

    with pytest.raises(FhirMappingLoadError, match="YAML parsing error"):
        load_fhir_mapping(mapping_path)


def test_loader_reports_missing_required_section(tmp_path):
    mapping_path = tmp_path / "missing.yaml"
    mapping_path.write_text(
        "mapping_id: missing_source\nfhir_version: R5\n",
        encoding="utf-8",
    )

    with pytest.raises(FhirMappingLoadError, match="'source' must be a mapping"):
        load_fhir_mapping(mapping_path)


def write_mapping_with_reject_values(tmp_path, reject_values_yaml):
    source = (MAPPING_DIRECTORY / "yk_oximeter.yaml").read_text(encoding="utf-8")
    original = "  reject_values:\n    spo2: [0]\n    pulse_rate: [0]\n"
    assert original in source
    mapping_path = tmp_path / "mapping.yaml"
    mapping_path.write_text(
        source.replace(original, reject_values_yaml),
        encoding="utf-8",
    )
    return mapping_path


def test_loader_reads_reject_values_constraint():
    mapping = load_fhir_mapping(MAPPING_DIRECTORY / "yk_oximeter.yaml")

    assert mapping.constraints["reject_values"] == {
        "spo2": [0],
        "pulse_rate": [0],
    }


def test_loader_rejects_reject_values_for_unknown_field(tmp_path):
    mapping_path = write_mapping_with_reject_values(
        tmp_path,
        "  reject_values:\n    perfusion_index_raw: [0]\n",
    )

    with pytest.raises(FhirMappingLoadError, match="unknown source field"):
        load_fhir_mapping(mapping_path)


@pytest.mark.parametrize("rejected", ["[]", "0", "[zero]", "[true]"])
def test_loader_rejects_invalid_reject_values(tmp_path, rejected):
    mapping_path = write_mapping_with_reject_values(
        tmp_path,
        f"  reject_values:\n    spo2: {rejected}\n",
    )

    with pytest.raises(FhirMappingLoadError, match="non-empty list of numbers"):
        load_fhir_mapping(mapping_path)


def test_registry_rejects_duplicate_route():
    mapping = load_fhir_mapping(MAPPING_DIRECTORY / "blood_pressure.yaml")
    duplicate = replace(mapping, mapping_id="duplicate_mapping")

    with pytest.raises(FhirMappingLoadError, match="Duplicate FHIR mapping route"):
        FhirMappingRegistry((mapping, duplicate))
