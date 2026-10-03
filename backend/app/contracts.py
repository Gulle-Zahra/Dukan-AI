from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    aliases: list[str]
    unit: str
    stock_qty: float
    reorder_level: float
    reorder_qty: float
    price: float
    supplier_id: int

class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: str
    balance: float
    last_credit_at: Optional[datetime]

class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: str

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    product_id: Optional[int]
    customer_id: Optional[int]
    qty: Optional[float]
    amount: Optional[float]
    raw_text: str
    created_at: datetime

class PendingMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    recipient_name: str
    phone: str
    message_text: str
    status: str
    source: str
    ref_id: Optional[int]
    created_at: datetime

class ActionResult(BaseModel):
    type: str
    status: Literal["done", "rejected"]
    detail: str

class AgentResponse(BaseModel):
    input_text: str
    transcript: Optional[str] = None
    actions: List[ActionResult]
    reply_text: str
    pending_message_ids: List[int]