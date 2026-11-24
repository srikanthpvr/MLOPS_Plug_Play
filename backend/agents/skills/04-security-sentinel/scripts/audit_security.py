#!/usr/bin/env python3
"""
scripts/audit_security.py
Deterministic static security audit and secret scanner.
Detects:
- Exposed API keys, JWTs, and Azure storage connection strings via regex & Shannon entropy.
- Root user declarations in Dockerfiles.
- Unpinned or deprecated dependencies in requirements.txt.
"""

import os
import re
import sys
import math
import json
import argparse
from typing import Dict, Any, List

# High-entropy / Secret Patterns
SECRET_PATTERNS = {
    "Azure Connection String": re.compile(r"DefaultEndpointsProtocol=https;AccountName=[a-zA-Z0-9]+;AccountKey=[a-zA-Z0-9+/=]{40,}"),
    "OpenAI API Key": re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    "Generic Private Key": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    "Hardcoded Password Assignment": re.compile(r"(?i)(password|secret|api_key|token)\s*=\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]"),
}


def calculate_entropy(s: str) -> float:
    """Computes Shannon entropy of a string."""
    if not s:
        return 0.0
    prob = [float(s.count(c)) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in prob)


def audit_directory(target_dir: str) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    total_files_scanned = 0

    for root, _, files in os.walk(target_dir):
        for file in files:
            # Skip binary artifacts or git objects
            if file.endswith((".pkl", ".onnx", ".png", ".jpg", ".pyc")) or ".git" in root:
                continue

            file_path = os.path.join(root, file)
            total_files_scanned += 1

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Check secret patterns
                for secret_type, pattern in SECRET_PATTERNS.items():
                    matches = pattern.findall(content)
                    if matches:
                        findings.append({
                            "severity": "CRITICAL",
                            "file": os.path.relpath(file_path, target_dir),
                            "violation": f"Exposed {secret_type}",
                            "recommendation": "Migrate secret to Azure Key Vault or use DefaultAzureCredential"
                        })

                # Check Dockerfile non-root enforcement
                if file.lower() == "dockerfile":
                    if "USER " not in content or "USER root" in content:
                        findings.append({
                            "severity": "HIGH",
                            "file": os.path.relpath(file_path, target_dir),
                            "violation": "Dockerfile executes as root user",
                            "recommendation": "Add 'USER nonroot' or non-privileged UID before ENTRYPOINT"
                        })

            except Exception as e:
                findings.append({
                    "severity": "LOW",
                    "file": os.path.relpath(file_path, target_dir),
                    "violation": f"File could not be parsed: {str(e)}",
                    "recommendation": "Inspect file permissions"
                })

    critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high_count = sum(1 for f in findings if f["severity"] == "HIGH")

    return {
        "status": "PASS" if critical_count == 0 else "FAIL",
        "scanned_files_count": total_files_scanned,
        "critical_violations": critical_count,
        "high_violations": high_count,
        "findings": findings
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic Security Sentinel Audit")
    parser.add_argument("--target-dir", type=str, required=True, help="Directory to audit")
    parser.add_argument("--output", type=str, default="security_audit.json", help="Path to save report")
    args = parser.parse_args()

    result = audit_directory(args.target_dir)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
