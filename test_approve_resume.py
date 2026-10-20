
from uuid import uuid4

from langgraph.types import Command

from app.graph.accounts_payable_graph import accounts_payable_graph


INVOICE_TEXT = """
Invoice Number: INV-2026-001
Supplier: Berlin Tech GmbH
Invoice Date: 2026-10-16
Due Date: 2026-11-15
Purchase Order Number: PO-1001
Currency: EUR
Subtotal: 1000.00
Tax Amount: 190.00
Total Amount: 1190.00
Description: Enterprise IT Infrastructure Services
"""


def main():
    # Each test uses a separate checkpoint thread.
    config = {
        "configurable": {
            "thread_id": f"approve-test-{uuid4().hex}"
        }
    }

    initial_state = {
        "invoice_text": INVOICE_TEXT,
        "existing_invoices": [],
        "bank_details_changed": False,
        "approval": None,
        "errors": [],
    }

    # ----------------------------------------------
    # STEP 1: Start workflow
    # ----------------------------------------------

    print("\nSTEP 1: Starting workflow...")

    result = accounts_payable_graph.invoke(
        initial_state,
        config=config,
    )

    interrupts = result.get("__interrupt__", [])

    assert interrupts, (
        "Expected workflow to pause for human approval."
    )

    review_request = interrupts[0].value

    assert review_request["type"] == "human_approval_required"
    assert review_request["invoice_number"] == "INV-2026-001"

    print("\nWorkflow paused for human approval.")
    print("Review request:", review_request)

    # ----------------------------------------------
    # STEP 2: Human approves invoice
    # ----------------------------------------------

    print("\nSTEP 2: Human approves invoice...")

    approval_response = {
        "invoice_number": review_request["invoice_number"],
        "decision": "approved",
        "reviewer": "Finance Manager",
        "reason": "Invoice verified and approved.",
    }

    result = accounts_payable_graph.invoke(
        Command(resume=approval_response),
        config=config,
    )

    assert not result.get("__interrupt__"), (
        "Workflow unexpectedly paused again."
    )

    # ----------------------------------------------
    # STEP 3: Verify final payment decision
    # ----------------------------------------------

    print("\nSTEP 3: Final payment decision")

    decision = result.get("payment_decision")

    assert isinstance(decision, dict), (
        "Payment decision must be a dictionary."
    )

    print("Invoice:", decision["invoice_number"])
    print("Status:", decision["status"])
    print("Reason:", decision["reason"])
    print(
        "Human approval required:",
        decision["requires_human_approval"],
    )

    # ----------------------------------------------
    # STEP 4: Security assertions
    # ----------------------------------------------

    assert decision["invoice_number"] == "INV-2026-001"

    assert decision["status"] == "approved_for_payment", (
        "Approved invoice did not receive expected status."
    )

    assert decision["requires_human_approval"] is True

    assert decision["approval"] is not None

    assert decision["approval"]["decision"] == "approved"

    assert (
        decision["approval"]["invoice_number"]
        == decision["invoice_number"]
    )

    assert result["current_step"] == "payment_decision"

    print("\nAPPROVE & RESUME TEST PASSED")
    print("No payment was executed.")


if __name__ == "__main__":
    main()
