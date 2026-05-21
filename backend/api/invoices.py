from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.invoice import Invoice

invoices_bp = Blueprint("invoices", __name__, url_prefix="/api/invoices")


@invoices_bp.route("/", methods=["GET"])
@jwt_required()
def list_invoices():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Invoice.query.filter_by(user_id=user_id)

    vendor = request.args.get("vendor")
    if vendor:
        query = query.filter(Invoice.vendor_name.ilike(f"%{vendor}%"))

    txn_type = request.args.get("transaction_type")
    if txn_type:
        query = query.filter_by(transaction_type=txn_type)

    synced = request.args.get("tally_synced")
    if synced is not None:
        query = query.filter_by(tally_synced=synced.lower() == "true")

    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "invoices": [inv.to_dict() for inv in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    }), 200


@invoices_bp.route("/<int:invoice_id>", methods=["GET"])
@jwt_required()
def get_invoice(invoice_id):
    user_id = int(get_jwt_identity())
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify({"invoice": invoice.to_dict()}), 200


@invoices_bp.route("/<int:invoice_id>", methods=["PUT"])
@jwt_required()
def update_invoice(invoice_id):
    user_id = int(get_jwt_identity())
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    data = request.get_json()
    updatable = [
        "invoice_number", "vendor_name", "vendor_gstin", "buyer_name",
        "buyer_gstin", "subtotal", "cgst", "sgst", "igst", "total_gst",
        "total_amount", "hsn_code", "description", "transaction_type",
        "ledger_category", "voucher_type",
    ]

    for field in updatable:
        if field in data:
            setattr(invoice, field, data[field])

    db.session.commit()
    return jsonify({"message": "Invoice updated", "invoice": invoice.to_dict()}), 200


@invoices_bp.route("/<int:invoice_id>", methods=["DELETE"])
@jwt_required()
def delete_invoice(invoice_id):
    user_id = int(get_jwt_identity())
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=user_id).first()
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    db.session.delete(invoice)
    db.session.commit()
    return jsonify({"message": "Invoice deleted"}), 200
