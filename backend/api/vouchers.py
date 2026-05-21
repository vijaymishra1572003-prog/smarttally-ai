from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.voucher import Voucher

vouchers_bp = Blueprint("vouchers", __name__, url_prefix="/api/vouchers")


@vouchers_bp.route("/", methods=["GET"])
@jwt_required()
def list_vouchers():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Voucher.query.filter_by(user_id=user_id)

    vtype = request.args.get("type")
    if vtype:
        from backend.models.voucher import VoucherType
        query = query.filter_by(voucher_type=VoucherType(vtype))

    synced = request.args.get("tally_synced")
    if synced is not None:
        query = query.filter_by(tally_synced=synced.lower() == "true")

    pagination = query.order_by(Voucher.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "vouchers": [v.to_dict() for v in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


@vouchers_bp.route("/<int:voucher_id>", methods=["GET"])
@jwt_required()
def get_voucher(voucher_id):
    user_id = int(get_jwt_identity())
    voucher = Voucher.query.filter_by(id=voucher_id, user_id=user_id).first()
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    result = voucher.to_dict()
    result["tally_xml"] = voucher.tally_xml
    return jsonify({"voucher": result}), 200


@vouchers_bp.route("/<int:voucher_id>", methods=["DELETE"])
@jwt_required()
def delete_voucher(voucher_id):
    user_id = int(get_jwt_identity())
    voucher = Voucher.query.filter_by(id=voucher_id, user_id=user_id).first()
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    db.session.delete(voucher)
    db.session.commit()
    return jsonify({"message": "Voucher deleted"}), 200
