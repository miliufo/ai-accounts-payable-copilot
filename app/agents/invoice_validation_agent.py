
from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field

from app.models.invoice import Invoice


class ValidationResult(BaseModel):
    is_valid: bool
    status: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def validate_invoice(invoice: Invoice) -> ValidationResult:
    """
    Validate an extracted invoice using deterministic
    financial and business rules.
    """

    errors = []
    warnings = []

    # Rule 1: Required business identifiers
    if not invoice.invoice_number.strip():
        errors.append("Invoice number is missing.")

    if not invoice.supplier_name.strip():
        errors.append("Supplier name is missing.")

    # Rule 2: Financial consistency
    expected_total = invoice.subtotal + invoice.tax_amount

    if abs(expected_total - invoice.total_amount) > Decimal("0.01"):
        errors.append(
            "Financial mismatch: subtotal + tax does not equal total."
        )

    # Rule 3: Positive invoice amount
    if invoice.total_amount <= 0:
        errors.append("Invoice total must be greater than zero.")

    # Rule 4: Due date consistency
    if invoice.due_date is not None:
        if invoice.due_date < invoice.invoice_date:
            errors.append(
                "Due date cannot be earlier than invoice date."
            )
    else:
        warnings.append("Invoice due date is missing.")

    # Rule 5: Future invoice date
    if invoice.invoice_date > date.today():
        warnings.append(
            "Invoice date is in the future."
        )

    # Rule 6: Purchase order reference
    if not invoice.purchase_order_number:
        warnings.append(
            "Purchase order reference is missing."
        )

    # Rule 7: Currency support
    supported_currencies = {"EUR", "USD", "GBP"}

    if invoice.currency.upper() not in supported_currencies:
        warnings.append(
            f"Currency {invoice.currency} requires manual review."
        )

    # Final decision
    is_valid = len(errors) == 0

    if errors:
        status = "rejected"
    elif warnings:
        status = "manual_review"
    else:
        status = "validated"

    return ValidationResult(
        is_valid=is_valid,
        status=status,
        errors=errors,
        warnings=warnings,
    )
