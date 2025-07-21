from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_core.messages import HumanMessage
from app.agent_llm import llm, make_prompt
import re

class ReviewState(TypedDict):
    diff: str
    style_feedback: str
    security_feedback: str
    performance_feedback: str
    logic_feedback: str
    final_review: str

def style_agent(state: ReviewState) -> ReviewState:
    prompt = make_prompt("Style & Syntax", state["diff"])
    response = llm.invoke(prompt)
    return {**state, "style_feedback": response.content}

def security_agent(state: ReviewState) -> ReviewState:
    prompt = make_prompt("Security", state["diff"])
    response = llm.invoke(prompt)
    return {**state, "security_feedback": response.content}

def performance_agent(state: ReviewState) -> ReviewState:
    prompt = make_prompt("Performance", state["diff"])
    response = llm.invoke(prompt)
    return {**state, "performance_feedback": response.content}

def logic_agent(state: ReviewState) -> ReviewState:
    prompt = make_prompt("Logic & Potential Bugs", state["diff"])
    response = llm.invoke(prompt)
    return {**state, "logic_feedback": response.content}

def merge_feedback(state: ReviewState) -> ReviewState:
    def clean_heading(text, expected_heading):
        pattern = r"^(#+\s*)?(\*+)?\s*Style\s*&\s*Syntax\s*Review\s*(\*+)?\s*[\n:]*"
        cleaned = re.sub(pattern, "", text.strip(), flags=re.IGNORECASE)

        return f"{expected_heading}\n{cleaned.strip()}"

    final_review = "\n\n".join([
        clean_heading(state["style_feedback"], "🔍 Style & Syntax:"),
        clean_heading(state["security_feedback"], "🛡️ Security:"),
        clean_heading(state["performance_feedback"], "🚀 Performance:"),
        clean_heading(state["logic_feedback"], "🐛 Logic & Potential Bugs:"),
    ])

    return {**state, "final_review": final_review}

graph_builder = StateGraph(ReviewState)
graph_builder.add_node("style", style_agent)
graph_builder.add_node("security", security_agent)
graph_builder.add_node("performance", performance_agent)
graph_builder.add_node("logic", logic_agent)
graph_builder.add_node("merge", merge_feedback)

graph_builder.set_entry_point("style")
graph_builder.add_edge("style", "security")
graph_builder.add_edge("security", "performance")
graph_builder.add_edge("performance", "logic")
graph_builder.add_edge("logic", "merge")
graph_builder.add_edge("merge", END)

graph = graph_builder.compile()
