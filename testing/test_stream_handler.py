import pytest

from fault_handling.stream_handler import StreamHandler


# TEST 1: First notification
def test_first_notification():
    handler = StreamHandler()

    result = handler.check_notification(1.0)

    assert result is None


# TEST 2: Calculate interval between notifications
def test_notification_interval():
    handler = StreamHandler()

    handler.check_notification(1.0)
    result = handler.check_notification(2.0)

    assert result == pytest.approx(1.0)


# TEST 3: Multiple notification intervals
def test_multiple_intervals():
    handler = StreamHandler()

    handler.check_notification(1.0)
    handler.check_notification(2.0)
    handler.check_notification(3.5)
    handler.check_notification(4.0)

    assert handler.intervals == pytest.approx(
        [1.0, 1.5, 0.5]
    )


# TEST 4: Calculate baseline with constant intervals
def test_baseline_constant_intervals():
    handler = StreamHandler()

    handler.intervals = [1.0] * 10

    median, mad = handler.calculate_baseline()

    assert median == pytest.approx(1.0)
    assert mad == pytest.approx(0.0)


# TEST 5: Calculate baseline with varying intervals
def test_baseline_varying_intervals():
    handler = StreamHandler()

    handler.intervals = [
        0.8, 0.9, 0.9, 1.0, 1.0,
        1.0, 1.1, 1.1, 1.2, 1.2
    ]

    median, mad = handler.calculate_baseline()

    assert median == pytest.approx(1.0)
    assert mad == pytest.approx(0.1)


# TEST 6: Normal notification interval
def test_normal_interval():
    handler = StreamHandler()

    baseline = (1.0, 0.05)
    interval = 1.0

    result = handler.detect_anomaly(interval, baseline)

    assert result is False


# TEST 7: Small variation in notification interval
def test_small_interval_variation():
    handler = StreamHandler()

    baseline = (1.0, 0.05)
    interval = 1.02

    result = handler.detect_anomaly(interval, baseline)

    assert result is False


# TEST 8: Large delay between notifications
def test_large_interval_anomaly():
    handler = StreamHandler()

    baseline = (1.0, 0.05)
    interval = 2.0

    result = handler.detect_anomaly(interval, baseline)

    assert result is True


# TEST 9: Notification arrives much earlier than expected
def test_early_notification_anomaly():
    handler = StreamHandler()

    baseline = (1.0, 0.05)
    interval = 0.2

    result = handler.detect_anomaly(interval, baseline)

    assert result is True


# TEST 10: Baseline with an outlier
def test_baseline_with_outlier():
    handler = StreamHandler()

    handler.intervals = [
        1.0, 1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0, 5.0
    ]

    median, mad = handler.calculate_baseline()

    assert median == pytest.approx(1.0)
    assert mad == pytest.approx(0.0)


# TEST 11: No anomaly with consistent faster data rate
def test_faster_data_rate():
    handler = StreamHandler()

    baseline = (0.2, 0.01)
    interval = 0.2

    result = handler.detect_anomaly(interval, baseline)

    assert result is False


# TEST 12: Detect a change from 1 Hz to 5 Hz
def test_data_rate_change():
    handler = StreamHandler()

    baseline = (1.0, 0.05)
    interval = 0.2

    result = handler.detect_anomaly(interval, baseline)

    assert result is True


# TEST 13: Detect anomaly when MAD is zero
# All calibration intervals are identical
def test_anomaly_zero_mad():
    handler = StreamHandler()

    baseline = (1.0, 0.0)

    assert handler.detect_anomaly(1.0, baseline) is False
    assert handler.detect_anomaly(2.0, baseline) is True


# TEST 14: No dropout during normal streaming
def test_no_dropout():
    handler = StreamHandler()

    handler.check_notification(1.0)

    assert handler.check_dropout(1.2, 0.6) is False


# TEST 15: Dropout after prolonged silence
def test_dropout_detected():
    handler = StreamHandler()

    handler.check_notification(1.0)

    assert handler.check_dropout(2.0, 0.6) is True


# TEST 16: Dropout clears when notifications resume
def test_dropout_recovery():
    handler = StreamHandler()

    handler.check_notification(1.0)

    assert handler.check_dropout(2.0, 0.6) is True

    handler.check_notification(2.1)

    assert handler.check_dropout(2.2, 0.6) is False


# TEST 17: No dropout before the first notification
def test_dropout_no_notifications():
    handler = StreamHandler()

    assert handler.check_dropout(1.0, 0.6) is False

def test_window_jitter():
    handler = StreamHandler()

    handler.jitter_intervals = [0.2, 0.21, 0.19, 0.2]

    result = handler.calculate_jitter_window(size=4)

    # Differences: 0.01, 0.02, 0.01
    # Mean = 0.04 / 3
    assert result == pytest.approx(0.04 / 3)


def test_window_jitter_uses_recent_intervals():
    handler = StreamHandler()

    handler.jitter_intervals = [0.5, 0.2, 0.21, 0.19, 0.2]

    result = handler.calculate_jitter_window(size=4)

    # Uses only the last four intervals:
    # [0.2, 0.21, 0.19, 0.2]
    # Mean = 0.04 / 3
    assert result == pytest.approx(0.04 / 3)


def test_window_jitter_insufficient_data():
    handler = StreamHandler()

    handler.intervals = [0.2, 0.21]

    assert handler.calculate_jitter_window(size=4) is None
