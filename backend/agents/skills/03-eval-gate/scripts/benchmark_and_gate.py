#!/usr/bin/env python3
"""
scripts/benchmark_and_gate.py
Automated Champion vs. Challenger model evaluation and latency benchmarking script.
Executes warmup runs, benchmarks p50, p95, and p99 inference latencies, compares
validation metrics against the production champion baseline, and outputs a gating decision.
"""

import os
import sys
import time
import json
import joblib
import argparse
from typing import Dict, Any, List
import numpy as np


def benchmark_latency(model, sample_input: np.ndarray, num_runs: int = 500, warmup_runs: int = 50) -> Dict[str, float]:
    """
    Measures inference latency percentiles with explicit warmup.
    """
    # Warmup runs to stabilize JIT/cache
    for _ in range(warmup_runs):
        _ = model.predict(sample_input)

    latencies_ms: List[float] = []
    for _ in range(num_runs):
        start = time.perf_counter()
        _ = model.predict(sample_input)
        latencies_ms.append((time.perf_counter() - start) * 1000.0)

    return {
        "p50_ms": round(float(np.percentile(latencies_ms, 50)), 3),
        "p95_ms": round(float(np.percentile(latencies_ms, 95)), 3),
        "p99_ms": round(float(np.percentile(latencies_ms, 99)), 3),
        "mean_ms": round(float(np.mean(latencies_ms)), 3),
        "min_ms": round(float(np.min(latencies_ms)), 3),
        "max_ms": round(float(np.max(latencies_ms)), 3),
    }


def evaluate_gate(
    candidate_metrics: Dict[str, Any],
    champion_metrics: Dict[str, Any],
    latency_stats: Dict[str, float],
    sla_p95_ms: float = 50.0
) -> Dict[str, Any]:
    """
    Evaluates whether the candidate model should replace the production champion.
    """
    cand_f1 = float(candidate_metrics.get("f1_score", 0.0))
    champ_f1 = float(champion_metrics.get("f1_score", 0.70))  # Default baseline if new model
    p95_latency = latency_stats["p95_ms"]

    f1_delta = round(cand_f1 - champ_f1, 4)
    latency_pass = p95_latency <= sla_p95_ms
    accuracy_pass = f1_delta >= -0.005  # within 0.5% tolerance

    rejection_reasons = []
    if not accuracy_pass:
        rejection_reasons.append(f"Challenger F1 ({cand_f1}) regressed below Champion F1 ({champ_f1}) by {abs(f1_delta):.4f}")
    if not latency_pass:
        rejection_reasons.append(f"p95 Latency ({p95_latency}ms) exceeds SLA budget ({sla_p95_ms}ms)")

    decision = "PROMOTED" if (accuracy_pass and latency_pass) else "REJECTED"

    return {
        "decision": decision,
        "is_promoted": decision == "PROMOTED",
        "comparison": {
            "challenger_f1": cand_f1,
            "champion_f1": champ_f1,
            "f1_delta": f1_delta,
            "accuracy_pass": accuracy_pass,
            "latency_p95_ms": p95_latency,
            "sla_p95_budget_ms": sla_p95_ms,
            "latency_pass": latency_pass,
        },
        "latency_benchmarks": latency_stats,
        "rejection_reasons": rejection_reasons,
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic Eval Gate and Benchmarking")
    parser.add_argument("--candidate-dir", type=str, required=True, help="Path to candidate artifact directory")
    parser.add_argument("--champion-dir", type=str, default="", help="Path to champion artifact directory")
    parser.add_argument("--sla-p95-ms", type=float, default=50.0, help="Maximum allowed p95 latency in ms")
    parser.add_argument("--output", type=str, default="gate_result.json", help="Output JSON path")
    args = parser.parse_args()

    # Load candidate metrics
    cand_metrics_path = os.path.join(args.candidate_dir, "metrics.json")
    cand_model_path = os.path.join(args.candidate_dir, "model.pkl")

    if not os.path.exists(cand_metrics_path) or not os.path.exists(cand_model_path):
        print(json.dumps({"error": "Candidate artifacts missing", "decision": "REJECTED"}))
        sys.exit(1)

    with open(cand_metrics_path, "r", encoding="utf-8") as f:
        cand_metrics = json.load(f)

    # Load champion metrics if exists
    champ_metrics = {"f1_score": 0.75, "accuracy": 0.78}
    if args.champion_dir:
        champ_metrics_path = os.path.join(args.champion_dir, "metrics.json")
        if os.path.exists(champ_metrics_path):
            with open(champ_metrics_path, "r", encoding="utf-8") as f:
                champ_metrics = json.load(f)

    # Load candidate model & benchmark latency
    model = joblib.load(cand_model_path)
    num_features = len(cand_metrics.get("feature_names", [0] * 10))
    synthetic_batch = np.random.randn(1, num_features)

    latency_stats = benchmark_latency(model, synthetic_batch, num_runs=300, warmup_runs=30)
    result = evaluate_gate(cand_metrics, champ_metrics, latency_stats, args.sla_p95_ms)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
