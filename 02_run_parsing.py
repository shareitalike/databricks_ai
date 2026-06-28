# Databricks Notebook Execution Script - Parsing
# Use this script in a Databricks Notebook cell to extract text from the Bronze table

# IMPORTANT: We need the PyMuPDF library to parse PDFs.
# Run this %pip command in the very first cell of your notebook:
# %pip install PyMuPDF

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append(os.path.abspath('src')) 

# 2. Import our OOP classes
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.ingestion.parser as parser_module
importlib.reload(parser_module)
from shopsphere_genai.ingestion.parser import DocumentParser

# 3. Initialize config and parser
config = ShopSphereGenAIConfig.from_env("dev")
parser = DocumentParser(spark=spark, config=config)

# 4. Execute the Distributed Parsing!
# This will read the binary data, extract the English text, and write it to the Silver table.
print("Starting distributed text extraction...")
parser.parse_documents()
print("Parsing complete!")

# 5. Verify the clean text landed in the Silver table!
display(spark.sql(f"SELECT path, text_content FROM {config.catalog_name}.{config.schema_name}.silver_parsed_documents"))
