
from datetime import date
from decimal import Decimal

from app.models.invoice import Invoice
from app.agents.po_matching_agent import match_invoice_to_po


def make_invoice(**overrides):
    """Create a sample invoice for testing."""

    data = {
        "invoice_number": "INV-2026-001",
        "supplier_name": "Berlin Tech GmbH",
        "invoice_date": date(2026, 10, 16),
        "due_date": date(2026, 11, 15),
        "purchase_order_number": "PO-1001",
        "currency": "EUR",
        "subtotal": Decimal("1000.00"),
        "tax_amount": Decimal("190.00"),
        "total_amount": Decimal("1190.00"),
        "description": "Enterprise IT Infrastructure Services",
    }

    data.update(overrides)
    return Invoice(**data)


def test_matching_invoice():
    invoice = make_invoice()

    result = match_invoice_to_po(invoice)

    assert result.matched is True
    assert result.status == "matched"
    assert result.errors == []


def test_supplier_mismatch():
    invoice = make_invoice(
        supplier_name="Unknown Supplier GmbH"
    )

    result = match_invoice_to_po(invoice)

    assert result.matched is False
    assert result.status == "mismatch"
    assert any("Supplier" in e for e in result.errors)


def test_total_amount_mismatch():
    invoice = make_invoice(
        total_amount=Decimal("1500.00")
    )

    result = match_invoice_to_po(invoice)

    assert result.matched is False
    assert result.status == "mismatch"
    assert any("total" in e.lower() for e in result.errors)


def test_currency_mismatch():
    invoice = make_invoice(currency="USD")

    result = match_invoice_to_po(invoice)

    assert result.matched is False
    assert result.status == "mismatch"


def test_missing_purchase_order():
    invoice = make_invoice(
        purchase_order_number="PO-9999"
    )

    result = match_invoice_to_po(invoice)

    assert result.matched is False
    assert result.status == "manual_review"


def test_invoice_without_po():
    invoice = make_invoice(
        purchase_order_number=None
    )

    result = match_invoice_to_po(invoice)

    assert result.matched is False
    assert result.status == "manual_review"
