# SmartTally AI

**AI-Powered Accounting, GST & Tally Automation Platform for CAs, Tax Professionals & Businesses**

SmartTally AI automates invoice processing, GST compliance, and Tally Prime integration using artificial intelligence. Upload invoices (PDF, images, CSV, Excel) and let AI extract data, detect ledgers, calculate GST, create vouchers, and sync directly with Tally Prime.

---

## Features

### Core AI Features
- **PDF/Image OCR** — Dual-engine OCR (PaddleOCR + Tesseract) with 99.5% accuracy
- **AI Data Extraction** — Extracts vendor, GSTIN, amounts, HSN codes, invoice numbers
- **AI Ledger Detection** — Maps vendors to accounting ledgers (e.g., Swiggy → Food Expense)
- **AI Voucher Creation** — Auto-generates Sales, Purchase, Receipt, Payment, Journal vouchers
- **AI GST Detection** — Detects GSTIN, tax rates, CGST/SGST/IGST breakup
- **AI Fraud Detection** — Identifies duplicate invoices, suspicious amounts, date anomalies
- **AI Chatbot** — Natural language queries ("Show March GST report")

### Tally Integration
- Direct Tally Prime XML API integration
- Auto-create ledgers, vouchers, stock items
- Real-time sync with full audit trail
- Fetch existing ledgers and company data

### GST Module
- Complete GST calculation engine
- GSTR-1/3B report generation
- HSN code lookup with tax rates
- Inter/Intra-state tax detection
- Export GST reports as PDF

### Automation
- **WhatsApp** — Send invoices, receive documents for auto-processing
- **Email** — Gmail API integration for auto-scanning invoice emails
- **Bulk Processing** — Process multiple files simultaneously

### Dashboard
- Admin dashboard with analytics charts
- AI processing dashboard with drag-and-drop upload
- GST dashboard with calculator
- Tally integration dashboard with sync status
- User management with role-based access

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, Tailwind CSS, Bootstrap 5, Chart.js |
| Backend | Python Flask, REST API |
| Auth | JWT, Role-based (Super Admin, CA Admin, Staff, Client) |
| Database | SQLAlchemy ORM (MySQL / SQLite) |
| AI | OpenAI GPT-4o-mini, Rule-based fallback |
| OCR | PaddleOCR, Tesseract, pdfplumber |
| Tally | Tally Prime XML API |
| Deploy | Docker, Gunicorn, Render/Railway/AWS |

---

## Quick Start

### Prerequisites
- Python 3.10+
- MySQL (optional, SQLite by default for dev)
- Tally Prime running on `localhost:9000` (for Tally sync)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd smarttally-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your settings

# Run the application
python run.py
```

The app will be available at `http://localhost:5000`

### Default Admin Credentials
- **Email:**
- **Password:*

---

## Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://localhost:5000
```

---

## Project Structure

```
smarttally-ai/
├── backend/
│   ├── api/              # REST API endpoints
│   │   ├── auth.py       # Authentication (Login, Register, OTP, JWT)
│   │   ├── upload.py     # File upload (single & batch)
│   │   ├── processing.py # AI processing pipeline
│   │   ├── dashboard.py  # Dashboard analytics
│   │   ├── invoices.py   # Invoice CRUD
│   │   ├── vouchers.py   # Voucher CRUD
│   │   ├── ledgers.py    # Ledger CRUD
│   │   ├── gst.py        # GST reports
│   │   ├── tally.py      # Tally sync
│   │   ├── users.py      # User management
│   │   ├── export.py     # CSV/Excel/PDF export
│   │   ├── chatbot.py    # AI chatbot
│   │   ├── whatsapp.py   # WhatsApp automation
│   │   ├── email_automation.py  # Email automation
│   │   └── companies.py  # Company management
│   ├── models/           # SQLAlchemy models
│   ├── app.py            # Flask app factory
│   ├── config.py         # Configuration
│   └── extensions.py     # Flask extensions
├── ai_engine/
│   ├── ocr_engine.py     # Multi-engine OCR processor
│   ├── ai_processor.py   # AI data extraction & classification
│   └── fraud_detector.py # AI fraud detection
├── tally_api/
│   └── tally_service.py  # Tally Prime XML API service
├── gst_module/
│   └── gst_calculator.py # GST calculation engine
├── chatbot/
│   └── chatbot_service.py # AI chatbot service
├── frontend/
│   ├── templates/        # Jinja2 HTML templates
│   │   ├── index.html    # Landing page
│   │   ├── base.html     # Base template
│   │   ├── auth/         # Login, Register, Forgot Password
│   │   ├── dashboard/    # Admin, Processing, GST, Tally, Users
│   │   └── components/   # Sidebar, chatbot modal
│   └── static/
│       ├── css/style.css  # Custom styles (glassmorphism, animations)
│       └── js/app.js      # Frontend JavaScript
├── uploads/              # Uploaded files directory
├── requirements.txt
├── run.py               # Dev server entry point
├── wsgi.py              # Production WSGI entry point
├── Dockerfile
├── docker-compose.yml
├── Procfile             # Render/Railway deployment
└── .env.example
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/verify-otp` | Verify OTP |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Reset password |
| POST | `/api/auth/refresh` | Refresh JWT token |
| GET | `/api/auth/me` | Get current user |

### File Processing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/` | Upload file |
| POST | `/api/upload/batch` | Upload multiple files |
| GET | `/api/upload/` | List uploaded files |
| POST | `/api/process/{id}` | Process file with AI |
| POST | `/api/process/bulk` | Bulk process files |

### Invoices & Vouchers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/invoices/` | List invoices |
| GET/PUT/DELETE | `/api/invoices/{id}` | CRUD operations |
| GET | `/api/vouchers/` | List vouchers |

### GST
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/gst/summary` | GST summary |
| GET | `/api/gst/reports` | List GST reports |
| POST | `/api/gst/reports/generate` | Generate GST report |

### Tally
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tally/status` | Check Tally connection |
| POST | `/api/tally/sync/voucher/{id}` | Sync voucher to Tally |
| POST | `/api/tally/sync/bulk` | Bulk sync |
| GET | `/api/tally/logs` | Sync logs |

### Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export/invoices/csv` | Export CSV |
| GET | `/api/export/invoices/excel` | Export Excel |
| GET | `/api/export/gst-report/{id}/pdf` | Export GST PDF |

### Chatbot
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chatbot/query` | AI chatbot query |

---

## User Roles

| Role | Permissions |
|------|------------|
| Super Admin | Full access to all features |
| CA Admin | Manage users, companies, full accounting |
| Staff User | Upload, process, view reports |
| Client User | View own data only |

---

## Deployment

### Render
1. Push to GitHub
2. Create new Web Service on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn wsgi:app`
5. Add environment variables from `.env.example`

### Railway
1. Connect GitHub repo
2. Railway auto-detects Python + Procfile
3. Add environment variables
4. Deploy

### AWS (EC2)
```bash
# Install dependencies
sudo apt update && sudo apt install python3-pip python3-venv nginx
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4 --daemon
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Optional |
| `TALLY_URL` | Tally Prime URL (default: localhost:9000) | Optional |
| `MAIL_USERNAME` | Gmail username | Optional |
| `MAIL_PASSWORD` | Gmail app password | Optional |
| `WHATSAPP_API_KEY` | WhatsApp API key | Optional |

---

## License

MIT License. Built with AI by SmartTally AI team.
