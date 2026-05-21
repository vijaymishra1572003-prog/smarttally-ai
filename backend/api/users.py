from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.user import User, Role
from backend.models.logs import AuditLog
from backend.api.auth import role_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("/", methods=["GET"])
@role_required(Role.SUPER_ADMIN, Role.CA_ADMIN)
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = User.query
    role_filter = request.args.get("role")
    if role_filter:
        query = query.filter_by(role=Role(role_filter))

    search = request.args.get("search")
    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "users": [u.to_dict() for u in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


@users_bp.route("/<int:uid>", methods=["GET"])
@role_required(Role.SUPER_ADMIN, Role.CA_ADMIN)
def get_user(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@users_bp.route("/", methods=["POST"])
@role_required(Role.SUPER_ADMIN, Role.CA_ADMIN)
def create_user():
    data = request.get_json()
    required = ["email", "password", "full_name"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"'{field}' is required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 409

    user = User(
        email=data["email"],
        full_name=data["full_name"],
        phone=data.get("phone"),
        role=Role(data.get("role", "client_user")),
        company_id=data.get("company_id"),
        is_verified=True,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    admin_id = int(get_jwt_identity())
    audit = AuditLog(
        action="create_user",
        entity_type="user",
        entity_id=user.id,
        new_values={"email": user.email, "role": user.role.value},
        user_id=admin_id,
        ip_address=request.remote_addr,
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({"message": "User created", "user": user.to_dict()}), 201


@users_bp.route("/<int:uid>", methods=["PUT"])
@role_required(Role.SUPER_ADMIN, Role.CA_ADMIN)
def update_user(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "phone" in data:
        user.phone = data["phone"]
    if "role" in data:
        user.role = Role(data["role"])
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "company_id" in data:
        user.company_id = data["company_id"]
    if "password" in data:
        user.set_password(data["password"])

    db.session.commit()
    return jsonify({"message": "User updated", "user": user.to_dict()}), 200


@users_bp.route("/<int:uid>", methods=["DELETE"])
@role_required(Role.SUPER_ADMIN)
def delete_user(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.is_active = False
    db.session.commit()
    return jsonify({"message": "User deactivated"}), 200


@users_bp.route("/activity-logs", methods=["GET"])
@role_required(Role.SUPER_ADMIN, Role.CA_ADMIN)
def activity_logs():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    logs = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "logs": [l.to_dict() for l in logs.items],
        "total": logs.total,
        "pages": logs.pages,
    }), 200
