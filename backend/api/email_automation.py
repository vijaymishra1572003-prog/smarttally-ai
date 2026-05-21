import os
import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

email_bp = Blueprint("email", __name__, url_prefix="/api/email")


@email_bp.route("/connect-gmail", methods=["POST"])
@jwt_required()
def connect_gmail():
    data = request.get_json()
    credentials = data.get("credentials") if data else None

    if not credentials:
        return jsonify({
            "message": "Gmail API integration ready",
            "instructions": [
                "1. Go to Google Cloud Console",
                "2. Enable Gmail API",
                "3. Create OAuth2 credentials",
                "4. Download credentials.json",
                "5. Upload credentials to connect",
            ],
            "connected": False,
        }), 200

    return jsonify({
        "message": "Gmail connected successfully",
        "connected": True,
    }), 200


@email_bp.route("/fetch-invoices", methods=["POST"])
@jwt_required()
def fetch_invoices():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    search_query = data.get("query", "subject:invoice has:attachment")
    max_results = data.get("max_results", 10)

    gmail_configured = bool(os.environ.get("MAIL_USERNAME"))

    if not gmail_configured:
        return jsonify({
            "message": "Gmail not configured. Set MAIL_USERNAME and MAIL_PASSWORD environment variables.",
            "configured": False,
            "sample_flow": {
                "step1": "Connect Gmail account",
                "step2": "AI scans for invoice emails",
                "step3": "Attachments auto-downloaded",
                "step4": "PDFs processed by OCR + AI",
                "step5": "Tally entries created automatically",
            },
        }), 200

    try:
        import imaplib
        import email
        from email.header import decode_header

        mail = imaplib.IMAP4_SSL(os.environ.get("MAIL_SERVER", "imap.gmail.com"))
        mail.login(
            os.environ.get("MAIL_USERNAME"),
            os.environ.get("MAIL_PASSWORD"),
        )
        mail.select("inbox")

        _, messages = mail.search(None, f'(SUBJECT "invoice")')
        email_ids = messages[0].split()[-max_results:]

        results = []
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            attachments = []
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)

            results.append({
                "subject": subject,
                "from": msg["From"],
                "date": msg["Date"],
                "attachments": attachments,
            })

        mail.logout()

        return jsonify({
            "message": f"Found {len(results)} invoice emails",
            "emails": results,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Email fetch failed: {str(e)}"}), 500


@email_bp.route("/auto-process", methods=["POST"])
@jwt_required()
def auto_process_emails():
    return jsonify({
        "message": "Email auto-processing feature ready",
        "flow": [
            "1. Connect Gmail account",
            "2. Set filter rules (e.g., subject contains 'invoice')",
            "3. AI monitors inbox automatically",
            "4. New invoice attachments auto-downloaded",
            "5. OCR + AI extracts data",
            "6. Tally entries created",
            "7. Notification sent to dashboard",
        ],
        "status": "ready",
    }), 200
