import enum
from datetime import datetime

from backend.extensions import db


class FileStatus(enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadedFile(db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    file_path = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.Enum(FileStatus), default=FileStatus.UPLOADED)
    ocr_text = db.Column(db.Text, nullable=True)
    ai_result = db.Column(db.JSON, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("uploaded_files", lazy="dynamic"))
    company = db.relationship("Company", backref=db.backref("uploaded_files", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status.value,
            "ocr_text": self.ocr_text,
            "ai_result": self.ai_result,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_number = db.Column(db.String(100), nullable=True, index=True)
    invoice_date = db.Column(db.Date, nullable=True)
    vendor_name = db.Column(db.String(255), nullable=True)
    vendor_gstin = db.Column(db.String(15), nullable=True)
    buyer_name = db.Column(db.String(255), nullable=True)
    buyer_gstin = db.Column(db.String(15), nullable=True)
    subtotal = db.Column(db.Float, default=0.0)
    cgst = db.Column(db.Float, default=0.0)
    sgst = db.Column(db.Float, default=0.0)
    igst = db.Column(db.Float, default=0.0)
    total_gst = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    hsn_code = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    transaction_type = db.Column(db.String(50), nullable=True)
    ledger_category = db.Column(db.String(100), nullable=True)
    voucher_type = db.Column(db.String(50), nullable=True)
    tally_synced = db.Column(db.Boolean, default=False)
    tally_sync_time = db.Column(db.DateTime, nullable=True)
    uploaded_file_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("invoices", lazy="dynamic"))
    company = db.relationship("Company", backref=db.backref("invoices", lazy="dynamic"))
    uploaded_file = db.relationship("UploadedFile", backref=db.backref("invoices", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "vendor_name": self.vendor_name,
            "vendor_gstin": self.vendor_gstin,
            "buyer_name": self.buyer_name,
            "buyer_gstin": self.buyer_gstin,
            "subtotal": self.subtotal,
            "cgst": self.cgst,
            "sgst": self.sgst,
            "igst": self.igst,
            "total_gst": self.total_gst,
            "total_amount": self.total_amount,
            "hsn_code": self.hsn_code,
            "description": self.description,
            "transaction_type": self.transaction_type,
            "ledger_category": self.ledger_category,
            "voucher_type": self.voucher_type,
            "tally_synced": self.tally_synced,
            "uploaded_file_id": self.uploaded_file_id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }
