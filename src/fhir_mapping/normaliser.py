"""Normalisation of decoded BLE measurements to FHIR JSON."""
from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

from ble_plugin.models import DecodedValue, SfloatSpecialValue
from ble_plugin.plugin_driver import DriverMeasurement

from .loader import FhirMappingRegistry
from .models import LoadedFhirMapping, NormalisationContext


class FhirNormalisationError(ValueError):
    """Raised when a supported measurement cannot produce valid output."""


class UnsupportedFhirMappingError(FhirNormalisationError):
    """Raised when no FHIR mapping exists for a measurement route."""


def _finite_physical_value(decoded: DecodedValue | None) -> int | float | None:
    if decoded is None:
        return None
    value = decoded.physical_value
    if isinstance(value, SfloatSpecialValue) or isinstance(value, bool):
        return None
    if not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _quantity(
    decoded: DecodedValue,
    unit_mapping: Mapping[str, Any],
    source_name: str,
) -> dict[str, Any]:
    value = _finite_physical_value(decoded)
    if value is None:
        raise FhirNormalisationError(
            f"Source field '{source_name}' has no finite numeric value"
        )

    decoded_unit = decoded.unit
    if decoded_unit is None or decoded_unit not in unit_mapping:
        raise FhirNormalisationError(
            f"Source field '{source_name}' has unsupported unit "
            f"{decoded_unit!r}"
        )

    unit_definition = unit_mapping[decoded_unit]
    multiplier = unit_definition.get("multiplier", 1)
    normalised_value = value * multiplier
    return {
        "value": normalised_value,
        "unit": unit_definition["unit"],
        "system": unit_definition["system"],
        "code": unit_definition["code"],
    }


def _base_observation(
    target: Mapping[str, Any],
    context: NormalisationContext,
    measurement: DriverMeasurement,
) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "resourceType": target["resource_type"],
        "meta": {"profile": deepcopy(target["profile"])},
    }
    observation.update(deepcopy(target["fixed"]))
    observation["subject"] = {"reference": context.patient_reference.strip()}
    if context.device_reference is not None:
        observation["device"] = {
            "reference": context.device_reference.strip(),
        }
    observation["effectiveDateTime"] = measurement.received_at.isoformat()
    return observation


class FhirNormaliser:
    """Normalise supported decoded measurements using loaded YAML mappings."""

    def __init__(self, registry: FhirMappingRegistry) -> None:
        self._registry = registry

    def normalise(
        self,
        measurement: DriverMeasurement,
        context: NormalisationContext,
    ) -> list[dict[str, Any]]:
        """Return FHIR R5 Observation dictionaries for one measurement."""
        mapping = self._registry.get(
            measurement.service_uuid,
            measurement.characteristic_uuid,
        )
        if mapping is None:
            raise UnsupportedFhirMappingError(
                "No FHIR mapping for service "
                f"{measurement.service_uuid} and characteristic "
                f"{measurement.characteristic_uuid}"
            )

        self._validate_context(context, measurement)
        self._validate_constraints(mapping, measurement)

        observations: list[dict[str, Any]] = []
        for output in mapping.outputs:
            observation = self._build_output(
                output,
                measurement,
                context,
            )
            if observation is not None:
                observations.append(observation)

        if len(observations) < mapping.minimum_outputs:
            raise FhirNormalisationError(
                f"Mapping '{mapping.mapping_id}' requires at least "
                f"{mapping.minimum_outputs} emitted Observation(s)"
            )
        return observations

    @staticmethod
    def _validate_context(
        context: NormalisationContext,
        measurement: DriverMeasurement,
    ) -> None:
        if (
            not isinstance(context.patient_reference, str)
            or not context.patient_reference.strip()
        ):
            raise FhirNormalisationError(
                "NormalisationContext.patient_reference is required"
            )
        if context.device_reference is not None and (
            not isinstance(context.device_reference, str)
            or not context.device_reference.strip()
        ):
            raise FhirNormalisationError(
                "NormalisationContext.device_reference cannot be empty"
            )
        if (
            measurement.received_at.tzinfo is None
            or measurement.received_at.utcoffset() is None
        ):
            raise FhirNormalisationError(
                "DriverMeasurement.received_at must be timezone-aware"
            )

    @staticmethod
    def _validate_constraints(
        mapping: LoadedFhirMapping,
        measurement: DriverMeasurement,
    ) -> None:
        for flag_name in mapping.constraints.get("reject_status_flags", ()):
            if measurement.payload.status_flags.get(flag_name) is True:
                raise FhirNormalisationError(
                    f"Measurement rejected because status flag "
                    f"'{flag_name}' is set"
                )

        requires = mapping.constraints.get("requires", {})
        values = measurement.payload.values
        for source_name, dependencies in requires.items():
            if source_name not in values:
                continue
            for dependency in dependencies:
                dependency_value = values.get(dependency)
                if _finite_physical_value(dependency_value) is None:
                    raise FhirNormalisationError(
                        f"Source field '{source_name}' requires a finite "
                        f"'{dependency}' value"
                    )

    def _build_output(
        self,
        output: Mapping[str, Any],
        measurement: DriverMeasurement,
        context: NormalisationContext,
    ) -> dict[str, Any] | None:
        target = output["target"]
        if "value" in output:
            return self._build_scalar_output(
                output,
                target,
                measurement,
                context,
            )
        return self._build_component_output(
            output,
            target,
            measurement,
            context,
        )

    @staticmethod
    def _build_scalar_output(
        output: Mapping[str, Any],
        target: Mapping[str, Any],
        measurement: DriverMeasurement,
        context: NormalisationContext,
    ) -> dict[str, Any] | None:
        value_mapping = output["value"]
        source_name = value_mapping["source"]
        decoded = measurement.payload.values.get(source_name)
        if _finite_physical_value(decoded) is None:
            if output["required"]:
                raise FhirNormalisationError(
                    f"Required source field '{source_name}' is missing or invalid"
                )
            return None

        observation = _base_observation(target, context, measurement)
        observation["valueQuantity"] = _quantity(
            decoded,
            value_mapping["unit_mapping"],
            source_name,
        )
        return observation

    @staticmethod
    def _build_component_output(
        output: Mapping[str, Any],
        target: Mapping[str, Any],
        measurement: DriverMeasurement,
        context: NormalisationContext,
    ) -> dict[str, Any] | None:
        components: list[dict[str, Any]] = []
        for component_mapping in output["components"]:
            source_name = component_mapping["source"]
            decoded = measurement.payload.values.get(source_name)
            if _finite_physical_value(decoded) is None:
                if component_mapping["required"]:
                    raise FhirNormalisationError(
                        f"Required source field '{source_name}' is "
                        "missing or invalid"
                    )
                continue

            components.append(
                {
                    "code": deepcopy(component_mapping["code"]),
                    "valueQuantity": _quantity(
                        decoded,
                        component_mapping["quantity"]["unit_mapping"],
                        source_name,
                    ),
                }
            )

        if not components:
            if output["required"]:
                raise FhirNormalisationError(
                    f"Required output '{output['name']}' has no valid components"
                )
            return None

        observation = _base_observation(target, context, measurement)
        observation["component"] = components
        return observation
