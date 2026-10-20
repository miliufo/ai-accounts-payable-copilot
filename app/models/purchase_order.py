
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrder(BaseModel):
    """
    Structured purchase order model used for
    invoice-to-PO matching.
    """

    model_config = ConfigDict(extra="forbid")

    po_number: str = Field(min_length=1)
    supplier_name: str = Field(min_length=1)

    order_date: date

    currency: str = Field(min_length=3, max_length=3)

    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    total_amount: Decimal = Field(gt=0)

    description: Optional[str] = None

    status: str = "approved"
