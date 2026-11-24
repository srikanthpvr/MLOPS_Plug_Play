from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class HyperparameterSpec(BaseModel):
    name: str
    type: str # "float", "int", "choice"
    default: Any
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    choices: Optional[List[Any]] = None
    description: str

class ModelCatalogItem(BaseModel):
    id: str
    name: str
    family: str # "Tabular GBDT", "Ensemble", "Linear", "Neural"
    description: str
    supported_tasks: List[str]
    default_hyperparameters: Dict[str, Any]
    specs: List[HyperparameterSpec]

class ChampionModelMetadata(BaseModel):
    model_id: str
    name: str
    version: str
    accuracy: float
    f1_score: float
    precision: float
    recall: float
    p95_latency_ms: float
    deployment_target: str
    last_trained: str
