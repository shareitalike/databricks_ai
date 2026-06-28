# Lesson 5: Embedding Generation & Versioning

We have our normalized, chunked text (1 row = 1 chunk). Now, we need to convert these text chunks into dense vectors (numbers) so the machine can calculate semantic similarity.

## 1. Business Context

**Who requested this?**
The AI Platform Team.

**Why?**
A computer doesn't know that "coffee maker" and "espresso machine" are related. But in vector space, the numbers representing those words are very close together. We need embeddings to enable semantic search.

**Business Impact**
Allows users to search by *concept* rather than exact keyword matches.

**Customer Problem**
"I searched for 'shoes' and got nothing because the database only had the word 'sneakers'."

**ROI & Metrics**
*   **Search Recall:** Increase from 40% (keyword) to 90% (semantic).

---

## 2. Simple Analogy

Imagine a giant map of a city (Vector Space).
Every concept in the world gets assigned a GPS coordinate (an Embedding).
"King" and "Queen" live on the same street.
"Coffee" and "Espresso" are next-door neighbors.
"Coffee" and "Tractor" live in entirely different states.
When a user asks a question, we turn their question into a GPS coordinate and find the closest paragraphs (chunks) on the map.

---

## 3. First Principles

*   **What:** Converting text into high-dimensional float arrays (e.g., 1024 dimensions).
*   **Why:** To perform mathematical similarity searches (Cosine Similarity).
*   **How:** Passing the chunked text through an Embedding Model (like BGE, OpenAI `text-embedding-3`, or Cohere).
*   **When:** The final step before syncing to a Vector Database.
*   **Tradeoffs:** Large dimension models (e.g., 3072 dims) capture incredible nuance but require massive storage and memory for the vector database. Small models (e.g., 384 dims) are cheap but less accurate.
*   **Failure Scenarios:** Model drift. The embedding model is updated by the provider, changing the "GPS coordinates." You cannot mix vectors from V1 of a model with vectors from V2.

---

## 4. Internal Working

1.  **Input:** A string: "The espresso machine has a 1-year warranty."
2.  **Tokenization:** The model breaks it into sub-words.
3.  **Neural Network:** The tokens pass through a transformer encoder.
4.  **Pooling:** The final hidden states are averaged (mean pooling) to represent the entire sentence.
5.  **Output:** An array `[0.012, -0.443, 0.991, ...]` of size N.

---

## 5. Databricks Implementation

We have two choices in Databricks:
1.  **Let Vector Search do it (Managed Embeddings):** Databricks Vector Search can automatically compute embeddings in the background as Delta tables update.
2.  **Compute them ourselves (Self-Managed):** We compute the embeddings in PySpark using the `ai_query` function and store the `array<float>` in Delta directly.

*We will use the Self-Managed approach.* Why? Because it teaches you how to handle high-throughput API calls from PySpark, and allows you to version the embeddings in Delta Lake.

---

## 6. Production Code

We will create `src/shopsphere_genai/embeddings/embedder.py`.

*(See the actual file in your workspace for the code)*

---

## 7. Explain Every Line of Code

Looking at `src/shopsphere_genai/embeddings/embedder.py`:

*   `from pyspark.sql.functions import expr`: We use Databricks' built-in `ai_query` SQL function, which is designed to call Mosaic AI Model Serving endpoints efficiently from PySpark.
*   `endpoint = config.embedding_model_endpoint`: We are calling the model hosted on Databricks (e.g., `databricks-bge-large-en`). No data leaves our VPC.
*   `expr(f"ai_query('{endpoint}', chunk_content)")`: This is magic. Databricks automatically batches these rows and sends them to the serving endpoint asynchronously. You don't have to write complex Python `asyncio` or thread pools.
*   `df.withColumn("embedding_v1", ...)`: Notice we named the column `embedding_v1`. **This is crucial for versioning.**

---

## 8. Architecture Diagram

```mermaid
graph TD
    A[(Pre-Gold Table \n Chunks)] --> B(Spark Job)
    B --> C{Databricks ai_query()}
    C <-->|Batch API Calls| D[Mosaic AI \n Embedding Endpoint]
    B --> E[(Gold Delta Table \n Chunks + Vectors)]
```

---

## 9. Production Problems

