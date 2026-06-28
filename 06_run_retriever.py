# Databricks Notebook Execution Script - The Retriever (RAG Phase 1)
# Use this script to search your Vector Database using natural language!

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

# 2. Import our OOP classes
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.search.retriever as retriever_module
importlib.reload(retriever_module)
from shopsphere_genai.search.retriever import ShopSphereRetriever

# 3. Initialize config and Retriever
config = ShopSphereGenAIConfig.from_env("dev")
retriever = ShopSphereRetriever(config=config)

# 4. Ask a question!
user_question = "What is the return policy for items I bought?"
print(f"User Question: {user_question}")

# 5. Retrieve the most relevant chunks from our Vector DB
results = retriever.retrieve_context(query=user_question, top_k=2)

# 6. Format and display the context we will eventually send to the LLM
formatted_context = retriever.format_for_llm(results)

print("\n--- RETRIEVED CONTEXT ---")
print(formatted_context)
