from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import AutoCaptureConfigInput
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class InferenceMonitor:
    """
    Enables Inference Tables on an Endpoint and provides analysis jobs.
    """
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        self.w = WorkspaceClient()
        self.endpoint_name = f"{self.config.project_name}_endpoint_prod"

    def enable_inference_tables(self):
        """
        Updates the serving endpoint to automatically log all payloads to a Delta Table.
        """
        print(f"Enabling Inference Tables for: {self.endpoint_name}")
        
        # Define where the logs should be stored in Unity Catalog
        capture_config = AutoCaptureConfigInput(
            catalog_name=self.config.catalog_name,
            schema_name="monitoring",
            table_name_prefix="agent_logs",
            enabled=True
        )
        
        # Update the endpoint. Note: In reality, you pass this config 
        # during the initial Endpoint creation or update in deploy.py.
        # This is isolated here for educational clarity.
        try:
            # self.w.serving_endpoints.update_config(...)
            print("Successfully configured Auto Capture. Logs will appear in: "
                  f"{self.config.catalog_name}.monitoring.agent_logs_{self.endpoint_name}")
        except Exception as e:
            print(f"Failed to enable capture: {e}")

    def run_nightly_judge_job(self, spark):
        """
        A mock of a Spark job that would run every night via Databricks Workflows.
        It reads yesterday's logs and runs LLM-as-a-Judge to find failing conversations.
        """
        table_name = f"{self.config.catalog_name}.monitoring.agent_logs_{self.endpoint_name}"
        
        print(f"Running Nightly Analysis on {table_name}")
        
        # 1. Read yesterday's logs
        # df = spark.sql(f"""
        #     SELECT request_metadata.client_request_id, 
        #            request_payload, 
        #            response_payload 
        #     FROM {table_name}
        #     WHERE to_date(timestamp) = current_date() - 1
        # """)
        
        # 2. Extract inputs and outputs from the raw JSON
        # (Requires Spark JSON parsing functions)
        
        # 3. Pass to mlflow.evaluate() using the techniques from Lesson 16!
        # ...
        
        print("Analysis complete. Check the 'Production Monitoring' MLflow experiment for results.")

# Example Usage
# config = ShopSphereGenAIConfig.from_env("prod")
# monitor = InferenceMonitor(config)
# monitor.enable_inference_tables()
