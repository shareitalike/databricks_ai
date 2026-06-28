from pyspark.sql import SparkSession
from pyspark.sql.functions import expr, col, md5
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class EmbeddingGenerator:
    """
    Generates high-dimensional vector embeddings for text chunks using
    Databricks Foundation Model APIs (Mosaic AI).
    """
    def __init__(self, spark: SparkSession, config: ShopSphereGenAIConfig):
        self.spark = spark
        self.config = config
        self.pre_gold_table = f"{self.config.catalog_name}.{self.config.schema_name}.pre_gold_chunks"
        self.gold_table = f"{self.config.catalog_name}.{self.config.schema_name}.gold_document_vectors"

    def generate_embeddings(self):
        print(f"Generating embeddings using endpoint: {self.config.embedding_model_endpoint}")
        
        df = self.spark.read.table(self.pre_gold_table)
        
        # Create a unique ID for each chunk. Essential for Vector DB Sync.
        df_with_id = df.withColumn("chunk_id", md5(col("chunk_content")))
        
        # Use ai_query to call the serving endpoint asynchronously across the cluster.
        # This is massively faster and more stable than custom Python threading.
        # Note: We version the column name based on the model.
        embedding_expr = f"ai_query('{self.config.embedding_model_endpoint}', chunk_content)"
        
        df_embedded = df_with_id.withColumn("embedding_vector", expr(embedding_expr))
        
        # Write to Gold Delta Table
        # This table will be the source for our Vector Search Index.
        (df_embedded.write
         .format("delta")
         .mode("overwrite")
         .option("delta.enableChangeDataFeed", "true") # CRITICAL: Required for Vector Search Sync
         .saveAsTable(self.gold_table)
        )
        
        print(f"Embeddings generated and saved to {self.gold_table}")
        return df_embedded
