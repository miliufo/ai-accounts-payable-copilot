
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_number: str = Field(min_length=1)

    decision: Literal[
        "approved",
        "rejected",
    ]

    reviewer: str = Field(min_length=1)

    reason: str = Field(min_length=1)

    reviewed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class PaymentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_number: str

    status: Literal[
        "pending_review",
        "on_hold",
        "approved_for_payment",
        "rejected",
    ]

    reason: str

    requires_human_approval: bool

    approval: Optional[ApprovalDecision] = None
