from datetime import datetime

from backend.extensions import db


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    gstin = db.Column(db.String(15), nullable=True, index=True)
    pan = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    tally_company_name = db.Column(db.String(255), nullable=True)
    tally_connected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "gstin": self.gstin,
            "pan": self.pan,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "phone": self.phone,
            "email": self.email,
            "tally_company_name": self.tally_company_name,
            "tally_connected": self.tally_connected,
            "created_at": self.created_at.isoformat(),
        }
