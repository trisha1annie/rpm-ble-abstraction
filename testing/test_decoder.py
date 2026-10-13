import pytest
import struct
import os
from ble_plugin.schema import (
    LoadedDeviceSchema, GattServiceSchema, CharacteristicSchema, PayloadSchema, FieldSchema, TypeDefinition, normalise_uuid
)
from ble_plugin.yaml_loader import load_schema
from ble_plugin.td_loader import load_wot_schema
from ble_plugin.decoder import decode, _parse_sfloat16
from ble_plugin.models import SfloatSpecialValue, DecodedValue
from ble_plugin.exceptions import UnsupportedSchemaFeatureError, PayloadDecodeError, UnexpectedFieldValueError
from routing.router import router

CHAR_UUID = "00002a35-0000-1000-8000-00805f9b34fb"


def build_mock_schema(fields, types=None):
    char = CharacteristicSchema(
        uuid="00002a35-0000-1000-8000-00805f9b34fb",
        name="test_char",
        access=("notify",),
        payload_schema=PayloadSchema(fields=tuple(fields))
    )
    return LoadedDeviceSchema(
        device_type="test",
        service=GattServiceSchema("00001810-0000-1000-8000-00805f9b34fb", "test"),
        characteristics=(char,),
        types=types or {}
    )


def test_little_endian_uint16():
    schema = build_mock_schema([
        FieldSchema("val", "uint16", 2)
    ])
    payload = b'\x34\x12'
    result = decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", payload)
    assert result.values["val"].raw_value == 0x1234
    assert result.values["val"].physical_value == 0x1234


def test_nested_date_time_struct():
    types = {
        "date_time": TypeDefinition(
            name="date_time",
            fields=(
                FieldSchema("year", "uint16", 2),
                FieldSchema("month", "uint8", 1),
            )
        )
    }
    schema = build_mock_schema([
        FieldSchema("ts", "struct", 3, ref="date_time")
    ], types)
    
    payload = b'\xE8\x07\x05'
    result = decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", payload)
    assert result.values["ts"].raw_value["year"] == 2024
    assert result.values["ts"].raw_value["month"] == 5


def test_normal_positive_sfloat():
    val, _ = _parse_sfloat16(b'\x78\x00', 0, "little_endian")
    assert val == 120.0


def test_negative_sfloat():
    val, _ = _parse_sfloat16(b'\xFE\x0F', 0, "little_endian")
    assert val == -2.0
    
    val, _ = _parse_sfloat16(b'\x02\xF0', 0, "little_endian")
    assert val == 0.2


def test_sfloat_special_values():
    assert _parse_sfloat16(b'\xFF\x07', 0, "little_endian")[0] == SfloatSpecialValue.NaN
    assert _parse_sfloat16(b'\xFE\x07', 0, "little_endian")[0] == SfloatSpecialValue.POSITIVE_INFINITY
    assert _parse_sfloat16(b'\x02\x08', 0, "little_endian")[0] == SfloatSpecialValue.NEGATIVE_INFINITY
    assert _parse_sfloat16(b'\x00\x08', 0, "little_endian")[0] == SfloatSpecialValue.NOT_AT_THIS_RESOLUTION
    assert _parse_sfloat16(b'\x01\x08', 0, "little_endian")[0] == SfloatSpecialValue.RESERVED


def test_bitfield_extraction():
    schema = build_mock_schema([
        FieldSchema("flags", "boolean[8]", 1, bitfield={
            "bit_0": "flag_a",
            "bit_1": "flag_b",
            "bit_2_to_3": {"name": "range_flag", "values": {0: "zero", 1: "one", 2: "two"}}
        })
    ])
    payload = b'\x09'
    result = decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", payload)
    assert result.status_flags["flag_a"] is True
    assert result.status_flags["flag_b"] is False
    assert result.status_flags["range_flag"] == "two"
    assert "flags" not in result.values


