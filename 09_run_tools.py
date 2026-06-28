# Databricks Notebook Execution Script - Tools & Unity Catalog
# Use this script to register a governed tool in Unity Catalog and test it!

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick for our new tools manager
import shopsphere_genai.agent.tools as tools_module
importlib.reload(tools_module)
from shopsphere_genai.agent.tools import UCFunctionManager

config = ShopSphereGenAIConfig.from_env("dev")

# 2. Register the governed tool in Unity Catalog
print("Registering the governed check_inventory tool in Unity Catalog...")
manager = UCFunctionManager(spark, config.catalog_name, config.schema_name)
manager.register_inventory_tool()

# 3. Initialize the Agent (Wait, we need to pass this tool to our agent!)
# For this lesson, we will just fetch the tool from Unity Catalog and print it to prove it works!
# IMPORTANT: You must provide a warehouse_id to run SQL functions.
# You can find this in Databricks -> SQL Warehouses -> Click a warehouse -> Overview -> Server Hostname (extract the ID)
# E.g., if hostname is 'adb-123.45.azuredatabricks.net', your warehouse ID is in the HTTP Path or UI.
# Alternatively, go to Compute -> SQL Warehouses -> click one -> URL contains /sql/warehouses/<id>

WAREHOUSE_ID = "0882de12737c4773"

print(f"\nFetching governed tools from Unity Catalog using Warehouse: {WAREHOUSE_ID}")
try:
    tools = manager.get_langchain_tools(warehouse_id=WAREHOUSE_ID)
    
    print("\n--- SUCCESSFULLY LOADED TOOLS ---")
    for tool in tools:
        print(f"Tool Name: {tool.name}")
        print(f"Description: {tool.description}")
        
    print("\nYou can now pass this `tools` list to the ShopSphereAgent in the next lesson!")
except Exception as e:
    print(f"\nError fetching tools: {e}")
    print("Did you forget to replace YOUR_WAREHOUSE_ID_HERE with a real SQL Warehouse ID?")
