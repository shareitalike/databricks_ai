# Enterprise AI Engineering - Interview Question Bank

Use this to prepare for Staff/Principal level AI and Data Engineering interviews.

## 1. System Design & Architecture
*   **Q: "Design an AI system that allows our sales team to query their commissions. The data is in Snowflake."**
    *   *Look for:* Mentions Text-to-SQL Agent. Critically, mentions Row-Level Security (RLS) so Sales Rep A cannot see Sales Rep B's commissions. Mentions using a Service Principal for the Agent.
*   **Q: "We built a RAG system but users complain it takes 15 seconds to answer. How do you optimize it?"**
    *   *Look for:* Breaking down latency. Is it the Embedding generation? The Vector DB lookup? Or the LLM generation? Proposes streaming the LLM output (Tokens/sec). Proposes Semantic Caching (if question is asked frequently, return cached answer in 50ms).
*   **Q: "How would you handle a chat agent that needs to maintain context over a 2-hour conversation without exceeding token limits?"**
    *   *Look for:* Summary Memory. Storing raw logs in Delta, but running a background job to summarize every 10 turns and only passing the rolling summary to the LLM.

## 2. RAG & Search Internals
*   **Q: "Explain the tradeoff between chunk size and retrieval accuracy."**
    *   *Look for:* Small chunks = highly relevant, but might lose context (e.g., a pronoun referring to a noun in the previous chunk). Large chunks = better context, but dilutes the embedding vector and increases token cost. Mention chunk overlap.
*   **Q: "What is 'Lost in the Middle' and how do you fix it?"**
    *   *Look for:* LLMs pay attention to the beginning and end of a prompt, but ignore the middle. Fix: Use a Reranker model (Cross-Encoder) to ensure the absolute most relevant chunk is placed at the very top or bottom of the context window.

## 3. LLMOps & Evaluation
*   **Q: "How do you test an LLM application before deploying to production?"**
    *   *Look for:* Rejecting manual testing. Implementing MLflow Evaluate with a Golden Dataset. Using LLM-as-a-Judge to measure semantic correctness and retrieval relevance. Establishing baseline metrics in CI/CD.
*   **Q: "Our production model's accuracy dropped over the last month. How do you debug this?"**
    *   *Look for:* Checking the Inference Tables. Looking at data drift in the user questions (are they asking about a new product the vector DB doesn't have?). Running the failing traces through the LLM Judge to identify if the Retriever failed or the Generator failed.

## 4. Security & Governance
*   **Q: "How do you protect a RAG application from Prompt Injection?"**
    *   *Look for:* Using an Input Guardrail model (like Llama Guard) deployed in front of the main agent. Implementing strict least-privilege access for the Agent's database tools.
*   **Q: "A user asks the bot to summarize a highly confidential document. How do we ensure they only see it if they have clearance?"**
    *   *Look for:* Identity pass-through. The user's OAuth token must be passed to the Vector Database, which must apply Unity Catalog Row-Level Security filters before returning any text chunks to the LLM.

## 5. Databricks Specifics
*   **Q: "Why use Databricks Vector Search instead of a standalone DB like Pinecone?"**
    *   *Look for:* Unity Catalog integration. Standalone DBs require you to manually sync data and manage two separate governance models. Databricks Vector Search automatically syncs from Delta tables and inherits UC permissions natively.
*   **Q: "What is the benefit of registering Tools as Unity Catalog Functions?"**
    *   *Look for:* Reusability across teams, central audit logging of tool execution, and the ability to write tools in SQL or Python while running them on Serverless compute.
