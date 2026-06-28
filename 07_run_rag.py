# Databricks Notebook Execution Script - Basic RAG
# Use this script to ask an LLM questions about your private documents!

# IMPORTANT: We need the LangChain core library for our prompts and Vector Search.
# Run this %pip command in the very first cell of your notebook:
# %pip install langchain-core databricks-vectorsearch

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

# 2. Import our OOP classes
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Hot-reload trick
import shopsphere_genai.agent.basic_rag as rag_module
importlib.reload(rag_module)
from shopsphere_genai.agent.basic_rag import BasicRAGChain

# 3. Initialize config and RAG Chain
config = ShopSphereGenAIConfig.from_env("dev")
rag = BasicRAGChain(config=config)

# 4. Ask a question!
user_question = "What is the return policy for items I bought?"
print(f"User Question: {user_question}")

# 5. Let the RAG pipeline do its magic
result = rag.ask(user_question)

print("\n\n=========================================")
print("🤖 AI ANSWER:")
print("=========================================")
print(result['answer'])
print("\n=========================================")
print("📚 SOURCES CITED:")
for source in result['citations']:
    print(f"- {source}")
print("=========================================")
