
from typing import TypedDict, Optional, Any


class AccountsPayableState(TypedDict, total=False):
    # Input
    invoice_text: str

    # Extracted invoice stored as JSON-compatible data
    invoice: dict[str, Any]

    # Agent results
    validation_result: dict[str, Any]
    po_match_result: dict[str, Any]
    duplicate_result: dict[str, Any]
    risk_result: dict[str, Any]

    # Human approval and final decision
    approval: Optional[dict[str, Any]]
    payment_decision: Optional[dict[str, Any]]

    # Workflow metadata
    current_step: str
    errors: list[str]

    # Additional risk inputs
    existing_invoices: list[dict[str, Any]]
    bank_details_changed: bool
