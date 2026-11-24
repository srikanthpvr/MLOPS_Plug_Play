from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DatasetSummary(BaseModel):
    name: str
    path: str
    rows: int
    columns: int
    size_kb: float
    is_baseline: bool

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_pct: float
    unique_count: int
    sample_values: List[Any]

class DatasetPreviewResponse(BaseModel):
    name: str
    total_rows: int
    total_columns: int
    columns: List[ColumnProfile]
    preview_rows: List[Dict[str, Any]]

class DriftAnalysisRequest(BaseModel):
    baseline_dataset: str
    current_dataset: str
