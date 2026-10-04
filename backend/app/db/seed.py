import os
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from .database import engine, Base, SessionLocal
from .models import Supplier, Product, Customer

load_dotenv()


def _wa(number: str) -> str:
    """Normalize to WhatsApp format 92XXXXXXXXXX: '+92 333-1234567' or '03331234567' -> '923331234567'."""
    digits = "".join(ch for ch in number if ch.isdigit())
    if digits.startswith("0"):
        digits = "92" + digits[1:]
    return digits


def _phone(env_var: str, fallback: str) -> str:
    """Real number from .env if set, otherwise the dummy fallback."""
    return _wa(os.getenv(env_var) or fallback)


# Real numbers live in backend/.env (git-ignored), never in this file:
#   DEMO_SUPPLIER_PHONE   -> receives all supplier reorder messages
#   DEMO_CUSTOMER_PHONE   -> receives Ahmed's reminders (and other customers' if CUSTOMER2 not set)
#   DEMO_CUSTOMER2_PHONE  -> receives Bilal's reminders
SUPPLIER_PHONE = _phone("DEMO_SUPPLIER_PHONE", os.getenv("DEMO_SUPPLIER_PHONE") )
CUSTOMER_PHONE = _phone("DEMO_CUSTOMER_PHONE", os.getenv("DEMO_CUSTOMER_PHONE") )
CUSTOMER2_PHONE = _phone("DEMO_CUSTOMER2_PHONE", os.getenv("DEMO_CUSTOMER2_PHONE") )


def reset_and_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # Suppliers
        s1 = Supplier(name="Tariq Traders", phone=SUPPLIER_PHONE)
        s2 = Supplier(name="Ali Wholesalers", phone=SUPPLIER_PHONE)
        s3 = Supplier(name="Zain Mart", phone=SUPPLIER_PHONE)
        db.add_all([s1, s2, s3])
        db.commit()

        # Products
        products_data = [
            ("Chawal", ["chawal", "chaawal", "rice", "چاول"], "packet", 50, 10, 20, 300, s1.id),
            ("Atta", ["atta", "flour", "آٹا"], "kg", 8, 10, 20, 150, s1.id),  # Low stock!
            ("Cheeni", ["cheeni", "sugar", "chini", "چینی"], "kg", 40, 15, 30, 140, s2.id),
            ("Daal", ["daal", "lentils", "دال"], "kg", 20, 5, 10, 250, s2.id),
            ("Ghee", ["ghee", "oil", "گھی"], "kg", 5, 10, 20, 500, s3.id),  # Low stock!
            ("Doodh", ["doodh", "milk", "دودھ"], "litre", 30, 10, 20, 200, s3.id),
            ("Chai Patti", ["chai patti", "tea", "چائے کی پتی"], "pack", 45, 10, 15, 400, s1.id),
            ("Namak", ["namak", "salt", "نمک"], "pack", 60, 5, 10, 50, s2.id),
            ("Sabun", ["sabun", "soap", "صابن"], "piece", 50, 15, 30, 100, s3.id),
            ("Biscuit", ["biscuit", "cookies", "بسکٹ"], "pack", 40, 10, 20, 30, s1.id),
        ]

        for name, aliases, unit, stock, reorder_level, reorder_qty, price, s_id in products_data:
            db.add(Product(name=name, aliases=aliases, unit=unit, stock_qty=stock, reorder_level=reorder_level,
                           reorder_qty=reorder_qty, price=price, supplier_id=s_id))

        # Customers
        old_date = datetime.now(timezone.utc) - timedelta(days=10)
        c1 = Customer(name="Ahmed", phone=CUSTOMER_PHONE, balance=1500, last_credit_at=old_date)
        c2 = Customer(name="Bilal", phone=CUSTOMER2_PHONE, balance=2000, last_credit_at=old_date)
        c3 = Customer(name="Rashid", phone=CUSTOMER_PHONE, balance=0)
        c4 = Customer(name="Fatima", phone=CUSTOMER2_PHONE, balance=0)
        c5 = Customer(name="Usman", phone=CUSTOMER_PHONE, balance=0)
        db.add_all([c1, c2, c3, c4, c5])
        db.commit()


if __name__ == "__main__":
    reset_and_seed()
    print("Database reset and seeded.")