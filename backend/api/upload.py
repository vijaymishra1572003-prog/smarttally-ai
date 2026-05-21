import os
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models.invoice import UploadedFile, FileStatus

upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


@upload_bp.route("/", methods=["POST"])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    original_filename = secure_filename(file.filename)
    file_ext = original_filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    uploaded = UploadedFile(
        filename=unique_filename,
        original_filename=original_filename,
        file_type=file_ext,
        file_size=file_size,
        file_path=file_path,
        status=FileStatus.UPLOADED,
        user_id=int(user_id),
        company_id=request.form.get("company_id", type=int),
    )
    db.session.add(uploaded)
    db.session.commit()

    return jsonify({
        "message": "File uploaded successfully",
        "file": uploaded.to_dict(),
    }), 201


@upload_bp.route("/batch", methods=["POST"])
@jwt_required()
def upload_batch():
    user_id = get_jwt_identity()
    files = request.files.getlist("files")

    if not files:
        return jsonify({"error": "No files provided"}), 400

    results = []
    for file in files:
        if file.filename == "" or not allowed_file(file.filename):
            continue

        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        file_size = os.path.getsize(file_path)

        uploaded = UploadedFile(
            filename=unique_filename,
            original_filename=original_filename,
            file_type=file_ext,
            file_size=file_size,
            file_path=file_path,
            status=FileStatus.UPLOADED,
            user_id=int(user_id),
        )
        db.session.add(uploaded)
        db.session.commit()
        results.append(uploaded.to_dict())

    return jsonify({
        "message": f"{len(results)} files uploaded",
        "files": results,
    }), 201


@upload_bp.route("/", methods=["GET"])
@jwt_required()
def list_files():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = UploadedFile.query.filter_by(user_id=int(user_id))
    status_filter = request.args.get("status")
    if status_filter:
        query = query.filter_by(status=FileStatus(status_filter))

    pagination = query.order_by(UploadedFile.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "files": [f.to_dict() for f in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    }), 200


@upload_bp.route("/<int:file_id>", methods=["GET"])
@jwt_required()
def get_file(file_id):
    user_id = get_jwt_identity()
    uploaded = UploadedFile.query.filter_by(id=file_id, user_id=int(user_id)).first()
    if not uploaded:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"file": uploaded.to_dict()}), 200


@upload_bp.route("/<int:file_id>", methods=["DELETE"])
@jwt_required()
def delete_file(file_id):
    user_id = get_jwt_identity()
    uploaded = UploadedFile.query.filter_by(id=file_id, user_id=int(user_id)).first()
    if not uploaded:
        return jsonify({"error": "File not found"}), 404

    if os.path.exists(uploaded.file_path):
        os.remove(uploaded.file_path)

    db.session.delete(uploaded)
    db.session.commit()
    return jsonify({"message": "File deleted"}), 200
