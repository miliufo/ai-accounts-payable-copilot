
from typing import Any

from app.models.invoice import Invoice


def detect_duplicate_invoice(
    invoice: Invoice,
    existing_invoices: list[dict[str, Any]],
) -> dict:
    """
    Detect duplicate invoices using supplier name
    and invoice number.

    This is an exact-match baseline. Persistent storage
    and advanced duplicate detection will be added later.
    """

    supplier = invoice.supplier_name.strip().casefold()
    invoice_number = invoice.invoice_number.strip().casefold()

    for existing in existing_invoices:
        existing_supplier = str(
            existing.get("supplier_name") or ""
        ).strip().casefold()

        existing_number = str(
            existing.get("invoice_number") or ""
        ).strip().casefold()

        if (
            supplier == existing_supplier
            and invoice_number == existing_number
        ):
            return {
                "is_duplicate": True,
                "status": "duplicate",
                "reason": (
                    "An invoice with the same supplier "
                    "and invoice number already exists."
                ),
                "matched_invoice": existing,
            }

    return {
        "is_duplicate": False,
        "status": "unique",
        "reason": "No matching invoice found.",
        "matched_invoice": None,
    }
