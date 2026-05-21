from datetime import datetime

from backend.extensions import db


class Ledger(db.Model):
    __tablename__ = "ledgers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    group_name = db.Column(db.String(255), nullable=False)
    parent_group = db.Column(db.String(255), nullable=True)
    gstin = db.Column(db.String(15), nullable=True)
    opening_balance = db.Column(db.Float, default=0.0)
    is_revenue = db.Column(db.Boolean, default=False)
    is_deemed_positive = db.Column(db.Boolean, default=False)
    tally_synced = db.Column(db.Boolean, default=False)
    tally_xml = db.Column(db.Text, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = db.relationship("Company", backref=db.backref("ledgers", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "group_name": self.group_name,
            "parent_group": self.parent_group,
            "gstin": self.gstin,
            "opening_balance": self.opening_balance,
            "is_revenue": self.is_revenue,
            "tally_synced": self.tally_synced,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }
