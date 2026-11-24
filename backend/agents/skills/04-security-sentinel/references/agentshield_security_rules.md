# Security Sentinel Reference: AgentShield Rules & Azure Key Vault

## 1. Zero-Secret Invariant & Azure Managed Identity
Traditional systems often pass storage keys or connection strings in code or Docker environment flags. This creates serious risk of secret exfiltration.

### Managed Identity Pattern:
In Python, always authenticate using Azure Identity SDK:
```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
blob_client = BlobServiceClient(account_url="https://<account>.blob.core.windows.net", credential=credential)
```

This ensures zero tokens are stored locally.

---

## 2. Container Non-Root Security Standards
Executing containerized inference engines as `root` (UID 0) gives potential attackers full host kernel privileges if a remote code execution vulnerability occurs.

### Standard Multi-Stage Non-Root Dockerfile Snippet:
```dockerfile
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
EXPOSE 8000
CMD ["uvicorn", "app_serve:app", "--host", "0.0.0.0", "--port", "8000"]
```
