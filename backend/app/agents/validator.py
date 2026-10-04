"""Business-rule checks before anything touches the DB. Reasons are short Roman Urdu."""
import difflib

from app.agents.normalize import fmt
from app.agents.schemas import ParsedAction

PRODUCT_ACTIONS = {"sale", "restock", "stock_out", "stock_query"}
QTY_ACTIONS = {"sale", "restock"}
MONEY_ACTIONS = {"credit", "payment"}
CUSTOMER_ACTIONS = {"credit", "payment", "balance_query"}


def suggest_product(name: str, repo) -> str | None:
    """Closest product name (by name or alias) for a 'did you mean' hint."""
    try:
        products = repo.list_products()
    except Exception:
        return None
    lookup = {}
    for p in products:
        for cand in [p.name, *(p.aliases or [])]:
            lookup[cand.lower()] = p.name
    hit = difflib.get_close_matches(name.lower(), list(lookup), n=1, cutoff=0.5)
    return lookup[hit[0]] if hit else None


def validate(action: ParsedAction, repo) -> tuple[bool, str]:
    a = action.action

    if a == "unknown":
        return False, "Samajh nahi aaya. Aise bolein: '20 packet chawal bike' ya 'Ahmed ko 500 udhaar'"

    product = None
    if a in PRODUCT_ACTIONS:
        if not action.item:
            return False, "Kaunsi cheez? Item ka naam batayein"
        product = repo.find_product(action.item)
        if product is None:
            guess = suggest_product(action.item, repo)
            if guess:
                return False, f"'{action.item}' nahi mila — kya aap ka matlab '{guess}' tha?"
            return False, f"'{action.item}' dukaan ki list mein nahi hai"

    if a in QTY_ACTIONS:
        q = action.quantity
        if q is None:
            return False, f"{product.name} ki miqdaar (quantity) batayein"
        if q <= 0 or q >= 10000:
            return False, f"Quantity {fmt(q)} sahi nahi lagti (1 se 9999 tak)"
        if a == "sale" and q > product.stock_qty:
            return False, (f"Stock mein sirf {fmt(product.stock_qty)} {product.unit} {product.name} hain, "
                           f"{fmt(q)} nahi bik sakte")

    if a in CUSTOMER_ACTIONS and not action.customer:
        return False, "Customer ka naam batayein"

    if a in MONEY_ACTIONS:
        amt = action.amount
        if amt is None:
            return False, f"{action.customer} ki raqam (amount) batayein"
        if amt <= 0 or amt >= 1_000_000:
            return False, f"Raqam Rs {fmt(amt)} sahi nahi lagti"

    return True, "ok"
