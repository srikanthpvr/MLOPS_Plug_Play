#!/usr/bin/env python3
"""
scripts/check_drift_and_schema.py
Stand-alone, deterministic data validation and statistical drift calculation script.
Computes:
- Kolmogorov-Smirnov (KS-test) for continuous numerical features.
- Population Stability Index (PSI) with Laplace smoothing (epsilon=1e-4) for categorical / binned continuous.
- Missing value percentage and schema integrity assertions.
"""

import sys
import json
import argparse
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats


def calculate_psi(baseline: np.ndarray, current: np.ndarray, num_bins: int = 10, epsilon: float = 1e-4) -> float:
    """
    Calculate Population Stability Index (PSI) between baseline and current data distributions.
    Uses Laplace smoothing to prevent division by zero or log(0).
    """
    baseline = baseline[~np.isnan(baseline)]
    current = current[~np.isnan(current)]
    
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    # Quantile binning on baseline distribution
    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(baseline, percentiles)
    bin_edges = np.unique(bin_edges)  # Prevent duplicate edge values

    if len(bin_edges) <= 1:
        return 0.0

    # Bin counts
    baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
    current_counts, _ = np.histogram(current, bins=bin_edges)

    # Fractions with Laplace smoothing
    baseline_fractions = (baseline_counts + epsilon) / (len(baseline) + epsilon * len(baseline_counts))
    current_fractions = (current_counts + epsilon) / (len(current) + epsilon * len(current_counts))

    # PSI calculation: sum((current - baseline) * ln(current / baseline))
    psi_value = np.sum((current_fractions - baseline_fractions) * np.log(current_fractions / baseline_fractions))
    return float(np.round(psi_value, 5))


def analyze_dataset_drift(baseline_df: pd.DataFrame, current_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs schema comparison and statistical drift checks across all shared columns.
    """
    report: Dict[str, Any] = {
        "summary": {
            "baseline_rows": len(baseline_df),
            "current_rows": len(current_df),
            "total_features": len(baseline_df.columns),
            "drifted_features_count": 0,
            "overall_status": "HEALTHY",
        },
        "features": {},
        "missing_values": {},
        "schema_diff": {
            "missing_in_current": list(set(baseline_df.columns) - set(current_df.columns)),
            "new_in_current": list(set(current_df.columns) - set(baseline_df.columns)),
        }
    }

    shared_cols = [c for c in baseline_df.columns if c in current_df.columns]

    for col in shared_cols:
        base_series = baseline_df[col]
        curr_series = current_df[col]

        # Missing values check
        base_null_pct = float(base_series.isnull().mean() * 100)
        curr_null_pct = float(curr_series.isnull().mean() * 100)
        report["missing_values"][col] = {
            "baseline_null_pct": round(base_null_pct, 2),
            "current_null_pct": round(curr_null_pct, 2),
            "null_spike": round(curr_null_pct - base_null_pct, 2)
        }

        # Numerical feature drift analysis
        if pd.api.types.is_numeric_dtype(base_series) and pd.api.types.is_numeric_dtype(curr_series):
            base_clean = base_series.dropna().to_numpy()
            curr_clean = curr_series.dropna().to_numpy()

            if len(base_clean) > 5 and len(curr_clean) > 5:
                # 2-sample Kolmogorov-Smirnov test
                ks_stat, p_val = stats.ks_2samp(base_clean, curr_clean)
                psi_val = calculate_psi(base_clean, curr_clean)

                is_drifted = (p_val < 0.05) or (psi_val >= 0.25)
                status = "CRITICAL_DRIFT" if psi_val >= 0.25 else ("WARNING" if is_drifted else "HEALTHY")

                if is_drifted:
                    report["summary"]["drifted_features_count"] += 1

                report["features"][col] = {
                    "type": "numeric",
                    "ks_statistic": round(float(ks_stat), 4),
                    "p_value": round(float(p_val), 5),
                    "psi": round(float(psi_val), 4),
                    "status": status,
                    "drift_detected": bool(is_drifted),
                    "baseline_mean": round(float(np.mean(base_clean)), 3),
                    "current_mean": round(float(np.mean(curr_clean)), 3),
                }

    # Overall health gate
    drift_ratio = report["summary"]["drifted_features_count"] / max(len(shared_cols), 1)
    if len(report["schema_diff"]["missing_in_current"]) > 0:
        report["summary"]["overall_status"] = "SCHEMA_ERROR"
    elif drift_ratio >= 0.3:
        report["summary"]["overall_status"] = "ACTION_REQUIRED"
    elif drift_ratio > 0.0:
        report["summary"]["overall_status"] = "MODERATE_SHIFT"
    else:
        report["summary"]["overall_status"] = "HEALTHY"

    return report


def main():
    parser = argparse.ArgumentParser(description="Deterministic Data Drift and Schema Checker")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline reference CSV")
    parser.add_argument("--current", type=str, required=True, help="Path to current inference/retrain CSV")
    parser.add_argument("--output", type=str, default="drift_report.json", help="Path to save output JSON report")
    args = parser.parse_args()

    try:
        baseline_df = pd.read_csv(args.baseline)
        current_df = pd.read_csv(args.current)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load dataset: {str(e)}", "overall_status": "LOAD_ERROR"}))
        sys.exit(1)

    result = analyze_dataset_drift(baseline_df, current_df)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
