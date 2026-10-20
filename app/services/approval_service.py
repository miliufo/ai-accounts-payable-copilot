
from typing import Optional

from app.models.approval import (
    ApprovalDecision,
    PaymentDecision,
)


def evaluate_payment_decision(
    invoice_number: str,
    risk_result: dict,
    approval: Optional[ApprovalDecision] = None,
) -> PaymentDecision:
    """
    Evaluate invoice payment eligibility based on risk
    assessment and human approval.

    This service never executes payments.

    Security rules:
    - Missing or invalid risk information fails closed.
    - Approval must belong to the correct invoice.
    - Human rejection always blocks payment.
    - High-risk invoices remain on hold.
    - Low- and medium-risk invoices require approval.
    """

    risk_level = risk_result.get("risk_level")

    # 1. Fail closed if risk information is invalid.
    if risk_level not in {"low", "medium", "high"}:
        return PaymentDecision(
            invoice_number=invoice_number,
            status="on_hold",
            reason="Missing or invalid risk assessment.",
            requires_human_approval=True,
        )

    # 2. Verify approval belongs to this invoice.
    if approval is not None:
        if approval.invoice_number != invoice_number:
            return PaymentDecision(
                invoice_number=invoice_number,
                status="on_hold",
                reason="Approval invoice number mismatch.",
                requires_human_approval=True,
            )

        # 3. Human rejection always blocks payment.
        if approval.decision == "rejected":
            return PaymentDecision(
                invoice_number=invoice_number,
                status="rejected",
                reason="Invoice rejected by human reviewer.",
                requires_human_approval=True,
                approval=approval,
            )

    # 4. High-risk invoices cannot be approved
    # through the standard approval workflow.
    if risk_level == "high":
        return PaymentDecision(
            invoice_number=invoice_number,
            status="on_hold",
            reason="High-risk invoice requires additional review.",
            requires_human_approval=True,
            approval=approval,
        )

    # 5. Medium-risk invoices require human approval.
    if risk_level == "medium":
        if approval is None:
            return PaymentDecision(
                invoice_number=invoice_number,
                status="pending_review",
                reason="Human approval required.",
                requires_human_approval=True,
            )

        if approval.decision == "approved":
            return PaymentDecision(
                invoice_number=invoice_number,
                status="approved_for_payment",
                reason="Invoice approved by human reviewer.",
                requires_human_approval=True,
                approval=approval,
            )

    # 6. Low-risk invoices also require standard review.
    if risk_level == "low":
        if approval is None:
            return PaymentDecision(
                invoice_number=invoice_number,
                status="pending_review",
                reason="Low-risk invoice awaiting standard review.",
                requires_human_approval=True,
            )

        if approval.decision == "approved":
            return PaymentDecision(
                invoice_number=invoice_number,
                status="approved_for_payment",
                reason="Low-risk invoice approved by human reviewer.",
                requires_human_approval=True,
                approval=approval,
            )

    # 7. Safe fallback for unexpected conditions.
    return PaymentDecision(
        invoice_number=invoice_number,
        status="on_hold",
        reason="Unexpected approval state.",
        requires_human_approval=True,
    )
