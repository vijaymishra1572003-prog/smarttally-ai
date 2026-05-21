import json
import re
import os
import logging

logger = logging.getLogger(__name__)

LEDGER_MAP = {
    "swiggy": {"category": "Food Expense", "group": "Indirect Expenses"},
    "zomato": {"category": "Food Expense", "group": "Indirect Expenses"},
    "amazon": {"category": "Purchase Account", "group": "Purchase Accounts"},
    "flipkart": {"category": "Purchase Account", "group": "Purchase Accounts"},
    "jio": {"category": "Internet Expense", "group": "Indirect Expenses"},
    "airtel": {"category": "Telephone Expense", "group": "Indirect Expenses"},
    "vodafone": {"category": "Telephone Expense", "group": "Indirect Expenses"},
    "petrol": {"category": "Fuel Expense", "group": "Indirect Expenses"},
    "diesel": {"category": "Fuel Expense", "group": "Indirect Expenses"},
    "hp petrol": {"category": "Fuel Expense", "group": "Indirect Expenses"},
    "indian oil": {"category": "Fuel Expense", "group": "Indirect Expenses"},
    "bharat petroleum": {"category": "Fuel Expense", "group": "Indirect Expenses"},
    "electricity": {"category": "Electricity Expense", "group": "Indirect Expenses"},
    "rent": {"category": "Rent Expense", "group": "Indirect Expenses"},
    "salary": {"category": "Salary Expense", "group": "Indirect Expenses"},
    "insurance": {"category": "Insurance Expense", "group": "Indirect Expenses"},
    "stationery": {"category": "Stationery Expense", "group": "Indirect Expenses"},
    "courier": {"category": "Courier Expense", "group": "Indirect Expenses"},
    "travel": {"category": "Travel Expense", "group": "Indirect Expenses"},
    "hotel": {"category": "Travel Expense", "group": "Indirect Expenses"},
    "uber": {"category": "Travel Expense", "group": "Indirect Expenses"},
    "ola": {"category": "Travel Expense", "group": "Indirect Expenses"},
    "office": {"category": "Office Expense", "group": "Indirect Expenses"},
    "maintenance": {"category": "Maintenance Expense", "group": "Indirect Expenses"},
    "bank": {"category": "Bank Charges", "group": "Indirect Expenses"},
    "interest": {"category": "Interest Expense", "group": "Indirect Expenses"},
    "professional": {"category": "Professional Fees", "group": "Indirect Expenses"},
    "legal": {"category": "Legal Expense", "group": "Indirect Expenses"},
    "advertising": {"category": "Advertising Expense", "group": "Indirect Expenses"},
    "marketing": {"category": "Marketing Expense", "group": "Indirect Expenses"},
    "software": {"category": "Software Expense", "group": "Indirect Expenses"},
    "subscription": {"category": "Subscription Expense", "group": "Indirect Expenses"},
    "sales": {"category": "Sales Account", "group": "Sales Accounts"},
}


class AIProcessor:
    """AI-powered invoice data extraction and classification."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")

    def extract_invoice_data(self, text):
        if not text or text.strip() == "":
            return self._empty_result()

        if self.api_key:
            try:
                return self._extract_with_openai(text)
            except Exception as e:
                logger.warning(f"OpenAI extraction failed: {e}")

        return self._extract_with_rules(text)

    def _extract_with_openai(self, text):
        import openai
        client = openai.OpenAI(api_key=self.api_key)

        prompt = f"""Analyze this invoice/document text and extract the following information as JSON:
{{
    "invoice_number": "string or null",
    "invoice_date": "YYYY-MM-DD or null",
    "vendor_name": "string or null",
    "vendor_gstin": "15-char GSTIN or null",
    "buyer_name": "string or null",
    "buyer_gstin": "15-char GSTIN or null",
    "subtotal": number,
    "cgst": number,
    "sgst": number,
    "igst": number,
    "total_gst": number,
    "total_amount": number,
    "hsn_code": "string or null",
    "description": "brief description",
    "transaction_type": "Sales or Purchase",
    "ledger_category": "appropriate ledger category",
    "voucher_type": "Sales/Purchase/Receipt/Payment/Journal",
    "debit_ledger": "ledger name",
    "credit_ledger": "ledger name"
}}

Document text:
{text[:3000]}

