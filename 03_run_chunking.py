# Databricks Notebook Execution Script - Chunking
# Use this script in a Databricks Notebook cell to break Silver text into Pre-Gold chunks

# IMPORTANT: We need the LangChain library to split text.
# Run this %pip command in the very first cell of your notebook:
# %pip install langchain

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

# 2. Import our OOP classes
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.embeddings.chunker as chunker_module
importlib.reload(chunker_module)
from shopsphere_genai.embeddings.chunker import TextChunker

# 3. Initialize config and chunker
config = ShopSphereGenAIConfig.from_env("dev")
chunker = TextChunker(spark=spark, config=config)

# 4. Execute the Distributed Chunking!
print("Starting distributed chunking...")
df_exploded = chunker.process_chunks()

# 5. Verify the chunks landed in the Pre-Gold table!
display(spark.sql(f"SELECT path, chunk_content FROM {config.catalog_name}.{config.schema_name}.pre_gold_chunks"))
