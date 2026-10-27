import pandas as pd

files = {
    "0ms": "results/real_oximeter_baseline_delayed_0ms.csv",
    "30ms": "results/real_oximeter_baseline_delayed_30ms.csv",
    "60ms": "results/real_oximeter_baseline_delayed_60ms.csv",
}

THRESHOLD = 30  # milliseconds

for condition, filename in files.items():
    df = pd.read_csv(filename)

    # Identify windows exceeding the threshold
    df["warning"] = df["jitter_ms"] > THRESHOLD

    # Require three consecutive warnings
    df["confirmed"] = (
        df["warning"]
        & df["warning"].shift(1, fill_value=False)
        & df["warning"].shift(2, fill_value=False)
    )

    # Count the start of each single-window warning episode
    df["single_event"] = (
        df["warning"]
        & ~df["warning"].shift(1, fill_value=False)
    )

    # Count the start of each three-window confirmed episode
    df["confirmed_event"] = (
        df["confirmed"]
        & ~df["confirmed"].shift(1, fill_value=False)
    )

    # Count warnings
    single_warnings = df["warning"].sum()
    confirmed_warnings = df["confirmed"].sum()

    # Estimate when jitter injection begins relative to CSV recording
    FAULT_ONSET_SECONDS = 10

    # Convert timestamps to elapsed time
    df["elapsed_s"] = df["timestamp"] - df["timestamp"].iloc[0]

    # Only consider detections after estimated fault onset
    post_fault = df[df["elapsed_s"] >= FAULT_ONSET_SECONDS]

    # First single-window detection
    single_detections = post_fault[post_fault["single_event"]]

    # First three-window confirmed detection
    confirmed_detections = post_fault[post_fault["confirmed_event"]]

    if not single_detections.empty:
        single_latency = (
            single_detections["elapsed_s"].iloc[0]
            - FAULT_ONSET_SECONDS
        )
        print(f"First single-window detection: {single_latency:.3f} s")
    else:
        print("No single-window detection after fault onset")

    if not confirmed_detections.empty:
        confirmed_latency = (
            confirmed_detections["elapsed_s"].iloc[0]
            - FAULT_ONSET_SECONDS
        )
        print(f"First three-window detection: {confirmed_latency:.3f} s")
    else:
        print("No three-window detection after fault onset")
    
    # Approximate fault onset in receiver CSV
    FAULT_ONSET_SECONDS = 10

    # Ignore first 2 seconds to reduce baseline-window carryover
    pre_fault = df[
        (df["elapsed_s"] >= 2)
        & (df["elapsed_s"] < FAULT_ONSET_SECONDS)
    ]

    # Allow 2 seconds for rolling windows to transition
    post_fault = df[
        df["elapsed_s"] >= FAULT_ONSET_SECONDS + 2
    ]

    print("\n--- Steady-state comparison ---")

    for period_name, period in [
        ("Pre-injection", pre_fault),
        ("Post-injection", post_fault),
    ]:
        print(f"\n{period_name}")
        print(f"Total windows: {len(period)}")

        for column in ["warning", "confirmed"]:
            count = int(period[column].sum())
            rate = 100 * count / len(period) if len(period) else 0

            print(f"{column}: {count} ({rate:.1f}%)")

    print(f"\nCondition: {condition}")
    print(f"Total intervals: {len(df)}")
    print(f"Single-window warnings: {single_warnings}")
    print(f"Three-window confirmed warnings: {confirmed_warnings}")
    print(f"Single-window warning episodes: {df['single_event'].sum()}")
    print(f"Three-window confirmed episodes: {df['confirmed_event'].sum()}")