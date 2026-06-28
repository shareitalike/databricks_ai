# Databricks Notebook Execution Script
# Use this script in a Databricks Notebook cell to run the Auto Loader Ingestion

import sys
import os
import time
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append(os.path.abspath('src'))  # Ensure 'src' is in the Python path 

# 2. Import the OOP classes using the correct package namespace!
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Critical Databricks Trick: Force reload the module to catch Git Pull updates
import shopsphere_genai.ingestion.loader as loader_module
importlib.reload(loader_module)
from shopsphere_genai.ingestion.loader import DocumentIngestor

# 3. Initialize the config for the 'dev' environment
config = ShopSphereGenAIConfig.from_env("dev")  # Load configuration for 'dev' environment

# 4. Initialize the Ingestor class
ingestor = DocumentIngestor(spark=spark, config=config)

# 5. Execute the pipeline!
ingestor.ingest_documents()

print("Auto Loader stream started! Waiting 15 seconds for data to process...")
time.sleep(15)

# 6. Verify the data landed in the Bronze table
display(spark.sql(f"SELECT * FROM {config.catalog_name}.{config.schema_name}.bronze_raw_documents")) 
