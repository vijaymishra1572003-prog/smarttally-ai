import random
import string
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)

from backend.extensions import db, limiter
from backend.models.user import User, Role
from backend.models.logs import AuditLog

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            if not user or user.role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_otp():
    return "".join(random.choices(string.digits, k=6))


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10/hour")
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["email", "password", "full_name"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"'{field}' is required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        email=data["email"],
        full_name=data["full_name"],
        phone=data.get("phone"),
        role=Role(data.get("role", "client_user")),
    )
    user.set_password(data["password"])
    user.otp_secret = generate_otp()

    db.session.add(user)
    db.session.commit()

    audit = AuditLog(
        action="user_registered",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        ip_address=request.remote_addr,
    )
    db.session.add(audit)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Registration successful",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "otp": user.otp_secret,
    }), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20/hour")
def login():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    audit = AuditLog(
        action="user_login",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        ip_address=request.remote_addr,
    )
    db.session.add(audit)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 200


@auth_bp.route("/verify-otp", methods=["POST"])
@jwt_required()
def verify_otp():
    data = request.get_json()
    if not data or "otp" not in data:
        return jsonify({"error": "OTP is required"}), 400

    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.otp_secret == data["otp"]:
        user.is_verified = True
        user.otp_secret = None
        db.session.commit()
        return jsonify({"message": "OTP verified successfully"}), 200

    return jsonify({"error": "Invalid OTP"}), 400


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5/hour")
def forgot_password():
    data = request.get_json()
    if not data or "email" not in data:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        return jsonify({"message": "If the email exists, a reset OTP has been sent"}), 200

    user.otp_secret = generate_otp()
    db.session.commit()

    return jsonify({
        "message": "Password reset OTP generated",
        "otp": user.otp_secret,
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("5/hour")
def reset_password():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["email", "otp", "new_password"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"'{field}' is required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or user.otp_secret != data["otp"]:
        return jsonify({"error": "Invalid email or OTP"}), 400

    user.set_password(data["new_password"])
    user.otp_secret = None
    db.session.commit()

    return jsonify({"message": "Password reset successful"}), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "phone" in data:
        user.phone = data["phone"]
    if "password" in data:
        user.set_password(data["password"])

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200
