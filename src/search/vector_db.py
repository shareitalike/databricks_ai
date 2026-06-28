from databricks.vector_search.client import VectorSearchClient
import time
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class VectorDBManager:
    """
    Manages the provisioning and synchronization of Databricks Vector Search indices.
    """
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        # The VSC client uses your underlying Databricks workspace credentials
        self.vsc = VectorSearchClient()
        self.endpoint_name = self.config.vector_search_endpoint_name
        self.source_table = f"{self.config.catalog_name}.{self.config.schema_name}.gold_document_vectors"
        self.index_name = f"{self.config.catalog_name}.{self.config.schema_name}.document_vs_index"

    def setup_endpoint(self):
        """Creates the serverless compute endpoint if it doesn't exist."""
        endpoints = [e['name'] for e in self.vsc.list_endpoints().get("endpoints", [])]
        
        if self.endpoint_name not in endpoints:
            print(f"Creating Vector Search endpoint: {self.endpoint_name}. This takes a few minutes...")
            self.vsc.create_endpoint(name=self.endpoint_name, endpoint_type="STANDARD")
            
            # Wait for endpoint to be ready
            while True:
                status = self.vsc.get_endpoint(self.endpoint_name)["endpoint_status"]["state"]
                if status == "ONLINE":
                    print("Endpoint is ONLINE.")
                    break
                print(f"Status: {status}. Waiting 30s...")
                time.sleep(30)
        else:
            print(f"Endpoint {self.endpoint_name} already exists.")

    def create_or_sync_index(self):
        """Creates the Delta sync index or triggers a sync if it exists."""
        indexes = [i['name'] for i in self.vsc.list_indexes(self.endpoint_name).get("vector_indexes", [])]
        
        if self.index_name not in indexes:
            print(f"Creating Delta Sync Index: {self.index_name}")
            self.vsc.create_delta_sync_index(
                endpoint_name=self.endpoint_name,
                source_table_name=self.source_table,
                index_name=self.index_name,
                pipeline_type="TRIGGERED", # Cost-effective for batch loads
                primary_key="chunk_id",
                embedding_dimension=1024, # Must match your embedding model (BGE-large is 1024)
                embedding_vector_column="embedding_vector",
                # We can sync extra columns for filtering during retrieval!
                sync_source_metadata=True 
            )
        else:
            print(f"Triggering sync for existing index: {self.index_name}")
            index = self.vsc.get_index(self.endpoint_name, self.index_name)
            index.sync()
            
        print("Vector Database sync initiated.")
