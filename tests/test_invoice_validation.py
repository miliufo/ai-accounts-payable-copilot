
from datetime import date
from decimal import Decimal

from app.models.invoice import Invoice
from app.agents.invoice_validation_agent import validate_invoice


def make_invoice(**overrides):
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


def test_valid_invoice():
    invoice = make_invoice()
    result = validate_invoice(invoice)

    assert result.is_valid is True
    assert result.status == "validated"
    assert result.errors == []
    assert result.warnings == []


def test_missing_purchase_order():
    invoice = make_invoice(purchase_order_number=None)
    result = validate_invoice(invoice)

    assert result.is_valid is True
    assert result.status == "manual_review"
    assert "Purchase order reference is missing." in result.warnings


def test_financial_mismatch():
    invoice = make_invoice(total_amount=Decimal("1500.00"))
    result = validate_invoice(invoice)

    assert result.is_valid is False
    assert result.status == "rejected"
    assert any("Financial mismatch" in e for e in result.errors)


def test_invalid_due_date():
    invoice = make_invoice(due_date=date(2026, 10, 1))
    result = validate_invoice(invoice)

    assert result.is_valid is False
    assert result.status == "rejected"
    assert any("Due date" in e for e in result.errors)


def test_zero_total():
    invoice = make_invoice(
        subtotal=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
    )
    result = validate_invoice(invoice)

    assert result.is_valid is False
    assert result.status == "rejected"
