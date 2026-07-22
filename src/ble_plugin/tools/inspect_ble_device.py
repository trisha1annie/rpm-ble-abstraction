"""
BLE device inspector - diagnostic command-line tool.

Usage:
    python -m ble_plugin.tools.inspect_ble_device [options]

Options:
    --scan-timeout SECONDS      Duration of BLE scan (default: 8.0)
    --device-id ID              Connect to this device and print its GATT tree
    --characteristic UUID       Subscribe to this characteristic (requires --device-id)
    --listen-seconds SECONDS    How long to collect notifications (default: 20.0)

Examples:
    # Scan only
    python -m ble_plugin.tools.inspect_ble_device --scan-timeout 10

    # Scan then connect and print GATT topology
    python -m ble_plugin.tools.inspect_ble_device --device-id AA:BB:CC:DD:EE:FF

    # Subscribe and print raw hex notifications
    python -m ble_plugin.tools.inspect_ble_device \
        --device-id AA:BB:CC:DD:EE:FF \
        --characteristic 00002a9d-0000-1000-8000-00805f9b34fb \
        --listen-seconds 30
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone

from ble_plugin.bleak_client import BleakBleClient, BleakScannerAdapter
from ble_plugin.schema import normalize_uuid


def _print_scan_results(devices) -> None:
    if not devices:
        print("No devices found.")
        return
    for i, dev in enumerate(devices, start=1):
        service_list = ", ".join(sorted(dev.advertised_service_uuids)) or "(none)"
        rssi_str = f"RSSI: {dev.rssi}" if dev.rssi is not None else "RSSI: n/a"
        name = dev.name or "(anonymous)"
        print(f"[{i}] {name} | {dev.device_id} | {rssi_str} | Services: [{service_list}]")


def _print_gatt(gatt) -> None:
    print(f"\nGATT topology for {gatt.device_id}:")
    for svc in gatt.services:
        print(f"  Service  {svc.uuid}")
        for char in svc.characteristics:
            props = ", ".join(sorted(char.properties))
            print(f"    Char   {char.uuid}  [{props}]")


async def _run(args: argparse.Namespace) -> int:
    scanner = BleakScannerAdapter()

    print(f"Scanning for {args.scan_timeout}s ...")
    devices = await scanner.scan(timeout_seconds=args.scan_timeout)
    _print_scan_results(devices)

    if args.device_id is None:
        return 0

    client = BleakBleClient(args.device_id)
    try:
        print(f"\nConnecting to {args.device_id} ...")
        await client.connect()
        print("Connected.")

        gatt = await client.discover_gatt()
        _print_gatt(gatt)

        if args.characteristic is None:
            return 0

        normalised_char = normalize_uuid(args.characteristic)
        print(
            f"\nListening on {normalised_char} for {args.listen_seconds}s ..."
            "\n(raw hex, no decoding)"
        )

        def _on_notification(uuid: str, data: bytes) -> None:
            ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            print(f"{ts} | {uuid} | {data.hex()}")

        await client.subscribe(normalised_char, _on_notification)
        await asyncio.sleep(args.listen_seconds)
        await client.unsubscribe(normalised_char)

    finally:
        await client.disconnect()
        print("\nDisconnected.")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m ble_plugin.tools.inspect_ble_device",
        description="Scan for BLE devices and optionally inspect or listen to one.",
    )
    parser.add_argument(
        "--scan-timeout",
        type=float,
        default=8.0,
        metavar="SECONDS",
        help="Duration of BLE scan in seconds (default: 8.0)",
    )
    parser.add_argument(
        "--device-id",
        type=str,
        default=None,
        metavar="ID",
        help="Backend address of device to connect to and inspect GATT topology",
    )
    parser.add_argument(
        "--characteristic",
        type=str,
        default=None,
        metavar="UUID",
        help="Characteristic UUID to subscribe to (requires --device-id)",
    )
    parser.add_argument(
        "--listen-seconds",
        type=float,
        default=20.0,
        metavar="SECONDS",
        help="Duration to listen for notifications in seconds (default: 20.0)",
    )

    args = parser.parse_args()

    if args.characteristic and not args.device_id:
        parser.error("--characteristic requires --device-id")

    try:
        sys.exit(asyncio.run(_run(args)))
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
