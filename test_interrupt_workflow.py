
from langgraph.types import Interrupt

from app.graph.accounts_payable_graph import accounts_payable_graph


def main():
    invoice_text = """
Invoice Number: INV-2026-001
Supplier: Berlin Tech GmbH
Invoice Date: 2026-10-16
Due Date: 2026-11-15
Purchase Order: PO-1001
Currency: EUR
Subtotal: 1000.00
Tax: 190.00
Total: 1190.00
Description: Enterprise IT Infrastructure Services
"""

    config = {
        "configurable": {
            "thread_id": "ap-interrupt-test-001"
        }
    }

    print("\nStarting Accounts Payable Workflow...")

    result = accounts_payable_graph.invoke(
        {
            "invoice_text": invoice_text,
            "existing_invoices": [],
            "bank_details_changed": False,
        },
        config=config,
    )

    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        print("\nNo interrupt occurred.")
        print("Current step:", result.get("current_step"))
        print("Payment decision:", result.get("payment_decision"))
        return

    print("\nHUMAN APPROVAL REQUIRED")
    print("=" * 50)

    for item in interrupts:
        if isinstance(item, Interrupt):
            print(item.value)
        else:
            print(item)

    snapshot = accounts_payable_graph.get_state(config)

    print("\nPaused at:", snapshot.next)
    print("\nWorkflow successfully interrupted.")


if __name__ == "__main__":
    main()
