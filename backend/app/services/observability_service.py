import time
import random
from typing import List, Dict, Any
from backend.app.schemas.observability_schemas import (
    ObservabilityMetricsResponse, MetricPoint, FeatureDriftSummary
)

def get_observability_dashboard() -> ObservabilityMetricsResponse:
    # Generate realistic 24-hour time series metrics
    timeseries: List[MetricPoint] = []
    current_time = time.time()

    for i in range(12, 0, -1):
        ts_str = time.strftime("%H:%M", time.localtime(current_time - (i * 1800)))
        p50 = round(random.uniform(1.2, 2.1), 2)
        p95 = round(p50 + random.uniform(1.5, 3.2), 2)
        p99 = round(p95 + random.uniform(2.0, 4.5), 2)
        rps = round(random.uniform(45.0, 110.0), 1)
        err = round(random.uniform(0.01, 0.08), 3)

        timeseries.append(MetricPoint(
            timestamp=ts_str,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            requests_per_sec=rps,
            error_rate_pct=err
        ))

    # Feature drifts
    feature_drifts = [
        FeatureDriftSummary(
            feature_name="monthly_charges",
            ks_p_value=0.00012,
            psi=0.312,
            status="CRITICAL_DRIFT",
            baseline_mean=65.2,
            current_mean=88.4
        ),
        FeatureDriftSummary(
            feature_name="internet_service",
            ks_p_value=0.0034,
            psi=0.284,
            status="CRITICAL_DRIFT",
            baseline_mean=0.8,
            current_mean=1.2
        ),
        FeatureDriftSummary(
            feature_name="tenure_months",
            ks_p_value=0.082,
            psi=0.065,
            status="HEALTHY",
            baseline_mean=23.8,
            current_mean=22.4
        ),
        FeatureDriftSummary(
            feature_name="contract_type",
            ks_p_value=0.041,
            psi=0.142,
            status="WARNING",
            baseline_mean=0.7,
            current_mean=0.5
        ),
        FeatureDriftSummary(
            feature_name="age",
            ks_p_value=0.155,
            psi=0.048,
            status="HEALTHY",
            baseline_mean=38.2,
            current_mean=39.1
        )
    ]

    drifted_count = sum(1 for f in feature_drifts if f.status in ("WARNING", "CRITICAL_DRIFT"))

    return ObservabilityMetricsResponse(
        model_name="Customer-Churn-Classifier",
        active_version="v2.1.0-prod",
        overall_health="ACTION_REQUIRED" if drifted_count >= 2 else "HEALTHY",
        champion_f1=0.862,
        current_p95_latency_ms=4.12,
        total_inferences_24h=142850,
        drifted_features_count=drifted_count,
        timeseries_metrics=timeseries,
        feature_drifts=feature_drifts
    )
