from datetime import datetime

from backend.extensions import db


class GSTReport(db.Model):
    __tablename__ = "gst_reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_type = db.Column(db.String(20), nullable=False)  # GSTR1, GSTR3B, GSTR9
    period_month = db.Column(db.Integer, nullable=False)
    period_year = db.Column(db.Integer, nullable=False)
    total_taxable_value = db.Column(db.Float, default=0.0)
    total_cgst = db.Column(db.Float, default=0.0)
    total_sgst = db.Column(db.Float, default=0.0)
    total_igst = db.Column(db.Float, default=0.0)
    total_cess = db.Column(db.Float, default=0.0)
    total_tax = db.Column(db.Float, default=0.0)
    total_invoices = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="draft")  # draft, filed, error
    report_data = db.Column(db.JSON, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = db.relationship("Company", backref=db.backref("gst_reports", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("gst_reports", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "report_type": self.report_type,
            "period_month": self.period_month,
            "period_year": self.period_year,
            "total_taxable_value": self.total_taxable_value,
            "total_cgst": self.total_cgst,
            "total_sgst": self.total_sgst,
            "total_igst": self.total_igst,
            "total_cess": self.total_cess,
            "total_tax": self.total_tax,
            "total_invoices": self.total_invoices,
            "status": self.status,
            "report_data": self.report_data,
            "company_id": self.company_id,
            "generated_by": self.generated_by,
            "created_at": self.created_at.isoformat(),
        }
