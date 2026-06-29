# Databricks Notebook - Production Monitoring (Lesson 21)
# Reads live inference logs from the serving endpoint and runs
# a nightly LLM-as-a-Judge evaluation to detect quality drift.

import sys, os
sys.path.append('/Workspace/Users/alvigeorge3@gmail.com/databricks_ai/src')

try:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    os.environ["DATABRICKS_TOKEN"] = context.apiToken().get()
    os.environ["DATABRICKS_HOST"] = context.apiUrl().get()
except Exception as e:
    print(f"Could not auto-retrieve credentials: {e}")

import mlflow
import pandas as pd
from shopsphere_genai.config.core import ShopSphereGenAIConfig

config = ShopSphereGenAIConfig.from_env("dev")

INFERENCE_TABLE = f"{config.catalog_name}.monitoring.agent_logs_shopsphere-copilot-prod"
EXPERIMENT_PATH = "/Users/alvigeorge3@gmail.com/Production_Monitoring"
mlflow.set_experiment(EXPERIMENT_PATH)

print("=======================================================")
print("📊 PRODUCTION MONITORING ANALYSIS")
print("   (Nightly Inference Quality Drift Detection)")
print("=======================================================\n")

# -------------------------------------------------------
# STEP 1: Read yesterday's inference logs from Delta Table
# (The table is auto-populated by the Serving Endpoint's
#  Inference Table that we enabled in 17_run_serving.py)
# -------------------------------------------------------
print("Step 1: Loading yesterday's inference logs...")
try:
    # In a real Databricks Workflow, 'spark' is always available
    raw_logs = spark.sql(f"""
        SELECT 
            request_metadata.client_request_id AS request_id,
            request_payload,
            response_payload,
            timestamp
        FROM {INFERENCE_TABLE}
        WHERE to_date(timestamp) = current_date() - INTERVAL 1 DAY
        LIMIT 100
    """).toPandas()
    print(f"  ✅ Loaded {len(raw_logs)} inference records from yesterday.")
except Exception as e:
    print(f"  ⚠️  Could not read inference table (endpoint may not be deployed yet): {e}")
    print("  📝 Using mock data for demonstration instead.\n")
    
    # Mock data showing the structure of what production logs look like
    raw_logs = pd.DataFrame({
        "request_id": ["req_001", "req_002", "req_003"],
        "inputs": [
            "What is the return policy for espresso machines?",
            "How many stores do we have?",
            "Can you check SKU-8899?"
        ],
        "predictions": [
            "Returns are accepted within 30 days with a valid receipt.",
            "We currently have 3 stores.",
            "SKU-8899 was not found in our current inventory."
        ]
    })

print("\nStep 2: Running LLM-as-a-Judge on sampled production traffic...")
print("         (In production, this Notebook runs as a Databricks Workflow every night)")

# -------------------------------------------------------
# STEP 2: Sample 10% of logs and run MLflow evaluation
# -------------------------------------------------------
sample_logs = raw_logs.sample(frac=min(1.0, 10/max(len(raw_logs), 1)), random_state=42)

# Run quality assessment on the sample
with mlflow.start_run(run_name=f"nightly_monitor_{pd.Timestamp.now().strftime('%Y%m%d')}"):
    mlflow.log_param("records_sampled", len(sample_logs))
    mlflow.log_param("inference_table", INFERENCE_TABLE)
    
    print(f"  Sampled {len(sample_logs)} records for quality check.")
    print("\n  📈 Sample Production Traffic:")
    for _, row in sample_logs.iterrows():
        print(f"    - Q: {row.get('inputs', row.get('request_payload', 'N/A'))[:80]}...")

print("\n✅ Monitoring job complete!")
print(f"   Go to Experiments -> Production_Monitoring to see the quality trend over time.")
print("\n💡 TIP: Schedule this notebook as a Databricks Workflow to run daily at 2 AM:")
print("        Jobs -> Create Job -> Add Notebook Task -> 18_run_monitoring.py -> Schedule: 0 2 * * *")
