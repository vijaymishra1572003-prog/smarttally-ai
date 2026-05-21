from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.ledger import Ledger

ledgers_bp = Blueprint("ledgers", __name__, url_prefix="/api/ledgers")


@ledgers_bp.route("/", methods=["GET"])
@jwt_required()
def list_ledgers():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    query = Ledger.query
    group = request.args.get("group")
    if group:
        query = query.filter_by(group_name=group)

    search = request.args.get("search")
    if search:
        query = query.filter(Ledger.name.ilike(f"%{search}%"))

    pagination = query.order_by(Ledger.name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "ledgers": [l.to_dict() for l in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


@ledgers_bp.route("/", methods=["POST"])
@jwt_required()
def create_ledger():
    data = request.get_json()
    if not data or "name" not in data or "group_name" not in data:
        return jsonify({"error": "Name and group_name are required"}), 400

    ledger = Ledger(
        name=data["name"],
        group_name=data["group_name"],
        parent_group=data.get("parent_group"),
        gstin=data.get("gstin"),
        opening_balance=float(data.get("opening_balance", 0)),
        is_revenue=data.get("is_revenue", False),
        is_deemed_positive=data.get("is_deemed_positive", False),
        company_id=data.get("company_id"),
    )
    db.session.add(ledger)
    db.session.commit()

    return jsonify({"message": "Ledger created", "ledger": ledger.to_dict()}), 201


@ledgers_bp.route("/<int:ledger_id>", methods=["PUT"])
@jwt_required()
def update_ledger(ledger_id):
    ledger = Ledger.query.get(ledger_id)
    if not ledger:
        return jsonify({"error": "Ledger not found"}), 404

    data = request.get_json()
    for field in ["name", "group_name", "parent_group", "gstin",
                   "opening_balance", "is_revenue", "is_deemed_positive"]:
        if field in data:
            setattr(ledger, field, data[field])

    db.session.commit()
    return jsonify({"message": "Ledger updated", "ledger": ledger.to_dict()}), 200


@ledgers_bp.route("/<int:ledger_id>", methods=["DELETE"])
@jwt_required()
def delete_ledger(ledger_id):
    ledger = Ledger.query.get(ledger_id)
    if not ledger:
        return jsonify({"error": "Ledger not found"}), 404

    db.session.delete(ledger)
    db.session.commit()
    return jsonify({"message": "Ledger deleted"}), 200
