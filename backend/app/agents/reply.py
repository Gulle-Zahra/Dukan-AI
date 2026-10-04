"""Template-based Roman Urdu summary for the shopkeeper (no LLM call)."""
from app.contracts import ActionResult


def build_reply(results: list[ActionResult], reorder_items: list[str] | None = None) -> str:
    lines = [("✅ " if r.status == "done" else "❌ ") + r.detail for r in results]
    for name in reorder_items or []:
        lines.append(f"📦 {name.capitalize()} kam hai, supplier ko message tayyar hai — approve karein")
    return "\n".join(lines) if lines else "❌ Kuch samajh nahi aaya, dobara bolein"
