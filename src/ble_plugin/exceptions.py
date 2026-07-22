class SchemaDrivenBleError(Exception):
    """Base exception for schema-driven BLE driver errors."""
    pass


class SchemaLoadError(SchemaDrivenBleError):
    """Raised when a YAML schema fails validation or cannot be loaded."""
    def __init__(self, message: str, source_path: str = None):
        self.source_path = source_path
        full_msg = f"{message} (in {source_path})" if source_path else message
        super().__init__(full_msg)


class PayloadDecodeError(SchemaDrivenBleError):
    """Raised when a payload cannot be decoded correctly (e.g., truncated data)."""
    def __init__(self, message: str, schema_file: str = None, characteristic_uuid: str = None, field_name: str = None, payload_length: int = None, byte_offset: int = None):
        self.schema_file = schema_file
        self.characteristic_uuid = characteristic_uuid
        self.field_name = field_name
        self.payload_length = payload_length
        self.byte_offset = byte_offset
        
        ctx = []
        if schema_file: ctx.append(f"file: {schema_file}")
        if characteristic_uuid: ctx.append(f"char: {characteristic_uuid}")
        if field_name: ctx.append(f"field: {field_name}")
        if payload_length is not None: ctx.append(f"len: {payload_length}")
        if byte_offset is not None: ctx.append(f"offset: {byte_offset}")
        
        ctx_str = ", ".join(ctx)
        full_msg = f"{message} [{ctx_str}]" if ctx else message
        super().__init__(full_msg)


class UnsupportedSchemaFeatureError(SchemaDrivenBleError):
    """Raised when the decoder encounters a YAML feature it does not yet support."""
    def __init__(self, message: str, schema_file: str = None, characteristic_uuid: str = None, field_name: str = None, feature_name: str = None):
        self.schema_file = schema_file
        self.characteristic_uuid = characteristic_uuid
        self.field_name = field_name
        self.feature_name = feature_name

        ctx = []
        if schema_file: ctx.append(f"file: {schema_file}")
        if characteristic_uuid: ctx.append(f"char: {characteristic_uuid}")
        if field_name: ctx.append(f"field: {field_name}")
        if feature_name: ctx.append(f"feature: {feature_name}")

        ctx_str = ", ".join(ctx)
        full_msg = f"{message} [{ctx_str}]" if ctx else message
        super().__init__(full_msg)


class BleTransportError(SchemaDrivenBleError):
    """Raised for general BLE transport or adapter failures."""
    def __init__(self, message: str, device_id: str = None, operation: str = None):
        self.device_id = device_id
        self.operation = operation

        ctx = []
        if device_id: ctx.append(f"device: {device_id}")
        if operation: ctx.append(f"op: {operation}")

        ctx_str = ", ".join(ctx)
        full_msg = f"{message} [{ctx_str}]" if ctx else message
        super().__init__(full_msg)


class BleNotConnectedError(BleTransportError):
    """Raised when an operation requires an active connection but none exists."""
    pass


class BleDiscoveryError(BleTransportError):
    """Raised when GATT service or characteristic discovery fails."""
    pass


class BleSubscriptionError(BleTransportError):
    """Raised when starting or stopping a notification/indication subscription fails."""
    pass
