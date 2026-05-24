from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage
from langchain_core.tools import tool
from vector_store import retrieve
from live_stats import get_live_matches, get_matches_by_date, search_player
import os
from dotenv import load_dotenv

load_dotenv()

# --- STATE ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    question: str
    answer: str
    tool_used: str | None
    tokens: int

# --- TOOLS ---
@tool
def retrieve_football_context(query: str) -> str:
    """Retrieves relevant football context from the knowledge base.
    Use for questions about tactics, player history, team history, or background context."""
    results = retrieve(query)
    return "\n".join(results)

@tool
def fetch_live_matches() -> str:
    """Fetches currently live football matches and scores.
    Use when asked about ongoing games or live scores."""
    return get_live_matches()

@tool
def fetch_matches_today() -> str:
    """Fetches today's football matches and results.
    Use when asked about today's matches or recent results."""
    return get_matches_by_date()

@tool
def fetch_player_info(name: str) -> str:
    """Searches for a football player by name and returns their current team.
    Use when asked about a specific player's current club."""
    return search_player(name)

tools = [
    retrieve_football_context,
    fetch_live_matches,
    fetch_matches_today,
    fetch_player_info
]

# --- MODEL ---
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
).bind_tools(tools)

system_prompt = SystemMessage(content="""You are a football intelligence assistant.
You have access to the following tools:
- retrieve_football_context: for tactics, player history, team history, background knowledge
- fetch_live_matches: for currently live scores
- fetch_matches_today: for today's matches and recent results
- fetch_player_info: for finding a player's current club

Always use the most relevant tool before answering. Be concise and specific.""")

# --- NODES ---
def agent_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    if not isinstance(messages[0], SystemMessage):
        messages = [system_prompt] + messages

    response = llm.invoke(messages)

    tool_used = state.get("tool_used")
    if response.tool_calls:
        tool_used = response.tool_calls[0]["name"]

    tokens = 0
    if response.usage_metadata:
        tokens = response.usage_metadata.get("total_tokens", 0)

    return {
        **state,
        "messages": state["messages"] + [response],
        "tool_used": tool_used,
        "tokens": tokens
    }

def finalize(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    return {
        **state,
        "answer": last_message.content
    }

# --- GRAPH ---
tool_node = ToolNode(tools)

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_node("finalize", finalize)

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "tools",
        "__end__": "finalize"
    }
)

graph.add_edge("tools", "agent")
graph.add_edge("finalize", END)

footy_graph = graph.compile()

def run_agent(question: str) -> dict:
    result = footy_graph.invoke({
        "messages": [HumanMessage(content=question)],
        "question": question,
        "answer": "",
        "tool_used": None,
        "tokens": 0
    })
    return {
        "answer": result["answer"],
        "tool_used": result["tool_used"],
        "tokens": result["tokens"]
    }