from datetime import datetime

from backend.extensions import db


class AILog(db.Model):
    __tablename__ = "ai_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.String(100), nullable=False)
    input_data = db.Column(db.Text, nullable=True)
    output_data = db.Column(db.Text, nullable=True)
    model_used = db.Column(db.String(50), nullable=True)
    tokens_used = db.Column(db.Integer, default=0)
    processing_time = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="success")
    error_message = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_file_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("ai_logs", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "processing_time": self.processing_time,
            "status": self.status,
            "error_message": self.error_message,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
        }


class TallyLog(db.Model):
    __tablename__ = "tally_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.String(100), nullable=False)
    request_xml = db.Column(db.Text, nullable=True)
    response_xml = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="success")
    error_message = db.Column(db.Text, nullable=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey("vouchers.id"), nullable=True)
    ledger_id = db.Column(db.Integer, db.ForeignKey("ledgers.id"), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("tally_logs", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "status": self.status,
            "error_message": self.error_message,
            "voucher_id": self.voucher_id,
            "ledger_id": self.ledger_id,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("audit_logs", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "ip_address": self.ip_address,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
        }
