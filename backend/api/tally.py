from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.voucher import Voucher
from backend.models.ledger import Ledger
from backend.models.invoice import Invoice
from backend.models.logs import TallyLog
from tally_api.tally_service import TallyService

tally_bp = Blueprint("tally", __name__, url_prefix="/api/tally")


@tally_bp.route("/status", methods=["GET"])
@jwt_required()
def tally_status():
    service = TallyService()
    status = service.check_connection()
    return jsonify(status), 200


@tally_bp.route("/sync/voucher/<int:voucher_id>", methods=["POST"])
@jwt_required()
def sync_voucher(voucher_id):
    user_id = int(get_jwt_identity())
    voucher = Voucher.query.filter_by(id=voucher_id, user_id=user_id).first()
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    service = TallyService()
    invoice = Invoice.query.get(voucher.invoice_id) if voucher.invoice_id else None

    if not voucher.tally_xml:
        voucher.tally_xml = service.generate_voucher_xml(voucher, invoice)

    result = service.push_voucher(voucher.tally_xml)

    log = TallyLog(
        action="sync_voucher",
        request_xml=voucher.tally_xml,
        response_xml=result.get("response", ""),
        status="success" if result.get("success") else "error",
        error_message=result.get("error"),
        voucher_id=voucher.id,
        company_id=voucher.company_id,
        user_id=user_id,
    )
    db.session.add(log)

    if result.get("success"):
        voucher.tally_synced = True
        from datetime import datetime
        voucher.tally_sync_time = datetime.utcnow()

    db.session.commit()

    return jsonify(result), 200 if result.get("success") else 500


@tally_bp.route("/sync/ledger/<int:ledger_id>", methods=["POST"])
@jwt_required()
def sync_ledger(ledger_id):
    user_id = int(get_jwt_identity())
    ledger = Ledger.query.get(ledger_id)
    if not ledger:
        return jsonify({"error": "Ledger not found"}), 404

    service = TallyService()
    if not ledger.tally_xml:
        ledger.tally_xml = service.generate_ledger_xml(ledger)

    result = service.push_ledger(ledger.tally_xml)

    log = TallyLog(
        action="sync_ledger",
        request_xml=ledger.tally_xml,
        response_xml=result.get("response", ""),
        status="success" if result.get("success") else "error",
        error_message=result.get("error"),
        ledger_id=ledger.id,
        company_id=ledger.company_id,
        user_id=user_id,
    )
    db.session.add(log)

    if result.get("success"):
        ledger.tally_synced = True

    db.session.commit()
    return jsonify(result), 200 if result.get("success") else 500


@tally_bp.route("/sync/bulk", methods=["POST"])
@jwt_required()
def bulk_sync():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    voucher_ids = data.get("voucher_ids", [])

    if not voucher_ids:
        unsynced = Voucher.query.filter_by(user_id=user_id, tally_synced=False).all()
        voucher_ids = [v.id for v in unsynced]

    service = TallyService()
    results = []

    for vid in voucher_ids:
        voucher = Voucher.query.get(vid)
        if not voucher:
            continue

        invoice = Invoice.query.get(voucher.invoice_id) if voucher.invoice_id else None
        if not voucher.tally_xml:
            voucher.tally_xml = service.generate_voucher_xml(voucher, invoice)

        result = service.push_voucher(voucher.tally_xml)

        log = TallyLog(
            action="bulk_sync_voucher",
            request_xml=voucher.tally_xml,
            response_xml=result.get("response", ""),
            status="success" if result.get("success") else "error",
            error_message=result.get("error"),
            voucher_id=voucher.id,
            company_id=voucher.company_id,
            user_id=user_id,
        )
        db.session.add(log)

        if result.get("success"):
            voucher.tally_synced = True
            from datetime import datetime
            voucher.tally_sync_time = datetime.utcnow()

        results.append({"voucher_id": vid, "success": result.get("success", False)})

    db.session.commit()
    return jsonify({"results": results}), 200


@tally_bp.route("/logs", methods=["GET"])
@jwt_required()
def tally_logs():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    logs = TallyLog.query.filter_by(user_id=user_id).order_by(
        TallyLog.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "logs": [l.to_dict() for l in logs.items],
        "total": logs.total,
        "pages": logs.pages,
    }), 200


@tally_bp.route("/companies", methods=["GET"])
@jwt_required()
def fetch_tally_companies():
    service = TallyService()
    result = service.fetch_companies()
    return jsonify(result), 200


@tally_bp.route("/ledgers", methods=["GET"])
@jwt_required()
def fetch_tally_ledgers():
    service = TallyService()
    company = request.args.get("company", "")
    result = service.fetch_ledgers(company)
    return jsonify(result), 200
