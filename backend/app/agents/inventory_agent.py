"""Inventory specialist: sale, restock, stock_out, stock_query."""
from app.agents.normalize import fmt
from app.agents.repo_provider import repo
from app.agents.schemas import ParsedAction
from app.contracts import ActionResult


def handle(action: ParsedAction, raw_text: str) -> ActionResult:
    a = action.action
    p = repo.find_product(action.item or "")
    if p is None:
        return ActionResult(type=a, status="rejected", detail=f"'{action.item}' nahi mila")

    if a == "sale":
        p = repo.adjust_stock(p.id, -action.quantity, "sale", raw_text)
        detail = f"{fmt(action.quantity)} {p.unit} {p.name} bik gaye (baqi: {fmt(p.stock_qty)})"
    elif a == "restock":
        p = repo.adjust_stock(p.id, action.quantity, "restock", raw_text)
        detail = f"{fmt(action.quantity)} {p.unit} {p.name} aa gaye (ab: {fmt(p.stock_qty)})"
    elif a == "stock_out":
        p = repo.set_stock(p.id, 0, raw_text)
        detail = f"{p.name.capitalize()} khatam — stock 0 kar diya"
    elif a == "stock_query":
        detail = f"{p.name.capitalize()}: {fmt(p.stock_qty)} {p.unit} bacha hai"
    else:
        return ActionResult(type=a, status="rejected", detail="Inventory ka kaam nahi")
    return ActionResult(type=a, status="done", detail=detail)
