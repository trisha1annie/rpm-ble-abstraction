import asyncio
import time
import pytest

from fault_handling.stream_handler import StreamHandler


@pytest.mark.asyncio
async def test_dropout_stream():
    handler = StreamHandler()

    calibration_intervals = 10

    dropout_count = 0
    recovery_count = 0
    notification_count = 0

    # Called whenever a simulated notification arrives
    def on_notification():
        nonlocal notification_count, recovery_count

        timestamp = time.monotonic()

        was_dropout = handler.dropout_active
        intervals_before = len(handler.intervals)

        interval = handler.check_notification(timestamp)
        notification_count += 1

        # Detect recovery when notifications resume
        if was_dropout:
            print("\n*** NOTIFICATION STREAM RESUMED ***\n")
            recovery_count += 1

            # Recovery gap should not enter timing statistics
            assert interval is None
            assert len(handler.intervals) == intervals_before
            assert handler.dropout_active is False
            return

        if interval is not None:
            print(
                f"Notification received | "
                f"Interval: {interval * 1000:.2f} ms"
            )

            # Establish baseline after calibration
            if handler.baseline is None:
                baseline = handler.establish_baseline(
                    sample_size=calibration_intervals
                )

                if baseline is not None:
                    print(
                        f"\nBaseline established: "
                        f"Median = {baseline[0] * 1000:.2f} ms\n"
                    )

            else:
                # Use the handler's current baseline
                median_interval, mad = handler.baseline
                timeout = 3 * median_interval

                if interval > timeout:
                    print("Long notification gap detected")

                elif handler.detect_anomaly(
                    interval, handler.baseline
                ):
                    print("Timing anomaly detected")

    # Runs independently of incoming notifications
    async def monitor_dropout():
        nonlocal dropout_count

        while True:
            await asyncio.sleep(0.1)

            if handler.baseline is None:
                continue

            median_interval, mad = handler.baseline
            timeout = 3 * median_interval

            event = handler.monitor_dropout(
                time.monotonic(),
                timeout
            )

            if event == "dropout_detected":
                print("\n*** POSSIBLE DROPOUT DETECTED ***\n")
                dropout_count += 1

    # Simulates the oximeter sending notifications
    async def simulate_notifications():
        nonlocal notification_count

        print("\n=== PHASE 1: Normal streaming (5 seconds) ===\n")

        for _ in range(25):
            on_notification()
            await asyncio.sleep(0.2)

        # Verify baseline established
        assert handler.baseline is not None
        assert dropout_count == 0
        assert handler.dropout_active is False

        print("\n=== PHASE 2: Dropout (3 seconds) ===\n")

        # No notifications during this period
        await asyncio.sleep(3)

        # Verify dropout detected during silence
        assert dropout_count == 1
        assert handler.dropout_active is True

        print("\n=== PHASE 3: Recovery (5 seconds) ===\n")

        for _ in range(25):
            on_notification()
            await asyncio.sleep(0.2)

        # Verify recovery
        assert recovery_count == 1
        assert handler.dropout_active is False
        assert dropout_count == 1
        assert notification_count == 50

        print("\n=== TEST COMPLETED ===")

    monitor_task = asyncio.create_task(monitor_dropout())

    try:
        await simulate_notifications()

    finally:
        monitor_task.cancel()

        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
