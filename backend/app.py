import os
import logging
from datetime import datetime

from flask import Flask, render_template, send_from_directory

from backend.config import config_by_name
from backend.extensions import db, jwt, migrate, cors, limiter


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "static"),
    )
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    limiter.init_app(app)

    logging.basicConfig(level=logging.INFO)

    from backend.api.auth import auth_bp
    from backend.api.upload import upload_bp
    from backend.api.processing import processing_bp
    from backend.api.dashboard import dashboard_bp
    from backend.api.invoices import invoices_bp
    from backend.api.gst import gst_bp
    from backend.api.tally import tally_bp
    from backend.api.users import users_bp
    from backend.api.export import export_bp
    from backend.api.chatbot import chatbot_bp
    from backend.api.whatsapp import whatsapp_bp
    from backend.api.email_automation import email_bp
    from backend.api.companies import companies_bp
    from backend.api.ledgers import ledgers_bp
    from backend.api.vouchers import vouchers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(gst_bp)
    app.register_blueprint(tally_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(ledgers_bp)
    app.register_blueprint(vouchers_bp)

    with app.app_context():
        from backend.models import (
            User, Role, Company, Invoice, UploadedFile,
            Voucher, Ledger, GSTReport, AILog, TallyLog, AuditLog,
        )
        db.create_all()
        _seed_admin(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Frontend routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("auth/login.html")

    @app.route("/register")
    def register_page():
        return render_template("auth/register.html")

    @app.route("/forgot-password")
    def forgot_password_page():
        return render_template("auth/forgot_password.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard/admin.html")

    @app.route("/dashboard/processing")
    def processing_page():
        return render_template("dashboard/processing.html")

    @app.route("/dashboard/gst")
    def gst_page():
        return render_template("dashboard/gst.html")

    @app.route("/dashboard/tally")
    def tally_page():
        return render_template("dashboard/tally.html")

    @app.route("/dashboard/users")
    def users_page():
        return render_template("dashboard/users.html")

    @app.route("/health")
    def health():
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

    return app


def _seed_admin(app):
    from backend.models.user import User, Role
    admin = User.query.filter_by(email="admin@smarttally.ai").first()
    if not admin:
        admin = User(
            email="admin@smarttally.ai",
            full_name="Super Admin",
            role=Role.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
