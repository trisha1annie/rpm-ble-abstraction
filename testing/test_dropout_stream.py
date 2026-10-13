import asyncio
import time
import pytest

from fault_handling.stream_handler import StreamHandler


@pytest.mark.asyncio
async def test_dropout_stream():
    handler = StreamHandler()

    baseline = None
    calibration_intervals = 10
    dropout_reported = False

    # Track events so pytest can verify them
    dropout_count = 0
    recovery_count = 0
    notification_count = 0

    # Called whenever a simulated notification arrives
    def on_notification():
        nonlocal baseline, notification_count

        timestamp = time.monotonic()
        interval = handler.check_notification(timestamp)
        notification_count += 1

        if interval is not None:
            print(
                f"Notification received | "
                f"Interval: {interval * 1000:.2f} ms"
            )

            if baseline is None:
                if len(handler.intervals) >= calibration_intervals:
                    baseline = handler.calculate_baseline()

                    print(
                        f"\nBaseline established: "
                        f"Median = {baseline[0] * 1000:.2f} ms\n"
                    )
            else:
                median_interval, mad = baseline
                timeout = 3 * median_interval

                if interval > timeout:
                    print("Long notification gap detected")
                elif handler.detect_anomaly(interval, baseline):
                    print("Timing anomaly detected")

    # Runs independently of incoming notifications
    async def monitor_dropout():
        nonlocal dropout_reported, dropout_count, recovery_count

        while True:
            await asyncio.sleep(0.1)

            if baseline is None:
                continue

            median_interval, mad = baseline
            timeout = 3 * median_interval

            dropout_detected = handler.check_dropout(
                time.monotonic(), timeout
            )

            if dropout_detected and not dropout_reported:
                print("\n*** POSSIBLE DROPOUT DETECTED ***\n")
                dropout_reported = True
                dropout_count += 1

            elif not dropout_detected and dropout_reported:
                print("\n*** NOTIFICATION STREAM RESUMED ***\n")
                dropout_reported = False
                recovery_count += 1

    # Simulates the oximeter sending notifications
    async def simulate_notifications():
        print("\n=== PHASE 1: Normal streaming (5 seconds) ===\n")

        for _ in range(25):
            on_notification()
            await asyncio.sleep(0.2)

        # Verify baseline was established
        assert baseline is not None
        assert dropout_count == 0

        print("\n=== PHASE 2: Dropout (3 seconds) ===\n")

        # No notifications during this period
        await asyncio.sleep(3)

        # Verify dropout was detected during silence
        assert dropout_count == 1
        assert dropout_reported is True

        print("\n=== PHASE 3: Recovery (5 seconds) ===\n")

        for _ in range(25):
            on_notification()
            await asyncio.sleep(0.2)

        # Verify recovery
        assert recovery_count == 1
        assert dropout_reported is False
        assert notification_count == 50

    monitor_task = asyncio.create_task(monitor_dropout())

    try:
        await simulate_notifications()
    finally:
        monitor_task.cancel()

        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

    print("\n=== TEST COMPLETED ===")
