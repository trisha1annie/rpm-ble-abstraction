import uuid
from dataclasses import dataclass, field
from typing import Optional, Any


BLUETOOTH_BASE_UUID_SUFFIX = "-0000-1000-8000-00805f9b34fb"


def normalise_uuid(uuid_val: str) -> str:
    """
    Normalise a Bluetooth UUID to its canonical 128-bit lowercase string representation.
    Accepts 16-bit (e.g. "1810", "0x1810", "181D") and 128-bit formats.
    Validates using uuid.UUID.
    """
    uuid_str = str(uuid_val).strip().lower()
    
    if uuid_str.startswith("0x"):
        uuid_str = uuid_str[2:]
        
    if len(uuid_str) == 4:
        uuid_str = f"0000{uuid_str}{BLUETOOTH_BASE_UUID_SUFFIX}"
        
    try:
        parsed_uuid = uuid.UUID(uuid_str)
        return str(parsed_uuid).lower()
    except ValueError:
        raise ValueError(f"Invalid UUID format: {uuid_val}")
@dataclass(frozen=True)
class TypeDefinition:
    name: str
    description: Optional[str] = None
    size_bytes: Optional[int] = None
    byte_order: Optional[str] = None
    fields: tuple['FieldSchema', ...] = field(default_factory=tuple)
    bits: dict[str, str] = field(default_factory=dict)
    decode: Optional[str] = None
    special_values: dict[int, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FieldSchema:
    name: str
    type_name: str  # Original type string like "boolean[8]", "uint16", "struct"
    size_bytes: int = 0  # 0 indicates variable/dependent size
    bitfield: dict[str, Any] = field(default_factory=dict)
    unit: Optional[str] = None
    unit_logic: Optional[dict[str, Any]] = None
    resolution: Optional[float] = None
    resolution_logic: Optional[dict[str, Any]] = None
    byte_order: Optional[str] = None
    present_if: Optional[str] = None
    always_present: bool = False
    expected_value: Any = None
    notes: Optional[str] = None
    ref: Optional[str] = None  # Reference to a custom TypeDefinition


@dataclass(frozen=True)
class PayloadSchema:
    fields: tuple[FieldSchema, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CharacteristicSchema:
    uuid: str  # Normalised 128-bit UUID
    name: str
    access: tuple[str, ...]
    payload_schema: Optional[PayloadSchema] = None
    condition: Optional[str] = None


@dataclass(frozen=True)
class GattServiceSchema:
    uuid: str  # Normalised 128-bit UUID
    name: str


@dataclass(frozen=True)
class LoadedDeviceSchema:
    device_type: str
    service: GattServiceSchema
    characteristics: tuple[CharacteristicSchema, ...] = field(default_factory=tuple)
    types: dict[str, TypeDefinition] = field(default_factory=dict)
    source_path: Optional[str] = None

