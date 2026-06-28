# Principal Engineer AI Insights Log

*A running log of mental models, analogies, and senior-level insights for transitioning from Data Engineering to AI Engineering.*

---

## Insight 1: The Mental Model of Generative AI (Deterministic vs. Probabilistic)

As a Data Engineer, you are used to **Deterministic Systems**. 
If you write `SELECT SUM(sales) FROM table`, you get the exact same number every single time. It is perfectly predictable.

Generative AI (Large Language Models or LLMs) is a **Probabilistic System**.
Think of an LLM like an incredibly well-read intern who has memorized the entire internet, but has a slight tendency to daydream. If you ask them a question, they don't look up a database row; they *guess* what the next word should be based on probability.

Because of this, AI Engineering is fundamentally about **Control**. 
Our job is to build a rigid, deterministic cage (using Python and Data Engineering guardrails) around this probabilistic intern so that they give us reliable, secure, and accurate answers every time.

## Insight 2: The Goal of the ShopSphere Project

Instead of building a simple script, we are building an Enterprise AI Copilot. 
When a store manager asks, "Check inventory for SKU-123. If out of stock, what is the replacement policy?", the AI must:
1. Understand the intent.
2. Query a SQL database deterministically to check inventory.
3. Perform a semantic Vector Search over unstructured PDF manuals to find the policy.
4. Ensure the user has the correct RBAC (Role-Based Access Control) to view that policy.
5. Synthesize the final answer securely.

## Insight 3: Auto Loader for Generative AI
AI models don't eat PDFs natively, they eat vectors. The ingestion pipeline must treat unstructured text files (PDFs) with the exact same incremental, event-driven rigor as structured JSON logs. Using Databricks Auto Loader ensures that when a new PDF lands in the bucket, it is processed exactly once, avoiding expensive re-computation of vectors later in the pipeline.

## Insight 4: The Databricks Python State Gotcha (`importlib.reload`)
When you are writing modular Python code in a Databricks Git Folder and executing it from a Databricks Notebook, the Python cluster caches your imported modules in memory. If you `git pull` a fix for `loader.py`, the Notebook will **not** see it automatically. Junior engineers will restart the entire cluster (wasting 5 minutes). Senior engineers use:
```python
import importlib
import shopsphere_genai.ingestion.loader as loader_module
importlib.reload(loader_module)
```
This forces the Python interpreter to hot-swap the new code from disk without dropping the cluster state!

## Insight 5: Why ingest PDFs into a Delta Table? (The Bronze Layer)
Junior engineers often write AI scripts that read PDFs directly from the S3 bucket/folder and parse them on the fly. This is a massive mistake at enterprise scale. We always ingest raw binaries into a Bronze Delta table first because:
1. **The Small File Problem:** Cloud storage (S3) is terrible at reading 100,000 tiny 1MB PDF files. It causes massive network overhead. Delta packs these binaries into optimized parquet files, allowing Spark to read them 100x faster.
2. **Lineage & Auditability:** A folder is a "dumb" filesystem. A Delta table lets you run `SELECT count(*) WHERE ingestion_timestamp = TODAY()` to audit exactly what arrived.
3. **Resilience:** If the AI text-parsing script crashes on PDF #49,999, you don't want to re-download 50,000 PDFs from the cloud bucket. The Bronze table acts as a secure, fast staging area so you can replay the parsing step instantly.
