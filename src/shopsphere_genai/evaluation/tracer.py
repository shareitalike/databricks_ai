import mlflow
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class ShopSphereTracer:
    """
    Initializes and manages MLflow Tracing for the AI Agent.
    Must be initialized before any LangChain objects are created.
    """
    def __init__(self, config: ShopSphereGenAIConfig, experiment_name: str):
        self.config = config
        self.experiment_name = experiment_name

    def setup_tracing(self):
        """
        Enables LangChain autologging and sets the MLflow experiment.
        """
        print(f"Setting up MLflow Tracing for experiment: {self.experiment_name}")
        
        # 1. Set the destination for the traces
        # If the experiment doesn't exist, MLflow creates it.
        mlflow.set_experiment(self.experiment_name)
        
        # 2. Enable Autologging
        # We call autolog with no arguments to use the safe, default tracing behavior
        # across all recent MLflow versions.
        mlflow.langchain.autolog()
        print("LangChain MLflow Tracing is ACTIVE.")

    def execute_with_custom_span(self, agent_function, user_input: str, user_id: str):
        """
        Demonstrates how to wrap an agent execution in a manual custom span
        to add business metadata (like user_id) that LangChain doesn't know about.
        """
        # start_span creates a new root (or child) span in the MLflow UI
        with mlflow.start_span(name="Agent_Execution_Wrapper") as span:
            
            # Add searchable attributes to the trace
            span.set_attributes({
                "user_id": user_id,
                "project": self.config.project_name,
                "environment": "production"
            })
            
            try:
                # Execute the actual agent
                # Because autolog is on, this execution will automatically attach 
                # as child spans under our "Agent_Execution_Wrapper" span.
                result = agent_function(user_input)
                
                # Log success
                span.set_status("OK")
                return result
                
            except Exception as e:
                # Log failure so we can easily filter for errors in the UI
                span.set_status("ERROR")
                span.set_attributes({"error_message": str(e)})
                raise e

# Example Usage:
# config = ShopSphereGenAIConfig.from_env("dev")
# tracer = ShopSphereTracer(config, "/Shared/ShopSphere/Agent_Traces")
# tracer.setup_tracing()
# 
# # Now import and run your agent. It will be traced automatically!
# # from agent.graph import app
# # result = tracer.execute_with_custom_span(lambda x: app.invoke(x), {"messages": [...]}, "user_123")
