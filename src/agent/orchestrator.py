from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.chat_models import ChatDatabricks
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
import sys
import os

# Assuming ShopSphereRetriever is available in your PYTHONPATH or local directory structure.
# For the sake of this script in the new directory, we mock the retriever import if not found.
try:
    from shopsphere_genai.search.retriever import ShopSphereRetriever
    from shopsphere_genai.config.core import ShopSphereGenAIConfig
    config = ShopSphereGenAIConfig.from_env("dev")
    retriever_instance = ShopSphereRetriever(config)
except ImportError:
    print("Warning: Original shopsphere_genai modules not found in path. Using mock retriever for demonstration.")
    class MockRetriever:
        def retrieve_context(self, query, top_k=3):
            return [{"text": f"Mock data for {query}", "source": "mock.pdf"}]
        def format_for_llm(self, docs):
            return str(docs)
    retriever_instance = MockRetriever()

# 1. Define the Tool
# The docstring is CRITICAL. The LLM reads this docstring to decide WHEN to use the tool.
@tool
def document_retriever(query: str) -> str:
    """
    Useful for answering questions about company policies, product manuals, 
    guidelines, and general text-based corporate knowledge.
    Input should be a specific search query.
    """
    docs = retriever_instance.retrieve_context(query)
    return retriever_instance.format_for_llm(docs)

class ShopSphereAgent:
    """
    The orchestrator that decides whether to chat or use tools.
    """
    def __init__(self):
        # We must use a model that supports tool calling (e.g., Llama 3)
        self.llm = ChatDatabricks(endpoint="databricks-meta-llama-3-70b-instruct", max_tokens=1000)
        self.tools = [document_retriever]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the ShopSphere Assistant. Use your tools if you need to look up factual information. If the user is just saying hello, respond politely without using tools."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        # Create the agent logic
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        
        # Create the executor that runs the while-loop
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True, # Set to True to see the "Thoughts" in the console
            max_iterations=3 # Prevents infinite cost loops
        )

    def chat(self, user_input: str) -> str:
        response = self.agent_executor.invoke({"input": user_input})
        return response["output"]

# Example Usage
# agent = ShopSphereAgent()
# print(agent.chat("Hello!")) # Will NOT use the tool
# print(agent.chat("What is the return policy?")) # WILL use the tool