def test_present_if_true_and_false():
    schema = build_mock_schema([
        FieldSchema("flags", "boolean[8]", 1, bitfield={"bit_0": "has_val1", "bit_1": "has_val2"}),
        FieldSchema("val1", "uint8", 1, present_if="flags.has_val1 == 1"),
        FieldSchema("val2", "uint8", 1, present_if="flags.has_val2 == 1")
    ])
    payload = b'\x01\x42'
    result = decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", payload)
    assert result.values["val1"].physical_value == 0x42
    assert "val2" not in result.values


def test_unsupported_decoder_feature():
    schema = build_mock_schema([
        FieldSchema("val", "float64", 8)
    ])
    with pytest.raises(UnsupportedSchemaFeatureError) as exc:
        decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", b'\x00'*8)
    assert "val" in str(exc.value)


def test_invalid_uuid():
    with pytest.raises(ValueError, match="Invalid UUID"):
        normalise_uuid("invalid-uuid-string")


def test_expected_integer_value_matches():
    schema = build_mock_schema([
        FieldSchema("flag", "uint8", 1, expected_value=0x81),
        FieldSchema("val", "uint8", 1),
    ])
    result = decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", b'\x81\x42')
    assert result.values["flag"].raw_value == 0x81
    assert result.values["val"].raw_value == 0x42


def test_expected_integer_value_mismatch():
    schema = build_mock_schema([
        FieldSchema("flag", "uint8", 1, expected_value=0x81),
        FieldSchema("val", "uint8", 1),
    ])
    with pytest.raises(UnexpectedFieldValueError, match="Field 'flag' has value 128, expected 129") as exc:
        decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", b'\x80\x42')
    assert exc.value.field_name == "flag"
    assert exc.value.byte_offset == 0


def test_expected_bytes_value_is_case_insensitive():
    schema = build_mock_schema([
        FieldSchema("tail", "bytes", 2, expected_value="AB00"),
    ])
    result = decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", b'\xab\x00')
    assert result.values["tail"].raw_value == "ab00"


def test_expected_bytes_value_mismatch():
    schema = build_mock_schema([
        FieldSchema("tail", "bytes", 2, expected_value="0000"),
    ])
    with pytest.raises(UnexpectedFieldValueError, match="Field 'tail'"):
        decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", b'\x00\x01')


def test_expected_value_not_enforced_for_float_fields():
    schema = build_mock_schema([
        FieldSchema("unused", "medfloat16", 2, expected_value="NaN"),
    ])
    result = decode(schema, "00002a35-0000-1000-8000-00805f9b34fb", b'\x78\x00')
    assert result.values["unused"].raw_value == 120.0


# --- Real Schema Decoding Tests ---

def get_real_schema(filename):
    base_dir = os.path.join(
        os.path.dirname(__file__), "..", "src", "gatt_registry", "decode_registry"
    )
    return load_schema(os.path.join(base_dir, filename))


def test_real_weight_scale():
    schema = get_real_schema("weight_scale.yaml")
    char_uuid = normalise_uuid("2A9D")
    
    # SI flags 0x00 (bit 0 = 0 -> kg), raw uint16 15100 (0x3AFC)
    # 15100 * 0.005 = 75.5 kg
    # Payload: flags (1 byte) + weight (2 bytes) = b'\x00\xFC\x3A'
    payload_si = b'\x00\xFC\x3A'
    result = decode(schema, char_uuid, payload_si)
    
    assert result.values["weight"].raw_value == 15100
    assert result.values["weight"].physical_value == 75.5
    assert result.values["weight"].unit == "kg"
    assert result.values["weight"].resolution == 0.005
    
    # Imperial flags 0x01 (bit 0 = 1 -> lb), raw uint16 16500 (0x4074)
    # 16500 * 0.01 = 165.0 lb
    # Payload: b'\x01\x74\x40'
    payload_imp = b'\x01\x74\x40'
    result2 = decode(schema, char_uuid, payload_imp)
    
    assert result2.values["weight"].raw_value == 16500
    assert result2.values["weight"].physical_value == 165.0
    assert result2.values["weight"].unit == "lb"
    assert result2.values["weight"].resolution == 0.01


