import os
import functools
import operator

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

from rumors_agents import create_agent, agent_node
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage

from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from rumors_tools import tavily_tool, show_for_user

from typing import Literal

load_dotenv()

model_name = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
llm = ChatOpenAI(model=model_name)

class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str

llm = ChatOpenAI(model="gpt-3.5-turbo")

# Research agent and node
research_agent = create_agent(
    llm,
    [tavily_tool],
    system_message="You should provide accurate data for the chart_generator to use.",
)
research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

# chart_generator
chart_agent = create_agent(
    llm,
    [show_for_user],
    system_message="Any information you display will be visible by the user.",
)

chart_node = functools.partial(agent_node, agent=chart_agent, name="chart_generator")

tools = [tavily_tool, show_for_user]
tool_node = ToolNode(tools)

tool_caller = "none"


def router(state):
    # This is the router
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        # The previous agent is invoking a tool
        tool_caller = state["sender"]
        return "call_tool"
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return "continue"

def tool_router(state):
    messages = state["messages"]
    latest_ai = next((item for item in reversed(messages) if isinstance(item, AIMessage)), None)
    return latest_ai.name
    

#########################################
###
###         Defint the Graph
###
##########################################

workflow = StateGraph(AgentState)

workflow.add_node("Researcher", research_node)
workflow.add_node("chart_generator", chart_node)
workflow.add_node("call_tool", tool_node)

workflow.add_conditional_edges(
    "Researcher",
    router,
    {"continue": "chart_generator", "call_tool": "call_tool", END: END},
)
workflow.add_conditional_edges(
    "chart_generator",
    router,
    {"continue": "Researcher", "call_tool": "call_tool", END: END},
)

def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return END

workflow.add_conditional_edges(
    "call_tool",
    # Each agent node updates the 'sender' field
    # the tool calling node does not, meaning
    # this edge will route back to the original agent
    # who invoked the tool
    tool_router, 
    {
        "Researcher": "Researcher",
        "chart_generator": "chart_generator",
    },
)

workflow.add_edge(START, "Researcher")
graph = workflow.compile()


events = graph.stream(
    {
        "messages": [
            HumanMessage(
                content="Get information and gie a short answer what is a platypus"
            )
        ],
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 150},
)

for s in events:
    print(s)
    print("----")