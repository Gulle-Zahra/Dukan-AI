from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime, timezone
from .database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    aliases = Column(JSON) # JSON list of strings
    unit = Column(String)
    stock_qty = Column(Float, default=0.0)
    reorder_level = Column(Float, default=0.0)
    reorder_qty = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    supplier_id = Column(Integer)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    balance = Column(Float, default=0.0)
    last_credit_at = Column(DateTime, nullable=True)

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # sale, restock, stock_out, credit, payment
    product_id = Column(Integer, nullable=True)
    customer_id = Column(Integer, nullable=True)
    qty = Column(Float, nullable=True)
    amount = Column(Float, nullable=True)
    raw_text = Column(String)
    created_at = Column(DateTime, default=utc_now)

class PendingMessage(Base):
    __tablename__ = "pending_messages"
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String) # supplier_order, payment_reminder
    recipient_name = Column(String)
    phone = Column(String)
    message_text = Column(String)
    status = Column(String, default="pending") # pending, approved, rejected
    source = Column(String) # user, scheduler
    ref_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)