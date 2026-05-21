import os
import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

import requests as http_requests

logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint("whatsapp", __name__, url_prefix="/api/whatsapp")


@whatsapp_bp.route("/send-invoice", methods=["POST"])
@jwt_required()
def send_invoice():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or "phone" not in data or "invoice_id" not in data:
        return jsonify({"error": "Phone number and invoice_id are required"}), 400

    from backend.models.invoice import Invoice
    invoice = Invoice.query.filter_by(id=data["invoice_id"], user_id=user_id).first()
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    api_key = os.environ.get("WHATSAPP_API_KEY")
    if not api_key:
        return jsonify({
            "message": "WhatsApp API not configured. Invoice details prepared.",
            "invoice_summary": {
                "invoice_number": invoice.invoice_number,
                "vendor": invoice.vendor_name,
                "amount": invoice.total_amount,
                "gst": invoice.total_gst,
            },
            "whatsapp_configured": False,
        }), 200

    message = (
        f"📄 *Invoice Details*\n\n"
        f"Invoice No: {invoice.invoice_number}\n"
        f"Vendor: {invoice.vendor_name}\n"
        f"Amount: ₹{invoice.total_amount:,.2f}\n"
        f"GST: ₹{invoice.total_gst:,.2f}\n"
        f"Date: {invoice.invoice_date}\n\n"
        f"_Sent via SmartTally AI_"
    )

    try:
        resp = http_requests.post(
            "https://api.whatsapp.com/send",
            json={"phone": data["phone"], "message": message},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        return jsonify({"message": "Invoice sent via WhatsApp", "status": resp.status_code}), 200
    except Exception as e:
        return jsonify({"error": f"WhatsApp send failed: {str(e)}"}), 500


@whatsapp_bp.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.get_json()
    logger.info(f"WhatsApp webhook received: {data}")

    if data and data.get("type") == "document":
        logger.info("Document received via WhatsApp - queued for processing")

    return jsonify({"status": "received"}), 200
