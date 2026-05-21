import enum
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from backend.extensions import db


class Role(enum.Enum):
    SUPER_ADMIN = "super_admin"
    CA_ADMIN = "ca_admin"
    STAFF_USER = "staff_user"
    CLIENT_USER = "client_user"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.Enum(Role), default=Role.CLIENT_USER, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    otp_secret = db.Column(db.String(32), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    profile_image = db.Column(db.String(500), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = db.relationship("Company", backref=db.backref("users", lazy="dynamic"))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "company_id": self.company_id,
            "profile_image": self.profile_image,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
        }
