---
name: eval-gate
description: >-
  Automated Model Evaluation Gate and Latency SLA Benchmarking Skill.
  Enforces Champion vs. Challenger quality gates, runs regression assertions,
  benchmarks batch inference latency distributions (p50, p95, p99) under simulated
  workload, and emits promotion or rejection decisions.
version: 1.0.0
tools:
  - benchmark_and_gate
---

# Evaluation Gate Agent Skill

## 1. Purpose & Scope
The **Evaluation Gate Agent** is the automated quality firewall preventing inferior or slow models from reaching production. It rigorously compares the newly trained **Challenger** model against the production **Champion** baseline, asserting both predictive superiority and latency compliance under tight SLA budgets.

---

## 2. Invariants & Deterministic Gating Rules
1. **Never Promote on Training Completion Alone**: A model completing training successfully is NOT sufficient for deployment.
2. **Predictive Superiority Rule**:
   $$F1_{\text{challenger}} \ge F1_{\text{champion}} - \delta, \quad \delta = 0.005$$
   (Allows maximum acceptable tolerance of $0.5\%$ only if latency improvements exceed $25\%$).
3. **Latency SLA Compliance**:
   $$p_{95}(\text{Challenger Latency}) \le \text{SLA Budget (e.g. } 50\text{ms)}$$
   Models exceeding the latency SLA are rejected regardless of high predictive accuracy.
4. **Cold-Start Elimination**: The benchmarking harness must execute at least 50 warmup requests before recording latency percentiles.

---

## 3. Execution Playbook
1. Load Candidate model artifact (`candidate/model.pkl`) and Champion baseline artifact (`champion/model.pkl` or `champion/metrics.json`).
2. Run `python scripts/benchmark_and_gate.py --candidate-dir artifacts/candidate --champion-dir artifacts/champion --sla-p95-ms 50.0 --output gate_result.json`.
3. Read the resulting `gate_result.json`:
   * If `status == "PROMOTED"` $\rightarrow$ Mark evaluation passed and route to Security Sentinel.
   * If `status == "REJECTED"` $\rightarrow$ Abort pipeline with detailed diagnostic metrics.
