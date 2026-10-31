
import pytest

from fault_handling.stream_handler import StreamHandler


def test_baseline_calculation():
    handler = StreamHandler()

    # Intervals in seconds:
    # 200, 210, 190, 200, 220 ms
    handler.intervals = [0.20, 0.21, 0.19, 0.20, 0.22]

    baseline = handler.calculate_baseline()

    # Median = 200 ms
    # Absolute deviations = 0, 10, 10, 0, 20 ms
    # MAD = 10 ms
    assert baseline[0] == pytest.approx(0.20)
    assert baseline[1] == pytest.approx(0.01)


def test_baseline_with_identical_intervals():
    handler = StreamHandler()
    handler.intervals = [0.2] * 10

    baseline = handler.calculate_baseline()

    assert baseline == (0.2, 0.0)


def test_baseline_with_no_intervals():
    handler = StreamHandler()

    assert handler.calculate_baseline() is None


def test_normal_interval_not_anomaly():
    handler = StreamHandler()

    baseline = (0.20, 0.01)

    # 205 ms is close to the 200 ms baseline.
    assert handler.detect_anomaly(0.205, baseline) is False


def test_large_interval_is_anomaly():
    handler = StreamHandler()

    baseline = (0.20, 0.01)

    # 300 ms is far from the baseline.
    assert handler.detect_anomaly(0.30, baseline) is True


def test_short_interval_is_anomaly():
    handler = StreamHandler()

    baseline = (0.20, 0.01)

    # 100 ms is also far from the baseline.
    assert handler.detect_anomaly(0.10, baseline) is True


def test_modified_z_score_boundary():
    handler = StreamHandler()

    baseline = (0.20, 0.01)

    # Modified Z-score is approximately 3.5.
    boundary = 0.20 + (3.5 * 0.01 / 0.6745)

    assert handler.detect_anomaly(boundary - 0.001, baseline) is False
    assert handler.detect_anomaly(boundary + 0.001, baseline) is True


def test_zero_mad_small_variation_not_anomaly():
    handler = StreamHandler()

    baseline = (0.20, 0.0)

    # 205 ms: only 5 ms above baseline.
    assert handler.detect_anomaly(0.205, baseline) is False


def test_zero_mad_within_relative_tolerance():
    handler = StreamHandler()

    baseline = (0.20, 0.0)

    # 215 ms is within 10% of the 200 ms baseline.
    assert handler.detect_anomaly(0.215, baseline) is False


def test_zero_mad_large_variation_is_anomaly():
    handler = StreamHandler()

    baseline = (0.20, 0.0)

    # 250 ms exceeds the 20 ms tolerance.
    assert handler.detect_anomaly(0.25, baseline) is True


def test_zero_mad_minimum_absolute_tolerance():
    handler = StreamHandler()

    baseline = (0.02, 0.0)

    # 10% of 20 ms is 2 ms, so the 5 ms floor applies.
    assert handler.detect_anomaly(0.024, baseline) is False
    assert handler.detect_anomaly(0.03, baseline) is True


def test_invalid_baseline_interval():
    handler = StreamHandler()

    assert handler.detect_anomaly(0.2, (0.0, 0.0)) is False
