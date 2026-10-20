
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Invoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_number: str = Field(min_length=1)
    supplier_name: str = Field(min_length=1)

    invoice_date: date
    due_date: Optional[date] = None

    purchase_order_number: Optional[str] = None

    currency: str = Field(min_length=3, max_length=3)

    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    total_amount: Decimal = Field(ge=0)

    description: Optional[str] = None
