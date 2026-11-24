import os
import time
from typing import Dict, Any
import numpy as np
import pandas as pd
from scipy import stats
from backend.app.agents.state import MLOpsState

def calculate_psi(baseline: np.ndarray, current: np.ndarray, num_bins: int = 10, epsilon: float = 1e-4) -> float:
    baseline = baseline[~np.isnan(baseline)]
    current = current[~np.isnan(current)]
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.unique(np.percentile(baseline, percentiles))
    if len(bin_edges) <= 1:
        return 0.0

    baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
    current_counts, _ = np.histogram(current, bins=bin_edges)

    baseline_fractions = (baseline_counts + epsilon) / (len(baseline) + epsilon * len(baseline_counts))
    current_fractions = (current_counts + epsilon) / (len(current) + epsilon * len(current_counts))

    psi_val = np.sum((current_fractions - baseline_fractions) * np.log(current_fractions / baseline_fractions))
    return float(np.round(psi_val, 5))


def run_data_sentinel(state: MLOpsState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append(f"[{time.strftime('%X')}] [Data Sentinel] Starting automated data ingestion & schema integrity check...")

    current_path = state.get("dataset_path")
    baseline_path = state.get("baseline_path")

    if not current_path or not os.path.exists(current_path):
        logs.append(f"[{time.strftime('%X')}] [Data Sentinel] Error: Dataset file not found at {current_path}")
        return {
            "status": "FAILED",
            "current_step": "data_sentinel_failed",
            "logs": logs
        }

    curr_df = pd.read_csv(current_path)

    # If no baseline provided, check data directory for default baseline
    if not baseline_path or not os.path.exists(baseline_path):
        default_base = os.path.join(os.path.dirname(current_path), "baseline_churn.csv")
        if os.path.exists(default_base):
            baseline_path = default_base
        else:
            baseline_path = current_path

    base_df = pd.read_csv(baseline_path)
    logs.append(f"[{time.strftime('%X')}] [Data Sentinel] Comparing current dataset ({len(curr_df)} rows) against baseline ({len(base_df)} rows)...")

    # Run KS-test and PSI on numeric columns
    features_report = {}
    drifted_count = 0
    numeric_cols = [c for c in curr_df.select_dtypes(include=[np.number]).columns if c in base_df.columns]

    for col in numeric_cols:
        b_vals = base_df[col].dropna().to_numpy()
        c_vals = curr_df[col].dropna().to_numpy()
        if len(b_vals) > 5 and len(c_vals) > 5:
            ks_stat, p_val = stats.ks_2samp(b_vals, c_vals)
            psi = calculate_psi(b_vals, c_vals)
            is_drifted = bool((p_val < 0.05) or (psi >= 0.25))
            if is_drifted:
                drifted_count += 1
            status = "CRITICAL_DRIFT" if psi >= 0.25 else ("WARNING" if is_drifted else "HEALTHY")
            features_report[col] = {
                "ks_stat": round(float(ks_stat), 4),
                "p_value": round(float(p_val), 5),
                "psi": round(float(psi), 4),
                "status": status,
                "is_drifted": bool(is_drifted),
                "baseline_mean": round(float(np.mean(b_vals)), 2),
                "current_mean": round(float(np.mean(c_vals)), 2)
            }

    overall_status = "CRITICAL_DRIFT" if drifted_count >= 2 else ("MODERATE_DRIFT" if drifted_count > 0 else "HEALTHY")
    logs.append(f"[{time.strftime('%X')}] [Data Sentinel] Analysis complete. {drifted_count} features showed drift. Status: {overall_status}.")

    report = {
        "summary": {
            "overall_status": overall_status,
            "drifted_features_count": drifted_count,
            "total_features": len(curr_df.columns),
            "rows_inspected": len(curr_df)
        },
        "features": features_report
    }

    return {
        "data_quality_report": report,
        "current_step": "data_sentinel_complete",
        "logs": logs
    }
