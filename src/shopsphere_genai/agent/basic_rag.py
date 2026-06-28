import mlflow.deployments
from langchain.prompts import PromptTemplate
from shopsphere_genai.config.core import ShopSphereGenAIConfig
from shopsphere_genai.search.retriever import ShopSphereRetriever

class BasicRAGChain:
    """
    Orchestrates the Retrieval-Augmented Generation process.
    Connects the custom Retriever to the Databricks LLM endpoint natively via MLflow.
    """
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        self.retriever = ShopSphereRetriever(config)
        
        # We use Databricks native MLflow client to avoid LangChain package conflicts
        self.deploy_client = mlflow.deployments.get_deploy_client("databricks")
        
        # Define the strict prompt template
        self.prompt_template = PromptTemplate.from_template(
            """You are a helpful assistant for ShopSphere retail employees.
            You must answer the user's question based ONLY on the provided context.
            If the context does not contain the answer, do not guess. Simply state: "I don't know based on the provided documents."
            
            CONTEXT:
            {context}
            
            USER QUESTION:
            {question}
            
            ANSWER:"""
        )

    def ask(self, query: str) -> dict:
        """
        Executes the full RAG pipeline and returns the answer with citations.
        """
        print(f"\n--- Processing Query: {query} ---")
        
        # 1. Retrieve Context
        docs = self.retriever.retrieve_context(query, top_k=3)
        
        if not docs:
            return {
                "answer": "I could not find any relevant documents in the system.",
                "citations": []
            }
            
        # 2. Format Context
        formatted_context = self.retriever.format_for_llm(docs)
        
        # 3. Assemble Prompt
        prompt = self.prompt_template.format(
            context=formatted_context,
            question=query
        )
        
        # 4. Invoke LLM via native MLflow
        print("Invoking LLM...")
        response = self.deploy_client.predict(
            endpoint=self.config.llm_endpoint,
            inputs={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 500
            }
        )
        answer = response["choices"][0]["message"]["content"]
        
        # 5. Assemble Citations for Trust
        # We use a set comprehension to remove duplicate source paths
        unique_sources = list({doc['source'] for doc in docs})
        
        return {
            "answer": answer,
            "citations": unique_sources
        }

# Example Usage:
# config = ShopSphereGenAIConfig.from_env("dev")
# rag = BasicRAGChain(config)
# result = rag.ask("How many days do customers have to return a broken espresso machine?")
# print(f"Answer:\n{result['answer']}")
# print(f"\nSources utilized: {result['citations']}")
