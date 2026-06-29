# Databricks Notebook - Model Serving Deployment (Lesson 20)
# Deploys the registered UC model to a live REST API Serving Endpoint.
# After this runs, any application can call your Omni-Agent via HTTP!

import sys, os
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

try:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    os.environ["DATABRICKS_TOKEN"] = context.apiToken().get()
    os.environ["DATABRICKS_HOST"] = context.apiUrl().get()
except Exception as e:
    print(f"Could not auto-retrieve credentials: {e}")

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput, 
    ServedEntityInput,
    AutoCaptureConfigInput
)
from shopsphere_genai.config.core import ShopSphereGenAIConfig

config = ShopSphereGenAIConfig.from_env("dev")
w = WorkspaceClient()

UC_MODEL_NAME = f"{config.catalog_name}.{config.schema_name}.shopsphere_copilot"
MODEL_VERSION  = 1   # <- Update to match the version registered in 16_run_registry.py
ENDPOINT_NAME  = "shopsphere-copilot-prod"

print("=======================================================")
print(f"🚀 DEPLOYING TO MODEL SERVING ENDPOINT")
print(f"   Model:    {UC_MODEL_NAME} v{MODEL_VERSION}")
print(f"   Endpoint: {ENDPOINT_NAME}")
print("=======================================================\n")

# 1. Define the entity to serve
served_entity = ServedEntityInput(
    entity_name=UC_MODEL_NAME,
    entity_version=str(MODEL_VERSION),
    workload_size="Small",      # Small / Medium / Large
    scale_to_zero_enabled=True  # Auto-pause during idle periods to save cost
)

# 2. Enable Inference Tables: automatically log all requests & responses to Delta
auto_capture = AutoCaptureConfigInput(
    catalog_name=config.catalog_name,
    schema_name="monitoring",
    table_name_prefix="agent_logs",
    enabled=True
)

endpoint_config = EndpointCoreConfigInput(
    name=ENDPOINT_NAME,
    served_entities=[served_entity],
    auto_capture_config=auto_capture
)

# 3. Create or update the endpoint (zero-downtime rolling update if it already exists)
existing = [e.name for e in w.serving_endpoints.list()]

if ENDPOINT_NAME in existing:
    print("Endpoint already exists. Performing zero-downtime config update...")
    w.serving_endpoints.update_config(
        name=ENDPOINT_NAME,
        served_entities=[served_entity]
    )
else:
    print("Creating new endpoint...")
    w.serving_endpoints.create(
        name=ENDPOINT_NAME,
        config=endpoint_config
    )

print(f"\n✅ Deployment initiated! State is now 'UPDATING'.")
print(f"   Monitor progress: Serving -> {ENDPOINT_NAME} in the Databricks UI.")
print(f"\n📡 Once READY, your agent will be callable via REST API at:")
print(f"   POST {os.environ.get('DATABRICKS_HOST')}/serving-endpoints/{ENDPOINT_NAME}/invocations")
print(f"\n   Example curl:")
print(f"""   curl -X POST \\
     -H "Authorization: Bearer $DATABRICKS_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{{"messages": [{{"role": "user", "content": "What is the return policy?"}}]}}' \\
     {os.environ.get('DATABRICKS_HOST')}/serving-endpoints/{ENDPOINT_NAME}/invocations""")
