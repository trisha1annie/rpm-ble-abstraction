import asyncio
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient
import sys

JITTER_MS = int(sys.argv[1]) if len(sys.argv) > 1 else 0

OUTPUT_FILE = Path(f"results/simulated_jitter_{JITTER_MS}ms.csv")

# Your simulated oximeter
DEVICE_ADDRESS = "4E110FF7-EE22-0B81-BB0D-79350113666B"

CHARACTERISTIC_UUID = "cdeacd81-5235-4c07-8846-93a37ee6b86d"

DURATION_SECONDS = 120
EXPECTED_INTERVAL_MS = 200


async def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamps = []
    records = []

    def notification_handler(sender, data):
        timestamp = time.perf_counter()

        interval_ms = None

        if timestamps:
            interval_ms = (timestamp - timestamps[-1]) * 1000

        timestamps.append(timestamp)

        records.append({
            "notification_number": len(timestamps),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "interval_ms": interval_ms,
            "payload_hex": bytes(data).hex(),
        })

        print(
            f"Notification {len(timestamps)} | "
            f"Interval: {interval_ms:.2f} ms"
            if interval_ms is not None
            else "First notification received"
        )

    print("Connecting to simulated oximeter...")

    async with BleakClient(DEVICE_ADDRESS) as client:
        print("Connected!")

        await client.start_notify(
            CHARACTERISTIC_UUID,
            notification_handler
        )

        print(f"Collecting notifications for {DURATION_SECONDS} seconds...")

        await asyncio.sleep(DURATION_SECONDS)

        await client.stop_notify(CHARACTERISTIC_UUID)

    with open(OUTPUT_FILE, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "notification_number",
                "timestamp_utc",
                "interval_ms",
                "payload_hex",
            ],
        )

        writer.writeheader()
        writer.writerows(records)

    intervals = [
        record["interval_ms"]
        for record in records
        if record["interval_ms"] is not None
    ]

    print("\n===== BASELINE SUMMARY =====")
    print(f"Notifications received: {len(records)}")
    print(f"Intervals recorded: {len(intervals)}")

    if intervals:
        import statistics

        median = statistics.median(intervals)
        mad = statistics.median(
            [abs(interval - median) for interval in intervals]
        )

        mean = statistics.mean(intervals)

        print(f"Mean interval: {mean:.2f} ms")
        print(f"Median interval: {median:.2f} ms")
        print(f"MAD: {mad:.2f} ms")
        print(f"Minimum interval: {min(intervals):.2f} ms")
        print(f"Maximum interval: {max(intervals):.2f} ms")

        print(
            f"Observed frequency: {1000 / mean:.2f} Hz"
        )

    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())