Return ONLY valid JSON, no other text."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert Indian accountant and GST specialist. Extract invoice data accurately."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1000,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"```json?\s*", "", content)
            content = content.rstrip("`").strip()

        return json.loads(content)

    def _extract_with_rules(self, text):
        result = self._empty_result()
        text_upper = text.upper()
        text_lower = text.lower()

        gstin_pattern = r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}"
        gstins = re.findall(gstin_pattern, text_upper)
        if len(gstins) >= 2:
            result["vendor_gstin"] = gstins[0]
            result["buyer_gstin"] = gstins[1]
        elif len(gstins) == 1:
            result["vendor_gstin"] = gstins[0]

        inv_patterns = [
            r"(?:Invoice\s*(?:No|Number|#|Num)[\s.:]*)\s*([A-Z0-9/-]+)",
            r"(?:Bill\s*(?:No|Number|#)[\s.:]*)\s*([A-Z0-9/-]+)",
            r"(?:INV[\s-]*)\s*([A-Z0-9/-]+)",
        ]
        for pat in inv_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                result["invoice_number"] = match.group(1).strip()
                break

        date_patterns = [
            r"(\d{2}[-/]\d{2}[-/]\d{4})",
            r"(\d{4}[-/]\d{2}[-/]\d{2})",
            r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
        ]
        for pat in date_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                result["invoice_date"] = self._parse_date(date_str)
                break

        amount_patterns = [
            (r"(?:Total|Grand\s*Total|Net\s*Amount|Amount\s*Payable)[\s.:]*(?:Rs\.?|INR|₹)?\s*([\d,]+\.?\d*)", "total_amount"),
            (r"(?:Sub\s*Total|Taxable\s*Value|Base\s*Amount)[\s.:]*(?:Rs\.?|INR|₹)?\s*([\d,]+\.?\d*)", "subtotal"),
            (r"(?:CGST|Central\s*GST)[\s@\d%.]*(?:Rs\.?|INR|₹)?\s*([\d,]+\.?\d*)", "cgst"),
            (r"(?:SGST|State\s*GST)[\s@\d%.]*(?:Rs\.?|INR|₹)?\s*([\d,]+\.?\d*)", "sgst"),
            (r"(?:IGST|Integrated\s*GST)[\s@\d%.]*(?:Rs\.?|INR|₹)?\s*([\d,]+\.?\d*)", "igst"),
        ]
        for pat, key in amount_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = match.group(1).replace(",", "")
                try:
                    result[key] = float(val)
                except ValueError:
                    pass

        if result["cgst"] or result["sgst"] or result["igst"]:
            result["total_gst"] = result["cgst"] + result["sgst"] + result["igst"]

        if result["subtotal"] and result["total_gst"] and not result["total_amount"]:
            result["total_amount"] = result["subtotal"] + result["total_gst"]

        hsn_match = re.search(r"(?:HSN|SAC)[\s.:]*(\d{4,8})", text, re.IGNORECASE)
        if hsn_match:
            result["hsn_code"] = hsn_match.group(1)

        result["ledger_category"] = self._detect_ledger(text_lower)
        result["voucher_type"] = self._detect_voucher_type(text_lower)
        result["transaction_type"] = result["voucher_type"]
        result["vendor_name"] = self._extract_vendor(text)

        if result["voucher_type"] == "Purchase":
            result["debit_ledger"] = result["ledger_category"] or "Purchase Account"
            result["credit_ledger"] = result["vendor_name"] or "Sundry Creditors"
        else:
            result["debit_ledger"] = result["vendor_name"] or "Sundry Debtors"
            result["credit_ledger"] = "Sales Account"

        lines = text.split("\n")
        desc_parts = [l.strip() for l in lines[:3] if l.strip()]
        result["description"] = " | ".join(desc_parts)[:200]

        return result

    def _detect_ledger(self, text):
        for keyword, info in LEDGER_MAP.items():
            if keyword in text:
                return info["category"]
        return "Miscellaneous Expense"

    def _detect_voucher_type(self, text):
        sale_keywords = ["sales invoice", "tax invoice", "sold to", "bill to", "ship to"]
        purchase_keywords = ["purchase", "bought", "supplier", "vendor invoice"]
        receipt_keywords = ["receipt", "received", "payment received"]
        payment_keywords = ["payment", "paid to", "expense"]

        for kw in sale_keywords:
            if kw in text:
                return "Sales"
        for kw in purchase_keywords:
            if kw in text:
                return "Purchase"
        for kw in receipt_keywords:
            if kw in text:
                return "Receipt"
        for kw in payment_keywords:
            if kw in text:
                return "Payment"
        return "Purchase"

    def _extract_vendor(self, text):
        lines = text.strip().split("\n")
        for line in lines[:5]:
            clean = line.strip()
            if clean and len(clean) > 3 and not re.match(r"^\d+$", clean):
                if not re.match(r"^(invoice|bill|tax|gst|date|no|number)", clean, re.IGNORECASE):
                    return clean[:100]
        return None

    def _parse_date(self, date_str):
        import re as _re
        m = _re.match(r"(\d{2})[-/](\d{2})[-/](\d{4})", date_str)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        m = _re.match(r"(\d{4})[-/](\d{2})[-/](\d{2})", date_str)
        if m:
            return date_str.replace("/", "-")
        return None

    def _empty_result(self):
        return {
            "invoice_number": None,
            "invoice_date": None,
            "vendor_name": None,
            "vendor_gstin": None,
            "buyer_name": None,
            "buyer_gstin": None,
            "subtotal": 0,
            "cgst": 0,
            "sgst": 0,
            "igst": 0,
            "total_gst": 0,
            "total_amount": 0,
            "hsn_code": None,
            "description": None,
            "transaction_type": "Purchase",
            "ledger_category": "Miscellaneous Expense",
            "voucher_type": "Purchase",
            "debit_ledger": "Purchase Account",
            "credit_ledger": "Sundry Creditors",
        }
