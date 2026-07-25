import struct
import math
from typing import Any, Tuple

from .schema import (
    LoadedDeviceSchema, CharacteristicSchema, FieldSchema, TypeDefinition, PayloadSchema
)
from .models import DecodedPayload, DecodedValue, SfloatSpecialValue
from .exceptions import UnsupportedSchemaFeatureError, PayloadDecodeError


def _evaluate_condition(condition: str, context_values: dict[str, Any], context_flags: dict[str, Any]) -> bool:
    """Evaluate conditions like 'flags.time_stamp_present == 1'."""
    condition = condition.strip()
    
    op_map = {
        " == ": lambda a, b: a == b,
        " != ": lambda a, b: a != b,
        " >= ": lambda a, b: a >= b,
        " <= ": lambda a, b: a <= b,
        " > ": lambda a, b: a > b,
        " < ": lambda a, b: a < b,
    }
    
    op_str = next((op for op in op_map if op in condition), None)
    if not op_str:
        raise UnsupportedSchemaFeatureError(f"Unsupported condition syntax: {condition}")
        
    left, right = condition.split(op_str, 1)
    left = left.strip()
    right = right.strip()
    
    try:
        right_val = int(right)
    except ValueError:
        try:
            right_val = float(right)
        except ValueError:
            right_val = right
        
    val = None
    if left.startswith("flags."):
        flag_name = left.split(".", 1)[1]
        val = context_flags.get(flag_name)
    else:
        raw_val = context_values.get(left)
        if isinstance(raw_val, DecodedValue):
            val = raw_val.physical_value
        else:
            val = raw_val
            
    if val is None:
        return False
        
    return op_map[op_str](val, right_val)


def _parse_sfloat16(data: bytes, offset: int, byte_order: str = "little_endian") -> Tuple[Any, int]:
    """Parse IEEE-11073 16-bit SFLOAT."""
    if byte_order != "little_endian":
        raise UnsupportedSchemaFeatureError(f"Unsupported SFLOAT byte_order: {byte_order}")
        
    val = struct.unpack_from('<H', data, offset)[0]
    
    if val == 0x07FF:
        return SfloatSpecialValue.NaN, 2
    elif val == 0x07FE:
        return SfloatSpecialValue.POSITIVE_INFINITY, 2
    elif val == 0x0802:
        return SfloatSpecialValue.NEGATIVE_INFINITY, 2
    elif val == 0x0800:
        return SfloatSpecialValue.NOT_AT_THIS_RESOLUTION, 2
    elif val == 0x0801:
        return SfloatSpecialValue.RESERVED, 2
        
    mantissa = val & 0x0FFF
    if mantissa >= 0x0800:
        mantissa = -((0x0FFF + 1) - mantissa)
        
    exponent = (val >> 12) & 0x0F
    if exponent >= 0x08:
        exponent = -((0x0F + 1) - exponent)
        
    magnitude = math.pow(10, exponent)
    result = mantissa * magnitude
    return round(result, abs(exponent) if exponent < 0 else 0), 2


def _parse_bitfield(data: bytes, offset: int, size_bytes: int, field_schema: FieldSchema, byte_order: str) -> Tuple[dict, int]:
    """Parse bitfield flags."""
    if byte_order != "little_endian":
        raise UnsupportedSchemaFeatureError(f"Unsupported bitfield byte_order: {byte_order}", field_name=field_schema.name)
        
    if size_bytes == 1:
        val = struct.unpack_from('<B', data, offset)[0]
    elif size_bytes == 2:
        val = struct.unpack_from('<H', data, offset)[0]
    elif size_bytes == 3:
        val = int.from_bytes(data[offset:offset+3], byteorder='little')
    elif size_bytes == 4:
        val = struct.unpack_from('<I', data, offset)[0]
    else:
        raise UnsupportedSchemaFeatureError(f"Unsupported bitfield size: {size_bytes}", field_name=field_schema.name)
        
    flags = {}
    for bit_name, bit_def in field_schema.bitfield.items():
        if isinstance(bit_def, str):
            if bit_name.startswith("bit_"):
                bit_idx = int(bit_name.split("_")[1])
                flags[bit_def] = bool(val & (1 << bit_idx))
        elif isinstance(bit_def, dict) and "name" in bit_def:
            if "_to_" in bit_name:
                parts = bit_name.replace("bit_", "").split("_to_")
                start_bit = int(parts[0])
                end_bit = int(parts[1])
                mask = ((1 << (end_bit - start_bit + 1)) - 1) << start_bit
                extracted = (val & mask) >> start_bit
                
                flag_name = bit_def["name"]
                values_map = bit_def.get("values", {})
                
                found_val = extracted
                for v_key, v_name in values_map.items():
                    if isinstance(v_key, str) and v_key.startswith("0b"):
                        if int(v_key, 2) == extracted:
                            found_val = v_name
                            break
                    elif v_key == extracted:
                        found_val = v_name
                        break
                flags[flag_name] = found_val
                
    return flags, size_bytes


def _get_byte_order(field_schema: FieldSchema) -> str:
    return field_schema.byte_order or "little_endian"


