# TradeSignalAI-v3 🚀

**TradeSignalAI-v3** is an enterprise-grade quantitative trading research, time-series forecasting, and walk-forward validation platform. Built with a zero-trust architecture, it integrates deep-learning time-series forecasting (PyTorch Kronos), smart money concepts (SMC), multi-timeframe indicator ensembles, and prospective paper/shadow trade simulation.

---

## 🌟 Key Architecture & Capabilities

```
       Point-in-Time Market Data (MT5 / TradingView / Synthetic Replay)
                                │
                                ▼
         Feature Engineering & Data Snapshot Hashing (SHA-256)
                                │
                                ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                   Multi-Model Ensemble                        │
  │  • PyTorch Kronos Time-Series Forecasting                     │
  │  • Smart Money Concepts (Order Blocks, FVG, Liquidity)       │
  │  • High-Dimensional Indicator Ensemble (Supertrend, RSI, etc)│
  │  • Multi-Agent Consensus & Calibrated Confidence Scoring      │
  └───────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
           Zero-Trust Risk Engine & Adversarial Failsafes
         (Max Drawdown, Session Gating, Mandatory SL/TP)
                                  │
                                  ▼
         Immutable Shadow-Live Engine & Paper Simulator
     (Strict Real-Money Lockout — 100% Simulated Paper Execution)
                                  │
                                  ▼
     Continuous Walk-Forward Calibration & Edge Drift Telemetry
```

### Core Features
- **Point-in-Time Data Integrity**: Every decision snapshot is cryptographically sealed with SHA-256 hashes of input features, eliminating lookahead and data snooping bias.
- **Kronos Time-Series Forecasting**: Deep learning architecture for prospective price path forecasting across multiple asset horizons.
- **Smart Money & Structural Analytics**: Real-time identification of market regimes, order flow imbalances, fair value gaps, and liquidity sweeps.
- **Fail-Closed Security**: Cryptographic dependencies and secret configuration fail closed; zero plaintext password fallback.
- **Strict Real-Money Lockout**: All execution defaults to paper/shadow simulation. Real-money routing is strictly locked out.

---

## 🛡️ Security & Real-Money Safety Boundary

> [!IMPORTANT]
> **Real-Money Lockout Invariant**: The repository operates strictly in paper simulation and shadow-live validation modes (`EXECUTION_MODE=DEMO`, `REAL_MONEY_ENABLED=false`). Broker adapters reject any attempt to route orders to live execution accounts.
>
> **Zero Secrets Policy**: Credentials must never be committed to source control. All secrets are loaded via environment variables or `.env` (strictly ignored by `.gitignore`).

---

## 🛠️ Getting Started

### 1. Prerequisites
- **Python:** 3.10+ (tested on Python 3.11)
- **Node.js:** 18+ and npm
- **Git**

### 2. Environment Configuration
Copy the safe template to your local `.env`:
```bash
cp .env.example .env
```
Populate your configuration locally in `.env`. Never commit `.env` to source control.

```env
ENVIRONMENT=development
EXECUTION_MODE=DEMO
AUTO_TRADING_ENABLED=true
DEBUG=false
REAL_MONEY_ENABLED=false

# JWT Secret (In production, must be at least 32 characters)
SECRET_KEY=your_development_secret_key_here
```

### 3. Backend Setup
Create and activate a virtual environment, then install dependencies:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

Run the backend development server:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation will be available at `http://127.0.0.1:8000/docs`.

### 4. Frontend Setup
Navigate to the `frontend/` directory, install packages, and launch Vite:
```bash
cd frontend
npm install
npm run dev
```
The user interface will be accessible at `http://localhost:3000`.

To build the production bundle:
```bash
cd frontend
npm run build
```

---

## 🧪 Testing & Validation

### Automated Security Regression Tests
Run the dedicated security hardening test suite:
```bash
pytest tests/test_security_hardening.py -v
```

### Password Fail-Closed Verification
```bash
pytest tests/test_password_fail_closed.py -v
```

### Master Regression Test Suite
Run the full test suite across all models, signals, and validation engines:
```bash
pytest tests/ -q
```

---

## 📁 Repository Structure

```
TradeSignalAI-v3/
├── app/                      # Backend FastAPI Application
│   ├── agents/               # Multi-agent consensus & research council
│   ├── analytics/            # Calibration, drift, and walk-forward engines
│   ├── api/                  # REST and WebSocket endpoints
│   ├── auth/                 # Argon2id / bcrypt password hashing & JWT security
│   ├── config/               # Settings loaded from environment (fails closed)
│   ├── core/                 # Pipeline, market clock, and snapshot manager
│   ├── database/             # SQLAlchemy ORM models and schema migrations
│   ├── execution/            # Execution abstraction & paper simulation adapter
│   ├── forecast/             # PyTorch Kronos time-series forecasting models
│   ├── logs/                 # Structured logging with automatic credential redaction
│   ├── market_data/          # Point-in-time market data providers & stream manager
│   ├── paper_trading/        # High-fidelity trade execution simulator
│   ├── shadow/               # Immutable shadow-live prediction engine
│   └── strategies/           # Quantitative indicators and strategy registry
├── frontend/                 # React + TypeScript + Vite + Tailwind UI
│   ├── src/                  # Source components, stores, and services
│   └── dist/                 # Compiled production assets
├── tests/                    # Unit, integration, and adversarial test suites
├── docs/                     # Architectural specifications and audit reports
├── .env.example              # Safe environment variable template
├── .gitleaks.toml            # Repository-level secret scanner configuration
└── .gitignore                # Zero-trust file exclusion rules
```

---

## 📄 License & Research Disclaimer
TradeSignalAI-v3 is provided for quantitative research, backtesting, and algorithmic evaluation purposes only. It does not provide financial or investment advice.
