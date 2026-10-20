
import uuid
from datetime import datetime, timezone

import streamlit as st
from langgraph.types import Command

from app.graph.accounts_payable_graph import accounts_payable_graph


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Accounts Payable Copilot",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SAMPLE INVOICE
# ============================================================

SAMPLE_INVOICE = """Invoice Number: INV-2026-001
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


# ============================================================
# SESSION MANAGEMENT
# ============================================================

def initialize_session():
    defaults = {
        "thread_id": None,
        "result": None,
        "invoice_text": SAMPLE_INVOICE,
        "pending_review": None,
        "workflow_status": "Not started",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session():
    for key in [
        "thread_id",
        "result",
        "pending_review",
        "workflow_status",
        "reviewer_name",
        "review_reason",
    ]:
        st.session_state.pop(key, None)


def get_config():
    return {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


# ============================================================
# DATA HELPERS
# ============================================================

def as_dict(value):
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    return {}


def get_interrupt(result):
    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return None

    return interrupts[0].value


def get_current_state():
    if not st.session_state.thread_id:
        return {}

    snapshot = accounts_payable_graph.get_state(
        get_config()
    )

    return snapshot.values or {}


def get_payment_status(state):
    payment = as_dict(
        state.get("payment_decision")
    )

    return payment.get("status", "unknown")


# ============================================================
# WORKFLOW EXECUTION
# ============================================================

def start_workflow(invoice_text):
    thread_id = str(uuid.uuid4())

    initial_state = {
        "invoice_text": invoice_text,
        "existing_invoices": [],
        "bank_details_changed": False,
        "approval": None,
        "errors": [],
    }

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = accounts_payable_graph.invoke(
        initial_state,
        config=config,
    )

    st.session_state.thread_id = thread_id
    st.session_state.result = result
    st.session_state.pending_review = get_interrupt(result)

    if st.session_state.pending_review:
        st.session_state.workflow_status = (
            "Awaiting human review"
        )
    else:
        st.session_state.workflow_status = "Completed"


def resume_workflow(decision, reviewer, reason):
    review = st.session_state.pending_review

    if not review:
        raise ValueError(
            "No pending human approval request."
        )

    if decision not in {"approved", "rejected"}:
        raise ValueError(
            "Invalid approval decision."
        )

    if not reviewer.strip():
        raise ValueError(
            "Reviewer name is required."
        )

    if not reason.strip():
        raise ValueError(
            "Review reason is required."
        )

    approval = {
        "invoice_number": review["invoice_number"],
        "decision": decision,
        "reviewer": reviewer.strip(),
        "reason": reason.strip(),
        "reviewed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    result = accounts_payable_graph.invoke(
        Command(resume=approval),
        config=get_config(),
    )

    st.session_state.result = result
    st.session_state.pending_review = get_interrupt(result)

    if st.session_state.pending_review:
        st.session_state.workflow_status = (
            "Awaiting human review"
        )
    else:
        st.session_state.workflow_status = "Completed"


# ============================================================
# INITIALIZE
# ============================================================

initialize_session()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Workflow Control")

    st.write("**Current Status**")

    status = st.session_state.workflow_status

    if status == "Awaiting human review":
        st.warning(status)
    elif status == "Completed":
        st.success(status)
    else:
        st.info(status)

    st.divider()

    st.subheader("Processing Pipeline")

    st.markdown(
        """
        1. Invoice Extraction
        2. Invoice Validation
        3. Purchase Order Matching
        4. Duplicate Detection
        5. Risk Assessment
        6. Human Approval
        7. Payment Decision
        """
    )

    st.divider()

    if st.button(
        "🔄 Reset Session",
        use_container_width=True,
    ):
        reset_session()
        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.title("🧾 AI Accounts Payable Copilot")

st.caption(
    "AI-assisted invoice processing, "
    "risk assessment, and human-in-the-loop approvals."
)

st.info(
    "Demo environment: This application evaluates "
    "payment eligibility but never executes real payments."
)


# ============================================================
# INVOICE INPUT
# ============================================================

st.subheader("1. Invoice Processing")

invoice_text = st.text_area(
    "Invoice Content",
    value=st.session_state.invoice_text,
    height=240,
    help="Paste the invoice text to start the workflow.",
)

if st.button(
    "🚀 Process Invoice",
    type="primary",
    use_container_width=True,
):
    if not invoice_text.strip():
        st.error(
            "Please enter invoice content."
        )
    else:
        try:
            with st.spinner(
                "Processing invoice through AI agents..."
            ):
                start_workflow(invoice_text)

            st.session_state.invoice_text = invoice_text

            st.rerun()

        except Exception as error:
            st.error(
                f"Workflow execution failed: {error}"
            )


# ============================================================
# WORKFLOW RESULTS
# ============================================================

if st.session_state.thread_id:

    try:
        state = get_current_state()

    except Exception as error:
        st.error(
            f"Unable to retrieve workflow state: {error}"
        )
        st.stop()

    invoice = as_dict(
        state.get("invoice")
    )

    validation = as_dict(
        state.get("validation_result")
    )

    po_match = as_dict(
        state.get("po_match_result")
    )

    duplicate = as_dict(
        state.get("duplicate_result")
    )

    risk = as_dict(
        state.get("risk_result")
    )

    payment_decision = as_dict(
        state.get("payment_decision")
    )

    st.divider()

    # ========================================================
    # INVOICE OVERVIEW
    # ========================================================

    st.subheader("2. Invoice Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Invoice Number",
            invoice.get(
                "invoice_number",
                "N/A"
            ),
        )

    with col2:
        st.metric(
            "Supplier",
            invoice.get(
                "supplier_name",
                "N/A"
            ),
        )

    with col3:
        amount = invoice.get(
            "total_amount",
            "N/A"
        )

        currency = invoice.get(
            "currency",
            ""
        )

        st.metric(
            "Total Amount",
            f"{amount} {currency}",
        )

    st.divider()

    # ========================================================
    # VERIFICATION RESULTS
    # ========================================================

    st.subheader("3. AI Verification Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.write("**Validation**")

        if validation.get("is_valid"):
            st.success("Passed")
        else:
            st.error("Failed")

    with col2:
        st.write("**PO Matching**")

        if po_match.get("matched"):
            st.success("Matched")
        else:
            st.warning("Not Matched")

    with col3:
        st.write("**Duplicate Detection**")

        if duplicate.get(
            "is_duplicate",
            False
        ):
            st.error("Duplicate Detected")
        else:
            st.success("Unique")

    with col4:
        st.write("**Risk Assessment**")

        risk_level = risk.get(
            "risk_level",
            "unknown"
        )

        if risk_level == "low":
            st.success("Low Risk")

        elif risk_level == "medium":
            st.warning("Medium Risk")

        elif risk_level == "high":
            st.error("High Risk")

        else:
            st.info("Unknown")

    with st.expander(
        "🔍 Detailed Agent Results"
    ):
        st.write("**Invoice Validation**")
        st.json(validation)

        st.write("**Purchase Order Matching**")
        st.json(po_match)

        st.write("**Duplicate Detection**")
        st.json(duplicate)

        st.write("**Risk Assessment**")
        st.json(risk)

    st.divider()

    # ========================================================
    # HUMAN APPROVAL
    # ========================================================

    st.subheader("4. Human Approval")

    review = st.session_state.pending_review

    if review:

        st.warning(
            "Workflow paused. Human approval "
            "is required before continuing."
        )

        review_col1, review_col2 = st.columns(2)

        with review_col1:
            st.write(
                "**Invoice Number:**",
                review.get(
                    "invoice_number",
                    "N/A"
                )
            )

            st.write(
                "**Supplier:**",
                review.get(
                    "supplier_name",
                    "N/A"
                )
            )

        with review_col2:
            st.write(
                "**Amount:**",
                review.get(
                    "total_amount",
                    "N/A"
                )
            )

            st.write(
                "**Risk Level:**",
                review.get(
                    "risk_level",
                    "N/A"
                )
            )

        st.divider()

        reviewer = st.text_input(
            "Reviewer Name",
            key="reviewer_name",
            placeholder="Enter reviewer name",
        )

        reason = st.text_area(
            "Review Reason",
            key="review_reason",
            placeholder="Explain your decision...",
        )

        approve_col, reject_col = st.columns(2)

        with approve_col:

            if st.button(
                "✅ Approve Invoice",
                type="primary",
                use_container_width=True,
            ):
                try:
                    with st.spinner(
                        "Recording human approval..."
                    ):
                        resume_workflow(
                            decision="approved",
                            reviewer=reviewer,
                            reason=reason,
                        )

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Approval failed: {error}"
                    )

        with reject_col:

            if st.button(
                "❌ Reject Invoice",
                use_container_width=True,
            ):
                try:
                    with st.spinner(
                        "Recording human rejection..."
                    ):
                        resume_workflow(
                            decision="rejected",
                            reviewer=reviewer,
                            reason=reason,
                        )

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Rejection failed: {error}"
                    )

    else:

        approval = as_dict(
            state.get("approval")
        )

        if approval:

            if approval.get(
                "decision"
            ) == "approved":

                st.success(
                    "Invoice approved by human reviewer."
                )

            elif approval.get(
                "decision"
            ) == "rejected":

                st.error(
                    "Invoice rejected by human reviewer."
                )

            with st.expander(
                "Human Approval Record"
            ):
                st.json(approval)

        else:
            st.info(
                "No pending human approval request."
            )

    st.divider()

    # ========================================================
    # FINAL PAYMENT DECISION
    # ========================================================

    st.subheader("5. Final Payment Decision")

    if payment_decision:

        payment_status = payment_decision.get(
            "status",
            "unknown"
        )

        if payment_status == "approved_for_payment":

            st.success(
                "✅ Approved for Payment"
            )

        elif payment_status == "rejected":

            st.error(
                "❌ Invoice Rejected"
            )

        elif payment_status == "on_hold":

            st.warning(
                "⚠️ Payment On Hold"
            )

        elif payment_status == "pending_review":

            st.info(
                "⏳ Pending Review"
            )

        else:

            st.info(
                f"Status: {payment_status}"
            )

        st.write(
            "**Decision Reason:**",
            payment_decision.get(
                "reason",
                "No reason provided."
            )
        )

        st.write(
            "**Human Approval Required:**",
            payment_decision.get(
                "requires_human_approval",
                False
            )
        )

        with st.expander(
            "Full Payment Decision"
        ):
            st.json(payment_decision)

    elif review:

        st.info(
            "Final payment decision is pending "
            "human review."
        )

    else:

        st.warning(
            "No payment decision available."
        )

    st.divider()

    # ========================================================
    # WORKFLOW AUDIT
    # ========================================================

    st.subheader("6. Workflow Audit")

    with st.expander(
        "View Workflow State"
    ):
        st.write(
            "**Current Step:**",
            state.get(
                "current_step",
                "unknown"
            )
        )

        st.write(
            "**Workflow Thread ID:**",
            st.session_state.thread_id
        )

        st.write(
            "**Workflow Errors:**"
        )

        st.json(
            state.get(
                "errors",
                []
            )
        )

    st.caption(
        "Security Notice: This application only "
        "determines payment eligibility. "
        "No real financial transactions are executed."
    )
