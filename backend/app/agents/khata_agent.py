"""Khata (customer credit) specialist: credit, payment, balance_query."""
from app.agents.normalize import fmt
from app.agents.repo_provider import repo
from app.agents.schemas import ParsedAction
from app.contracts import ActionResult


def _balance_text(balance: float) -> str:
    if balance > 0:
        return f"baqi: Rs {fmt(balance)}"
    if balance < 0:
        return f"advance: Rs {fmt(-balance)}"
    return "hisaab saaf"


def handle(action: ParsedAction, raw_text: str) -> ActionResult:
    a = action.action
    c = repo.find_or_create_customer(action.customer)

    if a == "credit":
        c = repo.add_credit(c.id, action.amount, raw_text)
        detail = f"{c.name} ke khate mein Rs {fmt(action.amount)} udhaar ({_balance_text(c.balance)})"
    elif a == "payment":
        c = repo.record_payment(c.id, action.amount, raw_text)
        detail = f"{c.name} ne Rs {fmt(action.amount)} jama karwaye ({_balance_text(c.balance)})"
    elif a == "balance_query":
        detail = (f"{c.name} ka udhaar: Rs {fmt(c.balance)}" if c.balance > 0
                  else f"{c.name}: {_balance_text(c.balance)}")
    else:
        return ActionResult(type=a, status="rejected", detail="Khata ka kaam nahi")
    return ActionResult(type=a, status="done", detail=detail)
