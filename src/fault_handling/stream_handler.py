from statistics import median

class StreamHandler: 
    def __init__(self): 
        self.previous_timestamp = None
        self.intervals = []
    
    """Check for previous notification and calculate time interval between the two"""
    def check_notification(self, timestamp: float):
        if self.previous_timestamp is None:
            self.previous_timestamp = timestamp
            return None
        
        interval = timestamp - self.previous_timestamp
        self.previous_timestamp = timestamp
        self.intervals.append(interval)
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
    def detect_anomaly(self, interval: float, baseline: tuple) -> bool: 
        median, mad = baseline

        """need to determine experiementally """
        if mad == 0: 
            return abs(interval - median) > 1e-9
        
        """need to determine experiementally """
        modified_z_score = (
            0.6745 * (interval - median)/mad
        )
        return abs(modified_z_score) > 3.5

    def check_dropout(self, current_time, timeout):
        if self.previous_timestamp is None:
            return False
        
        return (current_time - self.previous_timestamp > timeout)