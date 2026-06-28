import os
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class DeploymentManager:
    """
    Automates the deployment of registered UC models to Serverless Endpoints.
    """
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        self.w = WorkspaceClient()
        self.model_name = f"{self.config.catalog_name}.{self.config.schema_name}.shopsphere_copilot"
        self.endpoint_name = f"{self.config.project_name}_endpoint_prod"

    def deploy_model_version(self, version: int):
        """
        Creates or updates a Model Serving Endpoint with the specified model version.
        """
        print(f"Initiating deployment of {self.model_name} (Version: {version}) to {self.endpoint_name}")
        
        # 1. Define the serving configuration
        served_entity = ServedEntityInput(
            entity_name=self.model_name,
            entity_version=version,
            workload_size="Small", # CPU/RAM allocation per container
            scale_to_zero_enabled=True # Cost savings
        )
        
        config = EndpointCoreConfigInput(
            name=self.endpoint_name,
            served_entities=[served_entity]
        )
        
        # 2. Check if endpoint already exists
        existing_endpoints = [e.name for e in self.w.serving_endpoints.list()]
        
        if self.endpoint_name in existing_endpoints:
            print("Endpoint exists. Initiating zero-downtime update...")
            self.w.serving_endpoints.update_config(
                name=self.endpoint_name,
                served_entities=[served_entity]
            )
        else:
            print("Endpoint does not exist. Creating new endpoint...")
            self.w.serving_endpoints.create(
                name=self.endpoint_name,
                config=config
            )
            
        print("Deployment initiated. State transitions to 'UPDATING'.")
        print("Note: In production, you would poll w.serving_endpoints.get() until state == 'READY'.")

# Example Usage:
# config = ShopSphereGenAIConfig.from_env("dev")
# deployer = DeploymentManager(config)
# # Deploy version 1 of the model we registered in Lesson 19
# deployer.deploy_model_version(version=1)
