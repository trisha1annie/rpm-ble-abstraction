from statistics import median

class StreamHandler: 
    def __init__(self): 
        self.previous_timestamp = None
        self.intervals = []
        self.baseline = None
        self.rate_change_window = []
        self.dropout_active = False
        self.jitter_intervals = []
    
    """Check for previous notification and calculate time interval between the two"""
    def check_notification(self, timestamp: float):
        if self.previous_timestamp is None:
            self.previous_timestamp = timestamp
            return None
        
        interval = timestamp - self.previous_timestamp
        self.previous_timestamp = timestamp

        if self.dropout_active:
            self.dropout_active = False
            self.rate_change_window.clear()
            self.jitter_intervals.clear()
            return None
        
        self.intervals.append(interval)
        self.jitter_intervals.append(interval)

        if len(self.jitter_intervals) > 10:
            self.jitter_intervals.pop(0)
        return interval
    
    """Calculates a baseline rates for device: depend on the time intervals"""
    def calculate_baseline(self):
        if not self.intervals:
            return None
        
        """Median to determine typical interval between notifications"""
        median_interval = median(self.intervals)

        """Calculate the typical deviation"""
        deviations = [
            abs(interval - median_interval)
            for interval in self.intervals
        ]

        mad = median(deviations)
        return median_interval, mad

    
    """Caliculate a z score and compare against outlier detection threshold of 3.5"""
   
    def detect_anomaly(
        self,
        interval: float,
        baseline: tuple,
    ) -> bool:
        median_interval, mad = baseline

        if median_interval <= 0:
            return False

        # Minimum tolerance: 5 ms
        # Relative tolerance: 10% of expected interval
        tolerance = max(0.005, 0.10 * median_interval)

        if mad == 0:
            return abs(interval - median_interval) > tolerance

        modified_z_score = (
            0.6745 * (interval - median_interval) / mad
        )

        return abs(modified_z_score) > 3.5

    
    """Check if interval is greater than timeout"""
    def check_dropout(self, current_time, timeout):
        if self.previous_timestamp is None:
            return False
        
        return (current_time - self.previous_timestamp > timeout)
    
    """Accounts for accumulated absolute differences between observations"""
    def calculate_jitter(self, intervals: list[float]) -> float:
        if len(intervals) < 2:
            return 0.0
        
        differences = [
            abs(intervals[i] - intervals[i-1])
            for i in range(1, len(intervals))
        ]

        return sum(differences)/len(differences)

    
    """"""
    def calculate_jitter_window(self, size: int = 10):
        if size < 2:
            raise ValueError("Window size must atleast be 2")
        
        if len(self.jitter_intervals) < size: 
            return None
        
        return self.calculate_jitter(
            self.jitter_intervals[-size:]
        )

    def detect_jitter(self, curr_jitter:float, threshold: float) -> bool:
        return curr_jitter > threshold


    def calculate_rate(self, intervals: list[float]) -> float | None:
        if not intervals:
            return None

        median_interval = median(intervals)

        if median_interval <= 0:
            return None

        return 1 / median_interval

    def establish_baseline(self, sample_size: int = 10):
        if self.baseline is not None:
            return self.baseline

        if len(self.intervals) < sample_size:
            return None

        self.baseline = self.calculate_baseline()
        return self.baseline


    def detect_rate_change(
    self,
    interval: float,
    window_size: int = 5,
    threshold: float = 0.25
    ):
        if self.baseline is None:
            return False

        baseline_interval, _ = self.baseline

        if baseline_interval <= 0 or interval <= 0:
            return False

        relative_change = abs(
            interval - baseline_interval
        ) / baseline_interval

        if relative_change > threshold:
            self.rate_change_window.append(interval)
        else:
            self.rate_change_window.clear()
            return False

        if len(self.rate_change_window) < window_size:
            return False

        recent_intervals = self.rate_change_window[-window_size:]
        recent_median = median(recent_intervals)
        tolerance = 0.15

        stable = all(
            abs(value - recent_median) / recent_median <= tolerance
            for value in recent_intervals
        )

        if not stable:
            self.rate_change_window = recent_intervals
            return False

        # Adopt new rate
        deviations = [
            abs(value - recent_median)
            for value in recent_intervals
        ]

        self.baseline = (
            recent_median,
            median(deviations)
        )

        self.rate_change_window.clear()
        self.jitter_intervals.clear()
        return True
    
    def monitor_dropout(self, current_time, timeout):
        detected = self.check_dropout(current_time, timeout)
        
        if detected and not self.dropout_active:
            self.dropout_active = True
            return "dropout_detected"
        
        if not detected and self.dropout_active:
            self.dropout_active = False
            return "recovered"
        return None