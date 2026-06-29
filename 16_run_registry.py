# Databricks Notebook - Model Registry (Lesson 19)
# This notebook logs your trained Omni-Agent to MLflow and registers it in Unity Catalog.
# After this runs, your agent has an official versioned artifact in the UC Model Registry.

import sys, os, importlib
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

try:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    os.environ["DATABRICKS_TOKEN"] = context.apiToken().get()
    os.environ["DATABRICKS_HOST"] = context.apiUrl().get()
except Exception as e:
    print(f"Could not auto-retrieve credentials: {e}")

os.environ["DATABRICKS_SQL_HTTP_PATH"] = "/sql/1.0/warehouses/0882de12737c4773"

import mlflow
from mlflow.models import infer_signature
from shopsphere_genai.config.core import ShopSphereGenAIConfig
from shopsphere_genai.agent.omni_agent import ShopSphereOmniAgent

# Tell MLflow to use Unity Catalog as the Model Registry backend.
# This replaces the old "Workspace" registry with enterprise-grade governance.
mlflow.set_registry_uri("databricks-uc")

config = ShopSphereGenAIConfig.from_env("dev")
omni_agent = ShopSphereOmniAgent(config)

# The full UC path to the registered model: catalog.schema.model_name
UC_MODEL_NAME = f"{config.catalog_name}.{config.schema_name}.shopsphere_copilot"
EXPERIMENT_PATH = "/Users/alvigeorge3@gmail.com/Agent_Registration"
mlflow.set_experiment(EXPERIMENT_PATH)

print("=======================================================")
print(f"📦 REGISTERING OMNI-AGENT TO UNITY CATALOG")
print(f"   Model: {UC_MODEL_NAME}")
print("=======================================================\n")

# Define the input/output signature so downstream consumers know the exact JSON API shape
example_input = {"messages": [{"role": "user", "content": "What is the return policy?"}]}
example_output = {"messages": [{"role": "assistant", "content": "The return policy is 30 days."}]}
signature = infer_signature(example_input, example_output)

with mlflow.start_run(run_name="Agent_Registration_v1") as run:
    # 1. Log the LangChain agent to MLflow Tracking
    print("Step 1: Logging agent artifact to MLflow Tracking Server...")
    model_info = mlflow.langchain.log_model(
        lc_model=omni_agent.agent_executor,
        artifact_path="shopsphere_agent",
        signature=signature,
        input_example=example_input,
    )
    print(f"  ✅ Artifact URI: {model_info.model_uri}")

    # 2. Register the artifact in Unity Catalog Model Registry
    print(f"\nStep 2: Registering in Unity Catalog as '{UC_MODEL_NAME}'...")
    registered_model = mlflow.register_model(
        model_uri=model_info.model_uri,
        name=UC_MODEL_NAME
    )
    print(f"  ✅ Registered as Version: {registered_model.version}")

print(f"\n✅ Registration Complete!")
print(f"   Go to Catalog -> {config.catalog_name} -> {config.schema_name} -> Models")
print(f"   to see 'shopsphere_copilot' v{registered_model.version} in Unity Catalog!")
