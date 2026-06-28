import pandas as pd
import re
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, pandas_udf
from pyspark.sql.types import StringType
from shopsphere_genai.config.core import ShopSphereGenAIConfig

# Note: In a real environment, you must install PyMuPDF (fitz) on the cluster:
# %pip install PyMuPDF pandas pyarrow
try:
    import fitz  # PyMuPDF
except ImportError:
    pass # Handled for local dev without PyMuPDF

@pandas_udf(StringType())
def extract_pdf_text_udf(content_series: pd.Series) -> pd.Series:
    """
    Pandas UDF for vectorized text extraction from binary PDFs.
    Uses Apache Arrow for efficient serialization between JVM and Python.
    """
    results = []
    for content in content_series:
        if content is None:
            results.append(None)
            continue
            
        try:
            # Open PDF from memory stream (do not write to disk)
            doc = fitz.open(stream=content, filetype="pdf")
            text_blocks = []
            for page in doc:
                text_blocks.append(page.get_text())
                
            full_text = "\n".join(text_blocks)
            
            # Basic Cleaning: Remove excessive whitespace and control characters
            cleaned_text = re.sub(r'\s+', ' ', full_text).strip()
            
            # If empty (e.g. image-only PDF), flag it
            if not cleaned_text:
                results.append("<ERROR: IMAGE_ONLY_NO_TEXT_EXTRACTED>")
            else:
                results.append(cleaned_text)
                
        except Exception as e:
            # Crucial: Catch all exceptions so one bad PDF doesn't kill the cluster
            results.append(f"<ERROR: EXCEPTION_DURING_EXTRACTION: {str(e)}>")
            
    return pd.Series(results)

class DocumentParser:
    """
    Orchestrates the Bronze-to-Silver transformation pipeline.
    """
    def __init__(self, spark: SparkSession, config: ShopSphereGenAIConfig):
        self.spark = spark
        self.config = config
        self.bronze_table = f"{self.config.catalog_name}.{self.config.schema_name}.bronze_raw_documents"
        self.silver_table = f"{self.config.catalog_name}.{self.config.schema_name}.silver_cleaned_documents"
        self.checkpoint_path = f"/Volumes/{self.config.catalog_name}/{self.config.schema_name}/checkpoints/silver_parsing"

    def process_new_documents(self):
        """
        Reads incrementally from Bronze, extracts text, and writes to Silver.
        """
        print(f"Reading from Bronze: {self.bronze_table}")
        
        # Read stream from Bronze (Delta allows streaming reads)
        bronze_stream = self.spark.readStream.table(self.bronze_table)
        
        # Apply UDF to extract text
        # We drop the heavy 'content' binary column so we don't duplicate storage
        silver_df = (
            bronze_stream
            .withColumn("extracted_text", extract_pdf_text_udf(col("content")))
            .drop("content") 
            .filter(~col("extracted_text").startswith("<ERROR")) # Optionally filter errors, or keep them to debug
        )
        
        # Write to Silver
        query = (
            silver_df.writeStream
            .format("delta")
            .option("checkpointLocation", self.checkpoint_path)
            .outputMode("append")
            .trigger(availableNow=True) # Process all currently unparsed documents then stop
            .table(self.silver_table)
        )
        
        print(f"Parsing initialized. Writing to Silver: {self.silver_table}")
        return query
