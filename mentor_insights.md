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
