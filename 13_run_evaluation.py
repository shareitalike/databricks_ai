# Databricks Notebook Execution Script - Automated Evaluation (Lesson 15)
# Run this cell to evaluate the Omni-Agent against a golden dataset!

import sys
import os
import importlib
import pandas as pd

# 1. Ensure Python can find our 'src' folder
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

from shopsphere_genai.config.core import ShopSphereGenAIConfig
from shopsphere_genai.agent.omni_agent import ShopSphereOmniAgent
from shopsphere_genai.evaluation.evaluator import Benchmarker

# 2. Configure Authentication
os.environ["DATABRICKS_SQL_HTTP_PATH"] = "/sql/1.0/warehouses/0882de12737c4773"
try:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    token = context.apiToken().get()
    host = context.apiUrl().get()
    os.environ["DATABRICKS_TOKEN"] = token
    os.environ["DATABRICKS_HOST"] = host
except Exception as e:
    print(f"Could not auto-retrieve credentials: {e}")

# 3. Initialize Config and Agent
config = ShopSphereGenAIConfig.from_env("dev")
omni_agent = ShopSphereOmniAgent(config)

# 4. Create an MLflow-compatible wrapper for our agent
# MLflow passes a Pandas DataFrame of inputs.
def mlflow_agent_wrapper(inputs: pd.DataFrame) -> list:
    answers = []
    # MLflow expects the input column to be named 'inputs'
    for question in inputs["inputs"]:
        try:
            # We use a static thread_id so memory doesn't bleed across eval questions
            ans = omni_agent.invoke(question, thread_id="eval_thread")
            answers.append(ans)
        except Exception as e:
            answers.append(f"Error: {str(e)}")
    return answers

# 5. Initialize the Benchmarker
# We save evaluation results to a dedicated experiment
EXPERIMENT_PATH = "/Users/alvigeorge3@gmail.com/Agent_Evaluations"
benchmarker = Benchmarker(EXPERIMENT_PATH)

# 6. Define our Golden Dataset
# In a real enterprise, this is hundreds of rows loaded from a Delta Table.
golden_dataset = pd.DataFrame({
    "inputs": [
        "What is the return policy for handling returns without a receipt?",
        "Can you check if SKU-8899 is in stock anywhere?"
    ],
    "ground_truth": [
        "Returns without a receipt are generally not permitted. However, you can return items within 30 days of purchase for a full refund if you have proof of purchase.",
        "SKU-8899 is not found in the inventory database."
    ]
})

print("\n=======================================================")
print(f"⚖️ BEGINNING OMNI-AGENT EVALUATION on {len(golden_dataset)} questions")
print("=======================================================\n")

# 7. Run the MLflow evaluation!
try:
    results = benchmarker.run_evaluation(mlflow_agent_wrapper)
    print("\n✅ Done! Go to Experiments -> Agent_Evaluations in the Databricks UI to inspect the results!")
except Exception as e:
    print(f"\n❌ Evaluation Failed: {e}")
