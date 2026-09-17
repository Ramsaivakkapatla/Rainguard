# 🌾 RainGuard — Offline-First Parametric Crop Insurance

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/framework-Flask%203.1-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 41 Passed](https://img.shields.io/badge/tests-41%20passed-brightgreen.svg)]()

> **Crop protection that works even when the network doesn't.**
> An offline-first parametric insurance platform built for smallholder farmers in low-connectivity rural environments.

---

## 📖 Overview

Smallholder farmers in drought-prone and climate-vulnerable regions frequently suffer devastating crop losses, yet traditional crop insurance programs require weeks of claim verification, paperwork, and continuous internet connectivity that rural farms lack.

**RainGuard** addresses this through:
1. **Parametric Triggering**: Payouts are triggered automatically when verified rainfall falls below predefined thresholds (no manual claims or adjusters needed).
2. **Multi-Oracle Consensus**: Weather data is cross-validated across multiple independent stations with automatic outlier and manipulation detection.
3. **Offline-First Wallet**: Insurance claims, debits, and payouts operate offline on the farmer's device and synchronize automatically when connectivity is restored.
4. **Shared-Device Security**: Multi-farmer device sharing with PIN hashing, session timeouts, and rate limiting.
5. **Accessible Voice Interface**: Voice-assisted navigation and multi-language support designed for low-literacy users.

---

## 🏗️ Architecture

```
                                  ┌───────────────────────────────┐
                                  │    Multi-Oracle Data Feed     │
                                  │   (Stations A, B, C, etc.)    │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
┌──────────────────────┐          ┌───────────────────────────────┐
│                      │          │      Oracle Engine            │
│    Farmer Portal     │ ◄──────► │  • Freshness Verification     │
│   (Web / Mobile)     │          │  • Outlier / Tamper Detection │
│                      │          │  • Median Rainfall Consensus  │
└──────────┬───────────┘          └───────────────┬───────────────┘
           │                                      │
           │                                      ▼
           │                      ┌───────────────────────────────┐
           │                      │      Settlement Engine        │
           │                      │  • Parametric Policy Trigger  │
           │                      │  • Instant Claim Evaluation   │
           │                      └───────────────┬───────────────┘
           │                                      │
           ▼                                      ▼
┌──────────────────────┐          ┌───────────────────────────────┐
│   Offline Wallet     │ ◄──────► │   Sync & Audit Engine         │
│  • Local Balances    │  Offline │  • Event Replay Queue         │
│  • PENDING Txns      │   Sync   │  • Immutable Audit Log        │
└──────────────────────┘          └───────────────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Setup Virtual Environment

```bash
git clone https://github.com/Ramsaivakkapatla/Rainguard.git
cd Rainguard

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Application

```bash
python app.py
```

Visit **http://localhost:5000** in your web browser.

---

## 🧪 Running Unit Tests

RainGuard includes a comprehensive test suite covering the oracle engine, settlement engine, policy configuration, authentication, offline sync, and security layers:

```bash
# Run all tests
python -m pytest tests/ -v

# Run oracle-specific tests
python -m pytest tests/test_oracle.py -v
```

**Result:** `41 passed in ~0.5s`

---

## 🔑 Demo Farmer Credentials

For testing and demonstration, use the pre-configured accounts:

| Farmer ID | PIN | Name | Region |
| :--- | :---: | :--- | :--- |
| `DEMO-FARMER-001` | `1234` | Demo Farmer 1 | Demo District |
| `DEMO-FARMER-002` | `2345` | Demo Farmer 2 | Demo District |
| `DEMO-FARMER-003` | `3456` | Demo Farmer 3 | Demo District |

---

## ☁️ Production Deployment

### Option 1: Deploy on Render (Recommended)

1. Connect your GitHub repository to [Render](https://render.com).
2. Click **New +** -> **Web Service**.
3. Render will automatically detect [`render.yaml`](render.yaml) or configure:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 wsgi:app`
4. Set Environment Variables:
   - `SECRET_KEY`: *(Generate a secure random string)*
   - `FLASK_DEBUG`: `False`

### Option 2: Deploy on Railway

1. Click **New Project** -> **Deploy from GitHub Repo** on [Railway](https://railway.app).
2. Railway will automatically detect the [`Procfile`](Procfile) and [`requirements.txt`](requirements.txt).
3. The service starts automatically with zero extra configuration.

### Option 3: Deploy with Docker

```bash
# Build Docker image
docker build -t rainguard .

# Run container
docker run -d -p 5000:5000 -e SECRET_KEY="your-secret-key" rainguard
```

---

## 📡 API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/products` | `GET` | List active parametric insurance products |
| `/api/oracle/evaluate` | `GET` | Run multi-oracle consensus and return trusted rainfall |
| `/api/oracle/sources` | `GET` | Retrieve status of all weather stations |
| `/api/farmer/check-policy` | `GET` | Retrieve current policy status for authenticated farmer |
| `/api/farmer/activate-policy` | `POST` | Activate crop insurance policy |
| `/api/farmer/settle` | `POST` | Evaluate policy triggers and issue automatic payout |
| `/api/farmer/wallet/balance` | `GET` | Get farmer wallet balance and pending status |
| `/api/farmer/wallet/transactions` | `GET` | List farmer transaction ledger |
| `/api/farmer/sync` | `POST` | Reconcile offline transactions with cloud backend |
| `/api/health` | `GET` | Health check reporting status of all subsystems |

---

## 🛡️ Security & Privacy

- **Shared Device Mode**: Sessions automatically time out after inactivity; brute-force protection locks accounts after 5 failed PIN attempts.
- **Parametric Non-repudiation**: Payout calculations are strictly deterministic based on consensus rainfall vs policy thresholds.
- **Audit Logging**: Every settlement, transaction, and sync event is recorded with cryptographic timestamps in an immutable audit ledger.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
