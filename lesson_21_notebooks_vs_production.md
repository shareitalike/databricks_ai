# 🐍 Notebooks vs. Production: Managing Python Dependencies

You asked a fantastic engineering question: *"In the notebooks, we had to do weird `%pip install` hacks in a specific order. If we run direct Python files in production, how is this handled?"*

The short answer: **In production, you never use `%pip install`. You use a locked `requirements.txt` file and isolated environments (like Docker or Databricks Job Clusters).**

Here is the exact breakdown of why we did what we did in the notebooks, and how you convert it for a real production deployment.

---

## 1. The "Notebook Problem"
When you run a Databricks Notebook, you are attaching to a **Shared, Pre-configured Cluster**. 
Databricks pre-installs hundreds of libraries (Pandas, PySpark, MLflow, LangChain v0.1, etc.) into the environment before you even write your first line of code. This is called the *Databricks Machine Learning Runtime*.

**Why did we have to run pip commands in a specific order?**
Because the pre-installed libraries conflicted with the bleeding-edge tools we needed. 
1. The cluster came with an old version of `langchain`.
2. We needed the brand new `databricks-langchain` library.
3. We needed a very specific version of `langgraph`.
If we just ran `%pip install langgraph databricks-langchain`, pip would get confused, downgrade `langgraph` to satisfy an old dependency, and crash our agent. We had to force pip to install them sequentially and then restart the Python kernel to clear the old libraries from memory.

---

## 2. The "Production Solution" (Direct Python)
In real production, you do not run code in shared, pre-configured notebooks. You run **Direct Python Files** in a completely clean, isolated environment.

### How it works in Production:
Instead of `%pip` commands at the top of your files, you maintain a single file at the root of your project called `requirements.txt` (or `pyproject.toml` / `poetry.lock`).

**Example `requirements.txt`:**
```text
langchain==0.3.13
langchain-core==0.3.28
langgraph==0.2.60
langchain-community==0.3.13
databricks-langchain==0.1.0
databricks-sql-connector==3.3.0
```
Notice there are no commands, just exact version numbers.

### Where does this run?
When you deploy to production, you use **Databricks Asset Bundles (DABs)** or **Databricks Workflows (Jobs)**.

1. **Job Compute (Not Interactive Compute):** When a Databricks Job starts, it spins up a brand-new, completely blank virtual machine.
2. It looks at your `requirements.txt` file.
3. It installs exactly those libraries *simultaneously* using a proper dependency resolver.
4. It executes your direct Python file (e.g., `python src/shopsphere_genai/agent/omni_agent.py`).
5. When the job is done, it destroys the virtual machine.

Because the machine starts completely blank, there are no pre-installed library conflicts!

---

## 3. How to Convert Notebooks to Production

If you want to take the 18 files we just built and run them in a standard Python application (like an AWS EC2 instance, a Docker container, or a FastAPI web server), here is exactly what you do:

### A. Remove Notebook-Specific Magic
Delete all lines that start with `%pip` or `dbutils`. `dbutils` is a Databricks-only utility. 

*Instead of this:*
```python
%pip install langgraph==0.2.60
context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
token = context.apiToken().get()
```

*Do this (Standard Python):*
```python
import os
# The system administrator sets these environment variables on the production server
token = os.environ.get("DATABRICKS_TOKEN")
host = os.environ.get("DATABRICKS_HOST")
```

### B. Use an Entrypoint Script (e.g., `main.py`)
In a notebook, you click "Run Cell". In direct Python, you need a `main.py` that imports your code and triggers the execution.

```python
# main.py
from shopsphere_genai.config.core import ShopSphereGenAIConfig
from shopsphere_genai.agent.omni_agent import ShopSphereOmniAgent

if __name__ == "__main__":
    config = ShopSphereGenAIConfig.from_env("prod")
    agent = ShopSphereOmniAgent(config)
    
    # Run a continuous loop in the terminal
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        print("Agent:", agent.invoke(user_input))
```

### C. Run it from the Terminal
Open your standard terminal (Bash/PowerShell), activate your virtual environment, and run:
```bash
pip install -r requirements.txt
python main.py
```

## Summary for Interviews
If an interviewer asks: *"How do you handle dependency management when moving from Databricks Notebooks to Production?"*

You say:
> *"Notebooks are great for interactive development, but they suffer from state pollution and pre-installed dependency conflicts, which is why you often see complex `%pip` workarounds. For production, I strictly use **Databricks Workflows with Job Compute**. I package my code into a standard Python wheel or repository, define my exact dependencies in a `requirements.txt`, and let the Job cluster spin up a clean, isolated environment to execute the direct Python files."*
