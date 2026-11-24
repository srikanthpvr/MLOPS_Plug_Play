export interface DatasetSummary {
  name: string;
  path: string;
  rows: number;
  columns: number;
  size_kb: number;
  is_baseline: boolean;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  null_pct: number;
  unique_count: number;
  sample_values: any[];
}

export interface DatasetPreviewResponse {
  name: string;
  total_rows: number;
  total_columns: number;
  columns: ColumnProfile[];
  preview_rows: Record<string, any>[];
}

export interface HyperparameterSpec {
  name: string;
  type: string;
  default: any;
  min_val?: number;
  max_val?: number;
  choices?: any[];
  description: string;
}

export interface ModelCatalogItem {
  id: string;
  name: string;
  family: string;
  description: string;
  supported_tasks: string[];
  default_hyperparameters: Record<string, any>;
  specs: HyperparameterSpec[];
}

export interface ChampionModelMetadata {
  model_id: string;
  name: string;
  version: string;
  accuracy: number;
  f1_score: number;
  precision: number;
  recall: number;
  p95_latency_ms: number;
  deployment_target: string;
  last_trained: string;
}

export interface AgentRunStatusResponse {
  run_id: string;
  status: string;
  current_step: string;
  awaiting_hitl_approval: boolean;
  logs: string[];
  data_quality_report?: Record<string, any>;
  training_metrics?: Record<string, any>;
  eval_gate_result?: Record<string, any>;
  security_audit_report?: Record<string, any>;
  deploy_result?: Record<string, any>;
}

export interface MetricPoint {
  timestamp: string;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  requests_per_sec: number;
  error_rate_pct: number;
}

export interface FeatureDriftSummary {
  feature_name: string;
  ks_p_value: number;
  psi: number;
  status: "HEALTHY" | "WARNING" | "CRITICAL_DRIFT";
  baseline_mean: number;
  current_mean: number;
}

export interface ObservabilityMetricsResponse {
  model_name: string;
  active_version: string;
  overall_health: string;
  champion_f1: number;
  current_p95_latency_ms: number;
  total_inferences_24h: number;
  drifted_features_count: number;
  timeseries_metrics: MetricPoint[];
  feature_drifts: FeatureDriftSummary[];
}
