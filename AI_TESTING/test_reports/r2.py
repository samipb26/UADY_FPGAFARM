import csv
import numpy as np
import os

def calculate_r2_from_csv(csv_filepath):
    """
    Reads the benchmark CSV and calculates the R-squared value 
    for the Inference Latency trendline over time.
    """
    if not os.path.exists(csv_filepath):
        print(f"Error: File '{csv_filepath}' not found.")
        return

    latencies = []
    
    # Read the CSV and extract the Latency column
    with open(csv_filepath, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                latencies.append(float(row['Latency (ms)']))
            except (ValueError, KeyError) as e:
                print(f"Skipping row due to error: {e}")

    if len(latencies) < 2:
        print("Not enough data points to calculate a trendline.")
        return

    # Set up our X and Y arrays
    y = np.array(latencies)
    x = np.arange(1, len(y) + 1) # [1, 2, 3, ..., N]

    # 1. Calculate the Linear Regression Trendline (Degree 1)
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    
    # 2. Calculate R-Squared mathematically
    y_mean = np.mean(y)
    ssr = np.sum((y - y_pred)**2) # Sum of Squared Residuals (Model Error)
    sst = np.sum((y - y_mean)**2) # Total Sum of Squares (Baseline Variance)
    
    r2 = 1 - (ssr / sst) if sst != 0 else 0

    # Output the results
    print("-" * 40)
    print(f"Data Points Analyzed : {len(y)}")
    print(f"Average Latency      : {y_mean:.2f} ms")
    print(f"Trendline Slope      : {slope:.3f} ms / test")
    print("-" * 40)
    print(f"R-Squared (R^2)      : {r2:.4f}")
    print("-" * 40)

if __name__ == "__main__":
    # Point this to your CSV file
    csv_file = "benchmark_results_qwen25.csv" 
    calculate_r2_from_csv(csv_file)