
from datetime import date
from decimal import Decimal

from app.models.invoice import Invoice
from app.agents.duplicate_detection_agent import (
    detect_duplicate_invoice,
)


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


def test_duplicate_invoice():
    invoice = make_invoice()

    existing = [
        {
            "invoice_number": "INV-2026-001",
            "supplier_name": "Berlin Tech GmbH",
        }
    ]

    result = detect_duplicate_invoice(invoice, existing)

    assert result["is_duplicate"] is True
    assert result["status"] == "duplicate"
    assert result["matched_invoice"] == existing[0]


def test_unique_invoice():
    invoice = make_invoice(
        invoice_number="INV-2026-002"
    )

    existing = [
        {
            "invoice_number": "INV-2026-001",
            "supplier_name": "Berlin Tech GmbH",
        }
    ]

    result = detect_duplicate_invoice(invoice, existing)

    assert result["is_duplicate"] is False
    assert result["status"] == "unique"


def test_same_number_different_supplier():
    invoice = make_invoice(
        supplier_name="Amsterdam Cloud BV"
    )

    existing = [
        {
            "invoice_number": "INV-2026-001",
            "supplier_name": "Berlin Tech GmbH",
        }
    ]

    result = detect_duplicate_invoice(invoice, existing)

    assert result["is_duplicate"] is False


def test_case_insensitive_duplicate():
    invoice = make_invoice()

    existing = [
        {
            "invoice_number": "inv-2026-001",
            "supplier_name": "berlin tech gmbh",
        }
    ]

    result = detect_duplicate_invoice(invoice, existing)

    assert result["is_duplicate"] is True


def test_empty_invoice_database():
    invoice = make_invoice()

    result = detect_duplicate_invoice(invoice, [])

    assert result["is_duplicate"] is False
    assert result["status"] == "unique"


def test_whitespace_normalization():
    invoice = make_invoice()

    existing = [
        {
            "invoice_number": "  INV-2026-001  ",
            "supplier_name": " Berlin Tech GmbH ",
        }
    ]

    result = detect_duplicate_invoice(invoice, existing)

    assert result["is_duplicate"] is True
