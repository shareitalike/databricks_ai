from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_community.chat_models import ChatDatabricks
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.checkpoint.memory import MemorySaver
import json

# Mock Tool for demonstration (In reality, import from tools.py)
def check_inventory_tool(sku: str) -> str:
    return f"Inventory for {sku} is 5 units."
from langchain.tools import tool
@tool
def mock_inventory(sku: str) -> str:
    """Checks inventory for a SKU."""
    return check_inventory_tool(sku)

tools = [mock_inventory]
tool_executor = ToolExecutor(tools)
llm = ChatDatabricks(endpoint="databricks-meta-llama-3-70b-instruct", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# 1. Define the State
# The state is a dictionary. `add_messages` tells the graph to append to the list, not overwrite.
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# 2. Define the Nodes
def call_model(state: AgentState):
    """Node: Calls the LLM"""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    # We return a dict with the key 'messages' to append it to state
    return {"messages": [response]}

def call_tool(state: AgentState):
    """Node: Executes the Tool"""
    messages = state['messages']
    # The last message is the AI asking to use a tool
    last_message = messages[-1]
    
    # We construct a ToolInvocation
    action = ToolInvocation(
        tool=last_message.tool_calls[0]['name'],
        tool_input=last_message.tool_calls[0]['args'],
    )
    # Execute the tool
    response = tool_executor.invoke(action)
    
    # We create a ToolMessage to represent the result (LangChain standard)
    from langchain_core.messages import ToolMessage
    tool_message = ToolMessage(
        content=str(response), name=action.tool, tool_call_id=last_message.tool_calls[0]['id']
    )
    return {"messages": [tool_message]}

# 3. Define Conditional Edges
def should_continue(state: AgentState):
    """Condition: Decides whether to use a tool or finish."""
    messages = state['messages']
    last_message = messages[-1]
    
    # If there is no tool call, we are done
    if not last_message.tool_calls:
        return "end"
    # Otherwise, we continue to the tool node
    else:
        return "continue"

# 4. Build the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

# Add edges
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)
# After the tool runs, it ALWAYS goes back to the agent to synthesize
workflow.add_edge("action", "agent")

# Compile with a checkpointer for memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Example Usage
# config = {"configurable": {"thread_id": "session_123"}} # Equivalent to session_id
# inputs = {"messages": [HumanMessage(content="Check inventory for SKU-456")]}
# for output in app.stream(inputs, config=config):
#     # stream() yields the output of each node as it executes
#     for key, value in output.items():
#         print(f"Output from node '{key}':")
#         print("---")
#         print(value)
#     print("\n---\n")
