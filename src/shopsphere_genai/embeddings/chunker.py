import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, pandas_udf, explode
from pyspark.sql.types import ArrayType, StringType
from langchain.text_splitter import RecursiveCharacterTextSplitter
from shopsphere_genai.config.core import ShopSphereGenAIConfig

@pandas_udf(ArrayType(StringType()))
def chunk_text_udf(text_series: pd.Series) -> pd.Series:
    """
    Pandas UDF to chunk long documents.
    Returns an array of strings (chunks) for each document.
    """
    # Initialize the LangChain splitter
    # We use 500 tokens/characters as a safe baseline for BGE-large
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    results = []
    for text in text_series:
        if text is None or not str(text).strip():
            results.append([])
            continue
            
        try:
            chunks = splitter.split_text(text)
            results.append(chunks)
        except Exception:
            results.append([])
            
    return pd.Series(results)

class TextChunker:
    """
    Transforms Silver clean text into Pre-Gold chunked text.
    """
    def __init__(self, spark: SparkSession, config: ShopSphereGenAIConfig):
        self.spark = spark
        self.config = config
        self.silver_table = f"{self.config.catalog_name}.{self.config.schema_name}.silver_cleaned_documents"
        self.pre_gold_table = f"{self.config.catalog_name}.{self.config.schema_name}.pre_gold_chunks"

    def process_chunks(self):
        print(f"Chunking data from {self.silver_table}")
        
        # In a real streaming pipeline, this would be readStream.
        # For demonstration of transformation, we use batch read.
        df = self.spark.read.table(self.silver_table)
        
        # 1. Apply UDF to get an array of chunks
        df_array = df.withColumn("chunks_array", chunk_text_udf(col("extracted_text")))
        
        # 2. Explode the array so each chunk is its own row
        # We retain path and ingestion_timestamp for traceability
        df_exploded = (
            df_array
            .select("path", "ingestion_timestamp", explode("chunks_array").alias("chunk_content"))
            .filter("chunk_content != ''")
        )
        
        # Write to Pre-Gold
        df_exploded.write.format("delta").mode("overwrite").saveAsTable(self.pre_gold_table)
        print(f"Chunking complete. Wrote to {self.pre_gold_table}")
        return df_exploded
