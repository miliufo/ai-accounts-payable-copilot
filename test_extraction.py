
from pathlib import Path
from app.agents.invoice_extraction_agent import extract_invoice

def main():
    invoice_path = Path("data/invoices/sample_invoice.txt")

    invoice_text = invoice_path.read_text(encoding="utf-8")

    print("\n📄 Extracting invoice information...\n")

    invoice = extract_invoice(invoice_text)

    print("✅ INVOICE EXTRACTION RESULT")
    print("=" * 45)
    print(invoice.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
