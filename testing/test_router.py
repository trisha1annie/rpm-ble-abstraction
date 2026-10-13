
import pytest
import routing.router as router_module

from types import SimpleNamespace
from unittest.mock import Mock

from routing.router import router, RoutingError
from ble_plugin.exceptions import SchemaLoadError


# Helper: Create a fake schema with one characteristic
def make_schema(service_uuid, characteristic_uuid):
    return SimpleNamespace(
        service=SimpleNamespace(uuid=service_uuid),
        characteristics=[
            SimpleNamespace(uuid=characteristic_uuid)
        ],
    )


# Helper: Set up a fake schema directory and loader
def setup_router(monkeypatch, tmp_path, is_sig_pair, schemas):
    monkeypatch.setattr(router_module, "project_root", tmp_path)

    if is_sig_pair:
        schema_dir = tmp_path / "gatt_registry" / "decode_registry"
        loader_name = "load_schema"
    else:
        schema_dir = tmp_path / "wot" / "td"
        loader_name = "load_wot_schema"

    schema_dir.mkdir(parents=True)

    for filename in schemas:
        (schema_dir / filename).write_text("test schema")

    lookup = Mock()
    lookup.is_sig_pair.return_value = is_sig_pair

    monkeypatch.setattr(
        router_module,
        "BluetoothNumbersLookup",
        Mock(return_value=lookup),
    )

    schema_loader = Mock(side_effect=lambda path: schemas[
        __import__("pathlib").Path(path).name
    ])

    monkeypatch.setattr(router_module, loader_name, schema_loader)

    decoder = Mock(return_value=Mock())
    monkeypatch.setattr(router_module, "decode", decoder)

    return lookup, schema_loader, decoder


# TEST 1: Standard SIG UUID pair uses GATT registry
def test_standard_uuid_uses_gatt_registry(monkeypatch, tmp_path):
    schema = make_schema("1810", "2a35")

    lookup, loader, decoder = setup_router(
        monkeypatch,
        tmp_path,
        True,
        {"bp.yaml": schema},
    )

    result = router("1810", "2a35", b"\x01\x02")

    assert result is decoder.return_value
    loader.assert_called_once()
    decoder.assert_called_once()

    lookup.is_sig_pair.assert_called_once_with(
        router_module.normalize_uuid("1810"),
        router_module.normalize_uuid("2a35"),
    )


# TEST 2: Proprietary UUID pair uses WoT directory
def test_proprietary_uuid_uses_wot(monkeypatch, tmp_path):
    service_uuid = "12345678-1234-1234-1234-123456789abc"
    char_uuid = "87654321-4321-4321-4321-cba987654321"

    schema = make_schema(service_uuid, char_uuid)

    lookup, loader, decoder = setup_router(
        monkeypatch,
        tmp_path,
        False,
        {"custom.yaml": schema},
    )

    result = router(service_uuid, char_uuid, b"\x10")

    assert result is decoder.return_value
    loader.assert_called_once()
    decoder.assert_called_once()


# TEST 3: UUID normalization allows short and full UUIDs
def test_uuid_normalization(monkeypatch, tmp_path):
    schema = make_schema(
        "00001810-0000-1000-8000-00805f9b34fb",
        "00002a35-0000-1000-8000-00805f9b34fb",
    )

    _, _, decoder = setup_router(
        monkeypatch,
        tmp_path,
        True,
        {"bp.yaml": schema},
    )

    router("1810", "2a35", b"\x01")

    decoder.assert_called_once()


# TEST 4: Missing schema directory raises RoutingError
def test_missing_schema_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(router_module, "project_root", tmp_path)

    lookup = Mock()
    lookup.is_sig_pair.return_value = True

    monkeypatch.setattr(
        router_module,
        "BluetoothNumbersLookup",
        Mock(return_value=lookup),
    )

    with pytest.raises(RoutingError, match="Schema directory does not exist"):
        router("1810", "2a35", b"\x01")


# TEST 5: No matching service UUID raises RoutingError
def test_no_matching_service(monkeypatch, tmp_path):
    schema = make_schema("180d", "2a37")

    _, _, decoder = setup_router(
        monkeypatch,
        tmp_path,
        True,
        {"other.yaml": schema},
    )

    with pytest.raises(RoutingError, match="No matching schema found"):
        router("1810", "2a35", b"\x01")

    decoder.assert_not_called()


# TEST 6: Matching service but no matching characteristic
def test_no_matching_characteristic(monkeypatch, tmp_path):
    schema = make_schema("1810", "2a36")

    _, _, decoder = setup_router(
        monkeypatch,
        tmp_path,
        True,
        {"bp.yaml": schema},
    )

    with pytest.raises(RoutingError, match="No matching schema found"):
        router("1810", "2a35", b"\x01")

    decoder.assert_not_called()


# TEST 7: Invalid schema is skipped
def test_invalid_schema_is_skipped(monkeypatch, tmp_path):
    valid_schema = make_schema("1810", "2a35")

    _, loader, decoder = setup_router(
        monkeypatch,
        tmp_path,
        True,
        {
            "invalid.yaml": None,
            "valid.yaml": valid_schema,
        },
    )

    # Force the router to encounter invalid.yaml first
    schema_dir = tmp_path / "gatt_registry" / "decode_registry"

    original_rglob = type(schema_dir).rglob

    def ordered_rglob(self, pattern):
        paths = list(original_rglob(self, pattern))
        return sorted(paths, key=lambda p: p.name)

    monkeypatch.setattr(type(schema_dir), "rglob", ordered_rglob)

    def load_or_raise(path):
        if path.endswith("invalid.yaml"):
            raise SchemaLoadError("Invalid schema")

        return valid_schema

    loader.side_effect = load_or_raise

    result = router("1810", "2a35", b"\x01")

    assert result is decoder.return_value
    assert loader.call_count == 2


# TEST 8: Payload is passed unchanged to decoder
def test_payload_passed_to_decoder(monkeypatch, tmp_path):
    schema = make_schema("1810", "2a35")
    payload = bytes.fromhex("00645000")

    _, _, decoder = setup_router(
        monkeypatch,
        tmp_path,
        True,
        {"bp.yaml": schema},
    )

    router("1810", "2a35", payload)

    assert decoder.call_args.kwargs["payload"] == payload
    assert decoder.call_args.kwargs["schema"] is schema


# TEST 9: Empty schema directory raises RoutingError
def test_empty_schema_directory(monkeypatch, tmp_path):
    _, _, decoder = setup_router(
        monkeypatch,
        tmp_path,
        True,
        {},
    )

    with pytest.raises(RoutingError, match="No matching schema found"):
        router("1810", "2a35", b"\x01")

    decoder.assert_not_called()
