
from decimal import Decimal

from pydantic import ValidationError
import pytest

from app.models.invoice import Invoice


def test_valid_invoice():
    invoice = Invoice(
        invoice_number="INV-2026-001",
        supplier_name="Berlin Tech GmbH",
        invoice_date="2026-10-16",
        due_date="2026-11-15",
        purchase_order_number="PO-1001",
        currency="EUR",
        subtotal="1000.00",
        tax_amount="190.00",
        total_amount="1190.00",
    )

    assert invoice.invoice_number == "INV-2026-001"
    assert invoice.total_amount == Decimal("1190.00")
    assert invoice.currency == "EUR"


def test_negative_amount_rejected():
    with pytest.raises(ValidationError):
        Invoice(
            invoice_number="INV-002",
            supplier_name="Test Supplier",
            invoice_date="2026-10-16",
            currency="EUR",
            subtotal="-100.00",
            tax_amount="0.00",
            total_amount="0.00",
        )


def test_missing_invoice_number_rejected():
    with pytest.raises(ValidationError):
        Invoice(
            invoice_number="",
            supplier_name="Test Supplier",
            invoice_date="2026-10-16",
            currency="EUR",
            subtotal="100.00",
            tax_amount="19.00",
            total_amount="119.00",
        )
