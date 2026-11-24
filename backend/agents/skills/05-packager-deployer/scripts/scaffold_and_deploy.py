#!/usr/bin/env python3
"""
scripts/scaffold_and_deploy.py
Automated generator for production-ready FastAPI model serving microservices,
multi-stage non-root Dockerfiles, and Azure Container Apps deployment manifests.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any


DOCKERFILE_TEMPLATE = """# Multi-stage secure non-root Dockerfile for MLOps Serving
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN groupadd -g 10001 appgroup && useradd -u 10001 -g appgroup -s /bin/sh -m appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appgroup . .
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1
CMD ["uvicorn", "app_serve:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
"""

AZURE_CONTAINER_APP_BICEP_TEMPLATE = """// Azure Container App Deployment Manifest (Blue-Green Revision Support)
param location string = resourceGroup().location
param appName string = '{app_name}'
param containerImage string = '{container_image}'
param targetPort int = 8000

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {{
  name: appName
  location: location
  properties: {{
    configuration: {{
      ingress: {{
        external: true
        targetPort: targetPort
        traffic: [
          {{
            latestRevision: true
            weight: 100
          }}
        ]
      }}
    }}
    template: {{
      containers: [
        {{
          name: appName
          image: containerImage
          resources: {{
            cpu: json('1.0')
            memory: '2.0Gi'
          }}
          probes: [
            {{
              type: 'Liveness'
              httpGet: {{
                path: '/healthz'
                port: targetPort
              }}
            }}
            {{
              type: 'Readiness'
              httpGet: {{
                path: '/readyz'
                port: targetPort
              }}
            }}
          ]
        }}
      ]
      scale: {{
        minReplicas: 1
        maxReplicas: 10
      }}
    }}
  }}
}}
"""

FASTAPI_SERVE_TEMPLATE = '''"""
app_serve.py - Generated FastAPI Serving Microservice with Lifespan Loading
"""
import os
import joblib
import numpy as np
import pandas as pd
from contextlib import asynccontextmanager
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

model_store = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lifespan: Load model weights once during startup
    model_path = os.getenv("MODEL_PATH", "model.pkl")
    if os.path.exists(model_path):
        model_store["model"] = joblib.load(model_path)
        print(f"Successfully loaded model from {model_path}")
    else:
        print(f"Warning: Model path {model_path} not found.")
    yield
    model_store.clear()

app = FastAPI(title="{app_name}", version="1.0.0", lifespan=lifespan)

class PredictionRequest(BaseModel):
    data: List[Dict[str, Any]]

class PredictionResponse(BaseModel):
    predictions: List[Any]
    count: int

@app.get("/healthz")
async def healthz():
    return {{"status": "ok"}}

@app.get("/readyz")
async def readyz():
    if "model" not in model_store:
        raise HTTPException(status_code=503, detail="Model weights not loaded yet")
    return {{"status": "ready"}}

@app.post("/predict", response_model=PredictionResponse)
async def predict(payload: PredictionRequest):
    if "model" not in model_store:
        raise HTTPException(status_code=503, detail="Model is not ready")
    try:
        df = pd.DataFrame(payload.data)
        preds = model_store["model"].predict(df)
        return PredictionResponse(predictions=preds.tolist(), count=len(preds))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
'''


def scaffold_service(artifact_dir: str, output_dir: str, app_name: str) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)

    # 1. Write app_serve.py
    serve_code = FASTAPI_SERVE_TEMPLATE.format(app_name=app_name)
    serve_path = os.path.join(output_dir, "app_serve.py")
    with open(serve_path, "w", encoding="utf-8") as f:
        f.write(serve_code)

    # 2. Write Dockerfile
    docker_path = os.path.join(output_dir, "Dockerfile")
    with open(docker_path, "w", encoding="utf-8") as f:
        f.write(DOCKERFILE_TEMPLATE)

    # 3. Write requirements.txt
    req_path = os.path.join(output_dir, "requirements.txt")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("fastapi>=0.110.0\nuvicorn>=0.29.0\npydantic>=2.7.0\njoblib>=1.3.2\nscikit-learn>=1.4.0\npandas>=2.2.0\nnumpy>=1.26.0\n")

    # 4. Write Azure Bicep manifest
    bicep_path = os.path.join(output_dir, "azure_container_app.bicep")
    with open(bicep_path, "w", encoding="utf-8") as f:
        f.write(AZURE_CONTAINER_APP_BICEP_TEMPLATE.format(
            app_name=app_name,
            container_image=f"myregistry.azurecr.io/{app_name}:latest"
        ))

    return {
        "status": "SUCCESS",
        "app_serve_path": serve_path,
        "dockerfile_path": docker_path,
        "bicep_path": bicep_path
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic Service Scaffolder")
    parser.add_argument("--artifact-dir", type=str, required=True, help="Path to model artifacts")
    parser.add_argument("--output-dir", type=str, default="deploy_package", help="Output directory")
    parser.add_argument("--app-name", type=str, default="mlops-model-service", help="Name of service")
    args = parser.parse_args()

    result = scaffold_service(args.artifact_dir, args.output_dir, args.app_name)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