def _decode_field(field_schema: FieldSchema, data: bytes, offset: int, schema: LoadedDeviceSchema, char_uuid: str, context_values: dict, context_flags: dict) -> Tuple[Any, int, dict]:
    """Decode a single schema field."""
    is_present = True
    if field_schema.present_if:
        is_present = _evaluate_condition(field_schema.present_if, context_values, context_flags)
        
    if not is_present:
        return None, 0, {}
        
    size_bytes = field_schema.size_bytes
    if field_schema.type_name == "uint8":
        size_bytes = size_bytes or 1
    elif field_schema.type_name in ("uint16", "medfloat16", "sfloat16"):
        size_bytes = size_bytes or 2
    elif field_schema.type_name == "uint24":
        size_bytes = size_bytes or 3
    elif field_schema.type_name == "uint32":
        size_bytes = size_bytes or 4
    elif field_schema.type_name.startswith("boolean["):
        size_bytes = size_bytes or int(field_schema.type_name.replace("boolean[", "").replace("]", "")) // 8

    # Validate truncation if field size is known
    if size_bytes > 0 and offset + size_bytes > len(data):
        raise PayloadDecodeError(
            f"Payload truncated reading field '{field_schema.name}'",
            schema_file=schema.source_path,
            characteristic_uuid=char_uuid,
            field_name=field_schema.name,
            payload_length=len(data),
            byte_offset=offset
        )

    flags = {}
    byte_order = _get_byte_order(field_schema)
    if byte_order != "little_endian":
        raise UnsupportedSchemaFeatureError(f"Unsupported byte_order: {byte_order}", schema_file=schema.source_path, characteristic_uuid=char_uuid, field_name=field_schema.name)

    fmt_prefix = '<' if byte_order == 'little_endian' else '>'

    if field_schema.type_name == "uint8":
        val = struct.unpack_from(f'{fmt_prefix}B', data, offset)[0]
    elif field_schema.type_name == "uint16":
        val = struct.unpack_from(f'{fmt_prefix}H', data, offset)[0]
    elif field_schema.type_name == "uint24":
        if byte_order == 'little_endian':
            val = int.from_bytes(data[offset:offset+3], byteorder='little')
        else:
            val = int.from_bytes(data[offset:offset+3], byteorder='big')
    elif field_schema.type_name == "uint32":
        val = struct.unpack_from(f'{fmt_prefix}I', data, offset)[0]
    elif field_schema.type_name.startswith("boolean["):
        parsed_flags, sz = _parse_bitfield(data, offset, size_bytes, field_schema, byte_order)
        val = parsed_flags
        flags = parsed_flags
    elif field_schema.type_name in ("medfloat16", "sfloat16"):
        val, sz = _parse_sfloat16(data, offset, byte_order)
    elif field_schema.type_name == "struct":
        if not field_schema.ref or field_schema.ref not in schema.types:
            raise UnsupportedSchemaFeatureError(f"Missing or unknown struct ref: {field_schema.ref}", schema_file=schema.source_path, characteristic_uuid=char_uuid, field_name=field_schema.name)
            
        type_def = schema.types[field_schema.ref]
        val = {}
        sub_offset = offset
        for sub_field in type_def.fields:
            struct_context_values = {**context_values, **val}
            struct_context_flags = {**context_flags, **flags}
            sub_val, sub_sz, sub_flags = _decode_field(
                sub_field, data, sub_offset, schema, char_uuid, struct_context_values, struct_context_flags
            )
            if sub_val is not None:
                val[sub_field.name] = sub_val
                flags.update(sub_flags)
            sub_offset += sub_sz
        size_bytes = sub_offset - offset
    else:
        raise UnsupportedSchemaFeatureError(f"Unsupported type: {field_schema.type_name}", schema_file=schema.source_path, characteristic_uuid=char_uuid, field_name=field_schema.name)

    return val, size_bytes, flags


def decode(schema: LoadedDeviceSchema, characteristic_uuid: str, payload: bytes) -> DecodedPayload:
    """Decode binary payload bytes into structured values based on characteristic schema."""
    char_schema = next((c for c in schema.characteristics if c.uuid == characteristic_uuid), None)
    if not char_schema:
        raise ValueError(f"Characteristic {characteristic_uuid} not found in schema")
        
    payload_schema = char_schema.payload_schema
    if not payload_schema:
        raise ValueError(f"Characteristic {characteristic_uuid} has no payload_schema")

    values = {}
    status_flags = {}
    
    offset = 0
    for field_schema in payload_schema.fields:
        val, sz, flags = _decode_field(field_schema, payload, offset, schema, characteristic_uuid, values, status_flags)
        if val is not None:
            if field_schema.type_name.startswith("boolean["):
                status_flags.update(flags)
            else:
                unit = field_schema.unit
                resolution = field_schema.resolution
                if field_schema.unit_logic:
                    cond = field_schema.unit_logic.get("if")
                    if cond and _evaluate_condition(cond, values, status_flags):
                        then_block = field_schema.unit_logic.get("then", {})
                        unit = then_block.get("unit")
                        if "resolution" in then_block:
                            resolution = then_block.get("resolution")
                    else:
                        else_block = field_schema.unit_logic.get("else", {})
                        unit = else_block.get("unit")
                        if "resolution" in else_block:
                            resolution = else_block.get("resolution")
                        
                if field_schema.resolution_logic:
                    cond = field_schema.resolution_logic.get("if")
                    if cond and _evaluate_condition(cond, values, status_flags):
                        resolution = field_schema.resolution_logic.get("then", {}).get("resolution")
                    else:
                        resolution = field_schema.resolution_logic.get("else", {}).get("resolution")
                
                physical_val = val
                if resolution is not None and isinstance(val, (int, float)):
                    physical_val = val * resolution
                    
                values[field_schema.name] = DecodedValue(
                    raw_value=val,
                    physical_value=physical_val,
                    unit=unit,
                    resolution=resolution
                )
                status_flags.update(flags)
                
            offset += sz

    if offset < len(payload):
        raise PayloadDecodeError(
            f"Payload has unexpected trailing bytes (decoded {offset} bytes, payload length {len(payload)})",
            schema_file=schema.source_path,
            characteristic_uuid=characteristic_uuid,
            payload_length=len(payload),
            byte_offset=offset
        )

    return DecodedPayload(
        values=values,
        status_flags=status_flags
    )

