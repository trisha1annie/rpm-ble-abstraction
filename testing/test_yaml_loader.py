import pytest
import os
from ble_plugin.yaml_loader import load_schema
from ble_plugin.schema import normalise_uuid
from ble_plugin.exceptions import SchemaLoadError


def test_uuid_normalisation():
    # 16-bit UUIDs
    assert normalise_uuid("1810") == "00001810-0000-1000-8000-00805f9b34fb"
    assert normalise_uuid("0x1810") == "00001810-0000-1000-8000-00805f9b34fb"
    assert normalise_uuid("181d") == "0000181d-0000-1000-8000-00805f9b34fb"
    
    # 128-bit UUIDs
    full_uuid = "00002a35-0000-1000-8000-00805f9b34fb"
    assert normalise_uuid(full_uuid) == full_uuid
    assert normalise_uuid(full_uuid.upper()) == full_uuid
    
    # Invalid UUIDs
    with pytest.raises(ValueError):
        normalise_uuid("invalid")


def test_load_all_registry_files():
    base_dir = os.path.join(
        os.path.dirname(__file__), "..", "gatt_registry", "decode_registry"
    )
    
    bp_path = os.path.join(base_dir, "blood_pressure.yaml")
    oxi_path = os.path.join(base_dir, "pulse_oximeter.yaml")
    weight_path = os.path.join(base_dir, "weight_scale.yaml")
    
    bp_schema = load_schema(bp_path)
    assert bp_schema.device_type == "blood_pressure_monitor"
    assert bp_schema.service.uuid == "00001810-0000-1000-8000-00805f9b34fb"
    assert len(bp_schema.characteristics) > 0
    
    oxi_schema = load_schema(oxi_path)
    assert oxi_schema.device_type == "pulse_oximeter"
    
    weight_schema = load_schema(weight_path)
    assert weight_schema.device_type == "weight_scale"


def test_invalid_yaml_structure(tmp_path):
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("device_type: test\n# missing service")
    
    with pytest.raises(SchemaLoadError) as exc:
        load_schema(str(invalid_yaml))
    assert "Missing or invalid 'service'" in str(exc.value)


def test_invalid_yaml_field(tmp_path):
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text('''
device_type: test
service:
  uuid: "1810"
characteristics:
  - uuid: "2A35"
    access: ["indicate"]
    payload_schema:
      fields:
        - name: missing_type
''')
    
    with pytest.raises(SchemaLoadError) as exc:
        load_schema(str(invalid_yaml))
    assert "missing 'type'" in str(exc.value)
