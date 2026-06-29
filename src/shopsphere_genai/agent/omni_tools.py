import os
from langchain_core.tools import Tool
from shopsphere_genai.config.core import ShopSphereGenAIConfig
from shopsphere_genai.search.retriever import ShopSphereRetriever
from shopsphere_genai.agent.sql_agent import ShopSphereSQLAgent

def get_omni_tools(config: ShopSphereGenAIConfig):
    """
    Returns a unified list of LangChain tools that encompass all capabilities of the ShopSphere platform.
    """
    tools = []
    
    print("Loading RAG Sub-system...")
    try:
        retriever = ShopSphereRetriever(config)
        rag_tool = Tool(
            name="employee_handbook_search",
            func=retriever.retrieve_answers,
            description="Use this tool to search the employee handbook, retail guidelines, and corporate documents for store policies, return policies, onboarding, or general textual information. Input should be the user's question."
        )
        tools.append(rag_tool)
    except Exception as e:
        print(f"[WARN] Failed to load RAG Tool: {e}")

    print("Loading SQL Agent Sub-system...")
    try:
        sql_agent = ShopSphereSQLAgent(config)
        sql_tool = Tool(
            name="query_structured_data_warehouse",
            func=sql_agent.ask_data_question,
            description="Use this tool to query the structured data warehouse for numerical data, total store counts, aggregated sales revenue, database metrics, or finding out what stores exist. Input should be a clear, natural language question."
        )
        tools.append(sql_tool)
    except Exception as e:
        print(f"[WARN] Failed to load SQL Tool: {e}")
        
    print("Loading Unity Catalog Governed Tools...")
    try:
        from databricks_langchain.uc_ai import UCFunctionToolkit
        http_path = os.getenv("DATABRICKS_SQL_HTTP_PATH")
        if http_path:
            warehouse_id = http_path.split("/")[-1]
            toolkit = UCFunctionToolkit(warehouse_id=warehouse_id)
            uc_tools = toolkit.get_tools()
            
            # We want to specifically filter to our governed genai_core functions if possible
            # Or just include all for now.
            tools.extend(uc_tools)
        else:
            print("[WARN] DATABRICKS_SQL_HTTP_PATH not set. Skipping UC Tools.")
    except Exception as e:
        print(f"[WARN] Failed to load UC Tools: {e}")
        
    return tools
