from .database import engine, Base, SessionLocal
from .models import Supplier, Product, Customer
from datetime import datetime, timezone, timedelta

def reset_and_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        # Suppliers
        s1 = Supplier(name="Tariq Traders", phone="923001234567")
        s2 = Supplier(name="Ali Wholesalers", phone="923331234567")
        s3 = Supplier(name="Zain Mart", phone="923451234567")
        db.add_all([s1, s2, s3])
        db.commit()

        # Products
        products_data = [
            ("Chawal", ["chawal", "chaawal", "rice", "چاول"], "kg", 50, 10, 20, 300, s1.id),
            ("Atta", ["atta", "flour", "آٹا"], "kg", 8, 10, 20, 150, s1.id), # Low stock!
            ("Cheeni", ["cheeni", "sugar", "chini", "چینی"], "kg", 40, 15, 30, 140, s2.id),
            ("Daal", ["daal", "lentils", "دال"], "دال", 20, 5, 10, 250, s2.id),
            ("Ghee", ["ghee", "oil", "گھی"], "kg", 5, 10, 20, 500, s3.id), # Low stock!
            ("Doodh", ["doodh", "milk", "دودھ"], "liter", 30, 10, 20, 200, s3.id),
            ("Chai Patti", ["chai patti", "tea", "چائے کی پتی"], "pack", 45, 10, 15, 400, s1.id),
            ("Namak", ["namak", "salt", "نمک"], "pack", 60, 5, 10, 50, s2.id),
            ("Sabun", ["sabun", "soap", "صابن"], "piece", 50, 15, 30, 100, s3.id),
            ("Biscuit", ["biscuit", "cookies", "بسکٹ"], "pack", 40, 10, 20, 30, s1.id),
        ]
        
        for name, aliases, unit, stock, reorder_level, reorder_qty, price, s_id in products_data:
            db.add(Product(name=name, aliases=aliases, unit=unit, stock_qty=stock, reorder_level=reorder_level, reorder_qty=reorder_qty, price=price, supplier_id=s_id))
        
        # Customers
        old_date = datetime.now(timezone.utc) - timedelta(days=10)
        c1 = Customer(name="Ahmed", phone="923110000001", balance=1500, last_credit_at=old_date)
        c2 = Customer(name="Bilal", phone="923110000002", balance=2000, last_credit_at=old_date)
        c3 = Customer(name="Sana", phone="923110000003", balance=500, last_credit_at=old_date)
        c4 = Customer(name="Rashid", phone="923110000004", balance=0)
        c5 = Customer(name="Fatima", phone="923110000005", balance=0)
        c6 = Customer(name="Usman", phone="923110000006", balance=0)
        db.add_all([c1, c2, c3, c4, c5, c6])
        db.commit()