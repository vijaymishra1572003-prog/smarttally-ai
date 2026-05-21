from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from backend.extensions import db
from backend.models.invoice import Invoice
from backend.models.gst import GSTReport

gst_bp = Blueprint("gst", __name__, url_prefix="/api/gst")


@gst_bp.route("/summary", methods=["GET"])
@jwt_required()
def gst_summary():
    user_id = int(get_jwt_identity())
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)

    query = Invoice.query.filter_by(user_id=user_id)
    if month and year:
        query = query.filter(
            func.month(Invoice.invoice_date) == month,
            func.year(Invoice.invoice_date) == year,
        )

    total_cgst = db.session.query(func.sum(Invoice.cgst)).filter(
        Invoice.user_id == user_id
    ).scalar() or 0
    total_sgst = db.session.query(func.sum(Invoice.sgst)).filter(
        Invoice.user_id == user_id
    ).scalar() or 0
    total_igst = db.session.query(func.sum(Invoice.igst)).filter(
        Invoice.user_id == user_id
    ).scalar() or 0
    total_gst = db.session.query(func.sum(Invoice.total_gst)).filter(
        Invoice.user_id == user_id
    ).scalar() or 0
    total_taxable = db.session.query(func.sum(Invoice.subtotal)).filter(
        Invoice.user_id == user_id
    ).scalar() or 0

    return jsonify({
        "total_cgst": round(float(total_cgst), 2),
        "total_sgst": round(float(total_sgst), 2),
        "total_igst": round(float(total_igst), 2),
        "total_gst": round(float(total_gst), 2),
        "total_taxable_value": round(float(total_taxable), 2),
    }), 200


@gst_bp.route("/reports", methods=["GET"])
@jwt_required()
def list_reports():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    reports = GSTReport.query.filter_by(generated_by=user_id).order_by(
        GSTReport.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "reports": [r.to_dict() for r in reports.items],
        "total": reports.total,
        "pages": reports.pages,
    }), 200


@gst_bp.route("/reports/generate", methods=["POST"])
@jwt_required()
def generate_report():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or "month" not in data or "year" not in data:
        return jsonify({"error": "Month and year are required"}), 400

    month = data["month"]
    year = data["year"]
    report_type = data.get("report_type", "GSTR3B")
    company_id = data.get("company_id")

    query = Invoice.query.filter_by(user_id=user_id)
    if company_id:
        query = query.filter_by(company_id=company_id)

    query = query.filter(
        func.month(Invoice.invoice_date) == month,
        func.year(Invoice.invoice_date) == year,
    )

    invoices = query.all()

    total_cgst = sum(inv.cgst for inv in invoices)
    total_sgst = sum(inv.sgst for inv in invoices)
    total_igst = sum(inv.igst for inv in invoices)
    total_taxable = sum(inv.subtotal for inv in invoices)
    total_tax = total_cgst + total_sgst + total_igst

    report_data = {
        "invoices": [inv.to_dict() for inv in invoices],
        "hsn_summary": {},
    }

    for inv in invoices:
        hsn = inv.hsn_code or "NA"
        if hsn not in report_data["hsn_summary"]:
            report_data["hsn_summary"][hsn] = {
                "taxable_value": 0, "cgst": 0, "sgst": 0, "igst": 0,
            }
        report_data["hsn_summary"][hsn]["taxable_value"] += inv.subtotal
        report_data["hsn_summary"][hsn]["cgst"] += inv.cgst
        report_data["hsn_summary"][hsn]["sgst"] += inv.sgst
        report_data["hsn_summary"][hsn]["igst"] += inv.igst

    if not company_id:
        company_id = invoices[0].company_id if invoices else 1

    report = GSTReport(
        report_type=report_type,
        period_month=month,
        period_year=year,
        total_taxable_value=total_taxable,
        total_cgst=total_cgst,
        total_sgst=total_sgst,
        total_igst=total_igst,
        total_tax=total_tax,
        total_invoices=len(invoices),
        report_data=report_data,
        company_id=company_id,
        generated_by=user_id,
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({
        "message": "GST report generated",
        "report": report.to_dict(),
    }), 201


@gst_bp.route("/reports/<int:report_id>", methods=["GET"])
@jwt_required()
def get_report(report_id):
    user_id = int(get_jwt_identity())
    report = GSTReport.query.filter_by(id=report_id, generated_by=user_id).first()
    if not report:
        return jsonify({"error": "Report not found"}), 404
    return jsonify({"report": report.to_dict()}), 200
