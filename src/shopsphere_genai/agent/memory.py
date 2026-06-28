from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit
from langchain_core.runnables.history import RunnableWithMessageHistory

# Note: For this script to run locally without a Databricks cluster, 
# you would replace the Spark logic with a local SQLite DB.
# We show the Spark logic for enterprise architecture context.

class DeltaChatMessageHistory(BaseChatMessageHistory):
    """
    Custom LangChain memory backend that persists chat history to a Delta table.
    """
    def __init__(self, session_id: str, spark: SparkSession, table_name: str):
        self.session_id = session_id
        self.spark = spark
        self.table_name = table_name
        self.messages = []
        # In a real app, you would load existing history from Delta here via a Spark query.
        self._load_from_delta()

    def _load_from_delta(self):
        try:
            # Query Delta for this session, order by timestamp
            df = self.spark.sql(f"""
                SELECT message_json FROM {self.table_name} 
                WHERE session_id = '{self.session_id}' 
                ORDER BY timestamp ASC
            """)
            rows = df.collect()
            # Convert JSON strings back to LangChain message objects
            # (Requires json parsing, simplified here)
            pass
        except Exception:
            # Table might not exist yet
            pass

    def add_message(self, message: BaseMessage) -> None:
        """
        Appends a message to the internal list and writes it to Delta.
        """
        self.messages.append(message)
        
        # Serialize LangChain message to dict
        msg_dict = messages_to_dict([message])[0]
        import json
        msg_json = json.dumps(msg_dict)
        
        # Write to Delta
        try:
            # For high throughput, use a batched async writer or REST API, 
            # but Spark append works for demonstration.
            new_row = self.spark.createDataFrame([(self.session_id, msg_json)])\
                .toDF("session_id", "message_json")\
                .withColumn("timestamp", current_timestamp())
                
            new_row.write.format("delta").mode("append").saveAsTable(self.table_name)
        except Exception as e:
            print(f"Failed to save memory to Delta: {e}")

    def clear(self) -> None:
        self.messages = []
        try:
            self.spark.sql(f"DELETE FROM {self.table_name} WHERE session_id = '{self.session_id}'")
        except Exception:
            pass

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Factory function required by RunnableWithMessageHistory.
    """
    spark = SparkSession.builder.getOrCreate()
    # In production, get table name from config
    return DeltaChatMessageHistory(session_id, spark, "shopsphere_dev.genai_core.chat_memory")

# --- Wiring it to the Agent ---
# Assuming `agent_executor` is the object we created in Lesson 9
# 
# agent_with_chat_history = RunnableWithMessageHistory(
#     agent_executor,
#     get_session_history, # Factory function
#     input_messages_key="input", # Matches the prompt variable in Lesson 9
#     history_messages_key="chat_history", # Matches the placeholder in Lesson 9
# )
# 
# To invoke:
# response = agent_with_chat_history.invoke(
#     {"input": "What is my name?"},
#     config={"configurable": {"session_id": "user_john_123"}} # MUST pass session_id
# )
