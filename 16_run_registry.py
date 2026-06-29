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
    print("Step 1: Logging agent artifact to MLflow Tracking Server using Models-from-Code...")
    
    # Use explicit absolute path for Databricks Notebook environment
    entrypoint_path = "/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src/shopsphere_genai/agent/mlflow_entrypoint.py"
    
    model_info = mlflow.langchain.log_model(
        lc_model=entrypoint_path,
        artifact_path="shopsphere_agent",
        signature=signature,
        input_example=example_input,
        pip_requirements=[
            "langchain==0.3.13",
            "langchain-core==0.3.28",
            "langgraph==0.2.60",
            "langchain-community==0.3.13",
            "databricks-langchain",
            "databricks-sql-connector",
            "pydantic"
        ]
    )
    print(f"🔗 View Logged Model at: {model_info.model_uri}")

    # 2. Register the logged model into Unity Catalog!
    print("\nStep 2: Registering model to Unity Catalog...")
    registered_model = mlflow.register_model(
        model_uri=model_info.model_uri,
        name=UC_MODEL_NAME,
        await_registration_for=300
    )
    
    print(f"✅ Model registered successfully as Version {registered_model.version}!")

print("\n-------------------------------------------------------")
print("🎉 OMNI-AGENT IS NOW IN UNITY CATALOG!")
print("It is officially tracked, versioned, and governed.")
print(f"Go to Catalog -> {config.catalog_name} -> {config.schema_name} -> shopsphere_copilot to see it.")
print("Next, we will deploy it to a live Serverless Endpoint!")
print("-------------------------------------------------------")
