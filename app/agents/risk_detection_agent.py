
from decimal import Decimal
from typing import Optional

from app.models.invoice import Invoice


def assess_invoice_risk(
    invoice: Invoice,
    is_duplicate: bool = False,
    po_matched: bool = True,
    bank_details_changed: bool = False,
    high_amount_threshold: Decimal = Decimal("10000.00"),
) -> dict:
    """
    Assess invoice risk using explainable rules.

    Risk scores are illustrative and configurable.
    This function does not authorize payments.
    """

    score = 0
    risk_factors = []

    if is_duplicate:
        score += 50
        risk_factors.append(
            "Potential duplicate invoice detected."
        )

    if not po_matched:
        score += 30
        risk_factors.append(
            "Invoice does not match the purchase order."
        )

    if bank_details_changed:
        score += 50
        risk_factors.append(
            "Supplier bank details have changed."
        )

    if invoice.total_amount > high_amount_threshold:
        score += 20
        risk_factors.append(
            "Invoice exceeds the configured amount threshold."
        )

    score = min(score, 100)

    if score >= 50:
        risk_level = "high"
        recommendation = "hold_payment"
    elif score >= 20:
        risk_level = "medium"
        recommendation = "manual_review"
    else:
        risk_level = "low"
        recommendation = "standard_review"

    return {
        "invoice_number": invoice.invoice_number,
        "risk_score": score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendation": recommendation,
        "requires_human_review": risk_level != "low",
    }
