# 🚀 Autonomous MLOps Build Agent Suite

An autonomous, plug-and-play multi-agent MLOps platform engineered with **LangChain**, **LangSmith**, and **LangGraph**, designed for high-reliability deployment and monitoring on **Microsoft Azure**.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│  TIER 1: MLOps Engineer Interactive Console (React 19 + TypeScript)    │
│  [01 Data Hub]  [02 Model Lab]  [03 Agent Canvas]  [04 Observability]  │
│                                 [05 LangSmith Trace Hub]               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST & WebSocket (Real-Time Streams)
┌───────────────────────────────────▼────────────────────────────────────┐
│  TIER 2: Plug & Play Backend Gateway (FastAPI + Async Bus)            │
│  [06 FastAPI Asynchronous Gateway & Streaming Bus]                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Execute / Resume StateGraph
┌───────────────────────────────────▼────────────────────────────────────┐
│  TIER 3: Autonomous LangGraph Multi-Agent Build Suite                  │
│  [07 MLOps Supervisor & StateGraph Engine]                             │
│       │                                                                │
│       ▼                                                                │
│  [08 Data Sentinel] ──► [09 Training & HP] ──► [10 Eval Gate]          │
│                                                     │                  │
│                                                     ▼                  │
│  [12 Packager & Deployer] ◄────────────────── [11 AgentShield Sentinel]│
│  (State Persistence & HITL Approval Checkpointer)                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Managed Identity & Cloud Telemetry
┌───────────────────────────────────▼────────────────────────────────────┐
│  TIER 4: Microsoft Azure Cloud & Enterprise Observability Fabric       │
│  [13 Azure Blob / ADLS Gen2]      [14 Azure OpenAI Service]            │
│  [15 Azure Container Apps / ACR]  [16 Azure Key Vault & RBAC]          │
│  [17 LangSmith & App Insights]                                         │
└────────────────────────────────────────────────────────────────────────┘
```

The system architecture is available in three formats in this repository:
- **Interactive Browser Viewer**: `mlops_suite_hld_architecture.html`
- **Vector Preview**: `mlops_suite_hld_architecture.svg`
- **Draw.io Source XML**: `mlops_suite_hld_architecture.drawio`

---

## 🤖 Specialized Agent Skills Roster

Each agent in the suite is built as a complete, deterministic skill bundle containing master execution rules (`SKILL.md`), standalone Python scripts (`scripts/`), and in-depth references (`references/`):

1. **`01-data-sentinel`**: Two-sample Kolmogorov-Smirnov (KS) test and Laplace-smoothed Population Stability Index (PSI) drift detection with Pandera schema assertion.
2. **`02-training-tuning`**: Stratified cross-validation, hyperparameter bounds checking, and multi-format serialization (`.pkl`, `.onnx`) across LightGBM, XGBoost, Random Forest, and Logistic Regression.
3. **`03-eval-gate`**: Automated Champion vs Challenger gating with McNemar significance testing and batch inference latency SLA benchmarking ($p_{50}, p_{95}, p_{99}$).
4. **`04-security-sentinel`**: AgentShield credential governance (zero hardcoded secrets), Azure Managed Identity (`DefaultAzureCredential`) enforcement, and non-root Docker verification.
5. **`05-packager-deployer`**: Scaffolding of production-ready FastAPI microservices with Lifespan handlers, health probes (`/healthz`, `/readyz`), and Azure Container Apps Blue-Green deployment manifests.
6. **`06-mlops-supervisor`**: LangGraph StateGraph coordination, memory checkpointer persistence, Human-in-the-Loop (HITL) interrupt gates, and LangSmith tracing.

---

## 💻 Interactive Frontend Console

Built with **React 19 + TypeScript + Tailwind CSS**:
- **Data Hub**: Preview datasets, column schemas, null rates, and drift reference baselines.
- **Model Lab**: Interactive hyperparameter tuning sliders, SLA budget configuration, and one-click build dispatching.
- **Agent Canvas**: Live visual state transitions, WebSocket agent thought stream, and Human-in-the-Loop deployment approval modal.
- **Observability Desk**: Real-time $p_{95}$ latency distributions, feature drift heatmaps, and one-click model retrain triggers.

---

## ⚡ Quick Start

### One-Click Launch (Windows)
```cmd
run_mlops_platform.bat
```

### Manual Execution

#### 1. Backend (FastAPI + LangGraph)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* API Docs: `http://localhost:8000/docs`

#### 2. Frontend (React 19 + Vite)
```bash
cd frontend
npm install
npm run dev
```
* Web Cockpit: `http://localhost:5173`

---

## 🧪 Testing & Verification

Run the end-to-end integration test suite:
```bash
python backend/tests/test_e2e_pipeline.py
```
* Validates statistical drift math, dataset schema profiling, model training, evaluation gate rejection/promotion branches, and LangGraph HITL interrupt/resumption.