def test_real_blood_pressure():
    schema = get_real_schema("blood_pressure.yaml")
    char_uuid = normalise_uuid("2A35")
    
    # Flags 0 (mmHg, no timestamp, no pulse, etc)
    # Sys 120 (0x0078), Dia 80 (0x0050), MAP 90 (0x005A)
    # Payload: flags(1) + sys(2) + dia(2) + map(2) = b'\x00\x78\x00\x50\x00\x5A\x00'
    payload_base = b'\x00\x78\x00\x50\x00\x5A\x00'
    res_base = decode(schema, char_uuid, payload_base)
    
    assert res_base.values["systolic"].physical_value == 120.0
    assert res_base.values["diastolic"].physical_value == 80.0
    assert res_base.values["mean_arterial_pressure"].physical_value == 90.0
    assert res_base.values["systolic"].unit == "mmHg"
    assert "time_stamp" not in res_base.values
    
    # Flags bit_1(timestamp)=1, bit_2(pulse)=1 -> flags = 0x06
    # Sys(120), Dia(80), MAP(90) -> \x78\x00\x50\x00\x5A\x00
    # Timestamp: Year 2024 (\xE8\x07), Month 5 (\x05), Day 15 (\x0F), Hour 12 (\x0C), Min 30 (\x1E), Sec 45 (\x2D) -> \xE8\x07\x05\x0F\x0C\x1E\x2D
    # Pulse Rate: 72 (0x0048) -> \x48\x00
    payload_full = b'\x06' + b'\x78\x00\x50\x00\x5A\x00' + b'\xE8\x07\x05\x0F\x0C\x1E\x2D' + b'\x48\x00'
    res_full = decode(schema, char_uuid, payload_full)
    
    assert res_full.values["pulse_rate"].physical_value == 72.0
    ts = res_full.values["time_stamp"].raw_value
    assert ts["year"] == 2024
    assert ts["month"] == 5



def test_real_pulse_oximeter_base():
    schema = get_real_schema("pulse_oximeter.yaml")
    char_uuid = normalise_uuid("2A5F") # Continuous measurement
    
    # Flags 0x00: no fast/slow/status fields
    # spo2pr_normal_spo2: 98 (0x0062)
    # spo2pr_normal_pr: 72 (0x0048)
    payload_base = b'\x00' + b'\x62\x00' + b'\x48\x00'
    res_base = decode(schema, char_uuid, payload_base)
    
    assert res_base.values["spo2pr_normal_spo2"].physical_value == 98.0
    assert res_base.values["spo2pr_normal_pr"].physical_value == 72.0
    assert "spo2pr_fast_spo2" not in res_base.values
    assert "measurement_status" not in res_base.status_flags


def test_real_pulse_oximeter_fast():
    schema = get_real_schema("pulse_oximeter.yaml")
    char_uuid = normalise_uuid("2A5F")
    
    # Flags bit_0(spo2pr_fast_present)=1 -> flags = 0x01
    payload_fast = b'\x01' + b'\x62\x00' + b'\x48\x00' + b'\x63\x00' + b'\x49\x00'
    res_fast = decode(schema, char_uuid, payload_fast)
    
    assert res_fast.values["spo2pr_fast_spo2"].physical_value == 99.0
    assert res_fast.values["spo2pr_fast_pr"].physical_value == 73.0


def test_real_pulse_oximeter_slow():
    schema = get_real_schema("pulse_oximeter.yaml")
    char_uuid = normalise_uuid("2A5F")
    
    # Flags bit_1(spo2pr_slow_present)=1 -> flags = 0x02
    payload_slow = b'\x02' + b'\x62\x00' + b'\x48\x00' + b'\x61\x00' + b'\x47\x00'
    res_slow = decode(schema, char_uuid, payload_slow)
    
    assert res_slow.values["spo2pr_slow_spo2"].physical_value == 97.0
    assert res_slow.values["spo2pr_slow_pr"].physical_value == 71.0


