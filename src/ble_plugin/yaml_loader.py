import yaml
import os
from typing import Dict, Any, List

from .schema import (
    LoadedDeviceSchema, GattServiceSchema, CharacteristicSchema,
    PayloadSchema, FieldSchema, TypeDefinition, normalise_uuid
)
from .exceptions import SchemaLoadError


def _load_fields(fields_list: list, source_path: str, types_dict: dict) -> tuple[FieldSchema, ...]:
    if not isinstance(fields_list, list):
        raise SchemaLoadError("fields must be a list", source_path)
    
    parsed_fields = []
    for field_data in fields_list:
        if not isinstance(field_data, dict):
            raise SchemaLoadError("field entry must be a dictionary", source_path)
            
        name = field_data.get("name")
        if not name:
            raise SchemaLoadError("field missing 'name'", source_path)
            
        type_name = field_data.get("type")
        if not type_name:
            raise SchemaLoadError(f"field '{name}' missing 'type'", source_path)
            
        size_bytes_val = field_data.get("size_bytes", 0)
        size_bytes = 0
        if isinstance(size_bytes_val, int):
            size_bytes = size_bytes_val

        ref = field_data.get("ref")
        if type_name == "struct" and not ref:
            raise SchemaLoadError(f"field '{name}' of type struct missing 'ref'", source_path)
            
        if ref and ref not in types_dict:
            raise SchemaLoadError(f"field '{name}' references unknown type '{ref}'", source_path)
            
        parsed_fields.append(FieldSchema(
            name=name,
            type_name=type_name,
            size_bytes=size_bytes,
            bitfield=field_data.get("bitfield", {}),
            unit=field_data.get("unit"),
            unit_logic=field_data.get("unit_logic"),
            resolution=field_data.get("resolution"),
            resolution_logic=field_data.get("resolution_logic"),
            byte_order=field_data.get("byte_order"),
            present_if=field_data.get("present_if"),
            always_present=field_data.get("always_present", False),
            expected_value=field_data.get("expected_value"),
            notes=field_data.get("notes"),
            ref=ref
        ))
        
    return tuple(parsed_fields)


def _load_types(types_dict: dict, source_path: str) -> dict[str, TypeDefinition]:
    if not types_dict:
        return {}
    if not isinstance(types_dict, dict):
        raise SchemaLoadError("'types' must be a dictionary", source_path)
        
    parsed_types = {}
    for t_name, t_data in types_dict.items():
        if not isinstance(t_data, dict):
            raise SchemaLoadError(f"type '{t_name}' must be a dictionary", source_path)
            
        fields = tuple()
        if "fields" in t_data:
            fields = _load_fields(t_data["fields"], source_path, {})
            
        parsed_types[t_name] = TypeDefinition(
            name=t_name,
            description=t_data.get("description"),
            size_bytes=t_data.get("size_bytes"),
            byte_order=t_data.get("byte_order"),
            fields=fields,
            bits=t_data.get("bits", {}),
            decode=t_data.get("decode"),
            special_values=t_data.get("special_values", {})
        )
    return parsed_types


def load_schema(file_path: str) -> LoadedDeviceSchema:
    """Load and validate a YAML device schema."""
    if not os.path.exists(file_path):
        raise SchemaLoadError(f"File not found: {file_path}", file_path)
        
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SchemaLoadError(f"YAML parsing error: {e}", file_path)
            
    if not isinstance(data, dict):
        raise SchemaLoadError("Schema root must be a dictionary", file_path)
        
    device_type = data.get("device_type")
    if not device_type:
        raise SchemaLoadError("Missing 'device_type'", file_path)
        
    service_data = data.get("service")
    if not service_data or not isinstance(service_data, dict):
        raise SchemaLoadError("Missing or invalid 'service' section", file_path)
        
    service_uuid_raw = service_data.get("uuid")
    if not service_uuid_raw:
        raise SchemaLoadError("Service missing 'uuid'", file_path)
        
    try:
        service_uuid = normalise_uuid(service_uuid_raw)
    except ValueError as e:
        raise SchemaLoadError(f"Invalid service UUID: {e}", file_path)
        
    service = GattServiceSchema(
        uuid=service_uuid,
        name=service_data.get("name", "unknown_service")
    )
    
    types = _load_types(data.get("types", {}), file_path)
    
    chars_data = data.get("characteristics")
    if not chars_data or not isinstance(chars_data, list):
        raise SchemaLoadError("Missing or invalid 'characteristics' list", file_path)
        
    parsed_chars = []
    for char_data in chars_data:
        if not isinstance(char_data, dict):
            raise SchemaLoadError("Characteristic entry must be a dictionary", file_path)
            
        char_uuid_raw = char_data.get("uuid")
        if not char_uuid_raw:
            raise SchemaLoadError("Characteristic missing 'uuid'", file_path)
            
        try:
            char_uuid = normalise_uuid(char_uuid_raw)
        except ValueError as e:
            raise SchemaLoadError(f"Invalid characteristic UUID: {e}", file_path)
            
        access = char_data.get("access")
        if not access or not isinstance(access, list):
            raise SchemaLoadError(f"Characteristic '{char_uuid_raw}' missing 'access' list", file_path)
            
        payload_schema = None
        payload_data = char_data.get("payload_schema")
        
        if payload_data:
            if not isinstance(payload_data, dict):
                raise SchemaLoadError(f"Characteristic '{char_uuid_raw}' payload_schema must be a dictionary", file_path)
            fields_list = payload_data.get("fields")
            if not fields_list:
                raise SchemaLoadError(f"Characteristic '{char_uuid_raw}' payload_schema missing 'fields'", file_path)
                
            fields = _load_fields(fields_list, file_path, types)
            payload_schema = PayloadSchema(fields=fields)
            
        parsed_chars.append(CharacteristicSchema(
            uuid=char_uuid,
            name=char_data.get("name", char_uuid_raw),
            access=tuple(access),
            payload_schema=payload_schema,
            condition=char_data.get("condition")
        ))

    return LoadedDeviceSchema(
        device_type=device_type,
        service=service,
        characteristics=tuple(parsed_chars),
        types=types,
        source_path=file_path
    )
