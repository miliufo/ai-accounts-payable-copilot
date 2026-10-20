
import json
from decimal import Decimal
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder


PO_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "purchase_orders"


class POMatchResult(BaseModel):
    matched: bool
    status: str
    po_number: str | None = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def load_purchase_order(po_number: str) -> PurchaseOrder | None:
    """
    Load a purchase order from the local JSON dataset.
    """

    # Prevent unsafe filenames or directory traversal.
    if (
        not po_number
        or not all(c.isalnum() or c in "-_" for c in po_number)
    ):
        return None

    po_path = PO_DIRECTORY / f"{po_number}.json"

    if not po_path.is_file():
        return None

    data = json.loads(po_path.read_text(encoding="utf-8"))
    return PurchaseOrder.model_validate(data)


def match_invoice_to_po(invoice: Invoice) -> POMatchResult:
    """
    Compare an invoice against its referenced purchase order.
    """

    errors = []
    warnings = []

    po_number = invoice.purchase_order_number

    if not po_number:
        return POMatchResult(
            matched=False,
            status="manual_review",
            errors=[],
            warnings=["Invoice has no purchase order reference."],
        )

    po = load_purchase_order(po_number)

    if po is None:
        return POMatchResult(
            matched=False,
            status="manual_review",
            po_number=po_number,
            warnings=["Referenced purchase order was not found."],
        )

    # Rule 1: PO identifier
    if invoice.purchase_order_number != po.po_number:
        errors.append("Purchase order number mismatch.")

    # Rule 2: Supplier
    if invoice.supplier_name.strip().casefold() != po.supplier_name.strip().casefold():
        errors.append("Supplier name does not match purchase order.")

    # Rule 3: Currency
    if invoice.currency.upper() != po.currency.upper():
        errors.append("Invoice currency does not match purchase order.")

    # Rule 4: PO approval status
    if po.status.lower() != "approved":
        errors.append("Purchase order is not approved.")

    # Rule 5: Financial amounts
    tolerance = Decimal("0.01")

    if abs(invoice.subtotal - po.subtotal) > tolerance:
        errors.append("Invoice subtotal does not match purchase order.")

    if abs(invoice.tax_amount - po.tax_amount) > tolerance:
        errors.append("Invoice tax does not match purchase order.")

    if abs(invoice.total_amount - po.total_amount) > tolerance:
        errors.append("Invoice total does not match purchase order.")

    # Rule 6: Dates
    if invoice.invoice_date < po.order_date:
        warnings.append("Invoice date is earlier than purchase order date.")

    if errors:
        status = "mismatch"
    elif warnings:
        status = "manual_review"
    else:
        status = "matched"

    return POMatchResult(
        matched=status == "matched",
        status=status,
        po_number=po_number,
        errors=errors,
        warnings=warnings,
    )
