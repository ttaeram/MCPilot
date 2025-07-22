# app/services/review_service.py
import asyncio, re, httpx, os
from typing import TypedDict
from app.agent_llm import llm, make_prompt

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class ReviewState(TypedDict):
    diff: str
    style_feedback: str
    security_feedback: str
    performance_feedback: str
    logic_feedback: str
    final_review: str

def style_agent(state: ReviewState) -> dict:
    prompt = make_prompt("Style & Syntax", state["diff"])
    return {"style_feedback": llm.invoke(prompt).content}

def security_agent(state: ReviewState) -> dict:
    prompt = make_prompt("Security", state["diff"])
    return {"security_feedback": llm.invoke(prompt).content}

def performance_agent(state: ReviewState) -> dict:
    prompt = make_prompt("Performance", state["diff"])
    return {"performance_feedback": llm.invoke(prompt).content}

def logic_agent(state: ReviewState) -> dict:
    prompt = make_prompt("Logic & Potential Bugs", state["diff"])
    return {"logic_feedback": llm.invoke(prompt).content}

def merge_feedback(state: ReviewState) -> str:
    def clean(text, heading):
        pattern = r"^(#+\s*)?(\*+)?\s*(Style\s*&\s*Syntax|Security|Performance|Logic\s*&\s*Potential\s*Bugs)\s*(Review)?\s*(\*+)?\s*[\n:]*"
        return f"{heading}\n{re.sub(pattern, '', text.strip(), flags=re.IGNORECASE)}"

    return "\n\n".join([
        clean(state["style_feedback"], "🔍 Style & Syntax:"),
        clean(state["security_feedback"], "🛡️ Security:"),
        clean(state["performance_feedback"], "🚀 Performance:"),
        clean(state["logic_feedback"], "🐛 Logic & Potential Bugs:")
    ])

async def review_diff_concurrently(diff: str) -> ReviewState:
    state: ReviewState = {
        "diff": diff,
        "style_feedback": "",
        "security_feedback": "",
        "performance_feedback": "",
        "logic_feedback": "",
        "final_review": ""
    }

    results = await asyncio.gather(
        asyncio.to_thread(style_agent, state),
        asyncio.to_thread(security_agent, state),
        asyncio.to_thread(performance_agent, state),
        asyncio.to_thread(logic_agent, state),
    )

    for result in results:
        state.update(result)

    state["final_review"] = merge_feedback(state)
    return state

async def fetch_pr_files(files_url: str):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(files_url, headers=headers)
        response.raise_for_status()
        return response.json()
