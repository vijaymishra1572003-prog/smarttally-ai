import time

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.extensions import db
from backend.models.invoice import UploadedFile, Invoice, FileStatus
from backend.models.voucher import Voucher, VoucherType
from backend.models.ledger import Ledger
from backend.models.logs import AILog
from ai_engine.ocr_engine import OCREngine
from ai_engine.ai_processor import AIProcessor
from tally_api.tally_service import TallyService

processing_bp = Blueprint("processing", __name__, url_prefix="/api/process")


@processing_bp.route("/<int:file_id>", methods=["POST"])
@jwt_required()
def process_file(file_id):
    user_id = int(get_jwt_identity())
    uploaded = UploadedFile.query.filter_by(id=file_id, user_id=user_id).first()
    if not uploaded:
        return jsonify({"error": "File not found"}), 404

    if uploaded.status == FileStatus.COMPLETED:
        return jsonify({"error": "File already processed"}), 400

    uploaded.status = FileStatus.PROCESSING
    db.session.commit()

    start_time = time.time()
    try:
        ocr = OCREngine()
        ocr_text = ocr.extract_text(uploaded.file_path, uploaded.file_type)
        uploaded.ocr_text = ocr_text

        ai = AIProcessor()
        extracted = ai.extract_invoice_data(ocr_text)
        uploaded.ai_result = extracted

        from datetime import date
        invoice_date = None
        if extracted.get("invoice_date"):
            try:
                parts = extracted["invoice_date"].split("-")
                if len(parts) == 3:
                    invoice_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                invoice_date = date.today()
        else:
            invoice_date = date.today()

        invoice = Invoice(
            invoice_number=extracted.get("invoice_number"),
            invoice_date=invoice_date,
            vendor_name=extracted.get("vendor_name"),
            vendor_gstin=extracted.get("vendor_gstin"),
            buyer_name=extracted.get("buyer_name"),
            buyer_gstin=extracted.get("buyer_gstin"),
            subtotal=float(extracted.get("subtotal", 0)),
            cgst=float(extracted.get("cgst", 0)),
            sgst=float(extracted.get("sgst", 0)),
            igst=float(extracted.get("igst", 0)),
            total_gst=float(extracted.get("total_gst", 0)),
            total_amount=float(extracted.get("total_amount", 0)),
            hsn_code=extracted.get("hsn_code"),
            description=extracted.get("description"),
            transaction_type=extracted.get("transaction_type", "Purchase"),
            ledger_category=extracted.get("ledger_category"),
            voucher_type=extracted.get("voucher_type", "Purchase"),
            uploaded_file_id=uploaded.id,
            user_id=user_id,
            company_id=uploaded.company_id,
        )
        db.session.add(invoice)
        db.session.commit()

        voucher_type_map = {
            "Sales": VoucherType.SALES,
            "Purchase": VoucherType.PURCHASE,
            "Receipt": VoucherType.RECEIPT,
            "Payment": VoucherType.PAYMENT,
            "Journal": VoucherType.JOURNAL,
        }
        vtype = voucher_type_map.get(extracted.get("voucher_type", "Purchase"), VoucherType.PURCHASE)

        voucher = Voucher(
            voucher_type=vtype,
            voucher_date=invoice.invoice_date,
            party_name=invoice.vendor_name or invoice.buyer_name,
            debit_ledger=extracted.get("debit_ledger", "Purchase Account"),
            credit_ledger=extracted.get("credit_ledger", invoice.vendor_name or "Creditors"),
            amount=invoice.total_amount,
            narration=f"Auto-generated from invoice {invoice.invoice_number}",
            gstin=invoice.vendor_gstin or invoice.buyer_gstin,
            cgst=invoice.cgst,
            sgst=invoice.sgst,
            igst=invoice.igst,
            invoice_id=invoice.id,
            user_id=user_id,
            company_id=uploaded.company_id,
        )

        tally = TallyService()
        voucher.tally_xml = tally.generate_voucher_xml(voucher, invoice)
        db.session.add(voucher)

        uploaded.status = FileStatus.COMPLETED
        processing_time = time.time() - start_time

        ai_log = AILog(
            action="process_invoice",
            input_data=ocr_text[:500] if ocr_text else None,
            output_data=str(extracted)[:1000],
            model_used="gpt-4o-mini",
            processing_time=processing_time,
            status="success",
            user_id=user_id,
            uploaded_file_id=uploaded.id,
        )
        db.session.add(ai_log)
        db.session.commit()

        return jsonify({
            "message": "File processed successfully",
            "invoice": invoice.to_dict(),
            "voucher": voucher.to_dict(),
            "ocr_preview": ocr_text[:500] if ocr_text else None,
            "processing_time": round(processing_time, 2),
        }), 200

    except Exception as e:
        uploaded.status = FileStatus.FAILED
        ai_log = AILog(
            action="process_invoice",
            status="error",
            error_message=str(e),
            user_id=user_id,
            uploaded_file_id=uploaded.id,
            processing_time=time.time() - start_time,
        )
        db.session.add(ai_log)
        db.session.commit()
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


@processing_bp.route("/bulk", methods=["POST"])
@jwt_required()
def bulk_process():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    file_ids = data.get("file_ids", [])

    if not file_ids:
        return jsonify({"error": "No file IDs provided"}), 400

    results = []
    for fid in file_ids:
        uploaded = UploadedFile.query.filter_by(id=fid, user_id=user_id).first()
        if not uploaded or uploaded.status == FileStatus.COMPLETED:
            continue

        uploaded.status = FileStatus.PROCESSING
        db.session.commit()

        try:
            ocr = OCREngine()
            ocr_text = ocr.extract_text(uploaded.file_path, uploaded.file_type)
            uploaded.ocr_text = ocr_text

            ai = AIProcessor()
            extracted = ai.extract_invoice_data(ocr_text)
            uploaded.ai_result = extracted
            uploaded.status = FileStatus.COMPLETED
            db.session.commit()

            results.append({"file_id": fid, "status": "success", "data": extracted})
        except Exception as e:
            uploaded.status = FileStatus.FAILED
            db.session.commit()
            results.append({"file_id": fid, "status": "error", "error": str(e)})

    return jsonify({"results": results}), 200
