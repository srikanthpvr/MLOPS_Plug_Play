import {
  DatasetSummary,
  DatasetPreviewResponse,
  ModelCatalogItem,
  ChampionModelMetadata,
  AgentRunStatusResponse,
  ObservabilityMetricsResponse
} from "../types";

const BASE_URL = "/api";

export async function fetchDatasets(): Promise<DatasetSummary[]> {
  const res = await fetch(`${BASE_URL}/data/datasets`);
  if (!res.ok) throw new Error("Failed to fetch datasets");
  return res.json();
}

export async function fetchDatasetPreview(datasetName: string): Promise<DatasetPreviewResponse> {
  const res = await fetch(`${BASE_URL}/data/preview/${datasetName}`);
  if (!res.ok) throw new Error("Failed to fetch dataset preview");
  return res.json();
}

export async function fetchModelCatalog(): Promise<ModelCatalogItem[]> {
  const res = await fetch(`${BASE_URL}/models/catalog`);
  if (!res.ok) throw new Error("Failed to fetch model catalog");
  return res.json();
}

export async function fetchChampionModel(): Promise<ChampionModelMetadata> {
  const res = await fetch(`${BASE_URL}/models/champion`);
  if (!res.ok) throw new Error("Failed to fetch champion model");
  return res.json();
}

export async function triggerAgentRun(payload: {
  dataset_name: string;
  target_column?: string;
  model_type: string;
  hyperparameters: Record<string, any>;
  sla_p95_ms: number;
}): Promise<{ run_id: string; status: string; message: string }> {
  const res = await fetch(`${BASE_URL}/agents/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Failed to start agent run");
  return res.json();
}

export async function fetchAgentRunStatus(runId: string): Promise<AgentRunStatusResponse> {
  const res = await fetch(`${BASE_URL}/agents/runs/${runId}`);
  if (!res.ok) throw new Error("Failed to fetch agent status");
  return res.json();
}

export async function approveDeployment(runId: string, approved: boolean, notes?: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/agents/approve/${runId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved, notes })
  });
  if (!res.ok) throw new Error("Failed to submit approval");
  return res.json();
}

export async function fetchObservabilityDashboard(): Promise<ObservabilityMetricsResponse> {
  const res = await fetch(`${BASE_URL}/observability/dashboard`);
  if (!res.ok) throw new Error("Failed to fetch observability metrics");
  return res.json();
}
