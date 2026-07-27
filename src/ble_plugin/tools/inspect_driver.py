"""
CLI tool to test StandardPluginDriver against a connected BLE device or simulator.

Usage:
    python -m ble_plugin.tools.inspect_driver --device-id <MAC_ADDRESS>
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from ble_plugin.bleak_client import BleakBleClient
from ble_plugin.standard_plugin_driver import StandardPluginDriver


def _on_measurement(measurement) -> None:
    print(f"\n[MEASUREMENT RECEIVED] {measurement.received_at.isoformat()}")
    print(f"  Device:         {measurement.device_id}")
    print(f"  Service:        {measurement.service_uuid}")
    print(f"  Characteristic: {measurement.characteristic_uuid}")
    print(f"  Values:         {measurement.payload.values}")
    print(f"  Flags:          {measurement.payload.status_flags}")


async def _run(args: argparse.Namespace) -> int:
    if args.scan_timeout > 0:
        from ble_plugin.bleak_client import BleakScannerAdapter
        print(f"Scanning for {args.scan_timeout}s to resolve device path...")
        scanner = BleakScannerAdapter()
        await scanner.scan(timeout_seconds=args.scan_timeout)

    client = BleakBleClient(args.device_id)
    driver = StandardPluginDriver(client)

    print(f"Connecting to {args.device_id} via StandardPluginDriver ...")
    try:
        try:
            await driver.start(_on_measurement)
        except Exception as exc:
            if "InProgress" in str(exc):
                print("BlueZ scan in progress. Retrying connection in 2s...")
                await asyncio.sleep(2.0)
                await driver.start(_on_measurement)
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

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        sys.exit(asyncio.run(_run(args)))
    except KeyboardInterrupt:
        print("\nStopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
