"""Data models for FHIR normalisation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class NormalisationContext:
    """Patient and optional device reference for a measurement."""

    patient_reference: str
    device_reference: str | None = None


@dataclass(frozen=True)
class LoadedFhirMapping:
    """A validated FHIR mapping indexed by its BLE route."""

    mapping_id: str
    fhir_version: str
    device_type: str
    service_uuid: str
    characteristic_uuid: str
    characteristic_name: str
    minimum_outputs: int
    outputs: tuple[Mapping[str, Any], ...]
    constraints: Mapping[str, Any] = field(default_factory=dict)
    source_path: str | None = None
