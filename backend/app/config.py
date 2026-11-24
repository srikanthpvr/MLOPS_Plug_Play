import os
from pydantic import BaseModel

class AppSettings(BaseModel):
    app_mode: str = os.getenv("APP_MODE", "local")
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")

    # LangChain / LangSmith
    langchain_tracing_v2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "mlops-build-agent-suite")

    # Azure
    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    azure_storage_account: str = os.getenv("AZURE_STORAGE_ACCOUNT", "mlopsstorage")
    azure_storage_container: str = os.getenv("AZURE_STORAGE_CONTAINER", "datasets")
    azure_container_registry: str = os.getenv("AZURE_CONTAINER_REGISTRY", "myregistry.azurecr.io")

settings = AppSettings()
