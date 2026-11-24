---
name: mlops-supervisor
description: >-
  LangGraph Multi-Agent Orchestration, State Management, and LangSmith Tracing Skill.
  Controls the complete StateGraph flow across Data Sentinel, Training Agent,
  Evaluation Gate, Security Sentinel, and Packager Deployer. Manages MemorySaver
  checkpointer persistence and Human-in-the-Loop (HITL) interrupt approval gateways.
version: 1.0.0
tools:
  - run_supervisor_graph
---

# MLOps Supervisor Agent Skill

## 1. Purpose & Scope
The **MLOps Supervisor Agent** is the central brain and coordinator of the MLOps Build Agent Suite. Implemented as a **LangGraph StateGraph**, it manages state transitions, ensures threads can be saved and resumed from checkpoints, captures end-to-end telemetry into **LangSmith**, and halts at Human-in-the-Loop (HITL) checkpoints before production rollout.

---

## 2. Invariants & State Transition Rules
1. **Explicit State Schema**: Every subagent reads and mutates a single typed `MLOpsState` schema.
2. **Conditional Routing**:
   * If Data Sentinel reports `SCHEMA_ERROR` $\rightarrow$ Transition directly to `ERROR_ABORT`.
   * If Eval Gate reports `REJECTED` $\rightarrow$ Transition to `REJECTION_REPORT`.
   * If Eval Gate reports `PROMOTED` $\rightarrow$ Route to Security Sentinel.
3. **Mandatory HITL Gate**: Before the Packager Deployer executes cloud deployment, the graph executes `interrupt({"message": "Awaiting MLOps Engineer Approval"})`.
4. **LangSmith Tracing Invariant**: Every graph run must initialize with a unique `thread_id` and attach `callbacks=[LangChainTracer()]` for observability.

---

## 3. Execution Playbook
1. Initialize the LangGraph StateGraph with `MemorySaver` checkpointer.
2. Ingest user parameters from API (target dataset, model type, hyperparameter values, SLA budget).
3. Execute the graph until completion or HITL interruption.
4. When engineer approves via UI $\rightarrow$ resume graph execution from checkpoint thread ID.
