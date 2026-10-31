
import pytest

from fault_handling.stream_handler import StreamHandler


def test_jitter_with_no_intervals():
    handler = StreamHandler()

    assert handler.calculate_jitter([]) == 0.0


def test_jitter_with_one_interval():
    handler = StreamHandler()

    assert handler.calculate_jitter([0.2]) == 0.0


def test_zero_jitter():
    handler = StreamHandler()

    intervals = [0.2, 0.2, 0.2, 0.2]

    assert handler.calculate_jitter(intervals) == pytest.approx(0.0)


def test_jitter_calculation():
    handler = StreamHandler()

    intervals = [0.20, 0.25, 0.18, 0.22]

    # Differences: 50 ms, 70 ms, 40 ms
    # Mean = 53.33 ms
    jitter = handler.calculate_jitter(intervals)

    assert jitter == pytest.approx(0.0533333333)


def test_jitter_below_threshold():
    handler = StreamHandler()

    jitter = 0.02  # 20 ms
    threshold = 0.03  # 30 ms

    assert handler.detect_jitter(jitter, threshold) is False


def test_jitter_above_threshold():
    handler = StreamHandler()

    jitter = 0.05  # 50 ms
    threshold = 0.03  # 30 ms

    assert handler.detect_jitter(jitter, threshold) is True


def test_jitter_equal_to_threshold():
    handler = StreamHandler()

    assert handler.detect_jitter(0.03, 0.03) is False


def test_jitter_window_insufficient_intervals():
    handler = StreamHandler()

    handler.jitter_intervals = [0.2] * 5

    assert handler.calculate_jitter_window(size=10) is None


def test_jitter_window_calculation():
    handler = StreamHandler()

    handler.jitter_intervals = [
        0.20, 0.22, 0.19, 0.21, 0.20,
        0.23, 0.18, 0.22, 0.19, 0.20,
    ]

    expected = handler.calculate_jitter(
        handler.jitter_intervals
    )

    assert handler.calculate_jitter_window(size=10) == pytest.approx(
        expected
    )


def test_invalid_jitter_window_size():
    handler = StreamHandler()

    with pytest.raises(ValueError):
        handler.calculate_jitter_window(size=1)


def test_rolling_jitter_window_keeps_last_ten_intervals():
    handler = StreamHandler()

    # 12 intervals, all at 200 ms.
    timestamp = 0.0
    handler.check_notification(timestamp)

    for _ in range(12):
        timestamp += 0.2
        handler.check_notification(timestamp)

    assert len(handler.intervals) == 12
    assert len(handler.jitter_intervals) == 10
    assert handler.jitter_intervals == pytest.approx([0.2] * 10)


def test_jitter_window_reset_after_dropout():
    handler = StreamHandler()

    timestamp = 0.0
    handler.check_notification(timestamp)

    # Establish normal 200 ms intervals.
    for _ in range(10):
        timestamp += 0.2
        handler.check_notification(timestamp)

    handler.establish_baseline(sample_size=10)

    assert len(handler.jitter_intervals) == 10

    # Detect a dropout after the timeout.
    timeout = 3 * handler.baseline[0]
    event = handler.monitor_dropout(timestamp + 1.0, timeout)

    assert event == "dropout_detected"

    # First notification after dropout.
    interval = handler.check_notification(timestamp + 1.2)

    assert interval is None
    assert handler.jitter_intervals == []
    assert handler.dropout_active is False

    # First normal interval after recovery.
    handler.check_notification(timestamp + 1.4)

    assert len(handler.jitter_intervals) == 1
    assert handler.calculate_jitter_window(size=10) is None


def test_jitter_window_reset_after_rate_change():
    handler = StreamHandler()

    timestamp = 0.0
    handler.check_notification(timestamp)

    # Establish 1 Hz baseline.
    for _ in range(10):
        timestamp += 1.0
        handler.check_notification(timestamp)

    handler.establish_baseline(sample_size=10)

    assert len(handler.jitter_intervals) == 10

    # Transition to 5 Hz (200 ms intervals).
    changed = False

    for _ in range(5):
        timestamp += 0.2
        interval = handler.check_notification(timestamp)
        changed = handler.detect_rate_change(interval)

    assert changed is True
    assert handler.baseline[0] == pytest.approx(0.2)
    assert handler.jitter_intervals == []

    # A new window must be collected after the rate change.
    assert handler.calculate_jitter_window(size=10) is None
