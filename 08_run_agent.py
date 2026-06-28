# Databricks Notebook Execution Script - Single Agent
# Use this script to test your Tool-Calling RAG Agent!

# IMPORTANT: We need the full LangChain ecosystem for Agents!
# Run this %pip command in the very first cell of your notebook:
# %pip install langchain langchain-core langchain-databricks databricks-vectorsearch

import sys
import os
import importlib

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

# Hot-reload trick
import shopsphere_genai.agent.orchestrator as orchestrator_module
importlib.reload(orchestrator_module)
from shopsphere_genai.agent.orchestrator import ShopSphereAgent

# 2. Initialize the Agent
agent = ShopSphereAgent()

# 3. Test 1: Casual Chat (Should NOT trigger the database)
print("\n--- TEST 1: CHAT ---")
print("User: Hello!")
chat_response = agent.chat("Hello!")
print(f"Agent: {chat_response}")

# 4. Test 2: RAG Question (SHOULD trigger the Vector DB Tool)
print("\n--- TEST 2: RAG ---")
question = "What is the return policy for the espresso machine?"
print(f"User: {question}")
rag_response = agent.chat(question)
print(f"Agent: {rag_response}")
