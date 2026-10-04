"""In-memory stand-in for app/db/repo.py (same signatures). Enable with USE_FAKE_REPO=true."""
import difflib
from datetime import datetime, timedelta
from threading import Lock

from app.contracts import CustomerOut, PendingMessageOut, ProductOut, SupplierOut

_lock = Lock()
_products: dict[int, dict] = {}
_customers: dict[int, dict] = {}
_suppliers: dict[int, dict] = {}
_transactions: list[dict] = []
_pending: dict[int, dict] = {}


def reset() -> None:
    """Demo seed — mirrors what db/seed.py should contain."""
    with _lock:
        for d in (_products, _customers, _suppliers, _pending):
            d.clear()
        _transactions.clear()
        _suppliers.update({
            1: dict(id=1, name="Haji Rafiq Traders", phone="923001234567"),
            2: dict(id=2, name="Malik Flour Mills", phone="923211234567"),
        })
        rows = [
            # name, aliases, unit, stock, reorder_level, reorder_qty, price, supplier
            ("chawal", ["chawal", "chawl", "rice", "چاول"], "packet", 30, 5, 50, 350, 1),
            ("atta", ["atta", "aata", "flour", "آٹا"], "kg", 25, 10, 50, 120, 2),
            ("cheeni", ["cheeni", "chini", "sugar", "چینی"], "kg", 40, 10, 50, 150, 1),
            ("daal", ["daal", "dal", "lentils", "دال"], "kg", 15, 5, 25, 300, 1),
            ("ghee", ["ghee", "گھی"], "kg", 12, 4, 20, 550, 1),
            ("doodh", ["doodh", "dudh", "milk", "دودھ"], "packet", 24, 6, 48, 220, 1),
            ("cooking oil", ["cooking oil", "oil", "tel", "تیل"], "litre", 18, 5, 24, 600, 1),
        ]
        for i, (n, al, u, s, rl, rq, p, sup) in enumerate(rows, 1):
            _products[i] = dict(id=i, name=n, aliases=al, unit=u, stock_qty=float(s), reorder_level=float(rl),
                                reorder_qty=float(rq), price=float(p), supplier_id=sup)
        old = datetime.now() - timedelta(days=10)
        _customers.update({
            1: dict(id=1, name="Ahmed", phone="923331112222", balance=1000.0, last_credit_at=old),
            2: dict(id=2, name="Bilal", phone="923451112222", balance=800.0, last_credit_at=old),
            3: dict(id=3, name="Usman", phone=None, balance=0.0, last_credit_at=None),
        })


def _match_score(query: str, cand: str) -> float:
    return difflib.SequenceMatcher(None, query, cand.lower()).ratio() * 100


def find_product(name: str) -> ProductOut | None:
    q = (name or "").strip().lower()
    best, best_score = None, 0.0
    for p in _products.values():
        for cand in [p["name"], *p["aliases"]]:
            s = _match_score(q, cand)
            if s > best_score:
                best, best_score = p, s
    return ProductOut(**best) if best and best_score >= 80 else None


def list_products() -> list[ProductOut]:
    return [ProductOut(**p) for p in _products.values()]


def _txn(**kw):
    _transactions.append(dict(id=len(_transactions) + 1, created_at=datetime.now(), **kw))


def adjust_stock(product_id: int, delta: float, txn_type: str, raw_text: str) -> ProductOut:
    with _lock:
        p = _products[product_id]
        p["stock_qty"] += delta
        _txn(type=txn_type, product_id=product_id, qty=abs(delta), raw_text=raw_text)
        return ProductOut(**p)


def set_stock(product_id: int, qty: float, raw_text: str) -> ProductOut:
    with _lock:
        p = _products[product_id]
        p["stock_qty"] = qty
        _txn(type="stock_out", product_id=product_id, qty=qty, raw_text=raw_text)
        return ProductOut(**p)


def find_or_create_customer(name: str) -> CustomerOut:
    with _lock:
        for c in _customers.values():
            if c["name"].lower() == name.strip().lower():
                return CustomerOut(**c)
        cid = max(_customers, default=0) + 1
        _customers[cid] = dict(id=cid, name=name.strip(), phone=None, balance=0.0, last_credit_at=None)
        return CustomerOut(**_customers[cid])


def add_credit(customer_id: int, amount: float, raw_text: str) -> CustomerOut:
    with _lock:
        c = _customers[customer_id]
        c["balance"] += amount
        c["last_credit_at"] = datetime.now()
        _txn(type="credit", customer_id=customer_id, amount=amount, raw_text=raw_text)
        return CustomerOut(**c)


def record_payment(customer_id: int, amount: float, raw_text: str) -> CustomerOut:
    with _lock:
        c = _customers[customer_id]
        c["balance"] -= amount
        _txn(type="payment", customer_id=customer_id, amount=amount, raw_text=raw_text)
        return CustomerOut(**c)


def get_low_stock() -> list[ProductOut]:
    return [ProductOut(**p) for p in _products.values() if p["stock_qty"] <= p["reorder_level"]]


def get_overdue_customers(min_balance: float, days: int) -> list[CustomerOut]:
    cutoff = datetime.now() - timedelta(days=days)
    return [CustomerOut(**c) for c in _customers.values()
            if c["balance"] >= min_balance and c["last_credit_at"] and c["last_credit_at"] <= cutoff]


def get_supplier(supplier_id: int) -> SupplierOut | None:
    s = _suppliers.get(supplier_id)
    return SupplierOut(**s) if s else None


def has_pending_message(kind: str, ref_id: int) -> bool:
    return any(m["kind"] == kind and m["ref_id"] == ref_id and m["status"] == "pending"
               for m in _pending.values())


def create_pending_message(kind, recipient_name, phone, message_text, source, ref_id) -> PendingMessageOut:
    with _lock:
        mid = max(_pending, default=0) + 1
        _pending[mid] = dict(id=mid, kind=kind, recipient_name=recipient_name, phone=phone,
                             message_text=message_text, status="pending", source=source,
                             ref_id=ref_id, created_at=datetime.now())
        return PendingMessageOut(**_pending[mid])


def list_pending() -> list[PendingMessageOut]:  # test helper, not part of the contract
    return [PendingMessageOut(**m) for m in _pending.values()]


reset()
