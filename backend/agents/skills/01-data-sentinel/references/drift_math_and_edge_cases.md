# Data Sentinel Reference: Drift Mathematics & Edge Case Handling

## 1. Kolmogorov-Smirnov (KS) Two-Sample Test
The two-sample Kolmogorov-Smirnov test is a non-parametric statistical hypothesis test that compares the cumulative distributions $F_1(x)$ and $F_2(x)$ of two datasets.

The test statistic $D$ is defined as:
$$D = \sup_x |F_{\text{baseline}}(x) - F_{\text{current}}(x)|$$

### Edge Cases Handled:
1. **Identical Constant Distributions**: When all values in a column are constant (e.g. `0.0`), variance is 0. KS-test evaluates $D = 0$ with $p = 1.0$.
2. **Small Sample Sizes ($N < 30$)**: Standard asymptotic approximations fail; the script verifies $N \ge 5$ before computing stats.
3. **Infinite Values**: `inf` and `-inf` values are filtered alongside `NaN` prior to cumulative distribution computation.

---

## 2. Population Stability Index (PSI)
Population Stability Index measures the shift between an expected (baseline) and actual (current) population across $K$ quantile buckets:

$$\text{PSI} = \sum_{k=1}^{K} (Actual_k - Expected_k) \times \ln\left(\frac{Actual_k}{Expected_k}\right)$$

### Zero-Division Smoothing (Laplace Epsilon):
If an actual or expected bin has zero observations, $Actual_k = 0 \implies \ln(0)$ is undefined, and $Expected_k = 0 \implies \frac{Actual_k}{0}$ divides by zero.
Our implementation applies Laplace epsilon smoothing:
$$Actual_k = \frac{\text{Count}_k + \epsilon}{N_{\text{current}} + K \cdot \epsilon}, \quad \epsilon = 10^{-4}$$

This guarantees numerical stability without altering the resulting metric by more than $0.001$.

---

## 3. High-Cardinality Categorical Features
* When categorical features possess $> 50$ distinct categories (e.g., zip codes, user IDs), frequency binning collapses rare levels into an `__OTHER__` bin before calculating PSI.
