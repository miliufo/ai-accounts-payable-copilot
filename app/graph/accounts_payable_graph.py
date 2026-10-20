
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import AccountsPayableState
from app.graph.human_approval import human_approval_node

from app.models.invoice import Invoice
from app.models.approval import ApprovalDecision, PaymentDecision

from app.agents.invoice_extraction_agent import extract_invoice
from app.agents.invoice_validation_agent import validate_invoice
from app.agents.po_matching_agent import match_invoice_to_po
from app.agents.duplicate_detection_agent import detect_duplicate_invoice
from app.agents.risk_detection_agent import assess_invoice_risk

from app.services.approval_service import evaluate_payment_decision


def get_invoice(state: AccountsPayableState) -> Invoice:
    """
    Reconstruct the validated Invoice model from JSON-compatible state.
    """
    return Invoice.model_validate(state["invoice"])


def extraction_node(state: AccountsPayableState):
    invoice = extract_invoice(state["invoice_text"])

    return {
        "invoice": invoice.model_dump(mode="json"),
        "current_step": "extraction",
    }


def validation_node(state: AccountsPayableState):
    invoice = get_invoice(state)
    result = validate_invoice(invoice)

    return {
        "validation_result": result.model_dump(mode="json"),
        "current_step": "validation",
    }


def po_matching_node(state: AccountsPayableState):
    invoice = get_invoice(state)
    result = match_invoice_to_po(invoice)

    return {
        "po_match_result": result.model_dump(mode="json"),
        "current_step": "po_matching",
    }


def duplicate_detection_node(state: AccountsPayableState):
    invoice = get_invoice(state)

    result = detect_duplicate_invoice(
        invoice=invoice,
        existing_invoices=state.get("existing_invoices", []),
    )

    return {
        "duplicate_result": result,
        "current_step": "duplicate_detection",
    }


def risk_assessment_node(state: AccountsPayableState):
    invoice = get_invoice(state)

    po_result = state["po_match_result"]
    duplicate_result = state["duplicate_result"]

    result = assess_invoice_risk(
        invoice=invoice,
        is_duplicate=duplicate_result.get("is_duplicate", False),
        po_matched=po_result.get("matched", False),
        bank_details_changed=state.get("bank_details_changed", False),
    )

    return {
        "risk_result": result,
        "current_step": "risk_assessment",
    }


def payment_decision_node(state: AccountsPayableState):
    invoice = get_invoice(state)

    validation = state["validation_result"]
    po_match = state["po_match_result"]
    duplicate = state["duplicate_result"]

    # Fail closed: invalid invoices cannot be approved.
    if not validation.get("is_valid", False):
        decision = PaymentDecision(
            invoice_number=invoice.invoice_number,
            status="on_hold",
            reason="Invoice failed validation.",
            requires_human_approval=True,
        )

    elif duplicate.get("is_duplicate", False):
        decision = PaymentDecision(
            invoice_number=invoice.invoice_number,
            status="on_hold",
            reason="Potential duplicate invoice detected.",
            requires_human_approval=True,
        )

    elif not po_match.get("matched", False):
        decision = PaymentDecision(
            invoice_number=invoice.invoice_number,
            status="on_hold",
            reason="Purchase order matching failed or requires review.",
            requires_human_approval=True,
        )

    elif validation.get("warnings") or po_match.get("warnings"):
        decision = PaymentDecision(
            invoice_number=invoice.invoice_number,
            status="on_hold",
            reason="Invoice or purchase order warnings require manual review.",
            requires_human_approval=True,
        )

    else:
        approval_data = state.get("approval")

        approval = (
            ApprovalDecision.model_validate(approval_data)
            if approval_data is not None
            else None
        )

        decision = evaluate_payment_decision(
            invoice_number=invoice.invoice_number,
            risk_result=state["risk_result"],
            approval=approval,
        )

    return {
        "payment_decision": decision.model_dump(mode="json"),
        "current_step": "payment_decision",
    }


# --------------------------------------------------
# LangGraph Workflow
# --------------------------------------------------

builder = StateGraph(AccountsPayableState)

builder.add_node("extraction", extraction_node)
builder.add_node("validation", validation_node)
builder.add_node("po_matching", po_matching_node)
builder.add_node("duplicate_detection", duplicate_detection_node)
builder.add_node("risk_assessment", risk_assessment_node)
builder.add_node("human_approval", human_approval_node)
builder.add_node("payment_decision", payment_decision_node)

builder.add_edge(START, "extraction")
builder.add_edge("extraction", "validation")
builder.add_edge("validation", "po_matching")
builder.add_edge("po_matching", "duplicate_detection")
builder.add_edge("duplicate_detection", "risk_assessment")
builder.add_edge("risk_assessment", "human_approval")
builder.add_edge("human_approval", "payment_decision")
builder.add_edge("payment_decision", END)

# Checkpointing enables interrupt/resume.
checkpointer = MemorySaver()

accounts_payable_graph = builder.compile(
    checkpointer=checkpointer
)
