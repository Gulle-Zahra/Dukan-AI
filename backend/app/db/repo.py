from rapidfuzz import fuzz
from datetime import datetime, timezone, timedelta
from .database import SessionLocal
from .models import Product, Customer, Supplier, Transaction, PendingMessage
from app.contracts import ProductOut, CustomerOut, SupplierOut, TransactionOut, PendingMessageOut

def utc_now():
    return datetime.now(timezone.utc)

def find_product(name: str) -> ProductOut | None:
    with SessionLocal() as db:
        products = db.query(Product).all()
        best_match = None
        highest_score = 0
        for p in products:
            names_to_check = [p.name] + (p.aliases or [])
            for alias in names_to_check:
                score = fuzz.ratio(name.lower(), alias.lower())
                if score >= 80 and score > highest_score:
                    highest_score = score
                    best_match = p
        if best_match:
            return ProductOut.model_validate(best_match)
        return None

def list_products() -> list[ProductOut]:
    with SessionLocal() as db:
        return [ProductOut.model_validate(p) for p in db.query(Product).all()]

def adjust_stock(product_id: int, delta: float, txn_type: str, raw_text: str) -> ProductOut:
    with SessionLocal() as db:
        p = db.query(Product).get(product_id)
        p.stock_qty += delta
        txn = Transaction(type=txn_type, product_id=product_id, qty=abs(delta), raw_text=raw_text)
        db.add(txn)
        db.commit()
        db.refresh(p)
        return ProductOut.model_validate(p)

def set_stock(product_id: int, qty: float, raw_text: str) -> ProductOut:
    with SessionLocal() as db:
        p = db.query(Product).get(product_id)
        p.stock_qty = qty
        txn = Transaction(type="stock_out", product_id=product_id, qty=qty, raw_text=raw_text)
        db.add(txn)
        db.commit()
        db.refresh(p)
        return ProductOut.model_validate(p)

def find_or_create_customer(name: str) -> CustomerOut:
    with SessionLocal() as db:
        c = db.query(Customer).filter(Customer.name.ilike(name)).first()
        if not c:
            c = Customer(name=name, phone="")
            db.add(c)
            db.commit()
            db.refresh(c)
        return CustomerOut.model_validate(c)

def add_credit(customer_id: int, amount: float, raw_text: str) -> CustomerOut:
    with SessionLocal() as db:
        c = db.query(Customer).get(customer_id)
        c.balance += amount
        c.last_credit_at = utc_now()
        txn = Transaction(type="credit", customer_id=customer_id, amount=amount, raw_text=raw_text)
        db.add(txn)
        db.commit()
        db.refresh(c)
        return CustomerOut.model_validate(c)

def record_payment(customer_id: int, amount: float, raw_text: str) -> CustomerOut:
    with SessionLocal() as db:
        c = db.query(Customer).get(customer_id)
        c.balance -= amount
        txn = Transaction(type="payment", customer_id=customer_id, amount=amount, raw_text=raw_text)
        db.add(txn)
        db.commit()
        db.refresh(c)
        return CustomerOut.model_validate(c)

def get_low_stock() -> list[ProductOut]:
    with SessionLocal() as db:
        products = db.query(Product).filter(Product.stock_qty <= Product.reorder_level).all()
        return [ProductOut.model_validate(p) for p in products]

def get_overdue_customers(min_balance: float, days: int) -> list[CustomerOut]:
    cutoff = utc_now() - timedelta(days=days)
    with SessionLocal() as db:
        customers = db.query(Customer).filter(Customer.balance >= min_balance, Customer.last_credit_at <= cutoff).all()
        return [CustomerOut.model_validate(c) for c in customers]

def get_supplier(supplier_id: int) -> SupplierOut | None:
    with SessionLocal() as db:
        s = db.query(Supplier).get(supplier_id)
        return SupplierOut.model_validate(s) if s else None

def has_pending_message(kind: str, ref_id: int) -> bool:
    with SessionLocal() as db:
        return db.query(PendingMessage).filter_by(kind=kind, ref_id=ref_id, status="pending").first() is not None

def create_pending_message(kind, recipient_name, phone, message_text, source, ref_id) -> PendingMessageOut:
    with SessionLocal() as db:
        msg = PendingMessage(kind=kind, recipient_name=recipient_name, phone=phone, message_text=message_text, source=source, ref_id=ref_id)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return PendingMessageOut.model_validate(msg)