def test_real_pulse_oximeter_status():
    schema = get_real_schema("pulse_oximeter.yaml")
    char_uuid = normalise_uuid("2A5F")
    
    # Flags bit_2(measurement_status_present)=1 -> flags = 0x04
    # measurement_status: bit_5(measurement_ongoing) = 0x0020
    payload_status = b'\x04' + b'\x62\x00' + b'\x48\x00' + b'\x20\x00'
    res_status = decode(schema, char_uuid, payload_status)
    
    assert res_status.status_flags["measurement_ongoing"] is True
    assert res_status.status_flags.get("early_estimated_data") is False


# --- YK oximeter (WoT TD/BDO), payloads captured from a real device ---

YK_SERVICE_UUID = "cdeacd80-5235-4c07-8846-93a37ee6b86d"
YK_CHARACTERISTIC_UUID = "cdeacd81-5235-4c07-8846-93a37ee6b86d"


def get_yk_oximeter_schema():
    td_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "wot", "td", "oxi.yaml"
    )
    return load_wot_schema(td_path)


def decode_yk(hex_payload):
    return decode(
        get_yk_oximeter_schema(),
        YK_CHARACTERISTIC_UUID,
        bytes.fromhex(hex_payload),
    )


def test_yk_oximeter_measurement_at_rest():
    result = decode_yk("81624b450000000000000000000000")

    assert result.values["spo2"].physical_value == 98
    assert result.values["spo2"].unit == "%"
    assert result.values["pulse_rate"].physical_value == 75
    assert result.values["pulse_rate"].unit == "bpm"
    assert result.values["perfusion_index_raw"].physical_value == 69
    assert result.values["reserved"].raw_value == "00" * 11


def test_yk_oximeter_measurement_after_exercise():
    result = decode_yk("816371550000000000000000000000")

    assert result.values["spo2"].physical_value == 99
    assert result.values["pulse_rate"].physical_value == 113
    assert result.values["perfusion_index_raw"].physical_value == 85


def test_yk_oximeter_measurement_with_finger_removed():
    result = decode_yk("810000000000000000000000000000")

    assert result.values["spo2"].physical_value == 0
    assert result.values["pulse_rate"].physical_value == 0
    assert result.values["perfusion_index_raw"].physical_value == 0


def test_yk_oximeter_rejects_waveform_packet():
    with pytest.raises(UnexpectedFieldValueError) as exc:
        decode_yk("802a2827272828292a292800000000")
    assert exc.value.field_name == "flag"


def test_yk_oximeter_rejects_non_zero_reserved_bytes():
    with pytest.raises(UnexpectedFieldValueError) as exc:
        decode_yk("81624b450000000000000000000001")
    assert exc.value.field_name == "reserved"


def test_yk_oximeter_rejects_legacy_ten_byte_packet():
    with pytest.raises(PayloadDecodeError, match="Payload truncated"):
        decode_yk("81624800000000000000")


def test_yk_oximeter_rejects_trailing_bytes():
    with pytest.raises(PayloadDecodeError, match="unexpected trailing bytes"):
        decode_yk("81624b45000000000000000000000000")


def test_router_decodes_yk_oximeter_through_wot_schema():
    result = router(
        YK_SERVICE_UUID,
        YK_CHARACTERISTIC_UUID,
        bytes.fromhex("81624b450000000000000000000000"),
    )

    assert result.values["spo2"].physical_value == 98
    assert result.values["pulse_rate"].physical_value == 75


def test_invalid_fixed_field_size():
    schema = build_mock_schema([
        FieldSchema(
            name="val1",
            type_name="uint16",
            size_bytes=1
        )
    ])

    payload = b'\x34\x12'

    with pytest.raises(PayloadDecodeError, match="Invalid field size"):
        decode(schema, CHAR_UUID, payload)


def test_reserved_sfloat_encoding():
    schema = build_mock_schema([
        FieldSchema(
            name="systolic",
            type_name="sfloat16",
            size_bytes=2,
            required=True
        )
    ])

    payload = bytes.fromhex("0108")  # 0x0801, little-endian

    with pytest.raises(PayloadDecodeError, match="Reserved SFLOAT encoding"):
        decode(schema, CHAR_UUID, payload)