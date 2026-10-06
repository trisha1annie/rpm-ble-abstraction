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


def test_registry_rejects_duplicate_route():
    mapping = load_fhir_mapping(MAPPING_DIRECTORY / "blood_pressure.yaml")
    duplicate = replace(mapping, mapping_id="duplicate_mapping")

    with pytest.raises(FhirMappingLoadError, match="Duplicate FHIR mapping route"):
        FhirMappingRegistry((mapping, duplicate))
