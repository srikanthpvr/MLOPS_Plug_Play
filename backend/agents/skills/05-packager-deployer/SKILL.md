---
name: packager-deployer
description: >-
  Cloud Packaging, Serving Scaffolding, and Azure Deployment Skill.
  Generates production-ready FastAPI inference microservices with Lifespan handlers,
  health probes (/healthz, /readyz), multi-stage non-root Dockerfiles, and Azure
  Container Apps (ACA) / Kubernetes Blue-Green deployment manifests.
version: 1.0.0
tools:
  - scaffold_and_deploy
---

# Packager & Deployer Agent Skill

## 1. Purpose & Scope
The **Packager & Deployer Agent** transforms validated model artifacts into a fully containerized, production-hardened microservice ready for deployment to **Azure Container Apps** or **Azure Kubernetes Service (AKS)**.

---

## 2. Invariants & Serving Standards
1. **Lifespan Model Loading**: Model weights MUST be loaded into memory once during the application startup lifespan (`@asynccontextmanager`), never per HTTP request.
2. **Explicit Health Probes**:
   * `/healthz` (Liveness): Returns `200 OK` as long as the Uvicorn event loop is responsive.
   * `/readyz` (Readiness): Returns `200 OK` only when model weights are fully deserialized in memory and ready to serve predictions.
3. **Pydantic Request Schemas**: All inference payloads must be strictly typed and validated at the boundary.
4. **Blue-Green Revisions**: Azure Container Apps deployment manifests must use revision-based traffic splitting (e.g. 100% switch on success, with instant rollback).

---

## 3. Execution Playbook
1. Load model schema signature (`signature.json`) and serialized model artifact (`model.pkl`).
2. Run `python scripts/scaffold_and_deploy.py --artifact-dir artifacts/candidate --output-dir deploy/ --app-name ml-serving-service`.
3. Verify that the generated serving package passes synthetic liveness and readiness tests before notifying the MLOps Supervisor.
