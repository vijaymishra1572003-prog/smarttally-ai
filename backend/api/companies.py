from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.company import Company
from backend.models.user import User, Role
from backend.api.auth import role_required

companies_bp = Blueprint("companies", __name__, url_prefix="/api/companies")


@companies_bp.route("/", methods=["GET"])
@jwt_required()
def list_companies():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user.role in (Role.SUPER_ADMIN, Role.CA_ADMIN):
        companies = Company.query.all()
    else:
        companies = Company.query.filter_by(id=user.company_id).all() if user.company_id else []

    return jsonify({
        "companies": [c.to_dict() for c in companies],
    }), 200


@companies_bp.route("/", methods=["POST"])
@role_required(Role.SUPER_ADMIN, Role.CA_ADMIN)
def create_company():
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Company name is required"}), 400

    company = Company(
        name=data["name"],
        gstin=data.get("gstin"),
        pan=data.get("pan"),
        address=data.get("address"),
        city=data.get("city"),
        state=data.get("state"),
        pincode=data.get("pincode"),
        phone=data.get("phone"),
        email=data.get("email"),
        tally_company_name=data.get("tally_company_name"),
    )
    db.session.add(company)
    db.session.commit()

    return jsonify({"message": "Company created", "company": company.to_dict()}), 201


@companies_bp.route("/<int:company_id>", methods=["GET"])
@jwt_required()
def get_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    return jsonify({"company": company.to_dict()}), 200


@companies_bp.route("/<int:company_id>", methods=["PUT"])
@role_required(Role.SUPER_ADMIN, Role.CA_ADMIN)
def update_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404

    data = request.get_json()
    for field in ["name", "gstin", "pan", "address", "city", "state", "pincode",
                   "phone", "email", "tally_company_name"]:
        if field in data:
            setattr(company, field, data[field])

    db.session.commit()
    return jsonify({"message": "Company updated", "company": company.to_dict()}), 200


@companies_bp.route("/<int:company_id>", methods=["DELETE"])
@role_required(Role.SUPER_ADMIN)
def delete_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404

    db.session.delete(company)
    db.session.commit()
    return jsonify({"message": "Company deleted"}), 200
