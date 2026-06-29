from databricks_langchain import ChatDatabricks
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from shopsphere_genai.config.core import ShopSphereGenAIConfig
from shopsphere_genai.agent.omni_tools import get_omni_tools

class ShopSphereOmniAgent:
    def __init__(self, config: ShopSphereGenAIConfig):
        self.config = config
        
        print("Initializing LLM for Omni-Agent...")
        self.llm = ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct", temperature=0)
        
        print("\nGathering tools from all sub-systems...")
        self.tools = get_omni_tools(config)
        print(f"Successfully loaded {len(self.tools)} tools.")
        
        print("\nCreating Omni-Agent Execution Loop...")
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the ShopSphere Omni-Agent, a highly capable unified assistant for a retail company.
You have access to a set of specialized tools that allow you to answer different types of questions:

1. unstructured search (employee_handbook_search): Use this for policies, guidelines, rules, and general text information.
2. structured data query (query_structured_data_warehouse): Use this for numerical aggregates, total store counts, sales revenue, and structured inventory metrics.
3. governed operations (shopsphere_dev__genai_core__check_inventory): Use this to check the specific inventory of a single SKU.

Analyze the user's request and decide which tool(s) to use. If a question requires multiple tools (e.g. "What is the return policy, and how many stores do we have?"), you can use multiple tools in sequence.
Always provide a concise, friendly, and complete final answer to the user based on the results from the tools.
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        # Create the agent that uses OpenAI-style tool calling (which Databricks Llama 3 70B supports natively)
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        # The executor handles the actual loop of calling the tool, getting the result, and passing it back to the LLM
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            handle_parsing_errors=True
        )

    def invoke(self, question: str) -> str:
        """
        Executes the Omni-Agent loop for a given question.
        """
        print(f"\n--- Processing Request: '{question}' ---")
        try:
            result = self.agent_executor.invoke({"input": question})
            return result["output"]
        except Exception as e:
            return f"Agent failed to answer. Error: {e}"
