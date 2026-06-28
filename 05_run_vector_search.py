# Databricks Notebook Execution Script - Vector DB Sync
# Use this script to create a Vector Search Endpoint and Sync your Gold Table

# IMPORTANT: We need the Databricks Vector Search SDK.
# Run this %pip command in the very first cell of your notebook:
# %pip install databricks-vectorsearch

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

# 2. Import our OOP classes
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.search.vector_db as vector_db_module
importlib.reload(vector_db_module)
from shopsphere_genai.search.vector_db import VectorDBManager

# 3. Initialize config and Vector DB Manager
config = ShopSphereGenAIConfig.from_env("dev")
manager = VectorDBManager(config=config)

# 4. Provision the Serverless Endpoint
# WARNING: If this is your first time running this, it will take ~10 minutes to provision!
manager.setup_endpoint()

# 5. Create the Index and Sync the data
manager.create_or_sync_index()

print("Vector Search Database is syncing in the background!")
