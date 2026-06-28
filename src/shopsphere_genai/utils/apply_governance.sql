-- ======================================================================
-- ShopSphere GenAI - Unity Catalog Governance Script
-- This script should be executed by a Workspace Admin to secure the AI assets.
-- ======================================================================

-- 1. Create a Service Principal for the Agent
-- (In reality, this is done via the Account Console or Terraform)
-- We will refer to it as `ai_agent_sp`

-- 2. Grant access to the LLM Endpoints
-- The Agent needs to call Llama 3 and the Embedding model.
GRANT EXECUTE ON ENDPOINT `databricks-meta-llama-3-70b-instruct` TO `ai_agent_sp`;
GRANT EXECUTE ON ENDPOINT `databricks-bge-large-en` TO `ai_agent_sp`;
GRANT EXECUTE ON ENDPOINT `databricks-llama-guard` TO `ai_agent_sp`;

-- 3. Grant access to the Tools (UC Functions)
-- The Agent needs to execute our custom inventory checker.
GRANT EXECUTE ON FUNCTION shopsphere_dev.genai_core.check_inventory TO `ai_agent_sp`;

-- 4. Secure the Data Layer
-- We grant the Agent SELECT on the Gold tables for the SQL Agent to work.
GRANT SELECT ON TABLE shopsphere_dev.genai_core.sales_aggregated TO `ai_agent_sp`;

-- 5. Row-Level Security for Vector Search
-- We want to ensure that when a human queries the system, they only see 
-- documents relevant to their region. 
-- (Assuming the Delta table has a 'region' column).

CREATE OR REPLACE FUNCTION shopsphere_dev.genai_core.regional_manager_filter(region STRING)
RETURN IF(
  -- Global admins see everything
  IS_ACCOUNT_GROUP_MEMBER('global_admins'), TRUE,
  -- Otherwise, you must be in the specific region's group (e.g., 'region_na')
  IS_ACCOUNT_GROUP_MEMBER(CONCAT('region_', LOWER(region)))
);

-- Apply the filter to the source Delta table. 
-- The Databricks Vector Search index will automatically inherit this!
ALTER TABLE shopsphere_dev.genai_core.gold_document_vectors 
SET ROW FILTER shopsphere_dev.genai_core.regional_manager_filter ON (region);

-- 6. Grant Vector Index Access
-- We grant the human users (e.g., store managers) access to query the index.
-- The endpoint will execute the query as the human, passing their identity 
-- to the Row Filter above.
GRANT SELECT ON TABLE shopsphere_dev.genai_core.document_vs_index TO `store_managers`;
