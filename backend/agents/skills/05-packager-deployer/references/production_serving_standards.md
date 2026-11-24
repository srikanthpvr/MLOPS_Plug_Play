# Packager & Deployer Reference: Production Serving & Azure Container Apps

## 1. Concurrency and Worker Architecture
* **Uvicorn Multi-Worker Topology**: Standard production containers run `--workers 2` or `--workers 4` per pod/replica.
* **CPU/Memory Allocation**: Recommended baseline on Azure Container Apps: `cpu: 1.0`, `memory: 2.0Gi` for tree models; `cpu: 2.0`, `memory: 4.0Gi` for deep learning embeddings.

---

## 2. Health Probes & Blue-Green Traffic Splitting
* **Liveness Probe**: Monitored on `/healthz` with a 30s period. If Uvicorn hangs, Azure restarts the container replica.
* **Readiness Probe**: Monitored on `/readyz` with an initial 10s delay. Traffic is never routed to a replica until model weights are resident in RAM.
* **Zero-Downtime Blue-Green Deployment**: Azure Container Apps automatically provisions the new candidate revision, verifies readiness probes pass 100%, and only then switches traffic weights from revision `v1` to `v2`.
