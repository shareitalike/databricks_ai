import mlflow
from shopsphere_genai.config.core import ShopSphereGenAIConfig
from shopsphere_genai.agent.omni_agent import ShopSphereOmniAgent

# Initialize the config and agent
config = ShopSphereGenAIConfig.from_env("dev")
omni_agent = ShopSphereOmniAgent(config)

# MLflow Models-from-Code requirement:
# We must explicitly tell MLflow which Python object to use for inference when the model is deployed.
mlflow.models.set_model(omni_agent.agent_executor)
