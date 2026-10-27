import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/real_oximeter_baseline.csv")

# Remove rows without valid notification intervals
df = df.dropna(subset=["interval_ms"])

# 1. Histogram of notification intervals
plt.figure(figsize=(10, 5))
plt.hist(df["interval_ms"], bins=50)
plt.xlabel("Notification interval (ms)")
plt.ylabel("Frequency")
plt.title("Real Oximeter: Notification Interval Distribution")
plt.savefig("results/interval_histogram.png")
plt.show()

# 2. Notification intervals over time
plt.figure(figsize=(10, 5))
plt.plot(
    df["timestamp"] - df["timestamp"].iloc[0],
    df["interval_ms"]
)
plt.xlabel("Time (seconds)")
plt.ylabel("Notification interval (ms)")
plt.title("Real Oximeter: Notification Intervals Over Time")
plt.savefig("results/interval_timeline.png")
plt.show()

# 3. Modified Z-score distribution
plt.figure(figsize=(10, 5))
plt.hist(df["modified_z_score"].dropna(), bins=50)
plt.axvline(3.5, linestyle="--", label="Threshold +3.5")
plt.axvline(-3.5, linestyle="--", label="Threshold -3.5")
plt.xlabel("Modified Z-score")
plt.ylabel("Frequency")
plt.title("Real Oximeter: Modified Z-score Distribution")
plt.legend()
plt.savefig("results/zscore_histogram.png")
plt.show()

# 4. Jitter over time
plt.figure(figsize=(10, 5))
plt.plot(
    df["timestamp"] - df["timestamp"].iloc[0],
    df["jitter_ms"]
)
plt.axhline(30, linestyle="--", label="Current threshold: 30 ms")
plt.xlabel("Time (seconds)")
plt.ylabel("Jitter (ms)")
plt.title("Real Oximeter: Rolling Jitter")
plt.legend()
plt.savefig("results/jitter_timeline.png")
plt.show()