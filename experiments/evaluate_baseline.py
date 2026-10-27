import pandas as pd
from statistics import median

df = pd.read_csv("results/real_oximeter_baseline.csv")

intervals = df["interval_ms"].dropna().tolist()

for sample_size in [10, 20, 30, 50]:
    sample = intervals[:sample_size]

    baseline_median = median(sample)

    deviations = [
        abs(interval - baseline_median)
        for interval in sample
    ]

    baseline_mad = median(deviations)

    print(f"\nSample size: {sample_size}")
    print(f"Median: {baseline_median:.2f} ms")
    print(f"MAD: {baseline_mad:.2f} ms")
    