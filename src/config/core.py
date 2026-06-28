import os
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ShopSphereGenAIConfig:
    """
    Core configuration for the ShopSphere Retail Intelligence Platform.
    Using frozen=True ensures configuration is immutable during runtime.
    """
    project_name: str
    catalog_name: str
    schema_name: str
    volume_name: str
    vector_search_endpoint_name: str
    embedding_model_endpoint: str
    llm_endpoint: str
    
    @classmethod
    def from_env(cls, env: str = "dev") -> "ShopSphereGenAIConfig":
        """
        Factory method to load configuration based on environment.
        In an enterprise, these values are typically injected by CI/CD or 
        read from environment variables.
        """
        # We default to 'dev' catalog if not specified
        catalog = os.getenv("DATABRICKS_CATALOG", f"shopsphere_{env}")
        
        return cls(
            project_name="shopsphere_copilot",
            catalog_name=catalog,
            schema_name="genai_core",
            volume_name="raw_documents",
            vector_search_endpoint_name=os.getenv("VECTOR_SEARCH_ENDPOINT", f"vs_endpoint_{env}"),
            embedding_model_endpoint="databricks-bge-large-en",
            llm_endpoint="databricks-meta-llama-3-70b-instruct"
        )

# Example usage (would typically be in your main execution script)
# config = ShopSphereGenAIConfig.from_env(env="dev")
# print(f"Using catalog: {config.catalog_name}")
