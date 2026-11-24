from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MetricPoint(BaseModel):
    timestamp: str
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_sec: float
    error_rate_pct: float

class FeatureDriftSummary(BaseModel):
    feature_name: str
    ks_p_value: float
    psi: float
    status: str # "HEALTHY", "WARNING", "CRITICAL_DRIFT"
    baseline_mean: float
    current_mean: float

class ObservabilityMetricsResponse(BaseModel):
    model_name: str
    active_version: str
    overall_health: str
    champion_f1: float
    current_p95_latency_ms: float
    total_inferences_24h: int
    drifted_features_count: int
    timeseries_metrics: List[MetricPoint]
    feature_drifts: List[FeatureDriftSummary]
