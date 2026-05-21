import enum
from datetime import datetime

from backend.extensions import db


class VoucherType(enum.Enum):
    SALES = "Sales"
    PURCHASE = "Purchase"
    RECEIPT = "Receipt"
    PAYMENT = "Payment"
    JOURNAL = "Journal"
    CONTRA = "Contra"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"


class Voucher(db.Model):
    __tablename__ = "vouchers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    voucher_number = db.Column(db.String(50), nullable=True, index=True)
    voucher_type = db.Column(db.Enum(VoucherType), nullable=False)
    voucher_date = db.Column(db.Date, nullable=False)
    party_name = db.Column(db.String(255), nullable=True)
    debit_ledger = db.Column(db.String(255), nullable=True)
    credit_ledger = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Float, default=0.0)
    narration = db.Column(db.Text, nullable=True)
    gstin = db.Column(db.String(15), nullable=True)
    cgst = db.Column(db.Float, default=0.0)
    sgst = db.Column(db.Float, default=0.0)
    igst = db.Column(db.Float, default=0.0)
    tally_xml = db.Column(db.Text, nullable=True)
    tally_synced = db.Column(db.Boolean, default=False)
    tally_sync_time = db.Column(db.DateTime, nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("vouchers", lazy="dynamic"))
    company = db.relationship("Company", backref=db.backref("vouchers", lazy="dynamic"))
    invoice = db.relationship("Invoice", backref=db.backref("vouchers", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "voucher_number": self.voucher_number,
            "voucher_type": self.voucher_type.value,
            "voucher_date": self.voucher_date.isoformat() if self.voucher_date else None,
            "party_name": self.party_name,
            "debit_ledger": self.debit_ledger,
            "credit_ledger": self.credit_ledger,
            "amount": self.amount,
            "narration": self.narration,
            "gstin": self.gstin,
            "cgst": self.cgst,
            "sgst": self.sgst,
            "igst": self.igst,
            "tally_synced": self.tally_synced,
            "invoice_id": self.invoice_id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }
