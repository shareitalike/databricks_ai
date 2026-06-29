# Databricks Notebook Execution Script - Omni-Agent
# Run this cell to test the Master Omni-Agent!

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.agent.omni_tools as omni_tools_module
import shopsphere_genai.agent.omni_agent as omni_agent_module
importlib.reload(omni_tools_module)
importlib.reload(omni_agent_module)

from shopsphere_genai.agent.omni_agent import ShopSphereOmniAgent

# 2. Configure Authentication (for SQL and UC tools)
os.environ["DATABRICKS_SQL_HTTP_PATH"] = "/sql/1.0/warehouses/0882de12737c4773"

try:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    token = context.apiToken().get()
    host = context.apiUrl().get().replace("https://", "")
    os.environ["DATABRICKS_TOKEN"] = token
    os.environ["DATABRICKS_HOST"] = host
except Exception as e:
    print("Could not automatically retrieve Databricks credentials. Make sure you are running this inside a Databricks Notebook.")

# 3. Initialize Config and Omni-Agent
config = ShopSphereGenAIConfig.from_env("dev")
omni_agent = ShopSphereOmniAgent(config)

# 4. Test the Omni-Agent with 3 Distinct Scenarios!

questions = [
    # Scenario 1: Unstructured Policy Question -> Should trigger RAG (employee_handbook_search)
    "What is the company policy for handling returns without a receipt?",
    
    # Scenario 2: Structured Data Question -> Should trigger SQL Agent (query_structured_data_warehouse)
    "How many total stores do we currently have in our inventory?",
    
    # Scenario 3: Specific SKU Governance Check -> Should trigger UC Function (check_inventory)
    "Can you check if SKU-8899 is in stock anywhere?"
]

print("\n=======================================================")
print("🚀 BEGINNING OMNI-AGENT TESTS")
print("=======================================================\n")

for q in questions:
    print(f"\n[USER]: {q}")
    answer = omni_agent.invoke(q)
    print(f"\n[OMNI-AGENT]: {answer}")
    print("\n" + "-"*50)
