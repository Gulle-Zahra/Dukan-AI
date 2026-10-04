"""LangGraph pipeline: supervisor -> validator -> executor -> reorder -> reply."""
import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents import inventory_agent, khata_agent, reorder_agent
from app.agents.reply import build_reply
from app.agents.repo_provider import repo
from app.agents.schemas import ParsedIntent
from app.agents.supervisor import parse_intent
from app.agents.validator import validate
from app.contracts import ActionResult, AgentResponse

log = logging.getLogger("dukaan.graph")

INVENTORY = {"sale", "restock", "stock_out", "stock_query"}
KHATA = {"credit", "payment", "balance_query"}
STOCK_CHANGING = {"sale", "restock", "stock_out"}


class AgentState(TypedDict, total=False):
    input_text: str
    transcript: str | None
    parsed: ParsedIntent
    results: list[ActionResult | None]  # None = valid, waiting for executor
    touched_product_ids: list[int]
    pending_ids: list[int]
    reorder_items: list[str]
    reply_text: str


def supervisor_node(state: AgentState) -> dict:
    return {"parsed": parse_intent(state["input_text"])}


def validator_node(state: AgentState) -> dict:
    results: list[ActionResult | None] = []
    for act in state["parsed"].actions:
        try:
            ok, reason = validate(act, repo)
        except Exception as e:
            log.exception("validate failed")
            ok, reason = False, f"Check nahi ho saka ({type(e).__name__})"
        results.append(None if ok else ActionResult(type=act.action, status="rejected", detail=reason))
    return {"results": results}


def has_valid(state: AgentState) -> str:
    return "executor" if any(r is None for r in state["results"]) else "reply"


def executor_node(state: AgentState) -> dict:
    results, touched = list(state["results"]), []
    for i, act in enumerate(state["parsed"].actions):
        if results[i] is not None:
            continue
        try:
            if act.action == "sale":  # re-check: an earlier action in this sentence may have changed stock
                ok, reason = validate(act, repo)
                if not ok:
                    results[i] = ActionResult(type=act.action, status="rejected", detail=reason)
                    continue
            agent = inventory_agent if act.action in INVENTORY else khata_agent
            results[i] = agent.handle(act, state["input_text"])
            if results[i].status == "done" and act.action in STOCK_CHANGING:
                p = repo.find_product(act.item)
                if p:
                    touched.append(p.id)
        except Exception as e:
            log.exception("executor failed on %s", act)
            results[i] = ActionResult(type=act.action, status="rejected",
                                      detail=f"Kaam nahi ho saka ({type(e).__name__})")
    return {"results": results, "touched_product_ids": touched}


def reorder_node(state: AgentState) -> dict:
    pending, items = [], []
    for pid in dict.fromkeys(state.get("touched_product_ids") or []):
        ids = reorder_agent.check_and_draft([pid], source="user")
        if ids:
            pending += ids
            p = next((x for x in repo.get_low_stock() if x.id == pid), None)
            items.append(p.name if p else f"#{pid}")
    return {"pending_ids": pending, "reorder_items": items}


def reply_node(state: AgentState) -> dict:
    results = [r for r in state.get("results", []) if r is not None]
    return {"reply_text": build_reply(results, state.get("reorder_items"))}


def _build():
    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("validator", validator_node)
    g.add_node("executor", executor_node)
    g.add_node("reorder", reorder_node)
    g.add_node("reply", reply_node)
    g.add_edge(START, "supervisor")
    g.add_edge("supervisor", "validator")
    g.add_conditional_edges("validator", has_valid, {"executor": "executor", "reply": "reply"})
    g.add_edge("executor", "reorder")
    g.add_edge("reorder", "reply")
    g.add_edge("reply", END)
    return g.compile()


_graph = None


def run_agent(text: str, transcript: str | None = None) -> AgentResponse:
    global _graph
    try:
        if _graph is None:
            _graph = _build()
        out = _graph.invoke({"input_text": text, "transcript": transcript})
        return AgentResponse(
            input_text=text,
            transcript=transcript,
            actions=[r for r in out.get("results", []) if r is not None],
            reply_text=out.get("reply_text", ""),
            pending_message_ids=out.get("pending_ids", []),
        )
    except Exception:
        log.exception("run_agent crashed")
        msg = "Maaf kijiye, abhi kuch masla aa gaya — dobara koshish karein"
        return AgentResponse(
            input_text=text, transcript=transcript,
            actions=[ActionResult(type="error", status="rejected", detail=msg)],
            reply_text=f"❌ {msg}", pending_message_ids=[],
        )
