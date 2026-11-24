---
name: security-sentinel
description: >-
  AgentShield Security Invariants and Credential Governance Skill.
  Enforces zero hardcoded credentials (API keys, Azure connection strings, tokens),
  audits Azure Managed Identity bindings, verifies non-root Docker execution standards,
  and scans dependencies for dangerous vulnerabilities.
version: 1.0.0
tools:
  - audit_security
---

# AgentShield Security Sentinel Agent Skill

## 1. Purpose & Scope
The **Security Sentinel Agent** protects the enterprise infrastructure from vulnerability injections, data leaks, and unauthorized access. It audits generated serving code, environment files, Dockerfiles, and Azure configurations before any artifact can be deployed.

---

## 2. Invariants & Deterministic Security Rules
1. **Zero Hardcoded Secrets**: No file, environment variable, or prompt may contain plain-text Azure connection strings, API keys (`ey...`, `sk-...`), or database passwords.
2. **Identity Over Secrets**: Applications must authenticate to Azure services using **Managed Identity** (`DefaultAzureCredential`), not hardcoded service principal client secrets.
3. **Non-Root Container Invariant**: Generated Dockerfiles MUST explicitly create and declare a non-root user (`USER nonroot` or `USER 10001:10001`).
4. **Least-Privilege Enforcement**: Scans ensure storage access uses granular Azure RBAC roles (`Storage Blob Data Reader / Contributor`) rather than broad Owner/Contributor privileges.

---

## 3. Execution Playbook
1. Inspect the target deployment directory containing code, configs, and container manifests.
2. Run `python scripts/audit_security.py --target-dir <path> --output security_audit.json`.
3. Evaluate audit findings:
   * If `critical_violations > 0` $\rightarrow$ Abort deployment immediately and emit `SECURITY_ALERT`.
   * If zero critical violations $\rightarrow$ Append security certificate to state and allow Packager & Deployer to proceed.
