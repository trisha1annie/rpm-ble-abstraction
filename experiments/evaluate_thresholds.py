import pandas as pd

df = pd.read_csv("results/real_oximeter_baseline.csv")

# Evaluate modified Z-score thresholds
print("MODIFIED Z-SCORE THRESHOLDS")

z_scores = df["modified_z_score"].dropna()

for threshold in [2.5, 3.0, 3.5, 4.0, 5.0]:
    anomalies = (z_scores.abs() > threshold).sum()
    percentage = anomalies / len(z_scores) * 100

    print(
        f"Threshold {threshold}: "
        f"{anomalies}/{len(z_scores)} flagged "
        f"({percentage:.2f}%)"
    )


# Evaluate jitter thresholds
print("\nJITTER THRESHOLDS")

jitter_values = df["jitter_ms"].dropna()

for threshold in [30, 50, 75, 100]:
    flagged = (jitter_values > threshold).sum()
    percentage = flagged / len(jitter_values) * 100

    print(
        f"Threshold {threshold} ms: "
        f"{flagged}/{len(jitter_values)} flagged "
        f"({percentage:.2f}%)"
    )