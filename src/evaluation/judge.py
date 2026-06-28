import pandas as pd
import mlflow
from typing import Callable

# Important: This requires mlflow >= 2.8.0
try:
    from mlflow.metrics.genai import answer_correctness, relevance
except ImportError:
    print("Warning: mlflow.metrics.genai requires a newer version of MLflow.")
    
class LLMJudgeEvaluator:
    """
    Executes automated batch evaluation using an LLM to semantically judge the outputs.
    """
    def __init__(self, experiment_name: str, judge_endpoint: str):
        self.experiment_name = experiment_name
        self.judge_endpoint = f"endpoints:/{judge_endpoint}"
        mlflow.set_experiment(self.experiment_name)

    def run_judged_evaluation(self, agent_function: Callable[[str], str]):
        print(f"Starting LLM-as-a-Judge Eval. Judge: {self.judge_endpoint}")
        
        # 1. Load Dataset (Requires inputs, ground_truth, and optionally context)
        eval_data = pd.DataFrame({
            "inputs": ["What is the warranty on the blender?"],
            "ground_truth": ["The blender has a 2-year warranty."],
            # If evaluating RAG, you must provide the retrieved context 
            # so the judge can score 'relevance' and 'faithfulness'
            "context": ["ShopSphere Blender Warranty Policy: 2 years on parts."] 
        })
        
        # 2. Configure the GenAI Metrics
        # These metrics will prompt the judge_endpoint behind the scenes.
        try:
            correctness_metric = answer_correctness(model=self.judge_endpoint)
            relevance_metric = relevance(model=self.judge_endpoint)
        except NameError:
            print("MLflow GenAI metrics not loaded. Skipping...")
            return None

        # 3. Start MLflow Run
        with mlflow.start_run(run_name="LLM_Judge_Benchmark"):
            
            # Execute Evaluation with Extra Metrics
            results = mlflow.evaluate(
                model=agent_function,
                data=eval_data,
                model_type="question-answering",
                # The crucial addition: passing our LLM Judge metrics
                extra_metrics=[correctness_metric, relevance_metric] 
            )
            
            print("\n--- LLM Judge Evaluation Complete ---")
            for metric, value in results.metrics.items():
                print(f" - {metric}: {value}")
                
            return results

# Example Usage:
# def mock_agent(inputs): return "Blenders have a two year warranty."
# evaluator = LLMJudgeEvaluator("/Shared/ShopSphere/Agent_Evaluations", "databricks-meta-llama-3-70b-instruct")
# evaluator.run_judged_evaluation(mock_agent)
