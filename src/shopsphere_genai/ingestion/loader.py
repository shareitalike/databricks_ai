from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name, lit
from shopsphere_genai.config.core import ShopSphereGenAIConfig

class DocumentIngestor:
    """
    Handles the incremental streaming ingestion of raw documents (PDFs, JSON)
    from Unity Catalog Volumes into a Bronze Delta table.
    """
    def __init__(self, spark: SparkSession, config: ShopSphereGenAIConfig):
        self.spark = spark
        self.config = config
        
        # Define paths based on config
        self.volume_path = f"/Volumes/{self.config.catalog_name}/{self.config.schema_name}/{self.config.volume_name}"
        self.bronze_table_name = f"{self.config.catalog_name}.{self.config.schema_name}.bronze_raw_documents"
        self.checkpoint_path = f"/Volumes/{self.config.catalog_name}/{self.config.schema_name}/{self.config.volume_name}/_checkpoints/bronze_ingestion"

    def ingest_documents(self):
        """
        Starts the Auto Loader stream to ingest binary files.
        """
        print(f"Starting ingestion from: {self.volume_path}")
        
        # Read stream using Auto Loader (cloudFiles)
        df_stream = (
            self.spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "binaryFile")
            # For massive scale, useNotifications would be set to "true", 
            # but requires cloud infra setup (e.g. EventGrid/SQS)
            .option("cloudFiles.useNotifications", "false") 
            .option("pathGlobFilter", "*.pdf") # For this example, restricting to PDFs
            .load(self.volume_path)
        )
        
        # Add crucial audit metadata
        df_enriched = (
            df_stream
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("source_system", lit("Vendor_Portal"))
            # The 'binaryFile' format automatically gives us 'path', 'modificationTime', 'length', and 'content'
        )
        
        # Write stream to Delta Bronze table
        query = (
            df_enriched.writeStream
            .format("delta")
            .option("checkpointLocation", self.checkpoint_path)
            .outputMode("append")
            # Using AvailableNow allows it to act as an incremental batch job to save costs
            .trigger(availableNow=True) 
            .table(self.bronze_table_name)
        )
        
        print(f"Stream initialized. Writing to {self.bronze_table_name}")
        return query

# Example Usage:
# spark = SparkSession.builder.getOrCreate()
# config = ShopSphereGenAIConfig.from_env("dev")
# ingestor = DocumentIngestor(spark, config)
# query = ingestor.ingest_documents()
# query.awaitTermination()
