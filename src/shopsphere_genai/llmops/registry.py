import mlflow
from mlflow.models import infer_signature
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class ModelRegistryManager:
    """
    Handles logging and registering compiled AI Agents into Unity Catalog.
    """
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        # Tell MLflow to use Unity Catalog instead of the legacy workspace registry
        mlflow.set_registry_uri("databricks-uc")
        self.model_name = f"{self.config.catalog_name}.{self.config.schema_name}.shopsphere_copilot"

    def register_agent(self, agent_instance):
        """
        Logs the LangChain agent and registers it as a new version in UC.
        """
        print(f"Starting Registration Process for model: {self.model_name}")
        
        # We need an example input and output to infer the schema (signature)
        # This tells downstream UI applications exactly what JSON to send.
        example_input = {"messages": [{"role": "user", "content": "Hello"}]}
        example_output = {"messages": [{"role": "assistant", "content": "Hi there!"}]}
        signature = infer_signature(example_input, example_output)

        with mlflow.start_run(run_name="Agent_Registration_Run") as run:
            
            # 1. Log the model artifact to the MLflow tracking server
            # This captures the code, the prompts, and the pip dependencies.
            model_info = mlflow.langchain.log_model(
                lc_model=agent_instance, 
                artifact_path="agent_artifact",
                signature=signature,
                # In production, explicitly list dependencies to avoid 'ModuleNotFoundError'
                # pip_requirements=["langchain==0.1.16", "langgraph==0.0.35", "databricks-vectorsearch"]
            )
            
            print(f"Model logged. Artifact URI: {model_info.model_uri}")
            
            # 2. Register the logged artifact into Unity Catalog
            # This makes it visible to the entire enterprise under the catalog name.
            registered_model = mlflow.register_model(
                model_uri=model_info.model_uri,
                name=self.model_name
            )
            
            print(f"Successfully registered Version {registered_model.version} of {self.model_name}")
            return registered_model

# Example Usage:
# # Assume `app` is your compiled LangGraph workflow from Lesson 13
# config = ShopSphereGenAIConfig.from_env("dev")
# registry_manager = ModelRegistryManager(config)
# registered_model = registry_manager.register_agent(app)
