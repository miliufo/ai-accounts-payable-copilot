
from pathlib import Path

from app.graph.accounts_payable_graph import accounts_payable_graph
from app.models.approval import ApprovalDecision


INVOICE_PATH = Path("data/invoices/sample_invoice.txt")


def run_scenario(name, approval=None):
    invoice_text = INVOICE_PATH.read_text(encoding="utf-8")

    initial_state = {
        "invoice_text": invoice_text,
        "existing_invoices": [],
        "bank_details_changed": False,
        "approval": approval,
        "errors": [],
    }

    result = accounts_payable_graph.invoke(initial_state)

    decision = result["payment_decision"]

    print(f"\n{'=' * 55}")
    print(f"SCENARIO: {name}")
    print(f"{'=' * 55}")
    print(f"Invoice: {decision.invoice_number}")
    print(f"Status: {decision.status}")
    print(f"Reason: {decision.reason}")
    print(f"Human approval required: {decision.requires_human_approval}")

    return decision


def main():
    pending = run_scenario(
        "WITHOUT HUMAN APPROVAL"
    )

    approved = run_scenario(
        "HUMAN APPROVES",
        ApprovalDecision(
            invoice_number="INV-2026-001",
            decision="approved",
            reviewer="Finance Manager",
            reason="Invoice verified and approved.",
        ),
    )

    rejected = run_scenario(
        "HUMAN REJECTS",
        ApprovalDecision(
            invoice_number="INV-2026-001",
            decision="rejected",
            reviewer="Finance Manager",
            reason="Invoice requires correction.",
        ),
    )

    assert pending.status == "pending_review"
    assert approved.status == "approved_for_payment"
    assert rejected.status == "rejected"

    print("\nALL HUMAN APPROVAL WORKFLOW TESTS PASSED")


if __name__ == "__main__":
    main()
