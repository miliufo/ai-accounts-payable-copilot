
from datetime import date
from decimal import Decimal

from app.models.invoice import Invoice
from app.agents.risk_detection_agent import assess_invoice_risk


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


def test_low_risk_invoice():
    invoice = make_invoice()

    result = assess_invoice_risk(invoice)

    assert result["risk_score"] == 0
    assert result["risk_level"] == "low"
    assert result["recommendation"] == "standard_review"
    assert result["requires_human_review"] is False


def test_high_amount_invoice():
    invoice = make_invoice(
        total_amount=Decimal("15000.00")
    )

    result = assess_invoice_risk(invoice)

    assert result["risk_score"] == 20
    assert result["risk_level"] == "medium"
    assert result["recommendation"] == "manual_review"
    assert result["requires_human_review"] is True


def test_duplicate_invoice_high_risk():
    invoice = make_invoice()

    result = assess_invoice_risk(
        invoice,
        is_duplicate=True
    )

    assert result["risk_score"] == 50
    assert result["risk_level"] == "high"
    assert result["recommendation"] == "hold_payment"


def test_po_mismatch_medium_risk():
    invoice = make_invoice()

    result = assess_invoice_risk(
        invoice,
        po_matched=False
    )

    assert result["risk_score"] == 30
    assert result["risk_level"] == "medium"
    assert result["recommendation"] == "manual_review"


def test_bank_details_changed():
    invoice = make_invoice()

    result = assess_invoice_risk(
        invoice,
        bank_details_changed=True
    )

    assert result["risk_score"] == 50
    assert result["risk_level"] == "high"
    assert result["recommendation"] == "hold_payment"


def test_multiple_risk_factors():
    invoice = make_invoice(
        total_amount=Decimal("25000.00")
    )

    result = assess_invoice_risk(
        invoice,
        is_duplicate=True,
        po_matched=False,
        bank_details_changed=True
    )

    assert result["risk_score"] == 100
    assert result["risk_level"] == "high"
    assert len(result["risk_factors"]) == 4
    assert result["requires_human_review"] is True


def test_custom_amount_threshold():
    invoice = make_invoice(
        total_amount=Decimal("6000.00")
    )

    result = assess_invoice_risk(
        invoice,
        high_amount_threshold=Decimal("5000.00")
    )

    assert result["risk_score"] == 20
    assert result["risk_level"] == "medium"
