# Lesson 23: The Capstone Architecture Review

Congratulations. We have completed the ShopSphere AI Copilot project. We went from raw PDF manuals to a fully governed, traced, evaluated, and deployed Agentic system on Databricks.

This final lesson is the "Whiteboard Interview." If you can explain this architecture end-to-end, you are a Senior AI Engineer.

## The End-to-End Enterprise AI Architecture

Let's trace the lifecycle of a single user question:
*"Hi, I'm a store manager in NY. Check inventory for SKU-123. If it's out of stock, what is the policy for ordering a replacement part?"*

### Phase 1 & 2: The Data Foundation & Search (The Memory)
1.  **Ingestion:** The manufacturer uploaded the replacement policy PDF to an AWS S3 bucket. Databricks **Auto Loader** incrementally ingested the raw binary into a Unity Catalog (UC) Volume.
2.  **Processing:** A PySpark **Pandas UDF** parsed the PDF in parallel across a cluster, extracting the text.
3.  **Chunking & Embedding:** We used LangChain recursive chunking to break the text, and passed it to the `databricks-bge-large-en` Foundation Model Endpoint to generate vectors.
4.  **Storage:** The vectors were stored in a Delta Table with Change Data Feed enabled.
5.  **Indexing:** A Databricks **Vector Search Endpoint** continuously synced the Delta table into an HNSW index.

### Phase 3: The Agent (The Brain)
6.  **User Input:** The NY store manager types the question into the UI. The UI assigns a `session_id` and a `request_id`.
7.  **Input Guardrail:** The Databricks Serving Endpoint intercepts the question and passes it to **Llama Guard**. Llama Guard returns "SAFE".
8.  **Orchestration (LangGraph):** The question hits our compiled LangGraph State Machine. The graph fetches the user's chat history from the **Delta Memory Table** using the `session_id`.
9.  **Tool Selection (Llama 3 70B):** The LLM reads its System Prompt and realizes it needs to use a tool to check inventory.
10. **Governance (Unity Catalog):** The Agent (running as a Service Principal) attempts to call the `check_inventory(sku="SKU-123")` UC Function. Unity Catalog checks if the Service Principal has `EXECUTE` privileges. It does.
11. **Tool Execution (Serverless SQL):** The UC function executes against the Gold Sales table, returning "Out of stock".
12. **Vector Retrieval:** The LLM realizes it now needs the replacement policy. It calls the `document_retriever` tool.
13. **Row-Level Security:** The Vector DB evaluates a Unity Catalog Row Filter. Because the user is in NY, it only searches documents tagged for the NA region. It returns the policy.
14. **Synthesis:** The LLM combines the "Out of stock" data and the retrieved policy to formulate a helpful final answer.

### Phase 4 & 5: LLMOps (The Nerves)
15. **Output Guardrail:** The final answer is scanned for PII. It is clean.
16. **Telemetry (MLflow):** The entire execution (LLM prompts, tool latency, context retrieved) is automatically logged as a hierarchical Trace to MLflow.
17. **Online Monitoring (Inference Tables):** The raw JSON payload of the request and response is asynchronously dumped into the `monitoring.agent_logs` Delta table.
18. **Evaluation:** That night, a scheduled Spark job reads the Inference Table and runs **MLflow Evaluate** (using a secondary Judge LLM) to score the interaction for accuracy and toxicity, updating the AI team's dashboard.

---

## Senior Engineering Mindset

What makes this architecture "Senior"?
*   **Zero-Trust Security:** At no point did Python code dictate access rights. Unity Catalog Row-Level Security handled it.
*   **Modularity:** The Vector Database, the LLM, and the Tools are independent components connected via standard APIs. We can swap Llama 3 for GPT-5 tomorrow with a 1-line config change.
*   **Observability:** If the agent fails, the MLflow Trace tells us exactly *why* it failed in seconds, not days.
*   **Stateless Scaling:** The serving endpoint has no local memory. It can scale from 0 to 1,000 containers instantly without losing user context.

---

## Final Words

You now possess the blueprint for enterprise AI. 
Do not be intimidated by the hype. AI Engineering is just Software Engineering with a non-deterministic compiler. Apply the exact same rigor (CI/CD, Monitoring, Governance, Modularity) that you apply to traditional data pipelines, and you will build indestructible systems.

*The AI Engineering Bootcamp curriculum is complete.*
