
from langgraph.types import interrupt

from app.graph.state import AccountsPayableState
from app.models.approval import ApprovalDecision
from app.models.invoice import Invoice


def human_approval_node(state: AccountsPayableState) -> dict:
    """
    Pause the workflow until a human reviewer submits
    an approval or rejection decision.

    Invoice data is stored as a JSON-compatible dictionary.

    This node never executes payments.
    """

    # Reconstruct the validated invoice model.
    invoice = Invoice.model_validate(state["invoice"])

    validation = state["validation_result"]
    po_match = state["po_match_result"]
    duplicate = state["duplicate_result"]
    risk = state["risk_result"]

    # --------------------------------------------------
    # Step 1: Verify eligibility for standard approval
    # --------------------------------------------------

    eligible = (
        validation.get("is_valid", False)
        and not validation.get("warnings")
        and po_match.get("matched", False)
        and not po_match.get("warnings")
        and not duplicate.get("is_duplicate", False)
        and risk.get("risk_level") in {"low", "medium"}
    )

    # Ineligible invoices cannot enter standard approval.
    if not eligible:
        return {
            "approval": None,
            "current_step": "human_approval_skipped",
        }

    # --------------------------------------------------
    # Step 2: Pause workflow for human approval
    # --------------------------------------------------

    review_response = interrupt(
        {
            "type": "human_approval_required",
            "invoice_number": invoice.invoice_number,
            "supplier_name": invoice.supplier_name,
            "total_amount": str(invoice.total_amount),
            "currency": invoice.currency,
            "risk_level": risk["risk_level"],
            "message": (
                "Human review is required before payment "
                "eligibility can be determined."
            ),
        }
    )

    # --------------------------------------------------
    # Step 3: Validate the human review response
    # --------------------------------------------------

    if not isinstance(review_response, dict):
        raise ValueError(
            "Human approval response must be a dictionary."
        )

    approval = ApprovalDecision.model_validate(review_response)

    # Prevent approval of a different invoice.
    if approval.invoice_number != invoice.invoice_number:
        raise ValueError(
            "Approval invoice number mismatch."
        )

    # --------------------------------------------------
    # Step 4: Return JSON-compatible approval data
    # --------------------------------------------------

    return {
        "approval": approval.model_dump(mode="json"),
        "current_step": "human_approval_completed",
    }
