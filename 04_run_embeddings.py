# Databricks Notebook Execution Script - Embeddings
# Use this script to convert text chunks into vector embeddings using Databricks ai_query

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

# 2. Import our OOP classes
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.embeddings.embedder as embedder_module
importlib.reload(embedder_module)
from shopsphere_genai.embeddings.embedder import EmbeddingGenerator

# 3. Initialize config and embedder
config = ShopSphereGenAIConfig.from_env("dev")
embedder = EmbeddingGenerator(spark=spark, config=config)

# 4. Execute Vector Embeddings Generation!
print("Starting vector embedding generation via Databricks Foundation Models...")
df_gold = embedder.generate_embeddings()

# 5. Verify the embeddings landed in the Gold table!
display(spark.sql(f"SELECT chunk_content, embedding_vector FROM {config.catalog_name}.{config.schema_name}.gold_document_vectors"))
