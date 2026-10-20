
def test_low_risk_with_human_approval():
    from app.models.approval import ApprovalDecision
    from app.services.approval_service import evaluate_payment_decision

    approval = ApprovalDecision(
        invoice_number="INV-2026-001",
        decision="approved",
        reviewer="Finance Manager",
        reason="Invoice verified and approved.",
    )

    result = evaluate_payment_decision(
        invoice_number="INV-2026-001",
        risk_result={"risk_level": "low"},
        approval=approval,
    )

    assert result.status == "approved_for_payment"
    assert result.requires_human_approval is True
    assert result.approval is not None
    assert result.approval.reviewer == "Finance Manager"


def test_low_risk_without_human_approval():
    from app.services.approval_service import evaluate_payment_decision

    result = evaluate_payment_decision(
        invoice_number="INV-2026-001",
        risk_result={"risk_level": "low"},
        approval=None,
    )

    assert result.status == "pending_review"
    assert result.requires_human_approval is True
    assert result.approval is None
