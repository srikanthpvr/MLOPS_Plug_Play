# Evaluation Gate Reference: Gating Criteria & SLA Budgets

## 1. Regression Assertion Mathematics

Let $M_c$ be the candidate challenger model and $M_*$ be the production champion model evaluated over the test split $\mathcal{D}_{\text{test}}$.

The statistical difference in performance:
$$\Delta_{F1} = F1(M_c, \mathcal{D}_{\text{test}}) - F1(M_*, \mathcal{D}_{\text{test}})$$

### Criteria:
1. **Pass Condition**: $\Delta_{F1} \ge 0.0$ (Strict improvement).
2. **Tolerance Margin**: $\Delta_{F1} \in [-0.005, 0.0)$ is only accepted if $p_{95}(M_c) < 0.75 \times p_{95}(M_*)$ (latency reduction $\ge 25\%$).
3. **Hard Rejection**: $\Delta_{F1} < -0.005$ triggers an automatic rejection.

---

## 2. Latency Benchmarking & Jitter Elimination

Single-request latency measurements are notoriously noisy due to thread context switching, garbage collection, and dynamic frequency scaling.

### Mitigation Strategies:
* **JIT/Cache Warmup**: 30 to 50 inference passes are executed before timing starts to warm CPU instruction caches.
* **High-Precision Clocking**: Uses `time.perf_counter()` to obtain sub-microsecond resolution.
* **Percentile Profiling**: Focuses on $p_{95}$ and $p_{99}$ rather than arithmetic mean to measure tail latency and eliminate outlier spikes.
