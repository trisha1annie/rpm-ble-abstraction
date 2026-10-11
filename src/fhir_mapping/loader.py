"""Load and index the FHIR mappings."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

from ble_plugin.schema import normalise_uuid

from .models import LoadedFhirMapping


class FhirMappingLoadError(ValueError):
    """Raised when a FHIR mapping file is missing or malformed."""

    def __init__(self, message: str, source_path: str | None = None) -> None:
        self.source_path = source_path
        suffix = f" (in {source_path})" if source_path else ""
        super().__init__(f"{message}{suffix}")


def _require_mapping(value: Any, name: str, source_path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FhirMappingLoadError(f"'{name}' must be a mapping", source_path)
    return value


def _require_string(value: Any, name: str, source_path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FhirMappingLoadError(
            f"'{name}' must be a non-empty string",
            source_path,
        )
    return value


def _validate_unit_mapping(
    value: Any,
    name: str,
    source_path: str,
) -> None:
    unit_mapping = _require_mapping(value, name, source_path)
    if not unit_mapping:
        raise FhirMappingLoadError(f"'{name}' cannot be empty", source_path)

    for decoded_unit, quantity in unit_mapping.items():
        if not isinstance(decoded_unit, str) or not decoded_unit:
            raise FhirMappingLoadError(
                f"'{name}' keys must be decoded unit strings",
                source_path,
            )
        quantity_mapping = _require_mapping(
            quantity,
            f"{name}.{decoded_unit}",
            source_path,
        )
        _require_string(
            quantity_mapping.get("unit"),
            f"{name}.{decoded_unit}.unit",
            source_path,
        )
        _require_string(
            quantity_mapping.get("system"),
            f"{name}.{decoded_unit}.system",
            source_path,
        )
        _require_string(
            quantity_mapping.get("code"),
            f"{name}.{decoded_unit}.code",
            source_path,
        )
        multiplier = quantity_mapping.get("multiplier", 1)
        if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)):
            raise FhirMappingLoadError(
                f"'{name}.{decoded_unit}.multiplier' must be numeric",
                source_path,
            )


def _validate_target(value: Any, name: str, source_path: str) -> None:
    target = _require_mapping(value, name, source_path)
    if target.get("resource_type") != "Observation":
        raise FhirMappingLoadError(
            f"'{name}.resource_type' must be 'Observation'",
            source_path,
        )

    profiles = target.get("profile")
    if (
        not isinstance(profiles, list)
        or not profiles
        or any(not isinstance(profile, str) or not profile for profile in profiles)
    ):
        raise FhirMappingLoadError(
            f"'{name}.profile' must be a non-empty list of strings",
            source_path,
        )

    fixed = _require_mapping(target.get("fixed"), f"{name}.fixed", source_path)
    _require_string(fixed.get("status"), f"{name}.fixed.status", source_path)
    category = fixed.get("category")
    if not isinstance(category, list) or not category:
        raise FhirMappingLoadError(
            f"'{name}.fixed.category' must be a non-empty list",
            source_path,
        )
    code = _require_mapping(
        fixed.get("code"),
        f"{name}.fixed.code",
        source_path,
    )
    coding = code.get("coding")
    if not isinstance(coding, list) or not coding:
        raise FhirMappingLoadError(
            f"'{name}.fixed.code.coding' must be a non-empty list",
            source_path,
        )


def _adapt_unit_definition(
    value: Any,
    name: str,
    source_path: str,
) -> dict[str, Mapping[str, Any]]:
    """Normalise a unit block to decoded-unit keys."""
    value_mapping = _require_mapping(value, name, source_path)
    if "unit" in value_mapping:
        unit = dict(
            _require_mapping(
                value_mapping["unit"],
                f"{name}.unit",
                source_path,
            )
        )
        source_unit = unit.pop("source_unit", unit.get("unit"))
        source_unit = _require_string(
            source_unit,
            f"{name}.unit.source_unit",
            source_path,
        )
        return {source_unit: unit}

    configured_units = _require_mapping(
        value_mapping.get("unit_mapping"),
        f"{name}.unit_mapping",
        source_path,
    )
    adapted_units: dict[str, Mapping[str, Any]] = {}
    for key, configured_value in configured_units.items():
        configured_unit = dict(
            _require_mapping(
                configured_value,
                f"{name}.unit_mapping.{key}",
                source_path,
            )
        )
        source_unit = configured_unit.pop(
            "source_unit",
            configured_unit.get("unit"),
        )
        source_unit = _require_string(
            source_unit,
            f"{name}.unit_mapping.{key}.source_unit",
            source_path,
        )
        if source_unit in adapted_units:
            raise FhirMappingLoadError(
                f"Duplicate decoded unit '{source_unit}' in '{name}'",
                source_path,
            )
        adapted_units[source_unit] = configured_unit
    return adapted_units


def _adapt_value(
    value: Any,
    name: str,
    source_path: str,
) -> dict[str, Any]:
    value_mapping = _require_mapping(value, name, source_path)
    source = _require_string(
        value_mapping.get("value_source"),
        f"{name}.value_source",
        source_path,
    )
    return {
        "source": source,
        "unit_mapping": _adapt_unit_definition(
            value_mapping,
            name,
            source_path,
        ),
    }


def _adapt_target(
    value: Any,
    name: str,
    source_path: str,
) -> dict[str, Any]:
    target = _require_mapping(value, name, source_path)
    return {
        "resource_type": target.get("resource_type"),
        "profile": target.get("profile"),
        "fixed": target.get("fixed"),
    }


def _adapt_outputs(
    root: Mapping[str, Any],
    mapping_id: str,
    source_path: str,
) -> list[dict[str, Any]]:
    """Build the runtime outputs from the mapping file."""
    target = _require_mapping(root.get("target"), "target", source_path)
    primary: dict[str, Any] = {
        "name": mapping_id,
        "required": root.get("primary_required", True),
        "target": _adapt_target(target, "target", source_path),
    }

    if "components" in root:
        components = root["components"]
        if not isinstance(components, list) or not components:
            raise FhirMappingLoadError(
                "'components' must be a non-empty list",
                source_path,
            )
        primary["components"] = []
        for index, component_value in enumerate(components):
            name = f"components[{index}]"
            component = _require_mapping(component_value, name, source_path)
            required = component.get(
                "required",
                component.get("required_by_fhir", False),
            )
            primary["components"].append(
                {
                    "name": component.get("name"),
                    "source": component.get("source"),
                    "required": required,
                    "code": component.get("code"),
                    "quantity": {
                        "unit_mapping": _adapt_unit_definition(
                            component.get("value"),
                            f"{name}.value",
                            source_path,
                        )
                    },
                }
            )
    else:
        primary["value"] = _adapt_value(
            target.get("value"),
            "target.value",
            source_path,
        )

    outputs = [primary]
    additional = root.get("additional_measurements", [])
    if not isinstance(additional, list):
        raise FhirMappingLoadError(
            "'additional_measurements' must be a list",
            source_path,
        )
    for index, additional_value in enumerate(additional):
        name = f"additional_measurements[{index}]"
        measurement = _require_mapping(
            additional_value,
            name,
            source_path,
        )
        additional_target = _require_mapping(
            measurement.get("target"),
            f"{name}.target",
            source_path,
        )
        outputs.append(
            {
                "name": measurement.get("name"),
                "required": measurement.get("required", False),
                "target": _adapt_target(
                    additional_target,
                    f"{name}.target",
                    source_path,
                ),
                "value": _adapt_value(
                    additional_target.get("value"),
                    f"{name}.target.value",
                    source_path,
                ),
            }
        )
    return outputs


def _validate_output(
    value: Any,
    index: int,
    source_path: str,
) -> set[str]:
    name = f"outputs[{index}]"
    output = _require_mapping(value, name, source_path)
    _require_string(output.get("name"), f"{name}.name", source_path)
    if not isinstance(output.get("required"), bool):
        raise FhirMappingLoadError(
            f"'{name}.required' must be boolean",
            source_path,
        )
    _validate_target(output.get("target"), f"{name}.target", source_path)

    has_value = "value" in output
    has_components = "components" in output
    if has_value == has_components:
        raise FhirMappingLoadError(
            f"'{name}' must define exactly one of 'value' or 'components'",
            source_path,
        )

    source_fields: set[str] = set()
    if has_value:
        scalar = _require_mapping(output["value"], f"{name}.value", source_path)
        source_fields.add(
            _require_string(
                scalar.get("source"),
                f"{name}.value.source",
                source_path,
            )
        )
        _validate_unit_mapping(
            scalar.get("unit_mapping"),
            f"{name}.value.unit_mapping",
            source_path,
        )
        return source_fields

    components = output["components"]
    if not isinstance(components, list) or not components:
        raise FhirMappingLoadError(
            f"'{name}.components' must be a non-empty list",
            source_path,
        )
    component_names: set[str] = set()
    for component_index, component_value in enumerate(components):
        component_name = f"{name}.components[{component_index}]"
        component = _require_mapping(
            component_value,
            component_name,
            source_path,
        )
        logical_name = _require_string(
            component.get("name"),
            f"{component_name}.name",
            source_path,
        )
        if logical_name in component_names:
            raise FhirMappingLoadError(
                f"Duplicate component name '{logical_name}'",
                source_path,
            )
        component_names.add(logical_name)
        source_fields.add(
            _require_string(
                component.get("source"),
                f"{component_name}.source",
                source_path,
            )
        )
        if not isinstance(component.get("required"), bool):
            raise FhirMappingLoadError(
                f"'{component_name}.required' must be boolean",
                source_path,
            )
        _require_mapping(
            component.get("code"),
            f"{component_name}.code",
            source_path,
        )
        quantity = _require_mapping(
            component.get("quantity"),
            f"{component_name}.quantity",
            source_path,
        )
        _validate_unit_mapping(
            quantity.get("unit_mapping"),
            f"{component_name}.quantity.unit_mapping",
            source_path,
        )
    return source_fields


def load_fhir_mapping(file_path: str | Path) -> LoadedFhirMapping:
    """Load and structurally validate one supported FHIR mapping."""
    path = Path(file_path)
    source_path = str(path)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise FhirMappingLoadError("Mapping file not found", source_path) from error
    except yaml.YAMLError as error:
        raise FhirMappingLoadError(
            f"YAML parsing error: {error}",
            source_path,
        ) from error

    root = _require_mapping(data, "root", source_path)
    mapping_id = _require_string(root.get("mapping_id"), "mapping_id", source_path)
    if root.get("fhir_version") != "R5":
        raise FhirMappingLoadError(
            "'fhir_version' must be 'R5'",
            source_path,
        )

    source = _require_mapping(root.get("source"), "source", source_path)
    device_type = _require_string(
        source.get("device_type"),
        "source.device_type",
        source_path,
    )
    characteristic_name = _require_string(
        source.get("characteristic_name"),
        "source.characteristic_name",
        source_path,
    )
    try:
        service_uuid = normalise_uuid(
            _require_string(
                source.get("service_uuid"),
                "source.service_uuid",
                source_path,
            )
        )
        characteristic_uuid = normalise_uuid(
            _require_string(
                source.get("characteristic_uuid"),
                "source.characteristic_uuid",
                source_path,
            )
        )
    except ValueError as error:
        raise FhirMappingLoadError(str(error), source_path) from error

    minimum_outputs = root.get("minimum_outputs")
    if (
        isinstance(minimum_outputs, bool)
        or not isinstance(minimum_outputs, int)
        or minimum_outputs < 1
    ):
        raise FhirMappingLoadError(
            "'minimum_outputs' must be a positive integer",
            source_path,
        )

    outputs_data = _adapt_outputs(root, mapping_id, source_path)
    if minimum_outputs > len(outputs_data):
        raise FhirMappingLoadError(
            "'minimum_outputs' cannot exceed the number of outputs",
            source_path,
        )

    output_names: set[str] = set()
    source_fields: set[str] = set()
    for index, output_value in enumerate(outputs_data):
        output = _require_mapping(
            output_value,
            f"outputs[{index}]",
            source_path,
        )
        output_name = _require_string(
            output.get("name"),
            f"outputs[{index}].name",
            source_path,
        )
        if output_name in output_names:
            raise FhirMappingLoadError(
                f"Duplicate output name '{output_name}'",
                source_path,
            )
        output_names.add(output_name)
        source_fields.update(_validate_output(output, index, source_path))

    constraints = root.get("constraints", {})
    constraints_mapping = _require_mapping(
        constraints,
        "constraints",
        source_path,
    )
    reject_status_flags = constraints_mapping.get("reject_status_flags", [])
    if not isinstance(reject_status_flags, list) or any(
        not isinstance(flag_name, str) or not flag_name.strip()
        for flag_name in reject_status_flags
    ) or len(set(reject_status_flags)) != len(reject_status_flags):
        raise FhirMappingLoadError(
            "'constraints.reject_status_flags' must be a list of "
            "unique flag names",
            source_path,
        )

    requires = _require_mapping(
        constraints_mapping.get("requires", {}),
        "constraints.requires",
        source_path,
    )
    for field_name, dependencies in requires.items():
        if field_name not in source_fields:
            raise FhirMappingLoadError(
                f"Constraint refers to unknown source field '{field_name}'",
                source_path,
            )
        if (
            not isinstance(dependencies, list)
            or not dependencies
            or any(dependency not in source_fields for dependency in dependencies)
        ):
            raise FhirMappingLoadError(
                f"Constraint dependencies for '{field_name}' are invalid",
                source_path,
            )

    reject_values = _require_mapping(
        constraints_mapping.get("reject_values", {}),
        "constraints.reject_values",
        source_path,
    )
    for field_name, rejected in reject_values.items():
        if field_name not in source_fields:
            raise FhirMappingLoadError(
                f"Constraint refers to unknown source field '{field_name}'",
                source_path,
            )
        if (
            not isinstance(rejected, list)
            or not rejected
            or any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                for value in rejected
            )
        ):
            raise FhirMappingLoadError(
                f"Rejected values for '{field_name}' must be a non-empty "
                "list of numbers",
                source_path,
            )

    return LoadedFhirMapping(
        mapping_id=mapping_id,
        fhir_version="R5",
        device_type=device_type,
        service_uuid=service_uuid,
        characteristic_uuid=characteristic_uuid,
        characteristic_name=characteristic_name,
        minimum_outputs=minimum_outputs,
        outputs=tuple(outputs_data),
        constraints=constraints_mapping,
        source_path=source_path,
    )


class FhirMappingRegistry:
    """Mappings indexed by service and characteristic UUID."""

    def __init__(self, mappings: Iterable[LoadedFhirMapping]) -> None:
        by_route: dict[tuple[str, str], LoadedFhirMapping] = {}
        mapping_ids: set[str] = set()
        for mapping in mappings:
            if mapping.mapping_id in mapping_ids:
                raise FhirMappingLoadError(
                    f"Duplicate mapping_id '{mapping.mapping_id}'",
                    mapping.source_path,
                )
            route = (mapping.service_uuid, mapping.characteristic_uuid)
            if route in by_route:
                raise FhirMappingLoadError(
                    f"Duplicate FHIR mapping route {route[0]} / {route[1]}",
                    mapping.source_path,
                )
            mapping_ids.add(mapping.mapping_id)
            by_route[route] = mapping
        self._by_route = by_route

    @classmethod
    def from_directory(cls, directory: str | Path) -> "FhirMappingRegistry":
        """Load all YAML mappings in a directory exactly once."""
        mapping_directory = Path(directory)
        if not mapping_directory.is_dir():
            raise FhirMappingLoadError(
                "FHIR mapping directory does not exist",
                str(mapping_directory),
            )
        mappings = [
            load_fhir_mapping(path)
            for path in sorted(mapping_directory.glob("*.yaml"))
        ]
        if not mappings:
            raise FhirMappingLoadError(
                "FHIR mapping directory contains no YAML mappings",
                str(mapping_directory),
            )
        return cls(mappings)

    def get(
        self,
        service_uuid: str,
        characteristic_uuid: str,
    ) -> LoadedFhirMapping | None:
        """Return the mapping for a BLE route, if one exists."""
        try:
            route = (
                normalise_uuid(service_uuid),
                normalise_uuid(characteristic_uuid),
            )
        except ValueError:
            return None
        return self._by_route.get(route)
