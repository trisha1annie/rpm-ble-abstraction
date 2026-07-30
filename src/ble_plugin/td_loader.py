import json
from pathlib import Path

from .exceptions import SchemaLoadError
from .schema import LoadedDeviceSchema
from .yaml_loader import _build_loaded_schema


TYPE_MAP = {
    "xsd:unsignedByte": "uint8",
    "xsd:byte": "int8",
    "xsd:unsignedShort": "uint16",
    "xsd:short": "int16",
    "xsd:unsignedInt": "uint32",
    "xsd:int": "int32",
}


def load_wot_schema(file_path: str | Path) -> LoadedDeviceSchema:
    """Convert the wot td and bdo schema into standard scheme for the decoder"""
    td_path = Path(file_path)

    try:
        with td_path.open("r", encoding="utf-8") as file:
            td = json.load(file)
    except FileNotFoundError as error:
        raise SchemaLoadError(
            f"File not found: {td_path}",
            str(td_path),
        ) from error
    except json.JSONDecodeError as error:
        raise SchemaLoadError(
            f"TD JSON parsing error: {error}",
            str(td_path),
        ) from error

    try:
        measurement = td["properties"]["measurement"]
        form = measurement["forms"][0]

        service_uuid = form["ble:serviceUuid"]
        characteristic_uuid = form["ble:characteristicUuid"]
        bdo_reference = form["bdo:payloadSpecification"]
    except (KeyError, IndexError, TypeError) as error:
        raise SchemaLoadError(
            f"Invalid TD structure: {error}",
            str(td_path),
        ) from error

    bdo_file = (td_path.parent / bdo_reference).resolve()

    try:
        with bdo_file.open("r", encoding="utf-8") as file:
            bdo = json.load(file)
    except FileNotFoundError as error:
        raise SchemaLoadError(
            f"BDO file not found: {bdo_file}",
            str(td_path),
        ) from error
    except json.JSONDecodeError as error:
        raise SchemaLoadError(
            f"BDO JSON parsing error: {error}",
            str(bdo_file),
        ) from error

    if not isinstance(bdo, dict):
        raise SchemaLoadError(
            "BDO root must be a dictionary",
            str(bdo_file),
        )

    fields = bdo.get("bdo:field")

    if not isinstance(fields, list) or not fields:
        raise SchemaLoadError(
            "Missing or invalid 'bdo:field' list",
            str(bdo_file),
        )

    converted_fields = []

    for entry in fields:
        if not isinstance(entry, dict):
            raise SchemaLoadError(
                "Each BDO field must be a dictionary",
                str(bdo_file),
            )

        field_name = entry.get("bdo:name")

        if not field_name:
            raise SchemaLoadError(
                "BDO field missing 'bdo:name'",
                str(bdo_file),
            )

        field_type = entry.get("@type")

        if field_type == "bdo:ByteSequenceField":
            type_name = "bytes"
        else:
            data_type = entry.get("bdo:dataType")

            if data_type not in TYPE_MAP:
                raise SchemaLoadError(
                    f"Unsupported or missing datatype {data_type!r} "
                    f"for field {field_name!r}",
                    str(bdo_file),
                )

            type_name = TYPE_MAP[data_type]

        converted_field = {
            "name": field_name,
            "type": type_name,
            "size_bytes": entry.get("bdo:byteLength", 0),
            "unit": entry.get("bdo:unit"),
            "expected_value": entry.get("bdo:expectedValue"),
        }

        converted_fields.append(converted_field)

    operations = form.get("op", [])

    access = []

    if "readproperty" in operations:
        access.append("read")

    if "writeproperty" in operations:
        access.append("write")

    if "observeproperty" in operations:
        access.append("notify")

    if not access:
        raise SchemaLoadError(
            "TD form does not define a supported operation",
            str(td_path),
        )

    schema_data = {
        "device_type": td.get("title", td_path.stem),
        "service": {
            "uuid": service_uuid,
            "name": td.get("title", "unknown_service"),
        },
        "characteristics": [
            {
                "uuid": characteristic_uuid,
                "name": measurement.get("title", "measurement"),
                "access": access,
                "payload_schema": {
                    "fields": converted_fields,
                },
            }
        ],
        "types": {},
    }

    return _build_loaded_schema(
        schema_data,
        str(td_path),
    )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]

    schema = load_wot_schema(
        project_root / "wot" / "td" / "oxi.yaml"
    )

    print(schema)