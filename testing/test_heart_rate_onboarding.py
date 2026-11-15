"""End-to-end onboarding tests for Heart Rate Monitor (0x180D / 0x2A37)."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ble_plugin.discovery_models import (
    DiscoveredCharacteristic,
    DiscoveredGatt,
    DiscoveredService,
)
from ble_plugin.plugin_driver import DriverMeasurement
from ble_plugin.schema import normalise_uuid
from ble_plugin.standard_plugin_driver import StandardPluginDriver
from fhir_mapping import (
    FhirMappingRegistry,
    FhirNormalisationError,
    FhirNormaliser,
    NormalisationContext,
)


MAPPING_DIRECTORY = Path(__file__).resolve().parents[1] / "src" / "fhir_mapping"
FIXED_TIME = datetime(2026, 11, 3, 4, 0, tzinfo=timezone.utc)


class FakeHeartRateBleClient:

    def __init__(self) -> None:
        self.connected = False
        self.callbacks = {}

    @property
    def device_id(self) -> str:
        return "AA:BB:CC:18:0D:01"

    @property
    def is_connected(self) -> bool:
        return self.connected

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False
        self.callbacks.clear()

    async def discover_gatt(self) -> DiscoveredGatt:
        return DiscoveredGatt(
            device_id=self.device_id,
            services=(
                DiscoveredService(
                    uuid=normalise_uuid("180D"),
                    characteristics=(
                        DiscoveredCharacteristic(
                            uuid=normalise_uuid("2A37"),
                            properties=frozenset({"notify"}),
                        ),
                    ),
                ),
            ),
        )

    async def subscribe(self, characteristic_uuid: str, callback) -> None:
        self.callbacks[normalise_uuid(characteristic_uuid)] = callback

    async def unsubscribe(self, characteristic_uuid: str) -> None:
        self.callbacks.pop(normalise_uuid(characteristic_uuid), None)

    def set_disconnected_callback(self, callback) -> None:
        pass

    async def emit(self, payload: bytes) -> None:
        char_uuid = normalise_uuid("2A37")
        result = self.callbacks[char_uuid](char_uuid, payload)
        if result is not None:
            await result


def test_heart_rate_uint8_end_to_end_to_fhir():
    """Verify happy path: 8-bit heart rate + RR interval decodes and maps to FHIR."""
    async def run() -> None:
        client = FakeHeartRateBleClient()
        driver = StandardPluginDriver(client)
        normaliser = FhirNormaliser(
            FhirMappingRegistry.from_directory(MAPPING_DIRECTORY)
        )
        emitted: list[DriverMeasurement] = []

        await driver.start(emitted.append)
        # Flags 0x16: uint8 HR (0), contact detected/supported (1,1), RR present (1)
        # HR = 72 bpm (0x48), RR = 800/1024 s (0x0320)
        await client.emit(bytes.fromhex("16482003"))
        await driver.stop()

        assert len(emitted) == 1
        measurement = DriverMeasurement(
            device_id=emitted[0].device_id,
            service_uuid=emitted[0].service_uuid,
            characteristic_uuid=emitted[0].characteristic_uuid,
            payload=emitted[0].payload,
            received_at=FIXED_TIME,
        )
        observations = normaliser.normalise(
            measurement,
            NormalisationContext("Patient/hr-001", "Device/hr-strap"),
        )
        assert len(observations) == 1
        assert observations[0]["code"]["coding"][0]["code"] == "8867-4"
        assert observations[0]["valueQuantity"]["value"] == 72
        assert observations[0]["valueQuantity"]["code"] == "/min"

    asyncio.run(run())


def test_heart_rate_uint16_edge_case_maps_to_fhir():
    async def run() -> None:
        client = FakeHeartRateBleClient()
        driver = StandardPluginDriver(client)
        normaliser = FhirNormaliser(
            FhirMappingRegistry.from_directory(MAPPING_DIRECTORY)
        )
        emitted: list[DriverMeasurement] = []

        await driver.start(emitted.append)
        # Flags 0x01: uint16 HR = 260 bpm (0x0104 little-endian)
        await client.emit(bytes.fromhex("010401"))
        await driver.stop()

        assert len(emitted) == 1
        observations = normaliser.normalise(
             emitted[0],
            NormalisationContext("Patient/hr-001"),
        )
        assert len(observations) == 1
        assert observations[0]["valueQuantity"]["value"] == 260

    asyncio.run(run())


def test_heart_rate_rejects_zero_bpm_and_truncated_payload():
    async def run() -> None:
        client = FakeHeartRateBleClient()
        driver = StandardPluginDriver(client)
        normaliser = FhirNormaliser(
            FhirMappingRegistry.from_directory(MAPPING_DIRECTORY)
        )
        emitted: list[DriverMeasurement] = []

        await driver.start(emitted.append)
        await client.emit(bytes.fromhex("0000"))  # 0 bpm detached sensor
        await client.emit(bytes.fromhex("00"))    # Truncated: flags only
        await driver.stop()

        assert len(emitted) == 2
        with pytest.raises(FhirNormalisationError, match="rejected value 0"):
            normaliser.normalise(emitted[0], NormalisationContext("Patient/hr-001"))

        with pytest.raises(FhirNormalisationError, match="requires at least 1"):
            normaliser.normalise(emitted[1], NormalisationContext("Patient/hr-001"))

    asyncio.run(run())

