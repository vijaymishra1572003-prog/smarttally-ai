import os
import re
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

MONTH_MAP = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12,
}


class ChatbotService:
    """AI chatbot for accounting queries."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")

    def process_query(self, query, user_id):
        query_lower = query.lower().strip()

        if any(kw in query_lower for kw in ["gst report", "gst summary", "gst details"]):
            return self._handle_gst_query(query_lower, user_id)

        if any(kw in query_lower for kw in ["purchase summary", "purchase report"]):
            return self._handle_purchase_summary(query_lower, user_id)

        if any(kw in query_lower for kw in ["pending invoice", "unpaid", "outstanding"]):
            return self._handle_pending_invoices(user_id)

        if any(kw in query_lower for kw in ["sales summary", "sales report", "revenue"]):
            return self._handle_sales_summary(query_lower, user_id)

        if any(kw in query_lower for kw in ["tally status", "tally sync", "sync status"]):
            return self._handle_tally_status(user_id)

        if any(kw in query_lower for kw in ["help", "what can you do", "commands"]):
            return self._handle_help()

        if self.api_key:
            return self._handle_with_ai(query, user_id)

        return {
            "response": "I can help you with:\n"
                        "- 'Show March GST report'\n"
                        "- 'Generate purchase summary'\n"
                        "- 'Show pending invoices'\n"
                        "- 'Sales summary for April'\n"
                        "- 'Tally sync status'\n"
                        "Try one of these commands!",
            "type": "help",
        }

    def _handle_gst_query(self, query, user_id):
        from backend.extensions import db
        from backend.models.invoice import Invoice
        from sqlalchemy import func

        month = self._extract_month(query)
        year = self._extract_year(query)

        q = Invoice.query.filter_by(user_id=user_id)
        if month:
            q = q.filter(func.month(Invoice.invoice_date) == month)
        if year:
            q = q.filter(func.year(Invoice.invoice_date) == year)

        total_cgst = db.session.query(func.sum(Invoice.cgst)).filter(Invoice.user_id == user_id).scalar() or 0
        total_sgst = db.session.query(func.sum(Invoice.sgst)).filter(Invoice.user_id == user_id).scalar() or 0
        total_igst = db.session.query(func.sum(Invoice.igst)).filter(Invoice.user_id == user_id).scalar() or 0
        total_gst = float(total_cgst) + float(total_sgst) + float(total_igst)

        period = ""
        if month:
            month_names = ["", "January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"]
            period = f" for {month_names[month]}"
        if year:
            period += f" {year}"

        return {
            "response": f"GST Summary{period}:\n"
                        f"CGST: ₹{float(total_cgst):,.2f}\n"
                        f"SGST: ₹{float(total_sgst):,.2f}\n"
                        f"IGST: ₹{float(total_igst):,.2f}\n"
                        f"Total GST: ₹{total_gst:,.2f}",
            "type": "gst_summary",
            "data": {
                "cgst": float(total_cgst),
                "sgst": float(total_sgst),
                "igst": float(total_igst),
                "total": total_gst,
            },
        }

    def _handle_purchase_summary(self, query, user_id):
        from backend.extensions import db
        from backend.models.invoice import Invoice
        from sqlalchemy import func

        total_purchases = Invoice.query.filter_by(
            user_id=user_id, transaction_type="Purchase"
        ).count()
        total_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.user_id == user_id, Invoice.transaction_type == "Purchase"
        ).scalar() or 0

        return {
            "response": f"Purchase Summary:\n"
                        f"Total Purchases: {total_purchases}\n"
                        f"Total Amount: ₹{float(total_amount):,.2f}",
            "type": "purchase_summary",
        }

    def _handle_pending_invoices(self, user_id):
        from backend.models.invoice import Invoice

        pending = Invoice.query.filter_by(user_id=user_id, tally_synced=False).count()
        return {
            "response": f"You have {pending} invoices pending Tally sync.",
            "type": "pending_invoices",
            "count": pending,
        }

    def _handle_sales_summary(self, query, user_id):
        from backend.extensions import db
        from backend.models.invoice import Invoice
        from sqlalchemy import func

        total_sales = Invoice.query.filter_by(
            user_id=user_id, transaction_type="Sales"
        ).count()
        total_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.user_id == user_id, Invoice.transaction_type == "Sales"
        ).scalar() or 0

        return {
            "response": f"Sales Summary:\n"
                        f"Total Sales: {total_sales}\n"
                        f"Total Revenue: ₹{float(total_amount):,.2f}",
            "type": "sales_summary",
        }

    def _handle_tally_status(self, user_id):
        from tally_api.tally_service import TallyService
        service = TallyService()
        status = service.check_connection()

        return {
            "response": f"Tally Status: {'Connected' if status['connected'] else 'Disconnected'}\n"
                        f"{status['message']}",
            "type": "tally_status",
            "connected": status["connected"],
        }

    def _handle_help(self):
        return {
            "response": "Available commands:\n"
                        "📊 'Show March GST report' - View GST summary\n"
                        "🛒 'Generate purchase summary' - Purchase overview\n"
                        "📋 'Show pending invoices' - Unsynced invoices\n"
                        "💰 'Sales summary for April' - Sales overview\n"
                        "🔗 'Tally sync status' - Check Tally connection\n"
                        "❓ 'Help' - Show this message",
            "type": "help",
        }

    def _handle_with_ai(self, query, user_id):
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are SmartTally AI assistant, an expert in Indian accounting, GST, and Tally Prime. Help users with their accounting queries concisely."},
                    {"role": "user", "content": query},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return {
                "response": response.choices[0].message.content,
                "type": "ai_response",
            }
        except Exception as e:
            return {
                "response": f"AI processing error. Try specific commands like 'Show GST report'.",
                "type": "error",
            }

    def _extract_month(self, query):
        for name, num in MONTH_MAP.items():
            if name in query:
                return num
        return None

    def _extract_year(self, query):
        match = re.search(r"20\d{2}", query)
        if match:
            return int(match.group())
        return None
