# Databricks Notebook Execution Script - SQL Agent
# Use this script to test the Text-to-SQL Agent on your Unity Catalog Tables!

# IMPORTANT: You need the Databricks SQL Connector and LangChain SQL packages!
# Run this %pip command in the very first cell of your notebook:
# %pip install databricks-sql-connector databricks-sqlalchemy langchain-community langchain-databricks

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.agent.sql_agent as sql_agent_module
importlib.reload(sql_agent_module)
from shopsphere_genai.agent.sql_agent import ShopSphereSQLAgent

# 2. Configure Authentication
# The SQL agent needs to connect to a SQL warehouse.
# Replace this with your actual SQL Warehouse HTTP path!
# It looks like: /sql/1.0/warehouses/0882de12737c4773
os.environ["DATABRICKS_SQL_HTTP_PATH"] = "/sql/1.0/warehouses/0882de12737c4773"

# Note: In a Databricks Notebook, it will automatically use your current workspace credentials
# to generate the token and host if you don't provide them, but sqlalchemy requires an explicit token.
# To get your personal token securely in a notebook without pasting it, we use the dbutils notebook API:
try:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    token = context.apiToken().get()
    host = context.apiUrl().get().replace("https://", "")
    os.environ["DATABRICKS_TOKEN"] = token
    os.environ["DATABRICKS_HOST"] = host
except Exception as e:
    print("Could not automatically retrieve Databricks credentials. Make sure you are running this inside a Databricks Notebook.")

# 3. Initialize Config and Create Mock Tables
config = ShopSphereGenAIConfig.from_env("dev")

print("Creating mock tables in Unity Catalog...")
try:
    spark.sql(f"CREATE TABLE IF NOT EXISTS {config.catalog_name}.{config.schema_name}.store_inventory (store_id INT, store_name STRING, espresso_machines_in_stock INT)")
    spark.sql(f"INSERT INTO {config.catalog_name}.{config.schema_name}.store_inventory VALUES (1, 'NY Flagship', 5), (2, 'LA Downtown', 0), (3, 'Chicago Central', 12)")
    
    spark.sql(f"CREATE TABLE IF NOT EXISTS {config.catalog_name}.{config.schema_name}.sales_aggregated (store_id INT, month STRING, total_revenue DECIMAL(10,2))")
    spark.sql(f"INSERT INTO {config.catalog_name}.{config.schema_name}.sales_aggregated VALUES (1, 'October', 15000.00), (2, 'October', 8500.50), (3, 'October', 22000.00)")
except Exception as e:
    print(f"Error creating tables (they might already exist with data): {e}")

print("Initializing SQL Agent...")
agent = ShopSphereSQLAgent(config)

# 4. Ask a Natural Language Question about the Database
if agent.connected:
    question = "How many total stores are in the store_inventory table?"
    print(f"\nUser: {question}")
    answer = agent.ask_data_question(question)
    print(f"\nAgent: {answer}")
else:
    print("Agent failed to connect.")
