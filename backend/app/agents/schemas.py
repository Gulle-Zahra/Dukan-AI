from typing import Literal
from pydantic import BaseModel, Field

ActionType = Literal[
    "sale", "restock", "stock_out", "credit", "payment",
    "stock_query", "balance_query", "unknown",
]


class ParsedAction(BaseModel):
    action: ActionType
    item: str | None = Field(None, description="Item name exactly as the shopkeeper said it, lowercase")
    quantity: float | None = None
    unit: str | None = None
    customer: str | None = None
    amount: float | None = Field(None, description="Rupee amount for credit/payment")


class ParsedIntent(BaseModel):
    actions: list[ParsedAction]
