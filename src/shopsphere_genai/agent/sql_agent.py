import os
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_databricks import ChatDatabricks
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class ShopSphereSQLAgent:
    """
    An agent specifically designed to convert natural language to SQL
    and execute it against Databricks Gold tables.
    """
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        
        # Initialize the LLM (Must be a highly capable reasoning model like Llama 3.3 70B)
        self.llm = ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct", temperature=0)
        
        # Databricks SQL Connection
        # In a real environment, you use a PAT or OAuth token belonging to a Service Principal
        host = os.getenv("DATABRICKS_HOST", "your-workspace.cloud.databricks.com")
        http_path = os.getenv("DATABRICKS_SQL_HTTP_PATH", "/sql/1.0/warehouses/your-warehouse-id")
        token = os.getenv("DATABRICKS_TOKEN", "mock-token")
        
        # Extract warehouse ID from the HTTP path
        warehouse_id = http_path.split("/")[-1]
        
        print("Connecting to Databricks SQL Warehouse...")
        try:
            # We explicitly INCLUDE only the tables the agent is allowed to see.
            # Using from_databricks is the recommended and most robust method.
            self.db = SQLDatabase.from_databricks(
                catalog=self.config.catalog_name,
                schema=self.config.schema_name,
                host=host,
                api_token=token,
                warehouse_id=warehouse_id,
                include_tables=["sales_aggregated", "store_inventory"] 
            )
            
            # Create the LangChain SQL Agent
            self.agent_executor = create_sql_agent(
                llm=self.llm,
                db=self.db,
                agent_type="tool-calling",
                verbose=True,
                # Custom instructions to prevent massive queries
                prefix="You are a SQL expert. Always append LIMIT 10 to queries unless an aggregation is requested. Never execute DML statements (INSERT, UPDATE, DELETE)."
            )
            self.connected = True
        except Exception as e:
            print(f"Failed to connect to SQL Warehouse: {e}")
            self.connected = False

    def ask_data_question(self, question: str) -> str:
        """
        Executes the agent loop to answer a data question.
        """
        if not self.connected:
            return "SQL Agent is not connected to the database."
            
        print(f"\n--- Translating to SQL: '{question}' ---")
        try:
            response = self.agent_executor.invoke({"input": question})
            return response["output"]
        except Exception as e:
            return f"Agent failed to execute the query. Error: {e}"

# Example Usage
# config = ShopSphereGenAIConfig.from_env("dev")
# sql_agent = ShopSphereSQLAgent(config)
# answer = sql_agent.ask_data_question("Which 3 stores had the highest sales revenue last month?")
# print(answer)
