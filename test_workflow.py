
import json
from pathlib import Path

from app.graph.accounts_payable_graph import accounts_payable_graph


def main():
    invoice_path = Path("data/invoices/sample_invoice.txt")
    invoice_text = invoice_path.read_text(encoding="utf-8")

    initial_state = {
        "invoice_text": invoice_text,
        "existing_invoices": [],
        "bank_details_changed": False,
        "approval": None,
        "errors": [],
    }

    print("\nStarting AI Accounts Payable Workflow...\n")

    result = accounts_payable_graph.invoke(initial_state)

    invoice = result["invoice"]
    decision = result["payment_decision"]

    print("=" * 55)
    print("AI ACCOUNTS PAYABLE COPILOT")
    print("=" * 55)

    print("\nINVOICE")
    print(invoice.model_dump_json(indent=2))

    for title, key in [
        ("VALIDATION", "validation_result"),
        ("PURCHASE ORDER MATCHING", "po_match_result"),
        ("DUPLICATE DETECTION", "duplicate_result"),
        ("RISK ASSESSMENT", "risk_result"),
    ]:
        print(f"\n{title}")
        print(json.dumps(result[key], indent=2, default=str))

    print("\nPAYMENT DECISION")
    print(decision.model_dump_json(indent=2))

    print("\nFINAL WORKFLOW STEP:", result["current_step"])

    assert decision.status != "approved_for_payment", (
        "Invoice must not be approved for payment without review."
    )

    print("\nWorkflow completed. No payment was authorized.")


if __name__ == "__main__":
    main()
