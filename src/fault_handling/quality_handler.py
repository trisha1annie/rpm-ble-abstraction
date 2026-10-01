from ble_plugin.models import DecodedPayload
from ble_plugin.schema import PayloadSchema

"""Decides if a payload is invalid or not"""
"""If a required field is missing the handler marks the payload as invalid"""
def payload_quality(decode: DecodedPayload, schema: PayloadSchema) -> str:
    required_fields = set(
        field.name
        for field in schema.fields
        if field.required
    )

    decoded_fields = set(decode.values.keys())
    missing_required = required_fields-decoded_fields

    if missing_required: 
        return ("INVALID", missing_required)
    if decode.quality_flags: 
        return "USABLE"
    return "VALID PAYLOAD"