# Databricks Notebook Execution Script - MLflow Tracing (Lesson 14)
# Run this cell to test the Omni-Agent WITH full MLflow observability!
# After running, go to: Experiments -> shopsphere_omni_agent -> Click the latest run -> Traces tab

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

from shopsphere_genai.config.core import ShopSphereGenAIConfig

# 2. Import and hot-reload modules
import shopsphere_genai.agent.omni_tools as omni_tools_module
import shopsphere_genai.agent.omni_agent as omni_agent_module
import shopsphere_genai.evaluation.tracer as tracer_module
importlib.reload(omni_tools_module)
importlib.reload(omni_agent_module)
importlib.reload(tracer_module)

from shopsphere_genai.agent.omni_agent import ShopSphereOmniAgent
from shopsphere_genai.evaluation.tracer import ShopSphereTracer

# 3. Configure Authentication
os.environ["DATABRICKS_SQL_HTTP_PATH"] = "/sql/1.0/warehouses/0882de12737c4773"
try:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    token = context.apiToken().get()
    host = context.apiUrl().get()
    os.environ["DATABRICKS_TOKEN"] = token
    os.environ["DATABRICKS_HOST"] = host
except Exception as e:
    print(f"Could not auto-retrieve credentials: {e}")

# 4. Initialize Config
config = ShopSphereGenAIConfig.from_env("dev")

# 5. STEP 1: Set up MLflow Tracing BEFORE creating the agent
#    This is critical - autolog must be enabled before LangChain objects are instantiated
tracer = ShopSphereTracer(config, "/Shared/ShopSphere/Agent_Traces")
tracer.setup_tracing()

# 6. STEP 2: Now create the agent (it will be auto-instrumented)
omni_agent = ShopSphereOmniAgent(config)

# 7. STEP 3: Run the agent through the tracer to add business metadata to the trace
print("\n=======================================================")
print("🔍 BEGINNING TRACED OMNI-AGENT TESTS")
print("=======================================================\n")

USER_ID = "demo_user_001"

questions = [
    "What is the company policy for handling returns without a receipt?",
    "How many total stores do we currently have in our inventory?",
    "Can you check if SKU-8899 is in stock anywhere?"
]

for q in questions:
    print(f"\n[USER]: {q}")
    answer = tracer.execute_with_custom_span(
        agent_function=omni_agent.invoke,
        user_input=q,
        user_id=USER_ID
    )
    print(f"\n[OMNI-AGENT]: {answer}")
    print("\n" + "-"*50)

print("\n✅ Done! Go to Experiments -> ShopSphere/Agent_Traces in the Databricks UI to inspect the traces!")
