"""Reorder specialist: drafts supplier WhatsApp orders for low-stock products (needs approval)."""
import logging

from app.agents.normalize import fmt
from app.agents.repo_provider import repo

log = logging.getLogger("dukaan.reorder")


def draft_message(supplier_name: str, qty: float, unit: str, product_name: str) -> str:
    return f"Assalam o Alaikum {supplier_name}, mujhe {fmt(qty)} {unit} {product_name} chahiye. Shukriya."


def check_and_draft(product_ids: list[int], source: str = "user") -> list[int]:
    if not product_ids:
        return []
    low = {p.id: p for p in repo.get_low_stock()}  # one query, no per-product lookup needed
    new_ids: list[int] = []
    for pid in dict.fromkeys(product_ids):  # dedupe, keep order
        p = low.get(pid)
        if p is None:
            continue
        try:
            if repo.has_pending_message("supplier_order", p.id):
                continue
            supplier = repo.get_supplier(p.supplier_id) if p.supplier_id else None
            if supplier is None or not supplier.phone:
                log.info("No supplier/phone for %s, skipping reorder", p.name)
                continue
            msg = repo.create_pending_message(
                kind="supplier_order",
                recipient_name=supplier.name,
                phone=supplier.phone,
                message_text=draft_message(supplier.name, p.reorder_qty, p.unit, p.name),
                source=source,
                ref_id=p.id,
            )
            new_ids.append(msg.id)
            log.info("Drafted supplier_order #%s for %s (%s)", msg.id, p.name, source)
        except Exception:
            log.exception("Reorder draft failed for product %s", pid)
    return new_ids
