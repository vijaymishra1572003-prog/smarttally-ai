import io
import csv
from datetime import datetime

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.models.invoice import Invoice
from backend.models.gst import GSTReport

export_bp = Blueprint("export", __name__, url_prefix="/api/export")


@export_bp.route("/invoices/csv", methods=["GET"])
@jwt_required()
def export_invoices_csv():
    user_id = int(get_jwt_identity())
    invoices = Invoice.query.filter_by(user_id=user_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Invoice No", "Date", "Vendor", "Vendor GSTIN", "Buyer", "Buyer GSTIN",
        "Subtotal", "CGST", "SGST", "IGST", "Total GST", "Total Amount",
        "HSN Code", "Transaction Type", "Ledger Category", "Voucher Type",
        "Tally Synced",
    ])

    for inv in invoices:
        writer.writerow([
            inv.invoice_number, inv.invoice_date, inv.vendor_name,
            inv.vendor_gstin, inv.buyer_name, inv.buyer_gstin,
            inv.subtotal, inv.cgst, inv.sgst, inv.igst, inv.total_gst,
            inv.total_amount, inv.hsn_code, inv.transaction_type,
            inv.ledger_category, inv.voucher_type, inv.tally_synced,
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"invoices_{datetime.utcnow().strftime('%Y%m%d')}.csv",
    )


@export_bp.route("/invoices/excel", methods=["GET"])
@jwt_required()
def export_invoices_excel():
    try:
        import openpyxl
    except ImportError:
        return jsonify({"error": "openpyxl not installed"}), 500

    user_id = int(get_jwt_identity())
    invoices = Invoice.query.filter_by(user_id=user_id).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Invoices"

    headers = [
        "Invoice No", "Date", "Vendor", "Vendor GSTIN", "Buyer", "Buyer GSTIN",
        "Subtotal", "CGST", "SGST", "IGST", "Total GST", "Total Amount",
        "HSN Code", "Transaction Type", "Ledger Category", "Voucher Type",
        "Tally Synced",
    ]
    ws.append(headers)

    for inv in invoices:
        ws.append([
            inv.invoice_number, str(inv.invoice_date) if inv.invoice_date else "",
            inv.vendor_name, inv.vendor_gstin, inv.buyer_name, inv.buyer_gstin,
            inv.subtotal, inv.cgst, inv.sgst, inv.igst, inv.total_gst,
            inv.total_amount, inv.hsn_code, inv.transaction_type,
            inv.ledger_category, inv.voucher_type, str(inv.tally_synced),
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"invoices_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
    )


@export_bp.route("/gst-report/<int:report_id>/pdf", methods=["GET"])
@jwt_required()
def export_gst_pdf(report_id):
    user_id = int(get_jwt_identity())
    report = GSTReport.query.filter_by(id=report_id, generated_by=user_id).first()
    if not report:
        return jsonify({"error": "Report not found"}), 404

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        return jsonify({"error": "reportlab not installed"}), 500

    output = io.BytesIO()
    c = pdf_canvas.Canvas(output, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "SmartTally AI - GST Report")

    c.setFont("Helvetica", 12)
    y = height - 90
    c.drawString(50, y, f"Report Type: {report.report_type}")
    y -= 25
    c.drawString(50, y, f"Period: {report.period_month}/{report.period_year}")
    y -= 25
    c.drawString(50, y, f"Total Taxable Value: Rs. {report.total_taxable_value:,.2f}")
    y -= 25
    c.drawString(50, y, f"CGST: Rs. {report.total_cgst:,.2f}")
    y -= 25
    c.drawString(50, y, f"SGST: Rs. {report.total_sgst:,.2f}")
    y -= 25
    c.drawString(50, y, f"IGST: Rs. {report.total_igst:,.2f}")
    y -= 25
    c.drawString(50, y, f"Total Tax: Rs. {report.total_tax:,.2f}")
    y -= 25
    c.drawString(50, y, f"Total Invoices: {report.total_invoices}")
    y -= 25
    c.drawString(50, y, f"Status: {report.status}")
    y -= 40
    c.drawString(50, y, f"Generated: {report.created_at.strftime('%d-%m-%Y %H:%M')}")

    c.save()
    output.seek(0)

    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"gst_report_{report.report_type}_{report.period_month}_{report.period_year}.pdf",
    )
