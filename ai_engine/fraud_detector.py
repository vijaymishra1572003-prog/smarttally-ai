import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FraudDetector:
    """AI-powered fraud detection for invoices and transactions."""

    RULES = [
        {"name": "duplicate_invoice", "description": "Duplicate invoice number detected"},
        {"name": "high_amount", "description": "Unusually high transaction amount", "threshold": 1000000},
        {"name": "round_amount", "description": "Suspicious round amount"},
        {"name": "weekend_invoice", "description": "Invoice dated on weekend"},
        {"name": "future_date", "description": "Invoice date is in the future"},
        {"name": "invalid_gstin", "description": "Invalid GSTIN format"},
        {"name": "gst_mismatch", "description": "GST calculation mismatch"},
    ]

    def analyze(self, invoice_data, existing_invoices=None):
        alerts = []

        if existing_invoices and invoice_data.get("invoice_number"):
            for inv in existing_invoices:
                if inv.get("invoice_number") == invoice_data["invoice_number"]:
                    alerts.append({
                        "rule": "duplicate_invoice",
                        "severity": "high",
                        "message": f"Duplicate invoice: {invoice_data['invoice_number']}",
                    })
                    break

        total = invoice_data.get("total_amount", 0)
        if total > 1000000:
            alerts.append({
                "rule": "high_amount",
                "severity": "medium",
                "message": f"High amount: Rs. {total:,.2f}",
            })

        if total > 0 and total == int(total) and total >= 10000:
            alerts.append({
                "rule": "round_amount",
                "severity": "low",
                "message": f"Suspicious round amount: Rs. {total:,.2f}",
            })

        inv_date = invoice_data.get("invoice_date")
        if inv_date:
            try:
                if isinstance(inv_date, str):
                    dt = datetime.strptime(inv_date, "%Y-%m-%d")
                else:
                    dt = inv_date
                if dt.weekday() >= 5:
                    alerts.append({
                        "rule": "weekend_invoice",
                        "severity": "low",
                        "message": f"Invoice dated on {dt.strftime('%A')}",
                    })
                if dt > datetime.now():
                    alerts.append({
                        "rule": "future_date",
                        "severity": "high",
                        "message": "Invoice date is in the future",
                    })
            except (ValueError, TypeError):
                pass

        gstin = invoice_data.get("vendor_gstin") or invoice_data.get("buyer_gstin")
        if gstin and len(gstin) != 15:
            alerts.append({
                "rule": "invalid_gstin",
                "severity": "high",
                "message": f"Invalid GSTIN length: {gstin}",
            })

        subtotal = invoice_data.get("subtotal", 0)
        cgst = invoice_data.get("cgst", 0)
        sgst = invoice_data.get("sgst", 0)
        igst = invoice_data.get("igst", 0)
        total_gst = cgst + sgst + igst
        if subtotal > 0 and total_gst > 0:
            expected_total = subtotal + total_gst
            if abs(expected_total - total) > 1:
                alerts.append({
                    "rule": "gst_mismatch",
                    "severity": "medium",
                    "message": f"Amount mismatch: expected {expected_total:.2f}, got {total:.2f}",
                })

        risk_score = sum(
            3 if a["severity"] == "high" else 2 if a["severity"] == "medium" else 1
            for a in alerts
        )

        return {
            "alerts": alerts,
            "risk_score": min(risk_score, 10),
            "risk_level": "high" if risk_score >= 5 else "medium" if risk_score >= 3 else "low",
        }
