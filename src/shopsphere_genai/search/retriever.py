from databricks.vector_search.client import VectorSearchClient
from shopsphere_genai.config.core import ShopSphereGenAIConfig
from typing import List, Dict

class ShopSphereRetriever:
    """
    Executes similarity searches against the Databricks Vector Search Index.
    """
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        self.vsc = VectorSearchClient()
        self.index_name = f"{self.config.catalog_name}.{self.config.schema_name}.document_vs_index"
        
        # Get the index object once during initialization
        self.index = self.vsc.get_index(
            endpoint_name=self.config.vector_search_endpoint_name,
            index_name=self.index_name
        )

    def retrieve_context(self, query: str, top_k: int = 5, filters: dict = None) -> List[Dict]:
        """
        Takes a natural language query and returns the top_k most relevant document chunks.
        """
        print(f"Executing Vector Search for query: '{query}'")
        
        try:
            # First, we must convert the natural language query into a vector!
            # We use the Databricks native MLflow client to call the embedding endpoint.
            import mlflow.deployments
            deploy_client = mlflow.deployments.get_deploy_client("databricks")
            
            embedding_response = deploy_client.predict(
                endpoint=self.config.embedding_model_endpoint,
                inputs={"inputs": [query]}
            )
            query_vector = embedding_response["data"][0]["embedding"]
            
            # Execute the similarity search using the generated vector
            results = self.index.similarity_search(
                query_vector=query_vector,
                columns=["chunk_content", "path"], # Request specific metadata back
                num_results=top_k,
                filters=filters # e.g., {"source_system": "Vendor_Portal"}
            )
            
            # The Databricks SDK returns a specific JSON structure.
            # We parse it into a clean list of dictionaries for easier downstream use.
            formatted_results = []
            
            # The result object contains a 'data_array' where each inner list represents a row.
            # The 'columns' array tells us the schema of the inner list.
            if 'result' in results and 'data_array' in results['result']:
                data_matrix = results['result']['data_array']
                for row in data_matrix:
                    # row[0] is chunk_content, row[1] is source_path, row[2] is the similarity score
                    formatted_results.append({
                        "text": row[0],
                        "source": row[1],
                        "score": row[2]
                    })
                    
            return formatted_results
            
        except Exception as e:
            print(f"Retrieval Error: {e}")
            return []

    def format_for_llm(self, retrieved_docs: List[Dict]) -> str:
        """
        Formats the retrieved dictionaries into a single string to inject into the LLM prompt.
        """
        context_string = ""
        for i, doc in enumerate(retrieved_docs):
            context_string += f"\n--- Document {i+1} ---\n"
            context_string += f"Source: {doc['source']}\n"
            context_string += f"Content: {doc['text']}\n"
        return context_string

# Example Usage:
# config = ShopSphereGenAIConfig.from_env("dev")
# retriever = ShopSphereRetriever(config)
# docs = retriever.retrieve_context("What is the return policy for the espresso machine?")
# context = retriever.format_for_llm(docs)
# print(context)