**The Problem: Rate Limiting and API Timeouts**
If you have 10 million chunks and try to embed them all via an external API (like OpenAI), you will get HTTP 429 Too Many Requests, and the Spark job will fail.
*   **The Senior Solution:** 
    1. By using Databricks Foundation Model APIs via `ai_query`, Databricks handles the underlying retry logic and batching.
    2. If using an external API, you *must* write a Pandas UDF with exponential backoff (e.g., using the `tenacity` Python library) and control the partition size to limit concurrency.

**The Problem: The "Mixed Vectors" Disaster**
A Junior engineer decides to upgrade the model from `bge-small` to `bge-large`. They update the config and run the pipeline. Now, half the Delta table has 384-dimension vectors, and half has 1024-dimension vectors. The Vector Database crashes.
*   **The Senior Solution:** Embeddings are immutable relative to their model. If you change models, you must compute a *new column* (e.g., `embedding_v2`) for the entire table.

---

## 10. Design Decisions

**Why store Embeddings in a Delta Table before syncing to Vector DB?**
*   **Cost:** If the Vector DB crashes or needs to be rebuilt, you don't want to pay $10,000 to re-compute all embeddings from the LLM provider. You just re-sync the existing vectors from Delta.
*   **Time Travel:** Delta allows you to roll back if a batch of bad embeddings corrupts the dataset.

---

## 11. Cost Engineering

*   **Embedding Costs:** Typically charged per 1M tokens. Open-source models (like BGE on Databricks) are drastically cheaper than proprietary ones.
*   **Vector DB Storage:** Storing 100 million vectors of 1536 dimensions requires significant RAM in the Vector DB. 
*   **Optimization (Quantization):** Advanced teams use Binary Quantization (converting floats to 1s and 0s) or Scalar Quantization (converting 32-bit floats to 8-bit ints) to reduce Vector DB memory costs by 4x to 32x with minimal accuracy loss.

---

## 12. Enterprise Constraints

**Requirement:** Disaster Recovery (RTO < 4 hours).
*   **Redesign impact:** If our primary region (us-east-1) goes down, the Vector Search index is lost. Because we stored the `array<float>` directly in our Gold Delta table, recovering in us-west-2 simply requires spinning up a new Vector Index and pointing it at the replicated Delta table. Syncing takes minutes. Re-embedding would take days.

---

## 13. Architecture Review (Principal Engineer Defense)

**Principal:** "Why not just use Databricks Managed Embeddings where you point the Vector Index at the text column and it embeds it for you?"
**You:** "Managed Embeddings are fantastic for rapid prototyping and low-maintenance pipelines. However, in our Enterprise platform, we need absolute control over the vector lifecycle. By computing them in PySpark and storing them in Delta, we enable A/B testing of different embedding models simultaneously (`embedding_bge` vs `embedding_gte`), and we secure our DR strategy by holding the compiled vectors in our data lake."

---

## 14. Refactoring Journey

*   **Version 1:** Looping through rows and calling `requests.post()` to an API. Takes 5 days.
*   **Version 2:** Using a ThreadPoolExecutor in Python. Still fragile.
*   **Version 3 (Our Code):** Utilizing Databricks `ai_query` for native, optimized, high-throughput distributed inference directly in the Spark engine.

---

## 15. Interview Preparation (Senior Level)

1.  **Architecture:** "Why should you store your computed embeddings in a Data Lake before pushing them to a Vector Database?"
2.  **System Design:** "You need to migrate from OpenAI embeddings to an open-source model. How do you execute this migration in production with zero downtime for the users?"
3.  **Tradeoffs:** "Compare high-dimensional embeddings vs low-dimensional embeddings regarding search accuracy and infrastructure cost."
4.  **Debugging:** "Your Spark job calculating embeddings fails halfway through due to an API outage. How do you design the pipeline to resume without re-computing the first half?" (Answer: Checkpoint the Delta writes, or do a left anti-join against the target table before computing).
5.  **Coding:** "Write the PySpark SQL expression to call a Databricks serving endpoint."

---

## 16. Resume Thinking

**How to talk about this project:**
*   **Bullet:** *Architected a robust, disaster-recovery-ready embedding pipeline using Databricks `ai_query`, processing millions of text chunks while preventing vendor lock-in through Delta Lake vector versioning.*
