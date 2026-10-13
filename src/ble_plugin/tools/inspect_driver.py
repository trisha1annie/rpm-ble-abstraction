"""
CLI tool to test StandardPluginDriver against a connected BLE device or simulator.

Usage:
    python -m ble_plugin.tools.inspect_driver --device-id <MAC_ADDRESS>
    python -m ble_plugin.tools.inspect_driver --device-id <MAC_ADDRESS> \\
        --fhir --patient-reference Patient/example
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from ble_plugin.bleak_client import BleakBleClient
from ble_plugin.standard_plugin_driver import StandardPluginDriver

_MAPPING_DIRECTORY = Path(__file__).resolve().parents[2] / "fhir_mapping"


def _print_decoded(measurement) -> None:
    print(f"\n[MEASUREMENT RECEIVED] {measurement.received_at.isoformat()}")
    print(f"  Device:         {measurement.device_id}")
    print(f"  Service:        {measurement.service_uuid}")
    print(f"  Characteristic: {measurement.characteristic_uuid}")
    print(f"  Values:         {measurement.payload.values}")
    print(f"  Flags:          {measurement.payload.status_flags}")


def _on_measurement(measurement) -> None:
    _print_decoded(measurement)


def _make_fhir_callback(patient_reference: str, device_reference: str | None):
    from fhir_mapping import (
        FhirMappingRegistry,
        FhirNormalisationError,
        FhirNormaliser,
        NormalisationContext,
        UnsupportedFhirMappingError,
    )

    normaliser = FhirNormaliser(
        FhirMappingRegistry.from_directory(_MAPPING_DIRECTORY)
    )
    context = NormalisationContext(
        patient_reference=patient_reference,
        device_reference=device_reference,
    )

    def _on_measurement(measurement) -> None:
        _print_decoded(measurement)
        try:
            observations = normaliser.normalise(measurement, context)
        except UnsupportedFhirMappingError as exc:
            print(f"  FHIR:           skipped ({exc})")
            return
        except FhirNormalisationError as exc:
            print(f"  FHIR:           rejected ({exc})")
            return

        print("  FHIR Observations:")
        print(json.dumps(observations, indent=2))

    return _on_measurement


async def _run(args: argparse.Namespace) -> int:
    if args.scan_timeout > 0:
        from ble_plugin.bleak_client import BleakScannerAdapter
        print(f"Scanning for {args.scan_timeout}s to resolve device path...")
        scanner = BleakScannerAdapter()
        await scanner.scan(timeout_seconds=args.scan_timeout)

    client = BleakBleClient(args.device_id)
    driver = StandardPluginDriver(client)
    on_measurement = (
        _make_fhir_callback(args.patient_reference, args.device_reference)
        if args.fhir
        else _on_measurement
    )

    print(f"Connecting to {args.device_id} via StandardPluginDriver ...")
    if args.fhir:
        print(f"FHIR patient: {args.patient_reference}")
        if args.device_reference:
            print(f"FHIR device:  {args.device_reference}")
    try:
        try:
            await driver.start(on_measurement)
        except Exception as exc:
            if "InProgress" in str(exc):
                print("BlueZ scan in progress. Retrying connection in 2s...")
                await asyncio.sleep(2.0)
                await driver.start(on_measurement)
            else:
                raise
        print("Connected.")
        print(f"Subscribed routes: {sorted(driver.subscribed_characteristics)}")
        print("Listening for measurements... Press Ctrl+C to stop.\n")
        await asyncio.Event().wait()
    finally:
        print("Stopping driver...")
        await driver.stop()
        print("Driver stopped.")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m ble_plugin.tools.inspect_driver",
        description="Run StandardPluginDriver against a BLE device or simulator.",
    )
    parser.add_argument(
        "--device-id",
        type=str,
        required=True,
        metavar="ID",
        help="Backend MAC address of the device to connect to",
    )
    parser.add_argument(
        "--scan-timeout",
        type=float,
        default=3.0,
        metavar="SECONDS",
        help="Pre-connection scan timeout in seconds to cache device path (default: 3.0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--fhir",
        action="store_true",
        help="Also print FHIR R5 Observation JSON for supported measurements",
    )
    parser.add_argument(
        "--patient-reference",
        type=str,
        metavar="REF",
        help="FHIR patient reference, e.g. Patient/example (required with --fhir)",
    )
    parser.add_argument(
        "--device-reference",
        type=str,
        metavar="REF",
        help="Optional FHIR device reference, e.g. Device/bp-monitor",
    )

    args = parser.parse_args()
    if args.fhir and not args.patient_reference:
        parser.error("--patient-reference is required when --fhir is set")
    if args.patient_reference and not args.fhir:
        parser.error("--patient-reference requires --fhir")
    if args.device_reference and not args.fhir:
        parser.error("--device-reference requires --fhir")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        sys.exit(asyncio.run(_run(args)))
    except KeyboardInterrupt:
        print("\nStopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
