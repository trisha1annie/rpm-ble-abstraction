import pytest

from fault_handling.stream_handler import StreamHandler


def establish_1hz_baseline(handler):
    """Simulate 11 notifications, producing 10 intervals at 1 Hz."""
    for i in range(11):
        handler.check_notification(float(i))

    handler.establish_baseline(sample_size=10)


def send_intervals(handler, start_time, interval, count):
    """Simulate notifications arriving at a fixed interval."""
    timestamp = start_time
    changes = []

    for _ in range(count):
        timestamp += interval

        observed_interval = handler.check_notification(timestamp)
        changed = handler.detect_rate_change(observed_interval)

        changes.append(changed)

    return timestamp, changes


def test_initial_baseline():
    handler = StreamHandler()

    establish_1hz_baseline(handler)

    assert handler.baseline is not None
    assert handler.baseline[0] == pytest.approx(1.0)
    assert handler.baseline[1] == pytest.approx(0.0)

    assert handler.calculate_rate(
        handler.intervals
    ) == pytest.approx(1.0)


def test_rate_change_1hz_to_5hz():
    handler = StreamHandler()
    establish_1hz_baseline(handler)

    _, changes = send_intervals(
        handler,
        start_time=10.0,
        interval=0.2,
        count=5
    )

    assert changes == [False, False, False, False, True]

    assert handler.baseline[0] == pytest.approx(0.2)

    assert handler.calculate_rate(
        [handler.baseline[0]]
    ) == pytest.approx(5.0)


def test_rate_change_5hz_to_2hz():
    handler = StreamHandler()
    establish_1hz_baseline(handler)

    timestamp, _ = send_intervals(
        handler,
        start_time=10.0,
        interval=0.2,
        count=5
    )

    assert handler.baseline[0] == pytest.approx(0.2)

    _, changes = send_intervals(
        handler,
        start_time=timestamp,
        interval=0.5,
        count=5
    )

    assert changes == [False, False, False, False, True]

    assert handler.baseline[0] == pytest.approx(0.5)

    assert handler.calculate_rate(
        [handler.baseline[0]]
    ) == pytest.approx(2.0)


def test_single_anomaly_does_not_change_baseline():
    handler = StreamHandler()
    establish_1hz_baseline(handler)

    interval = handler.check_notification(12.0)

    changed = handler.detect_rate_change(interval)

    assert changed is False
    assert handler.baseline[0] == pytest.approx(1.0)


def test_dropout_timeout_adapts_to_rate():
    handler = StreamHandler()
    establish_1hz_baseline(handler)

    # At 1 Hz, the expected interval is 1 second.
    timeout_1hz = 3 * handler.baseline[0]

    assert timeout_1hz == pytest.approx(3.0)

    # Simulate a rate change to 5 Hz.
    timestamp, _ = send_intervals(
        handler,
        start_time=10.0,
        interval=0.2,
        count=5
    )

    timeout_5hz = 3 * handler.baseline[0]

    assert timeout_5hz == pytest.approx(0.6)

    # No dropout before the timeout.
    assert handler.check_dropout(
        timestamp + 0.5,
        timeout_5hz
    ) is False

    # Dropout after the timeout.
    assert handler.check_dropout(
        timestamp + 0.7,
        timeout_5hz
    ) is True