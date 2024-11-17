from langchain_core.messages import HumanMessage, SystemMessage
from rumors_supervisor import supervisor_agent, members
from rumors_tools import tavily_tool, show_for_user

import functools
import operator
from typing import Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage

from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import create_react_agent
from typing import Annotated

from langchain_openai import ChatOpenAI

import os

### --------------------- LLM ------------------------------------

model_name = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
llm = ChatOpenAI(model=model_name)

### -------------------------------------------------------------------
###
###                 Agens and Graph
###
###--------------------------------------------------------------------


def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {
        "messages": [HumanMessage(content=result["messages"][-1].content, name=name)]
    }

class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str

def create_graph():
    supervisor_node = functools.partial(supervisor_agent, llm=llm)

    research_agent = create_react_agent(llm, tools=[tavily_tool], messages_modifier=SystemMessage(content="You should provide accurate data "))
    research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

    # NOTE: THIS PERFORMS ARBITRARY CODE EXECUTION. PROCEED WITH CAUTION
    code_agent = create_react_agent(llm, tools=[show_for_user], messages_modifier=SystemMessage(content="Any information you display will be visible by the user"))
    code_node = functools.partial(agent_node, agent=code_agent, name="Designer")

    workflow = StateGraph(AgentState)
    workflow.add_node("Researcher", research_node)
    workflow.add_node("Designer", code_node)
    workflow.add_node("supervisor", supervisor_node)

    ### ----------------------- Edges -----------------------------

    for member in members:
        # We want our workers to ALWAYS "report back" to the supervisor when done
        workflow.add_edge(member, "supervisor")
    # The supervisor populates the "next" field in the graph state
    # which routes to a node or finishes
    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    # Finally, add entrypoint
    workflow.add_edge(START, "supervisor")

    graph = workflow.compile()
    return graph