from pyspark.sql import SparkSession
# In a real environment, you need the Databricks specific LangChain integrations
from langchain_databricks import UCFunctionToolkit

class UCFunctionManager:
    """
    Manages the lifecycle of Unity Catalog Functions used as Agent Tools.
    """
    def __init__(self, spark: SparkSession, catalog: str, schema: str):
        self.spark = spark
        self.catalog = catalog
        self.schema = schema

    def register_inventory_tool(self):
        """
        Creates a governed Python function inside Unity Catalog.
        This function checks inventory for a given SKU.
        """
        function_name = f"{self.catalog}.{self.schema}.check_inventory"
        
        print(f"Registering UC Function: {function_name}")
        
        # We use SQL to define the UC function.
        # The COMMENT is critical—it acts as the prompt for the LLM.
        create_sql = f"""
        CREATE OR REPLACE FUNCTION {function_name}(sku STRING)
        RETURNS STRING
        LANGUAGE PYTHON
        COMMENT 'Fetches the current inventory count for a specific product SKU. Use this whenever the user asks if an item is in stock.'
        AS $$
            # In production, this would query a Delta table using the Spark session.
            # For demonstration, we use mock logic.
            mock_db = {{
                "SKU-123": "5 items in stock",
                "SKU-999": "Out of stock"
            }}
            return mock_db.get(sku, "SKU not found in inventory database.")
        $$
        """
        self.spark.sql(create_sql)
        print("Function registered successfully.")

    def get_langchain_tools(self, warehouse_id: str):
        """
        Fetches the governed functions from UC and converts them to LangChain tools.
        """
        toolkit = UCFunctionToolkit(warehouse_id=warehouse_id)
        tools = toolkit.get_tools(
            function_names=[f"{self.catalog}.{self.schema}.check_inventory"]
        )
        return tools

# Example Usage
# spark = SparkSession.builder.getOrCreate()
# manager = UCFunctionManager(spark, "shopsphere_dev", "genai_core")
# manager.register_inventory_tool()
# tools = manager.get_langchain_tools(warehouse_id="your_warehouse_id_here")
# # You can now pass 'tools' into your AgentExecutor from Lesson 9!
