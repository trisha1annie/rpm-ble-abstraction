from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum, auto


class SfloatSpecialValue(Enum):
    """Explicit representation for non-finite/special SFLOAT values."""
    NaN = auto()
    POSITIVE_INFINITY = auto()
    NEGATIVE_INFINITY = auto()
    NOT_AT_THIS_RESOLUTION = auto()
    RESERVED = auto()


@dataclass(frozen=True)
class DecodedValue:
    """Represents a successfully decoded physical value, preserving raw context."""
    raw_value: Any
    physical_value: Any
    unit: Optional[str] = None
    resolution: Optional[float] = None


@dataclass(frozen=True)
class DecodedPayload:
    """Represents a successfully decoded generic payload."""
    values: dict[str, DecodedValue]
    status_flags: dict[str, Any]
    warnings: tuple[str, ...] = field(default_factory=tuple)
