# Utilities for normalising Bluetooth UUIDs

from __future__ import annotations

BLUETOOTH_BASE_UUID_SUFFIX = "-0000-1000-8000-00805F9B34FB"


def normalize_uuid(value: str) -> str:
#Convert Bluetooth UUIDs into a consistent uppercase form
    if not isinstance(value, str): 
        raise TypeError('Value must be a string')
    
    normalize = value.strip().upper()

    if normalize.startswith('0X'):
        normalize = normalize[2:]
    
    if len(normalize) == 4:
        return normalize

    if (
        len(normalize) == 36
        and normalize.startswith("0000")
        and normalize.endswith(BLUETOOTH_BASE_UUID_SUFFIX)
    ):
        return normalize[4:8]

    if len(normalize) == 36:
        return normalize

    raise ValueError(
        f"Unsupported Bluetooth UUID format: {value!r}"
    )


