import os
from typing import List, Dict, Any, Optional
import pandas as pd
from backend.app.schemas.data_schemas import DatasetSummary, ColumnProfile, DatasetPreviewResponse

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

def list_datasets() -> List[DatasetSummary]:
    datasets = []
    if not os.path.exists(DATA_DIR):
        return datasets

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            path = os.path.join(DATA_DIR, file)
            size_kb = round(os.path.getsize(path) / 1024, 2)
            try:
                df = pd.read_csv(path, nrows=100)
                # Count total rows safely
                with open(path, "r", encoding="utf-8") as f:
                    row_count = sum(1 for _ in f) - 1
                
                is_baseline = "baseline" in file.lower()
                datasets.append(DatasetSummary(
                    name=file,
                    path=path,
                    rows=max(row_count, 0),
                    columns=len(df.columns),
                    size_kb=size_kb,
                    is_baseline=is_baseline
                ))
            except Exception:
                pass
    return datasets


def get_dataset_preview(dataset_name: str) -> Optional[DatasetPreviewResponse]:
    path = os.path.join(DATA_DIR, dataset_name)
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)
    columns_profile: List[ColumnProfile] = []

    for col in df.columns:
        series = df[col]
        null_pct = round(float(series.isnull().mean() * 100), 2)
        unique_cnt = int(series.nunique())
        sample_vals = series.dropna().head(4).tolist()

        columns_profile.append(ColumnProfile(
            name=col,
            dtype=str(series.dtype),
            null_pct=null_pct,
            unique_count=unique_cnt,
            sample_values=sample_vals
        ))

    preview_rows = df.head(15).to_dict(orient="records")

    return DatasetPreviewResponse(
        name=dataset_name,
        total_rows=len(df),
        total_columns=len(df.columns),
        columns=columns_profile,
        preview_rows=preview_rows
    )
