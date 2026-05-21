from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from backend.extensions import db
from backend.models.invoice import Invoice, UploadedFile, FileStatus
from backend.models.voucher import Voucher
from backend.models.gst import GSTReport
from backend.models.logs import AILog, TallyLog, AuditLog
from backend.models.user import User, Role

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user.role in (Role.SUPER_ADMIN, Role.CA_ADMIN):
        total_invoices = Invoice.query.count()
        total_files = UploadedFile.query.count()
        processed_files = UploadedFile.query.filter_by(status=FileStatus.COMPLETED).count()
        pending_files = UploadedFile.query.filter_by(status=FileStatus.UPLOADED).count()
        failed_files = UploadedFile.query.filter_by(status=FileStatus.FAILED).count()
        total_vouchers = Voucher.query.count()
        synced_vouchers = Voucher.query.filter_by(tally_synced=True).count()
        total_users = User.query.count()
    else:
        total_invoices = Invoice.query.filter_by(user_id=user_id).count()
        total_files = UploadedFile.query.filter_by(user_id=user_id).count()
        processed_files = UploadedFile.query.filter_by(user_id=user_id, status=FileStatus.COMPLETED).count()
        pending_files = UploadedFile.query.filter_by(user_id=user_id, status=FileStatus.UPLOADED).count()
        failed_files = UploadedFile.query.filter_by(user_id=user_id, status=FileStatus.FAILED).count()
        total_vouchers = Voucher.query.filter_by(user_id=user_id).count()
        synced_vouchers = Voucher.query.filter_by(user_id=user_id, tally_synced=True).count()
        total_users = 0

    total_gst = db.session.query(func.sum(Invoice.total_gst)).scalar() or 0
    total_revenue = db.session.query(func.sum(Invoice.total_amount)).scalar() or 0

    return jsonify({
        "total_invoices": total_invoices,
        "total_files": total_files,
        "processed_files": processed_files,
        "pending_files": pending_files,
        "failed_files": failed_files,
        "total_vouchers": total_vouchers,
        "synced_vouchers": synced_vouchers,
        "total_gst": round(total_gst, 2),
        "total_revenue": round(total_revenue, 2),
        "total_users": total_users,
    }), 200


@dashboard_bp.route("/recent-activity", methods=["GET"])
@jwt_required()
def recent_activity():
    user_id = int(get_jwt_identity())
    limit = request.args.get("limit", 10, type=int)

    activities = AuditLog.query.filter_by(user_id=user_id).order_by(
        AuditLog.created_at.desc()
    ).limit(limit).all()

    return jsonify({
        "activities": [a.to_dict() for a in activities],
    }), 200


@dashboard_bp.route("/charts/monthly-revenue", methods=["GET"])
@jwt_required()
def monthly_revenue():
    year = request.args.get("year", datetime.utcnow().year, type=int)

    results = db.session.query(
        func.month(Invoice.created_at).label("month"),
        func.sum(Invoice.total_amount).label("total"),
        func.sum(Invoice.total_gst).label("gst"),
    ).filter(
        func.year(Invoice.created_at) == year
    ).group_by(
        func.month(Invoice.created_at)
    ).all()

    months = {r.month: {"revenue": float(r.total or 0), "gst": float(r.gst or 0)} for r in results}
    chart_data = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i in range(1, 13):
        data = months.get(i, {"revenue": 0, "gst": 0})
        chart_data.append({
            "month": month_names[i - 1],
            "revenue": data["revenue"],
            "gst": data["gst"],
        })

    return jsonify({"chart_data": chart_data}), 200


@dashboard_bp.route("/charts/processing-stats", methods=["GET"])
@jwt_required()
def processing_stats():
    total = UploadedFile.query.count()
    completed = UploadedFile.query.filter_by(status=FileStatus.COMPLETED).count()
    failed = UploadedFile.query.filter_by(status=FileStatus.FAILED).count()
    processing = UploadedFile.query.filter_by(status=FileStatus.PROCESSING).count()
    uploaded = UploadedFile.query.filter_by(status=FileStatus.UPLOADED).count()

    return jsonify({
        "total": total,
        "completed": completed,
        "failed": failed,
        "processing": processing,
        "uploaded": uploaded,
    }), 200


@dashboard_bp.route("/error-logs", methods=["GET"])
@jwt_required()
def error_logs():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    logs = AILog.query.filter_by(status="error").order_by(
        AILog.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "logs": [l.to_dict() for l in logs.items],
        "total": logs.total,
        "pages": logs.pages,
    }), 200
