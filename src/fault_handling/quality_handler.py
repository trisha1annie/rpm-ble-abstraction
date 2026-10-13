from ble_plugin.models import DecodedPayload
from ble_plugin.schema import PayloadSchema

"""Decides if a payload is invalid or not"""
"""If a required field is missing the handler marks the payload as invalid"""
def payload_quality(decode: DecodedPayload, schema: PayloadSchema) -> tuple[str, set[str]]:
    required_fields = set(
        field.name
        for field in schema.fields
        if field.required
    )

    decoded_fields = set(decode.values.keys())
    missing_required = required_fields-decoded_fields

    if missing_required: 
        return ("INVALID", missing_required)

    recoverable_payload_flags = {
        "truncated_payload", 
        "trailing_bytes"
    }

    if any(
        value and flag not in recoverable_payload_flags 
        for flag, value in decode.quality_flags.items()
    ):
        return ("INVALID", set())

    if any(decode.quality_flags.values()): 
        return ("USABLE", set())
    return ("VALID PAYLOAD", set())

def handle_payload(
    decoded_payload: DecodedPayload,
    quality_status: str
) -> DecodedPayload | None:
    if quality_status == "INVALID":
        return None
    return decoded_payload